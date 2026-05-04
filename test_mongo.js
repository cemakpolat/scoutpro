/**
 * test_mongo.js — ScoutPro MongoDB spot-check
 *
 * Run from the host:
 *   node test_mongo.js
 *
 * Or inside the mongo container:
 *   docker exec -i scoutpro-mongo mongosh \
 *     -u root -p scoutpro123 --authenticationDatabase admin \
 *     /test_mongo.js
 */
const { MongoClient } = require('mongodb');

const MONGO_URL =
  process.env.MONGODB_URL ||
  'mongodb://root:scoutpro123@localhost:27017/scoutpro?authSource=admin';

async function test() {
  const c = new MongoClient(MONGO_URL);
  await c.connect();
  const db = c.db('scoutpro');

  // ── match_events ──────────────────────────────────────────────────────────
  const shot = await db.collection('match_events').findOne({ type_name: 'miss' });
  console.log('\n── match_events (shot) ──────────────────────────────────────');
  if (shot) {
    console.log('  type_name   :', shot.type_name);
    console.log('  location    :', JSON.stringify(shot.location));
    console.log('  player_id   :', shot.player_id);
    console.log('  team_id     :', shot.team_id);
    console.log('  event_source:', shot.event_source);            // NEW
    console.log('  scoutpro_ev :', shot.scoutpro_event_id);       // NEW
    console.log('  provider_ids:', JSON.stringify(shot.provider_ids)); // NEW
  } else {
    console.log('  (no shot events — run ./manage.sh seed)');
  }

  const pass = await db.collection('match_events').findOne({ type_name: 'pass' });
  console.log('\n── match_events (pass) ──────────────────────────────────────');
  if (pass) {
    console.log('  type_name      :', pass.type_name);
    console.log('  location       :', JSON.stringify(pass.location));
    console.log('  progressive    :', pass.progressive_pass);        // enrichment field
    console.log('  entered_final  :', pass.entered_final_third);     // enrichment field
    console.log('  analytical_xg  :', pass.analytical_xg);          // enrichment field
    console.log('  event_source   :', pass.event_source);
  } else {
    console.log('  (no pass events)');
  }

  // ── players ───────────────────────────────────────────────────────────────
  const pl = await db.collection('players').findOne({ scoutpro_id: { $exists: true } });
  console.log('\n── players ──────────────────────────────────────────────────');
  if (pl) {
    console.log('  name         :', pl.name);
    console.log('  scoutpro_id  :', pl.scoutpro_id);                // NEW — sp_pl_...
    console.log('  provider_ids :', JSON.stringify(pl.provider_ids)); // { opta: "101380" }
    console.log('  position     :', pl.position);
    console.log('  nationality  :', pl.nationality);
  } else {
    console.log('  (no players with scoutpro_id)');
  }

  // ── collection counts ─────────────────────────────────────────────────────
  console.log('\n── counts ───────────────────────────────────────────────────');
  for (const col of ['players', 'teams', 'matches', 'match_events', 'player_statistics']) {
    const n = await db.collection(col).countDocuments({});
    console.log(`  ${col.padEnd(22)}: ${n}`);
  }

  await c.close();
}

test().catch(console.error);

