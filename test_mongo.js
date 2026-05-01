const { MongoClient } = require('mongodb');

async function test() {
  const c = new MongoClient('mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin');
  await c.connect();
  const db = c.db('scoutpro');
  const m = await db.collection('match_events').findOne({ type_name: 'shot' });
  console.log("Shot:", m.type_name, m.location, "team_id", m.team_id, "player_id", m.player_id);
  const p = await db.collection('match_events').findOne({ type_name: 'pass' });
  console.log("Pass:", p.type_name, p.location, "team_id", p.team_id, "player_id", p.player_id);
  await c.close();
}
test().catch(console.error);
