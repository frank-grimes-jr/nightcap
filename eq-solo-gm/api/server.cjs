const express = require('express')
const mysql = require('mysql2/promise')
const cors = require('cors')
const fs = require('fs')

const CLIENT_INI_PATH =
  'E:\\eq_local_dev\\Client_RoF2_Dev\\everquest_rof2\\eqclient.ini'

function getExpansionClientSettings(expansionId) {
  const useLuclin = expansionId >= 3
  return {
    AllLuclinPcModelsOff: useLuclin ? 'FALSE' : 'TRUE',
    modelsLabel: useLuclin ? '3D Luclin models' : 'Classic 2D models',
  }
}

function readIni() {
  try {
    return fs.readFileSync(CLIENT_INI_PATH, 'utf8')
  } catch {
    return null
  }
}

function currentLuclinSetting(iniContent) {
  return iniContent?.match(/^AllLuclinPcModelsOff=(.*)$/m)?.[1]?.trim() ?? null
}

const app = express()
app.use(express.json())
app.use(cors())

const pool = mysql.createPool({
  host: 'localhost',
  port: 3307,
  user: 'eqemu',
  password: 'eqemu',
  database: 'peq',
  waitForConnections: true,
  connectionLimit: 10,
})

// ── Characters ────────────────────────────────────────────────────────────────

