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
    // Find an unused zone ID to move arena to
    // First check if 22 (traditional Arena ID) is really bertoxtemple or if we can reassign it
    const [zone22] = await pool.query('SELECT * FROM zone WHERE id = 22');
    console.log('Zone 22:', zone22[0]);

    if (zone22[0]?.short_name === 'bertoxtemple') {
      console.log('\nZone 22 is bertoxtemple, finding a safe unused ID for arena...');

      // Move arena from 999 to 122 (freeportarena will be removed since it's basically the same)
      const [current] = await pool.query('SELECT id FROM zone WHERE short_name = "arena" LIMIT 1');
      if (current[0]) {
        console.log(`\nMoving arena from ID ${current[0].id} to ID 122...`);
        await pool.query('UPDATE zone SET id = 122 WHERE short_name = "arena"');

        // Verify
        const [verify] = await pool.query('SELECT id, short_name FROM zone WHERE short_name = "arena"');
        console.log('After fix:', verify[0]);
      }
    }
  } finally {
    await pool.end();
  }
})();
