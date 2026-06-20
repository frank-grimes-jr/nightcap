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
    // Find the current IDs
    const [zones] = await pool.query('SELECT id, short_name FROM zone WHERE short_name IN (?, ?)', ['freportw', 'arena']);
    console.log('Current state:', zones);

    const freportw = zones.find(z => z.short_name === 'freportw');
    const arena = zones.find(z => z.short_name === 'arena');

    if (freportw && arena) {
      console.log(`\nFixing zone IDs using temporary ID:`);
      console.log(`  ${freportw.short_name} (${freportw.id}) → 9`);
      console.log(`  ${arena.short_name} (${arena.id}) → 22`);

      // Use a temp ID (999) to avoid conflicts during swap
      await pool.query('UPDATE zone SET id = ? WHERE id = ?', [999, arena.id]);      // arena: old ID → 999
      await pool.query('UPDATE zone SET id = ? WHERE id = ?', [9, freportw.id]);    // freportw: 133 → 9
      await pool.query('UPDATE zone SET id = ? WHERE id = ?', [22, 999]);           // arena: 999 → 22

      console.log('\nZone IDs corrected!');

      // Verify
      const [verify] = await pool.query('SELECT id, short_name FROM zone WHERE short_name IN (?, ?)', ['freportw', 'arena']);
      console.log('After fix:', verify);
    }
  } finally {
    await pool.end();
  }
})();
