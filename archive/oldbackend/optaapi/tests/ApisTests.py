"""
@author: Cem Akpolat
@created by cemakpolat at 2021-08-20
"""
from src.events.Events import EventIDs
from src.restapi.APIHelpers import PlayerEventStatistics
from src.feedAPI import PlayerAPI as papi
from src.feedAPI import GameAPI as gapi
from src.feedAPI import TeamAPI as tapi
from src.feedAPI.EventHandler import EventHandler
from src.events.GoalkeeperEvents import GoalkeeperEvents
from src.events.AssistEvents import AssistEvents


class PlayerAPITests:
    def __init__(self):
        self.competition_id = "115"
        self.season_id = "2018"
        self.team_name = "Besiktas"
        self.player_name = "Guven Yalcin"
        self.player = papi.PlayerAPI(self.competition_id, self.season_id)

    def test(self):
        print(self.player.getPlayerData(self.team_name, self.player_name))
        # result = self.player.getPlayerEvents(self.team_name, self.player_name)
        # print(result)
        result = self.player.callPlayer(self.team_name, self.player_name)
        print(result)

        # return the statistic only for the user for all events within a season
        # player.callPlayer(team_name,player_name)

        # player.getTeamAllPlayerNames(team_name)
        # print(player.getPlayerID(player_name,team_name))
        # print(player.getAllPlayerIDs(team_name))


class TeamAPITests:
    def __init__(self):
        self.competition_id = "115"
        self.season_id = "2018"
        self.team_name = "Besiktas"
        self.player_name = "Guven Yalcin"
        self.team = tapi.TeamAPI(self.competition_id, self.season_id)

    def test(self):
        uID = "1002377"

        print(self.team.getTeamEventsInterval(self.team_name, 0, 5))  # ok
        # print(self.team.getTeamsEvents("sd", "sds"))
        print(self.team.getAllTeamIDs())
        # print(self.team.getAllTeamNames())
        print(self.team.getSeasonTeamsEvents())


class GameAPITests:
    def __init__(self):
        self.competition_id = "115"
        self.season_id = "2018"
        self.team_name = "Galatasaray"
        self.player_name = "Fernando Muslera"
        self.player = papi.PlayerAPI(self.competition_id, self.season_id)
        self.team = tapi.TeamAPI(self.competition_id, self.season_id)
        self.team_id = tapi.TeamAPI(self.competition_id, self.season_id).getTeamID(
            self.team_name
        )

    def test(self):
        uID = "1002377"
        team = tapi.TeamAPI(self.competition_id, self.season_id)
        # print(team.getTeamEventsInterval(self.team_name, 0, 5)) # ok
        print(team.getTeamsEvents("sd", "sds"))

    def test_goal_keeper(self):
        print(self.team.getTeamAllPlayers(self.team_name))
        gk = GoalkeeperEvents()
        self.team_name = "Besiktas"
        self.player_name = "Adem Ljajic"
        game = gapi.GameAPI(self.competition_id, self.season_id)
        playerID = self.player.getPlayerID(self.player_name, self.team_name)
        events = game.getAllSeasonGameEvents(self.team_id, playerID)

        data = {}
        data["events"] = events
        data["teamID"] = self.team_id
        data["playerID"] = playerID

        gk.callEventHandler(data)

        # self.player_name = "Martin Linnes"
        # self.team_name = "Galatasaray"
        # result = self.player.getPlayerGamesPlayed(self.team_name,self.player_name,30)
        # print(result)

    def test_assist_events(self):
        self.team_name = "Besiktas"
        self.player_name = "Adem Ljajic"
        self.team_id = tapi.TeamAPI(self.competition_id, self.season_id).getTeamID(
            self.team_name
        )
        game = gapi.GameAPI(self.competition_id, self.season_id)
        player_id = self.player.getPlayerID(self.player_name, self.team_name)
        events = game.getAllSeasonGameEvents(self.team_id, player_id)

        fixtures = 34
        values = self.player.getPlayerGamesPlayed(self.team_name, self.player_name, fixtures)
        print(values)
        total_minutes = 100
        data = {}
        data["events"] = events
        data["teamID"] = self.team_id
        data["playerID"] = player_id
        data["total_minutes"] = total_minutes
        assev = AssistEvents()
        assev.callEventHandler(data)


class StatisticAPI:
    def __init__(self):
        self.competition_id = "115"
        self.season_id = "2018"
        self.team_name = "Besiktas"
        # self.player_name = "Guven Yalcin"
        self.player_name = "Adem Ljajic"
        self.player = papi.PlayerAPI(self.competition_id, self.season_id)

    def get_aerial(self):
        data = {
                "event": "aerial",
                "filters": ['totalDuels', 'won', 'lost', 'wonPercentage', 'attackingHalf']
              }

        print(self.player.getAerial(self.team_name, self.player_name, data["filters"]))

    def test(self):
        import time

        current = time.time()

        events = self.player.get_player_events(self.team_name, self.player_name)

        print("get player", time.time() - current)
        print(len(events))
        ehandler = EventHandler()
        # results = ehandler.handleAllEvents(events)
        data = {}
        data["events"] = events
        results = ehandler.handle_single_event(EventIDs.TouchEvents, data)
        print("stats", time.time() - current)
        player_stat = PlayerEventStatistics(self.player_name, '', self.competition_id, self.season_id, self.team_name,
                                            results.copy())
        player_stat.storeInDB()
        print(results)
        # TODO: Retrieve from the database to see whether the data is correclty written


import time

current = time.time()

# ptest = PlayerAPITests()
# ptest.test()
# ttest = TeamAPITests()
# value = ttest.test()
# print(len(value))
# gtest = GameAPITests()
# gtest.test_goal_keeper()
# gtest.test_assist_events()
stest = StatisticAPI()
stest.get_aerial()
# stest.test()
# disconnect_all()
print(time.time() - current)

# get all teams, get their players, save all their statistical values
