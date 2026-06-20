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
    // Get the actual columns in the zone table
    const [cols] = await pool.query('DESCRIBE zone');
    console.log('Zone table columns:');
    cols.forEach(c => console.log(`  ${c.Field} (${c.Type}) ${c.Key}`));

    // Check freportw specifically — both id and zoneidnumber
    const [fw] = await pool.query('SELECT id, zoneidnumber, short_name, long_name FROM zone WHERE short_name = ?', ['freportw']);
    console.log('\nfreportw:', fw[0]);

    const [ar] = await pool.query('SELECT id, zoneidnumber, short_name, long_name FROM zone WHERE short_name = ?', ['arena']);
    console.log('arena:', ar[0]);

    // What zone does character_data reference?
    const [chars] = await pool.query('SELECT name, zone_id FROM character_data WHERE deleted_at IS NULL LIMIT 5');
    console.log('\ncharacter_data.zone_id samples:');
    chars.forEach(c => console.log(`  ${c.name}: zone_id ${c.zone_id}`));

    // What does zone_id 9 map to in the zone table via zoneidnumber?
    const [z9] = await pool.query('SELECT id, zoneidnumber, short_name FROM zone WHERE zoneidnumber = 9 LIMIT 3');
    console.log('\nZone with zoneidnumber=9:', z9);

  } finally {
    await pool.end();
  }
})();
