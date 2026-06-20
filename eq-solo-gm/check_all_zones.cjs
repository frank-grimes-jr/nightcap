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
    const [zones] = await pool.query('SELECT id, short_name, long_name FROM zone WHERE id IN (9, 22, 133) ORDER BY id');
    console.log(JSON.stringify(zones, null, 2));
  } finally {
    await pool.end();
  }
})();
