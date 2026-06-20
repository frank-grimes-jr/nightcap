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
    // Get all zone IDs sorted
    const [zones] = await pool.query('SELECT id FROM zone ORDER BY id');
    const usedIds = new Set(zones.map(z => z.id));

    // Find first gap
    let unused = 1;
    while (usedIds.has(unused)) {
      unused++;
    }

    console.log(`First unused zone ID: ${unused}`);
    console.log(`Moving arena from 999 to ${unused}...`);

    await pool.query('UPDATE zone SET id = ? WHERE short_name = "arena"', [unused]);

    const [verify] = await pool.query('SELECT id, short_name FROM zone WHERE short_name = "arena"');
    console.log('Arena is now at:', verify[0]);
  } finally {
    await pool.end();
  }
})();
