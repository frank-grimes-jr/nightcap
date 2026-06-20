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
    const [zones] = await pool.query('SELECT id, short_name, long_name FROM zone WHERE short_name LIKE ? ORDER BY id', ['%arena%']);
    console.log('Zones matching "arena":');
    console.log(JSON.stringify(zones, null, 2));
  } finally {
    await pool.end();
  }
})();
