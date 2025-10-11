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
