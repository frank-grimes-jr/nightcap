const mysql = require('mysql2/promise');

(async () => {
  const pool = mysql.createPool({
    host: 'localhost',
    port: 3307,
    user: 'eqemu',
    password: 'eqemu',
    database: 'peq'
  });
  try {
    // Check arena location
    const [arena] = await pool.query('SELECT id, short_name, long_name FROM zone WHERE short_name = ?', ['arena']);
    console.log('Arena zone:', arena[0] || 'NOT FOUND');

    // Find zones with duplicate short_names that share the SAME long_name (real corruption)
    // Duplicate short_names are normal for instanced content, so we filter by count and look for anomalies
    const [highDups] = await pool.query(`
      SELECT short_name, COUNT(*) as count, MIN(id) as min_id, MAX(id) as max_id
      FROM zone
      GROUP BY short_name
      HAVING count > 10
      ORDER BY count DESC
      LIMIT 10
    `);

    console.log('\nShort names with many entries (may be expected for instances):');
    highDups.forEach(d => console.log(`  ${d.short_name}: ${d.count} entries (IDs ${d.min_id}-${d.max_id})`));

    // The real question: are key Classic-era zones at expected IDs?
    // These are the zones EQEmu hardcodes behavior around
    const knownZones = [
      { id: 9, expected: 'freportw' },
      { id: 10, expected: 'arena2' },
      { id: 1, expected: 'abysmal' },
      { id: 19, expected: 'befallen' },
      { id: 23, expected: 'blackburrow' },
      { id: 31, expected: 'butcher' },
      { id: 62, expected: 'gfaydark' },
      { id: 63, expected: 'gfaydarkb' },
      { id: 46, expected: 'erudnext' },
      { id: 48, expected: 'felwithea' },
      { id: 75, expected: 'nektulos' },
      { id: 130, expected: 'freeportarena' },
    ];

    console.log('\nKey zone ID checks:');
    for (const z of knownZones) {
      const [rows] = await pool.query('SELECT short_name FROM zone WHERE id = ?', [z.id]);
      const actual = rows[0]?.short_name || 'NOT FOUND';
      const status = actual === z.expected ? '✓' : '⚠️ MISMATCH';
      console.log(`  ID ${String(z.id).padEnd(4)} expected=${z.expected.padEnd(20)} actual=${actual} ${status}`);
    }

  } finally {
    await pool.end();
  }
})();
