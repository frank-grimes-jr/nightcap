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
    const [rows] = await pool.query('SELECT id, short_name, long_name FROM zone WHERE short_name IN (?, ?)' , ['freportw', 'arena']);
    console.log(JSON.stringify(rows, null, 2));
  } finally {
    await pool.end();
  }
})();
