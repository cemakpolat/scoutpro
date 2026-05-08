db = db.getSiblingDB('scoutpro');

// Create collections
db.createCollection('players');
db.createCollection('teams');
db.createCollection('matches');
db.createCollection('statistics');

// Create indexes
db.players.createIndex({ "uID": 1 }, { unique: true });
db.players.createIndex({ "name": "text" });
db.teams.createIndex({ "uID": 1 }, { unique: true });
db.matches.createIndex({ "uID": 1 }, { unique: true });
db.matches.createIndex({ "date": 1 });

print('MongoDB initialization completed');

// Historical Querying & Data Freshness Indexes
db.getSiblingDB("scoutpro").events.createIndex(
    { "match_id": 1, "provider": 1, "data_freshness": 1 },
    { name: "event_history_provider_freshness_idx" }
);

db.getSiblingDB("scoutpro").matches.createIndex(
    { "id": 1, "provider": 1, "data_freshness": 1 },
    { name: "match_history_provider_freshness_idx" }
);