app.get('/api/characters', async (req, res) => {
  try {
    const [rows] = await pool.query(`
      SELECT cd.id, cd.name, cd.level, cd.class, cd.race, cd.zone_id,
             cd.aa_points, cd.aa_points_spent, cd.exp, cd.str, cd.sta,
             cd.agi, cd.dex, cd.wis, cd.int, cd.cha, cd.cur_hp, cd.mana,
             cc.platinum, cc.gold, cc.silver, cc.copper,
             cc.platinum_bank, cc.gold_bank
      FROM character_data cd
      LEFT JOIN character_currency cc ON cc.id = cd.id
      WHERE cd.deleted_at IS NULL
      ORDER BY cd.name
      LIMIT 500
    `)
    res.json(rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Level Boost ───────────────────────────────────────────────────────────────

app.post('/api/character/:id/boost', async (req, res) => {
  const { id } = req.params
  const { level } = req.body
  if (!level || level < 1 || level > 125)
    return res.status(400).json({ error: 'Invalid level' })
  try {
    const [[maxLvlRow]] = await pool.query(
      "SELECT rule_value FROM rule_values WHERE rule_name = 'Character:MaxLevel' AND ruleset_id = 1 LIMIT 1"
    )
    const maxLevel = parseInt(maxLvlRow?.rule_value ?? '125')
    const clampedLevel = Math.min(level, maxLevel)
    await pool.query(
      `UPDATE character_data SET level = ?, exp = 0, level2 = ? WHERE id = ?`,
      [clampedLevel, clampedLevel, id]
    )
    res.json({
      success: true,
      level: clampedLevel,
      capped: clampedLevel < level,
      maxLevel,
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Currency ──────────────────────────────────────────────────────────────────

app.post('/api/character/:id/currency', async (req, res) => {
  const { id } = req.params
  const { platinum } = req.body
  if (!platinum || platinum < 1)
    return res.status(400).json({ error: 'Invalid amount' })
  try {
    await pool.query(
      `
      INSERT INTO character_currency (id, platinum, gold, silver, copper,
        platinum_bank, gold_bank, silver_bank, copper_bank,
        platinum_cursor, gold_cursor, silver_cursor, copper_cursor,
        radiant_crystals, career_radiant_crystals, ebon_crystals, career_ebon_crystals)
      VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
      ON DUPLICATE KEY UPDATE platinum = platinum + ?
    `,
      [id, platinum, platinum]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── AA Points ─────────────────────────────────────────────────────────────────

app.post('/api/character/:id/aa', async (req, res) => {
  const { id } = req.params
  const { points } = req.body
  if (!points || points < 1)
    return res.status(400).json({ error: 'Invalid points' })
  try {
    await pool.query(
      `UPDATE character_data SET aa_points = aa_points + ? WHERE id = ?`,
      [points, id]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Max Skills ────────────────────────────────────────────────────────────────

app.post('/api/character/:id/maxskills', async (req, res) => {
  const { id } = req.params
  try {
    const [[char]] = await pool.query(
      `SELECT class, level FROM character_data WHERE id = ?`,
      [id]
    )
    if (!char) return res.status(404).json({ error: 'Character not found' })

    const [skillCaps] = await pool.query(
      `
      SELECT skill_id, MAX(cap) AS max_cap
      FROM skill_caps
      WHERE class_id = ? AND level <= ?
      GROUP BY skill_id
    `,
      [char.class, char.level]
    )

    for (const sc of skillCaps) {
      await pool.query(
        `
        INSERT INTO character_skills (id, skill_id, value)
        VALUES (?, ?, ?)
        ON DUPLICATE KEY UPDATE value = VALUES(value)
      `,
        [id, sc.skill_id, sc.max_cap]
      )
    }

    res.json({ success: true, updated: skillCaps.length })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Teleport ──────────────────────────────────────────────────────────────────

app.post('/api/character/:id/teleport', async (req, res) => {
  const { id } = req.params
  const { zone_id, x, y, z } = req.body
  if (!zone_id) return res.status(400).json({ error: 'Missing zone_id' })
  try {
    await pool.query(
      `UPDATE character_data SET zone_id = ?, x = ?, y = ?, z = ?, heading = 0 WHERE id = ?`,
      [zone_id, x || 0, y || 0, z || 0, id]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Zones ─────────────────────────────────────────────────────────────────────

app.get('/api/zones', async (req, res) => {
  try {
    const [rows] = await pool.query(`
      SELECT id, short_name, long_name, safe_x, safe_y, safe_z
      FROM zone
      WHERE long_name != '' AND long_name IS NOT NULL
      ORDER BY long_name
      LIMIT 1000
    `)
    res.json(rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Server Rules ──────────────────────────────────────────────────────────────

const TRACKED_RULES = [
  'Character:ExpMultiplier',
  'Character:AAExpMultiplier',
  'AA:ExpPerPoint',
  'Zone:GlobalLootMultiplier',
  'Character:DeathExpLossMult',
  'Zone:LootQuantityMult',
  'Zone:MinimumHPForKnockback',
]

app.get('/api/rules', async (req, res) => {
  try {
    const placeholders = TRACKED_RULES.map(() => '?').join(',')
    const [rows] = await pool.query(
      `SELECT ruleset_id, rule_name, rule_value, notes
       FROM rule_values
       WHERE rule_name IN (${placeholders})
       GROUP BY rule_name
       HAVING MIN(ruleset_id)`,
      TRACKED_RULES
    )
    res.json(rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.patch('/api/rules/:name', async (req, res) => {
  const ruleName = decodeURIComponent(req.params.name)
  const { value } = req.body
  if (value === undefined)
    return res.status(400).json({ error: 'Missing value' })
  try {
    const [result] = await pool.query(
      `UPDATE rule_values SET rule_value = ? WHERE rule_name = ?`,
      [String(value), ruleName]
    )
    res.json({ success: true, affected: result.affectedRows })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Expansion Lock ────────────────────────────────────────────────────────────

const EXPANSION_DEFS = [
  { id: 0, name: 'Classic', short: 'Classic', max_level: 50, year: 1999 },
  {
    id: 1,
    name: 'Ruins of Kunark',
    short: 'Kunark',
    max_level: 60,
    year: 2000,
  },
  {
    id: 2,
    name: 'Scars of Velious',
    short: 'Velious',
    max_level: 60,
    year: 2000,
  },
  {
    id: 3,
    name: 'Shadows of Luclin',
    short: 'Luclin',
    max_level: 65,
    year: 2001,
  },
  { id: 4, name: 'Planes of Power', short: 'PoP', max_level: 65, year: 2002 },
  { id: 5, name: 'Legacy of Ykesha', short: 'LoY', max_level: 65, year: 2003 },
  {
    id: 6,
    name: 'Lost Dungeons of Norrath',
    short: 'LDoN',
    max_level: 65,
    year: 2003,
  },
  { id: 7, name: 'Gates of Discord', short: 'GoD', max_level: 65, year: 2004 },
  { id: 8, name: 'Omens of War', short: 'OoW', max_level: 70, year: 2004 },
  {
    id: 9,
    name: 'Dragons of Norrath',
    short: 'DoN',
    max_level: 70,
    year: 2005,
  },
  {
    id: 10,
    name: 'Depths of Darkhollow',
    short: 'DoDH',
    max_level: 70,
    year: 2005,
  },
  { id: 11, name: 'Prophecy of Ro', short: 'PoR', max_level: 75, year: 2006 },
  { id: 12, name: "Serpent's Spine", short: 'TSS', max_level: 75, year: 2006 },
  { id: 13, name: 'The Buried Sea', short: 'TBS', max_level: 75, year: 2007 },
  {
    id: 14,
    name: 'Secrets of Faydwer',
    short: 'SoF',
    max_level: 80,
    year: 2007,
  },
  {
    id: 15,
    name: 'Seeds of Destruction',
    short: 'SoD',
    max_level: 85,
    year: 2009,
  },
  { id: 16, name: 'Underfoot', short: 'UF', max_level: 85, year: 2009 },
  { id: 17, name: 'House of Thule', short: 'HoT', max_level: 90, year: 2010 },
  { id: 18, name: 'Veil of Alaris', short: 'VoA', max_level: 95, year: 2011 },
  { id: 19, name: 'Rain of Fear', short: 'RoF', max_level: 100, year: 2012 },
]

app.get('/api/expansion/status', async (req, res) => {
  try {
    const [[expRule]] = await pool.query(
      "SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion' AND ruleset_id = 1 LIMIT 1"
    )
    const [[maxLvlRule]] = await pool.query(
      "SELECT rule_value FROM rule_values WHERE rule_name = 'Character:MaxLevel' AND ruleset_id = 1 LIMIT 1"
    )
    const id = parseInt(expRule?.rule_value ?? '0')
    const exp = EXPANSION_DEFS.find((e) => e.id === id)
    res.json({
      expansion_id: id,
      expansion_name: exp?.name ?? 'Unknown',
      expansion_short: exp?.short ?? '?',
      max_level: parseInt(maxLvlRule?.rule_value ?? '0'),
      year: exp?.year ?? null,
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.get('/api/expansion/:id/preview', async (req, res) => {
  const targetId = parseInt(req.params.id)
  const target = EXPANSION_DEFS.find((e) => e.id === targetId)
  if (!target) return res.status(400).json({ error: 'Invalid expansion' })
  try {
    const [[expRule]] = await pool.query(
      "SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion' AND ruleset_id = 1 LIMIT 1"
    )
    const [[maxLvlRule]] = await pool.query(
      "SELECT rule_value FROM rule_values WHERE rule_name = 'Character:MaxLevel' AND ruleset_id = 1 LIMIT 1"
    )
    const [[lockedZoneCount]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM zone WHERE expansion > ? AND bypass_expansion_check = 0',
      [targetId]
    )
    const [[addedZoneCount]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM zone WHERE expansion = ?',
      [targetId]
    )
    const [lockedZones] = await pool.query(
      `SELECT long_name, short_name, expansion FROM zone
       WHERE expansion > ? AND bypass_expansion_check = 0
       ORDER BY expansion, long_name LIMIT 300`,
      [targetId]
    )
    const [addedZones] = await pool.query(
      'SELECT long_name, short_name FROM zone WHERE expansion = ? ORDER BY long_name',
      [targetId]
    )
    const [[hiddenAAs]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM aa_ranks WHERE expansion > ?',
      [targetId]
    )
    const [[accessibleAAs]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM aa_ranks WHERE expansion <= ?',
      [targetId]
    )
    const [[charsOverCap]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM character_data WHERE level > ? AND deleted_at IS NULL',
      [target.max_level]
    )
    // Zone breakdown by expansion for locked zones
    const [zonesByExp] = await pool.query(
      `SELECT expansion, COUNT(*) as count FROM zone
       WHERE expansion > ? AND bypass_expansion_check = 0
       GROUP BY expansion ORDER BY expansion`,
      [targetId]
    )

    const iniContent = readIni()
    const currentModelSetting = currentLuclinSetting(iniContent)
    const targetClient = getExpansionClientSettings(targetId)

    res.json({
      target,
      current_expansion_id: parseInt(expRule?.rule_value ?? '0'),
      current_max_level: parseInt(maxLvlRule?.rule_value ?? '0'),
      locked_zone_count: lockedZoneCount.cnt,
      added_zone_count: addedZoneCount.cnt,
      locked_zones: lockedZones,
      added_zones: addedZones,
      zones_by_exp: zonesByExp,
      hidden_aa_count: hiddenAAs.cnt,
      accessible_aa_count: accessibleAAs.cnt,
      chars_over_cap: charsOverCap.cnt,
      client: {
        current_all_luclin_off: currentModelSetting,
        target_all_luclin_off: targetClient.AllLuclinPcModelsOff,
        models_label: targetClient.modelsLabel,
        will_change:
          currentModelSetting !== null &&
          currentModelSetting.toUpperCase() !==
            targetClient.AllLuclinPcModelsOff,
        ini_found: iniContent !== null,
      },
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.post('/api/expansion/apply', async (req, res) => {
  const { expansion_id } = req.body
  const target = EXPANSION_DEFS.find((e) => e.id === expansion_id)
  if (!target) return res.status(400).json({ error: 'Invalid expansion' })
  try {
    const changes = []

    await pool.query(
      "UPDATE rule_values SET rule_value = ? WHERE rule_name = 'Expansion:CurrentExpansion' AND ruleset_id = 1",
      [String(expansion_id)]
    )
    changes.push({
      icon: '🌍',
      label: `Expansion:CurrentExpansion → ${expansion_id} (${target.name})`,
    })

    await pool.query(
      "UPDATE rule_values SET rule_value = ? WHERE rule_name IN ('Character:MaxLevel','Character:MaxExpLevel') AND ruleset_id = 1",
      [String(target.max_level)]
    )
    changes.push({ icon: '📊', label: `Level cap → ${target.max_level}` })

    // AAs are intentionally NOT era-gated on this server (multiclass system grants
    // access to many classes' AAs at level 1). Keep UseCurrentExpansionAAOnly=false
    // so the era lock governs zones + level cap only, not AA visibility.
    // ponytail: flip to 'true' here if you ever want era-authentic AA gating.
    await pool.query(
      "UPDATE rule_values SET rule_value = 'false' WHERE rule_name = 'Expansion:UseCurrentExpansionAAOnly' AND ruleset_id = 1"
    )
    changes.push({
      icon: '✨',
      label: 'AA visibility left open (UseCurrentExpansionAAOnly=false)',
    })

    const [[lockedZ]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM zone WHERE expansion > ? AND bypass_expansion_check = 0',
      [expansion_id]
    )
    changes.push({
      icon: '🗺️',
      label: `${lockedZ.cnt} zones locked (expansion > ${expansion_id})`,
    })

    const [[hiddenAA]] = await pool.query(
      'SELECT COUNT(*) as cnt FROM aa_ranks WHERE expansion > ?',
      [expansion_id]
    )
    changes.push({
      icon: '✨',
      label: `${hiddenAA.cnt} AA ranks hidden (expansion > ${expansion_id})`,
    })

    const [capResult] = await pool.query(
      'UPDATE character_data SET level = ?, level2 = ?, exp = 0 WHERE level > ? AND deleted_at IS NULL',
      [target.max_level, target.max_level, target.max_level]
    )
    if (capResult.affectedRows > 0) {
      changes.push({
        icon: '⚔️',
        label: `${capResult.affectedRows} character(s) capped to level ${target.max_level}`,
      })
      changes.push({
        icon: '⚠️',
        label: `If any capped characters were online when this ran, their level will revert on logout — log them out now and re-apply.`,
        warning: true,
      })
    }

    // MOTD
    const motd = `[LocalDev] Era: ${target.name} (${target.short}) — Level Cap ${target.max_level} — ${target.year}`
    await pool.query("UPDATE variables SET value = ? WHERE varname = 'MOTD'", [
      motd,
    ])
    changes.push({ icon: '📢', label: `MOTD → "${motd}"` })

    // Client-side: update eqclient.ini model setting
    const clientTarget = getExpansionClientSettings(expansion_id)
    try {
      let iniContent = readIni()
      if (iniContent !== null) {
        const current = currentLuclinSetting(iniContent)
        if (
          current !== null &&
          current.toUpperCase() !== clientTarget.AllLuclinPcModelsOff
        ) {
          iniContent = iniContent.replace(
            /^AllLuclinPcModelsOff=.*$/m,
            `AllLuclinPcModelsOff=${clientTarget.AllLuclinPcModelsOff}`
          )
          fs.writeFileSync(CLIENT_INI_PATH, iniContent, 'utf8')
          changes.push({
            icon: '🖥',
            label: `eqclient.ini: AllLuclinPcModelsOff → ${clientTarget.AllLuclinPcModelsOff} (${clientTarget.modelsLabel})`,
          })
        } else {
          changes.push({
            icon: '🖥',
            label: `eqclient.ini: ${clientTarget.modelsLabel} already set, no change needed`,
          })
        }
      }
    } catch (iniErr) {
      changes.push({
        icon: '⚠',
        label: `Client INI update skipped: ${iniErr.message}`,
      })
    }

    // Rebuild spell vendor stock for the new expansion
    try {
      const vendorResults = await refreshSpellVendors(expansion_id)
      const totalScrolls = vendorResults.reduce((s, a) => s + a.count, 0)
      changes.push({
        icon: '📜',
        label: `Spell vendors refreshed: ${totalScrolls} scrolls across ${vendorResults.length} archetypes`,
      })
    } catch (vendorErr) {
      changes.push({
        icon: '⚠️',
        label: `Spell vendor refresh failed: ${vendorErr.message}`,
        warning: true,
      })
    }

    res.json({ success: true, expansion: target, changes })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.get('/api/expansions', (_req, res) => res.json(EXPANSION_DEFS))

// ── Client Settings ───────────────────────────────────────────────────────────

app.get('/api/client/settings', (_req, res) => {
  const iniContent = readIni()
  if (!iniContent)
    return res
      .status(404)
      .json({ error: 'eqclient.ini not found', path: CLIENT_INI_PATH })
  const allOff = currentLuclinSetting(iniContent) ?? 'FALSE'
  res.json({
    AllLuclinPcModelsOff: allOff,
    usingLuclinModels: allOff.toUpperCase() !== 'TRUE',
  })
})

app.patch('/api/client/settings', (req, res) => {
  const { AllLuclinPcModelsOff } = req.body
  const val = String(AllLuclinPcModelsOff ?? '').toUpperCase()
  if (val !== 'TRUE' && val !== 'FALSE')
    return res.status(400).json({ error: 'Must be TRUE or FALSE' })
  try {
    let iniContent = readIni()
    if (!iniContent)
      return res.status(404).json({ error: 'eqclient.ini not found' })
    iniContent = iniContent.replace(
      /^AllLuclinPcModelsOff=.*$/m,
      `AllLuclinPcModelsOff=${val}`
    )
    fs.writeFileSync(CLIENT_INI_PATH, iniContent, 'utf8')
    res.json({ success: true, AllLuclinPcModelsOff: val })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── MOTD ─────────────────────────────────────────────────────────────────────

app.get('/api/motd', async (_req, res) => {
  try {
    const [[row]] = await pool.query(
      "SELECT value FROM variables WHERE varname = 'MOTD' LIMIT 1"
    )
    res.json({ motd: row?.value ?? '' })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.patch('/api/motd', async (req, res) => {
  const { motd } = req.body
  if (typeof motd !== 'string')
    return res.status(400).json({ error: 'Missing motd string' })
  try {
    await pool.query("UPDATE variables SET value = ? WHERE varname = 'MOTD'", [
      motd,
    ])
    res.json({ success: true, motd })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Progression Tracking ─────────────────────────────────────────────────────

const PROGRESSION_BOSSES = [
  {
    expansion_id: 0,
    short: 'Classic',
    bosses: [
      {
        key: 'classic_nagafen',
        name: 'Lord Nagafen',
        zone: "Nagafen's Lair",
        zone_short: 'soldungb',
      },
      {
        key: 'classic_vox',
        name: 'Lady Vox',
        zone: 'Permafrost Keep',
        zone_short: 'permafrost',
      },
      {
        key: 'classic_cazic',
        name: 'Cazic-Thule',
        zone: 'Plane of Fear',
        zone_short: 'fearplane',
      },
      {
        key: 'classic_innoruuk',
        name: 'Innoruuk',
        zone: 'Plane of Hate',
        zone_short: 'hateplane',
      },
      {
        key: 'classic_phinigel',
        name: 'Phinigel Autropos',
        zone: 'Kedge Keep',
        zone_short: 'kedge',
      },
    ],
  },
  {
    expansion_id: 1,
    short: 'Kunark',
    bosses: [
      {
        key: 'kunark_venril',
        name: 'Venril Sathir',
        zone: "Karnor's Castle",
        zone_short: 'karnor',
      },
      {
        key: 'kunark_trakanon',
        name: 'Trakanon',
        zone: 'Old Sebilis',
        zone_short: 'sebilis',
      },
      {
        key: 'kunark_gorenaire',
        name: 'Gorenaire',
        zone: 'Dreadlands',
        zone_short: 'dreadlands',
      },
      {
        key: 'kunark_severilous',
        name: 'Severilous',
        zone: 'Emerald Jungle',
        zone_short: 'emeraldjungle',
      },
      {
        key: 'kunark_talendor',
        name: 'Talendor',
        zone: 'Skyfire Mountains',
        zone_short: 'skyfire',
      },
      {
        key: 'kunark_pharadar',
        name: 'Phara Dar',
        zone: "Veeshan's Peak",
        zone_short: 'vp',
      },
    ],
  },
  {
    expansion_id: 2,
    short: 'Velious',
    bosses: [
      {
        key: 'velious_tormax',
        name: 'King Tormax',
        zone: 'Kael Drakkel',
        zone_short: 'kael',
      },
      {
        key: 'velious_avatarwar',
        name: 'Avatar of War',
        zone: 'Kael Drakkel',
        zone_short: 'kael',
      },
      {
        key: 'velious_dain',
        name: 'Dain Frostreaver IV',
        zone: 'Icewell Keep',
        zone_short: 'thurgadinb',
      },
      {
        key: 'velious_yelinak',
        name: 'Lord Yelinak',
        zone: 'Skyshrine',
        zone_short: 'skyshrine',
      },
      {
        key: 'velious_tunare',
        name: 'Tunare',
        zone: 'Plane of Growth',
        zone_short: 'growth',
      },
      {
        key: 'velious_vulak',
        name: 'Vulak`Aerr',
        zone: 'Temple of Veeshan',
        zone_short: 'templeveeshan',
      },
    ],
  },
  {
    expansion_id: 3,
    short: 'Luclin',
    bosses: [
      {
        key: 'luclin_grieg',
        name: 'Grieg Veneficius',
        zone: "Grieg's End",
        zone_short: 'griegsend',
      },
      {
        key: 'luclin_rumble',
        name: 'Rumblecrush',
        zone: 'Umbral Plains',
        zone_short: 'umbral',
      },
      {
        key: 'luclin_seru',
        name: 'Lord Inquisitor Seru',
        zone: 'Sanctus Seru',
        zone_short: 'sseru',
      },
      {
        key: 'luclin_ssraeshza',
        name: 'Emperor Ssraeshza',
        zone: 'Ssraeshza Temple',
        zone_short: 'ssratemple',
      },
      {
        key: 'luclin_aten_ha_ra',
        name: 'Aten Ha Ra',
        zone: 'Vex Thal',
        zone_short: 'vexthal',
      },
      {
        key: 'luclin_vaxi_aten',
        name: 'Va Xi Aten Ha Ra',
        zone: 'Vex Thal',
        zone_short: 'vexthal',
      },
    ],
  },
  {
    expansion_id: 4,
    short: 'PoP',
    bosses: [
      {
        key: 'pop_bertoxxulous',
        name: 'Bertoxxulous',
        zone: 'Crypt of Decay',
        zone_short: 'codecay',
      },
      {
        key: 'pop_rallos',
        name: 'Rallos Zek',
        zone: 'Plane of Tactics',
        zone_short: 'tactics',
      },
      {
        key: 'pop_agnarr',
        name: 'Agnarr the Stormlord',
        zone: 'Bastion of Thunder',
        zone_short: 'bothunder',
      },
      {
        key: 'pop_mithaniel',
        name: 'Lord Mithaniel Marr',
        zone: 'Halls of Honor',
        zone_short: 'hohonorb',
      },
      {
        key: 'pop_fennin',
        name: 'Fennin Ro',
        zone: 'Plane of Fire',
        zone_short: 'pofire',
      },
      {
        key: 'pop_saryrn',
        name: 'Saryrn',
        zone: 'Plane of Torment',
        zone_short: 'torment',
      },
      {
        key: 'pop_quarm',
        name: 'Quarm',
        zone: 'Plane of Time B',
        zone_short: 'potimeb',
      },
    ],
  },
  {
    expansion_id: 5,
    short: 'LoY',
    note: 'LoY added no traditional raid content — auto-unlocks ~15 days after Rallos Zek on live progression. Targets below are optional group-level named mobs.',
    bosses: [
      {
        key: 'loy_rottgrime',
        name: 'Captain Rottgrime',
        zone: "Hate's Fury: The Scorned Maiden",
        zone_short: 'hatesfury',
      },
      {
        key: 'loy_drusella',
        name: 'Drusella Sathir',
        zone: 'Crypt of Nadox',
        zone_short: 'nadox',
      },
      {
        key: 'loy_mordlon',
        name: 'Arch Lich Mordlon',
        zone: 'Torgiran Mines',
        zone_short: 'torgiran',
      },
    ],
  },
  {
    expansion_id: 6,
    short: 'LDoN',
    note: 'LDoN has no fixed raid bosses — entirely instanced adventure content. Complete the hard adventure from each of the 5 dungeon themes for era completion.',
    bosses: [
      {
        key: 'ldon_guk',
        name: 'Deepest Guk (Hard)',
        zone: 'Deepest Guk',
        zone_short: 'gukd',
      },
      {
        key: 'ldon_miragul',
        name: "Miragul's Menagerie (Hard)",
        zone: "Miragul's Menagerie",
        zone_short: 'mira',
      },
      {
        key: 'ldon_mmca',
        name: 'Mistmoore Catacombs (Hard)',
        zone: 'Mistmoore Catacombs',
        zone_short: 'mmca',
      },
      {
        key: 'ldon_ruja',
        name: 'Rujarkian Hills (Hard)',
        zone: 'Rujarkian Hills',
        zone_short: 'ruja',
      },
      {
        key: 'ldon_takish',
        name: 'Ruins of Takish-Hiz (Hard)',
        zone: 'Ruins of Takish-Hiz',
        zone_short: 'takd',
      },
    ],
  },
  {
    expansion_id: 7,
    short: 'GoD',
    bosses: [
      {
        key: 'god_tunik',
        name: 'Spirit of Tunik Tamuik',
        zone: 'Ikkinz: Trial of Righteousness',
        zone_short: 'ikkinz1',
      },
      {
        key: 'god_vrex',
        name: 'Vrex Barxt Qurat',
        zone: 'Uqua, the Ocean God Chantry',
        zone_short: 'uqua',
      },
      {
        key: 'god_curse',
        name: 'Cursebearer',
        zone: 'Inktu`Ta, the Unmasked Chapel',
        zone_short: 'inktu',
      },
      {
        key: 'god_tkarish',
        name: 'Zun`Muram Tkarish Zyk',
        zone: 'Txevu, Lair of the Elite',
        zone_short: 'txevu',
      },
      {
        key: 'god_tunat',
        name: 'Tunat`Muram Cuu Vauax',
        zone: 'Tacvi, Seat of the Slaver',
        zone_short: 'tacvi',
      },
    ],
  },
  {
    expansion_id: 8,
    short: 'OoW',
    bosses: [
      {
        key: 'oow_feratha',
        name: 'Feratha',
        zone: "Riftseekers' Sanctum",
        zone_short: 'riftseekers',
      },
      {
        key: 'oow_keldovan',
        name: 'Keldovan the Harrier',
        zone: 'Anguish, the Fallen Palace',
        zone_short: 'anguish',
      },
      {
        key: 'oow_hanvar',
        name: 'Warden Hanvar',
        zone: 'Anguish, the Fallen Palace',
        zone_short: 'anguish',
      },
      {
        key: 'oow_vangl',
        name: 'Arch Magus Vangl',
        zone: 'Anguish, the Fallen Palace',
        zone_short: 'anguish',
      },
      {
        key: 'oow_matamuram',
        name: 'Overlord Mata Muram',
        zone: 'Anguish, the Fallen Palace',
        zone_short: 'anguish',
      },
    ],
  },
  {
    expansion_id: 9,
    short: 'DoN',
    bosses: [
      {
        key: 'don_volkara',
        name: 'Volkara',
        zone: "Lavaspinner's Lair",
        zone_short: 'lavaspinners',
      },
      {
        key: 'don_rikkukin',
        name: 'Rikkukin the Defender',
        zone: 'The Ascent',
        zone_short: 'theascent',
      },
      {
        key: 'don_kessdona',
        name: 'Kessdona the Enlightened',
        zone: 'The Ascent',
        zone_short: 'theascent',
      },
      {
        key: 'don_yarlir',
        name: 'Yar`Lir the Living Storm',
        zone: 'Thundercrest Isles',
        zone_short: 'thundercrest',
      },
      {
        key: 'don_vishimtar',
        name: 'Vishimtar the Fallen',
        zone: 'The Accursed Nest',
        zone_short: 'thenest',
      },
    ],
  },
  {
    expansion_id: 10,
    short: 'DoDH',
    bosses: [
      {
        key: 'dodh_maestro',
        name: 'Maestro Tan`lor',
        zone: 'Theater of Blood',
        zone_short: 'theaterofblood',
      },
      {
        key: 'dodh_sendaii',
        name: 'Sendaii, the Hive Queen',
        zone: 'The Hive',
        zone_short: 'thehive',
      },
      {
        key: 'dodh_draygun',
        name: 'Emperor Draygun',
        zone: 'Demi-Plane of Blood',
        zone_short: 'demiplane',
      },
      {
        key: 'dodh_mayong',
        name: 'Mayong Mistmoore',
        zone: 'Demi-Plane of Blood',
        zone_short: 'demiplane',
      },
    ],
  },
  {
    expansion_id: 11,
    short: 'PoR',
    bosses: [
      {
        key: 'por_ragewind',
        name: 'Ragewind',
        zone: 'The Devastation',
        zone_short: 'devastation',
      },
      {
        key: 'por_aryer',
        name: 'Ar`yer the Warlord',
        zone: 'Sverag, Stronghold of Rage',
        zone_short: 'sverag',
      },
      {
        key: 'por_sullon',
        name: 'Sullon Zek Mistress of Rage',
        zone: 'Razorthorn, Rise of the Ykesha',
        zone_short: 'razorthorn',
      },
      {
        key: 'por_ayonae',
        name: 'Ayonae Ro',
        zone: 'Deathknell, Tower of Dissonance',
        zone_short: 'deathknell',
      },
    ],
  },
  {
    expansion_id: 12,
    short: 'TSS',
    bosses: [
      {
        key: 'tss_ambersnout',
        name: 'Ambersnout the Aberration',
        zone: 'Ashengate, West',
        zone_short: 'ashengatewest',
      },
      {
        key: 'tss_sothgar',
        name: 'Sothgar the Twiceborn',
        zone: 'Ashengate, West',
        zone_short: 'ashengatewest',
      },
      {
        key: 'tss_kingodeen',
        name: 'King Odeen',
        zone: 'Frostcrypt',
        zone_short: 'frostcrypt',
      },
      {
        key: 'tss_dynleth',
        name: 'Dyn`leth, Firstborn of Lethar',
        zone: 'Ashengate, North',
        zone_short: 'ashengatenorth',
      },
      {
        key: 'tss_lethar',
        name: 'Lethar',
        zone: 'Ashengate, North',
        zone_short: 'ashengatenorth',
      },
    ],
  },
  {
    expansion_id: 13,
    short: 'TBS',
    bosses: [
      {
        key: 'tbs_urfloxiz',
        name: 'Ur-Floxiz Lochmaul',
        zone: 'Solteris, the Throne of Ro',
        zone_short: 'solteris',
      },
      {
        key: 'tbs_aprosis',
        name: 'Aprosis the Fourth Confidant',
        zone: 'Solteris, the Throne of Ro',
        zone_short: 'solteris',
      },
      {
        key: 'tbs_irrissa',
        name: 'Irrissa the Seer',
        zone: 'Solteris, the Throne of Ro',
        zone_short: 'solteris',
      },
      {
        key: 'tbs_mayong',
        name: 'Mayong Mistmoore',
        zone: 'Solteris, the Throne of Ro',
        zone_short: 'solteris',
      },
      {
        key: 'tbs_solusekro',
        name: 'Solusek Ro',
        zone: 'Solteris, the Throne of Ro',
        zone_short: 'solteris',
      },
    ],
  },
  {
    expansion_id: 14,
    short: 'SoF',
    bosses: [
      {
        key: 'sof_meldrath',
        name: 'Meldrath the Malignant',
        zone: "Meldrath's Majestic Mansion",
        zone_short: 'meldrath',
      },
      {
        key: 'sof_darkelor',
        name: 'Dar`Kelor',
        zone: 'Crystallos, Lair of the Awakened',
        zone_short: 'crystallos',
      },
      {
        key: 'sof_kerafyrm',
        name: 'Kerafyrm the Awakened',
        zone: 'Crystallos, Lair of the Awakened',
        zone_short: 'crystallos',
      },
    ],
  },
  {
    expansion_id: 15,
    short: 'SoD',
    bosses: [
      {
        key: 'sod_pallorax',
        name: 'Pallorax the Soul Slayer',
        zone: 'Korafax, Home of the Riders',
        zone_short: 'korafax',
      },
      {
        key: 'sod_ksathrax',
        name: 'Venom Lord Ksathrax',
        zone: 'Korafax, Home of the Riders',
        zone_short: 'korafax',
      },
      {
        key: 'sod_firiona',
        name: 'Firiona Vie',
        zone: 'Citadel of the Worldslayer',
        zone_short: 'discord',
      },
      {
        key: 'sod_lanys',
        name: 'Lanys T`Vyl',
        zone: 'Citadel of the Worldslayer',
        zone_short: 'discord',
      },
      {
        key: 'sod_brekt',
        name: 'Lord Brekt',
        zone: 'Citadel of the Worldslayer',
        zone_short: 'discord',
      },
    ],
  },
  {
    expansion_id: 16,
    short: 'UF',
    bosses: [
      {
        key: 'uf_brell',
        name: 'Brell Serilis',
        zone: "Brell's Temple",
        zone_short: 'brellstemple',
      },
      {
        key: 'uf_gatekeeper',
        name: 'The Gatekeeper',
        zone: 'The Convorteum',
        zone_short: 'convorteum',
      },
      {
        key: 'uf_stonewarden',
        name: 'The Stone Warden',
        zone: 'The Convorteum',
        zone_short: 'convorteum',
      },
      {
        key: 'uf_firstcreation',
        name: 'The First Creation',
        zone: 'The Convorteum',
        zone_short: 'convorteum',
      },
    ],
  },
  {
    expansion_id: 17,
    short: 'HoT',
    bosses: [
      {
        key: 'hot_cazic',
        name: 'Cazic-Thule',
        zone: 'Fear Itself',
        zone_short: 'fearitself',
      },
      {
        key: 'hot_morell',
        name: 'Morell Thule',
        zone: "Morell's Castle",
        zone_short: 'morellcastle',
      },
      {
        key: 'hot_sanctum',
        name: 'Morell Thule',
        zone: 'Sanctum Somnium',
        zone_short: 'sanctumomnium',
      },
    ],
  },
  {
    expansion_id: 18,
    short: 'VoA',
    bosses: [
      {
        key: 'voa_illdaera',
        name: 'Avatar of Illdaera',
        zone: 'Argath, Bastion of Illdaera',
        zone_short: 'argath',
      },
      {
        key: 'voa_herald',
        name: 'The Herald of Oratory',
        zone: 'Valley of Lunanyn',
        zone_short: 'lunanyn',
      },
      {
        key: 'voa_prexus',
        name: 'Avatar of Prexus',
        zone: 'Sarith, City of Tides',
        zone_short: 'sarith',
      },
      {
        key: 'voa_kingbeasts',
        name: 'King of the Beasts',
        zone: "Beasts' Domain",
        zone_short: 'beastsdomain',
      },
      {
        key: 'voa_triunity',
        name: 'The Triunity',
        zone: 'Sepulcher of Order',
        zone_short: 'sepulcher',
      },
    ],
  },
  {
    expansion_id: 19,
    short: 'RoF',
    bosses: [
      {
        key: 'rof_tormax',
        name: 'King Tormax',
        zone: 'Kael Drakkel (Shard)',
        zone_short: 'kaelshard',
      },
      {
        key: 'rof_grelleth',
        name: 'Grelleth, Her Majesty the Queen',
        zone: "Grelleth's Palace, the Chateau of Filth",
        zone_short: 'grelleth',
      },
      {
        key: 'rof_xorbb',
        name: 'The Return of King Xorbb',
        zone: 'Valley of King Xorbb',
        zone_short: 'xorbb',
      },
      {
        key: 'rof_vulak',
        name: 'Vulak`Aerr',
        zone: 'Corrupted Temple of Veeshan',
        zone_short: 'chardok2',
      },
      {
        key: 'rof_terror',
        name: 'Terror',
        zone: 'Heart of Fear: The Epicenter',
        zone_short: 'heartoffear',
      },
    ],
  },
]

async function initProgressionTable() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS gm_progression_kills (
      character_id INT NOT NULL,
      boss_key VARCHAR(100) NOT NULL,
      killed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (character_id, boss_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  `)
}

app.get('/api/progression/bosses', (_req, res) => res.json(PROGRESSION_BOSSES))

app.get('/api/character/:id/progression', async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT boss_key FROM gm_progression_kills WHERE character_id = ?',
      [req.params.id]
    )
    res.json({ kills: rows.map((r) => r.boss_key) })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.post('/api/character/:id/progression/:bossKey', async (req, res) => {
  const { id, bossKey } = req.params
  try {
    await pool.query(
      'INSERT IGNORE INTO gm_progression_kills (character_id, boss_key) VALUES (?, ?)',
      [id, bossKey]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.delete('/api/character/:id/progression/:bossKey', async (req, res) => {
  const { id, bossKey } = req.params
  try {
    await pool.query(
      'DELETE FROM gm_progression_kills WHERE character_id = ? AND boss_key = ?',
      [id, bossKey]
    )
    res.json({ success: true })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── NPC Tuning (zone-level difficulty) ───────────────────────────────────────

app.get('/api/npc-scale/:zone', async (req, res) => {
  try {
    const [rows] = await pool.query(`
      SELECT type, level, hp, ac, accuracy, slow_mitigation,
             attack, strength, stamina, agility, dexterity,
             wisdom, intelligence, pr, mr, dr, cr, fr, corrupt,
             physical_resist, special_abilities
      FROM npc_scale_global_base
      WHERE type = 'all' OR type = 'named'
      ORDER BY type, level
      LIMIT 200
    `)
    res.json(rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Account Management ───────────────────────────────────────────────────────

app.get('/api/accounts', async (_req, res) => {
  try {
    const [rows] = await pool.query(`
      SELECT id, account_name, source_loginserver, last_login_date, created_at
      FROM login_accounts
      ORDER BY created_at DESC
      LIMIT 100
    `)
    res.json(rows)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.delete('/api/accounts/:id', async (req, res) => {
  const { id } = req.params
  if (!id || isNaN(id))
    return res.status(400).json({ error: 'Invalid account ID' })
  try {
    const [[account]] = await pool.query(
      'SELECT account_name FROM login_accounts WHERE id = ?',
      [id]
    )
    if (!account) return res.status(404).json({ error: 'Account not found' })

    await pool.query('DELETE FROM login_accounts WHERE id = ?', [id])
    await pool.query(
      'DELETE FROM account WHERE lsaccount_id = ? AND ls_id = ?',
      [id, 'local']
    )

    res.json({ success: true, deleted: account.account_name })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.patch('/api/accounts/:id/password', async (req, res) => {
  const { id } = req.params
  const { new_password } = req.body
  if (!id || isNaN(id))
    return res.status(400).json({ error: 'Invalid account ID' })
  if (!new_password || new_password.length < 1)
    return res.status(400).json({ error: 'Password required' })

  try {
    const [[account]] = await pool.query(
      'SELECT account_name FROM login_accounts WHERE id = ?',
      [id]
    )
    if (!account) return res.status(404).json({ error: 'Account not found' })

    const encrypted = require('crypto')
      .createHash('md5')
      .update(new_password)
      .digest('hex')

    await pool.query(
      'UPDATE login_accounts SET account_password = ? WHERE id = ?',
      [encrypted, id]
    )

    res.json({
      success: true,
      message:
        'Password updated (note: set to MD5 for immediate use; will be upgraded to SCrypt on next login)',
    })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Spell Vendor Refresh ─────────────────────────────────────────────────────
//
// Rebuilds merchantlist for the three spell vendor archetypes based on the
// current expansion. Called automatically when expansion is applied, and
// available as a standalone endpoint for manual refresh.
//
// Archetype → class columns in spells_new (classes1..16, value = min level, 255=unavailable)
// Archetype → items.classes bitmask (bit = 2^(classId-1))
const SPELL_ARCHETYPES = [
  {
    merchantId: 99221,
    label: 'Pure Casters (Nec/Wiz/Mag/Enc)',
    classCols: [11, 12, 13, 14],
    classBits: 1024 + 2048 + 4096 + 8192, // 15360
  },
  {
    merchantId: 99222,
    label: 'Priests (Clr/Dru/Shm)',
    classCols: [2, 6, 10],
    classBits: 2 + 32 + 512, // 546
  },
  {
    merchantId: 99223,
    label: 'Hybrids (Pal/Rng/SK/Brd/Bst)',
    classCols: [3, 4, 5, 8, 15],
    classBits: 4 + 8 + 16 + 128 + 16384, // 16540
  },
]

async function refreshSpellVendors(expansionId) {
  const results = []
  for (const arch of SPELL_ARCHETYPES) {
    await pool.query('DELETE FROM merchantlist WHERE merchantid = ?', [
      arch.merchantId,
    ])

    // Spell scrolls: book=1, spellid>0, accessible to archetype, within expansion
    const classAccessChecks = arch.classCols
      .map((c) => `sn.classes${c} != 255`)
      .join(' OR ')

    const [scrolls] = await pool.query(
      `SELECT i.id, i.name
       FROM items i
       INNER JOIN spells_new sn ON sn.id = i.spellid
       WHERE i.book = 1
         AND i.spellid > 0
         AND (i.classes & ?) > 0
         AND i.expansion <= ?
         AND (${classAccessChecks})
       ORDER BY i.name
       LIMIT 500`,
      [arch.classBits, expansionId]
    )

    let slot = 1
    for (const scroll of scrolls) {
      await pool.query(
        'INSERT INTO merchantlist (merchantid, slot, item, faction_required, level_required, alt_currency_cost, classes_required, probability) VALUES (?, ?, ?, -100, 0, 0, 65535, 100)',
        [arch.merchantId, slot++, scroll.id]
      )
    }

    results.push({ label: arch.label, count: scrolls.length })
  }
  return results
}

app.post('/api/vendors/refresh', async (_req, res) => {
  try {
    const [[expRow]] = await pool.query(
      "SELECT CAST(rule_value AS UNSIGNED) AS val FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion' AND ruleset_id = 1 LIMIT 1"
    )
    const expansionId = expRow?.val ?? 0
    const results = await refreshSpellVendors(expansionId)
    res.json({ success: true, expansion: expansionId, archetypes: results })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── Health check ──────────────────────────────────────────────────────────────

app.get('/api/ping', async (_req, res) => {
  try {
    await pool.query('SELECT 1')
    res.json({ ok: true, db: 'connected' })
  } catch (err) {
    res.status(500).json({ ok: false, error: err.message })
  }
})

const PORT = 3001
app.listen(PORT, () => {
  initProgressionTable().catch((e) =>
    console.error('Progression table init failed:', e)
  )
  console.log(`\n  EQ Solo GM API  →  http://localhost:${PORT}\n`)
})
