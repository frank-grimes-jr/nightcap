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
    const [zones] = await pool.query(`
      SELECT id, short_name, long_name
      FROM zone
      ORDER BY id
    `);

    console.log(`Total zones in database: ${zones.length}\n`);
    console.log('Zone ID Audit:');
    console.log('─'.repeat(80));

    zones.forEach(z => {
      console.log(`ID: ${String(z.id).padEnd(4)} | ${z.short_name.padEnd(25)} | ${z.long_name}`);
    });

    // Check for obvious issues
    console.log('\n' + '─'.repeat(80));
    console.log('Potential Issues:');

    // Check for duplicate IDs (shouldn't happen but worth checking)
    const idCounts = {};
    zones.forEach(z => {
      idCounts[z.id] = (idCounts[z.id] || 0) + 1;
    });

    Object.entries(idCounts).forEach(([id, count]) => {
      if (count > 1) {
        console.log(`⚠️  Zone ID ${id} appears ${count} times!`);
      }
    });

    // Check for large gaps
    const ids = zones.map(z => z.id);
    const maxId = Math.max(...ids);
    const minId = Math.min(...ids);
    const gaps = [];

    for (let i = minId; i < maxId; i++) {
      if (!ids.includes(i)) {
        gaps.push(i);
      }
    }

    if (gaps.length > 0 && gaps.length < 20) {
      console.log(`\n📍 Gaps in zone IDs (${gaps.length} missing):`);
      console.log(gaps.slice(0, 20).join(', ') + (gaps.length > 20 ? '...' : ''));
    } else if (gaps.length > 0) {
      console.log(`\n📍 ${gaps.length} total gaps in zone ID sequence`);
    }

    console.log(`\n📊 Zone ID range: ${minId} - ${maxId}`);
  } finally {
    await pool.end();
  }
})();
