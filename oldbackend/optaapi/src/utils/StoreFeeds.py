import sys

sys.path.append("..")  # Adds higher directory to python modules path.
from src.parse import Parser
from src.feedAPI import Connector

# all accessible competition ids
competition_ids = [
    22,
    87,
    115,
    21,
    5,
    6,
    8,
    10,
    24,
    104,
    23,
    102,
    9,
    112,
    99,
    135,
    100,
    226,
    90,
    119,
    724,
    363,
    364,
    270,
    558,
    371,
    589,
    375,
    749,
    98,
    199,
    385,
    208,
    20,
]
# all accessible season ids
season_ids = [2016, 2017, 2018, 2019]


def storeAllGames():
    # game to be tested:
    # 2017, 935627 | 2018-old, 1002377

    # tests to be done f1, f9, f24, f40

    competition_id = 115
    season_id = 2017
    gameId = 935627

    connector = Connector.main_conn
    connector.connect()
    connector.getFeed(Parser.Feeds.feed1, competition_id, season_id, None)
    connector.getFeed(Parser.Feeds.feed9, competition_id, season_id, gameId)
    connector.getFeed(Parser.Feeds.feed24, competition_id, season_id, "g" + str(gameId))
    connector.getFeed(Parser.Feeds.feed40, competition_id, season_id, None)
    connector.disconnect()


def storeGamesLoop():
    connector = Connector.main_conn
    connector.connect()

    # tests to be done f1, f9, f24, f40

    for competition_id in competition_ids:
        for season_id in season_ids:
            feed1 = connector.getFeed(
                Parser.Feeds.feed1, competition_id, season_id, None
            )
            # get all game Ids
            gameIds = []
            for game in feed1.matchData:
                if game.uID is not None:
                    gameIds.append(game.uID.replace("g", ""))

            # get all matches in f9 and all f24 events
            for gameId in gameIds:
                connector.getFeed(Parser.Feeds.feed9, competition_id, season_id, gameId)
                connector.getFeed(
                    Parser.Feeds.feed24, competition_id, season_id, "g" + str(gameId)
                )
                # time.sleep(1)

            # store all team data for each semester
            connector.getFeed(Parser.Feeds.feed40, competition_id, season_id, None)
        # time.sleep(randint(1,3))

    connector.disconnect()


storeAllGames()

# Accessible Competitions

# England Premier League: 8
# England Championship:  10
# UEFA Champions League: 5
# UEFA Europa League: 6
# France Ligue 1: 24
# France Ligue 2: 104
# Spain La Liga: 23
# Spain La Liga 2: 102
# Italy Serie A: 21
# Germany Bundesliga: 22
# Germany Bundesliga 2: 87
# Netherlands Eredivisie: 9
# Belgium First Divison: 112
# Portugal Primeira Liga: 99
# Russia Premier League: 129
# Switzerland Super League: 135
# Turkish Super League: 115
# Denmark Super Liga: 100
# Sweden Allsvenskan: 226
# Norway Tippeligaen: 90
# Austria Bundesliga: 119
# Argentina SuperLiga: 724
# Brazil Serie A: 363
# Brazil Serie B: 364
# Chile Primera: 370 & 558
# Colombia Primera A: 371 & 589
# Peru Primera: 375 & 749
# USA MLS: 98
# Mexico Primera: 199 & 385
# Chinese Super League: 208
# Japan J1 League: 20
