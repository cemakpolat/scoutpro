"""
Author: Cem Akpolat

"""
import json
import sys

# import feedAPI.QueryPipeline

sys.path.append("..")  # Adds higher directory to python modules path.
from src.feedAPI import Connector
from src.parse import Parser
from src.feedAPI.EventHandler import EventHandler, GamesandMinutesEvents
from src.events.Events import EventIDs
from src.events.QTypes import QTypes
from src.restapi import APIHelpers
from src.utils.Utils import *
from src.dbase.DBHelper import *
from src.feedAPI import GameAPI
from src.feedAPI import EventAPI
from src.feedAPI import TeamAPI
from src.feedAPI.QueryPipeline import QueryPipeline


class PlayerAPI:
    def __init__(self, competitionID, seasonID):
        self.competitionID = int(competitionID)
        self.seasonID = int(seasonID)
        self.connector = Connector.main_conn
        self.doc_name = get_doc_name
        self.online = False
        self.event_api_connection = False
        self.game_api_connection = False
        self.team_api_connection = False
        self.db_port = 27017
        self.host = "localhost"
        self.connector.connect()

    def getAerial(self, team_name, player_name, params):
        # http://docs.mongoengine.org/apireference.html#mongoengine.queryset.QuerySet.select_related
        stat = PlayerStatistics.objects(
            Q(playerName=player_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()

        # print(stat.aerialEvent.id)
        keys = AerialEvent.objects.exclude("id").only(*params).get(id=stat.aerialEvent.id)
        # keys = AerialEvent.objects.get(id=stat.aerialEvent.id).exclude("id").only(*params).first()
        print(keys.to_json())
        all_keys = []
        for k in keys:
            if k !="id":
                all_keys.append(k)

        return all_keys

    def setCompetitionSeason(self, competition_id, season_id):
        self.competitionID = competition_id
        self.seasonID = season_id

    def setOnline(self, value):
        self.online = value

    def evapi(self):
        if self.event_api_connection is False:
            self.event_api_connection = EventAPI.EventAPI(competition_id=self.competitionID, season_id=self.seasonID)
            return self.event_api_connection
        else:
            return self.event_api_connection

    def gapi(self):
        if self.game_api_connection is False:
            self.game_api_connection = GameAPI.GameAPI(competitionID=self.competitionID, seasonID=self.seasonID)
            return self.game_api_connection
        else:
            return self.game_api_connection

    def tapi(self):
        if self.team_api_connection is False:
            self.team_api_connection = TeamAPI.TeamAPI(competitionID=self.competitionID, seasonID=self.seasonID)
            return self.team_api_connection
        else:
            return self.team_api_connection

    # Test passed

    def getPlayerData(self, teamName, playerName):
        feed = self.connector.getFeed("feed40", self.competitionID, self.seasonID, None)
        print(teamName, playerName)
        playerData = {}

        teamSearched = None
        for team in feed.team:
            if team.name == teamName:
                teamSearched = team
                print(team.name)
                break

        for player in teamSearched.players:
            if player.name == playerName:
                print(player.name)
                for stat in player.stats:
                    playerData[stat.type] = stat.value
        return playerData

#? codes that start from here until new yellow comment contain new query based fetch functions

    # -----------------------Get Player Statistic Object---------------------

    def get_team_fast(self, player_name, is_current_team):  # * is_current_team-> True: current_team, False: old_Team
        '''
        This function returns the team name of player. Depend on given is_current_team
        flag it can give current team name or if player transferred in season it can give old team name.
        :param player_name: It is a string that stands for the player name.
        :param is_current_team: It is a boolean parameter to specify whether desired team name current or old teamç
        '''
        if is_current_team:
            team_type = "team"
        else:
            team_type = "playerChanges"

        pipeline = [
            {
                "$match": {
                    "competitionID": int(self.competitionID),
                    "seasonID": int(self.seasonID)
                }
            },
            {
                "$project": {
                    team_type: 1
                }
            },
            {
                "$unset": "_id"
            },
            {
                "$lookup": {
                    "from": "f40__team",
                    "localField": team_type,
                    "foreignField": "_id",
                    "as": "teams"
                }
            },
            {
                "$unset": team_type
            },
            {
                "$unwind": "$teams"
            },
            {
                "$addFields": {
                    "team_name": "$teams.name",
                    "players": "$teams.players"
                }
            },
            {
                "$project": {
                    "team_name": 1,
                    "players": 1
                }
            },
            {
                "$lookup": {
                    "from": "f40__player",
                    "localField": "players",
                    "foreignField": "_id",
                    "as": "players"
                }
            },
            {
                "$unwind": "$players"
            },
            {
                "$addFields": {
                    "player_name": "$players.name"
                }
            },
            {
                "$project": {
                    "player_name": 1,
                    "team_name": 1
                }
            },
            {
                "$match": {
                    "player_name": player_name,
                }
            }
        ]

        result = F40_Root.objects.aggregate(pipeline)
        teams = []
        for doc in result:
            teams.append(doc["team_name"])
        if len(teams) == 1:
            return teams[0], False
        elif len(teams) > 1:
            return teams[0], True
        else:
            return None, False

    def handlePlayerGames(self, player_name, games_events,
                          currentTeamName, oldTeamName, requested_statistics=None):
        '''
        This function take the games_event of given player and handle those events and
        returns the statistics about those events. This is a helper function for game
        analysis of player.
        :param player_name: It is a string that stands for the player name.
        :param games_events: It is a list of F24_Game or list of list of F24_Event that contain
        mainly all events to be handled.
        e.g. [F24_Game, F24_Game, F24_Game...] or [[F24_Event, F24_Event, ..], [], [], ...]
        :param currentTeamName: It is a string that stands for the current team name (If it is exists).
        :param oldTeamName: It is a string that stands for the old team name (If it is exists).
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        Default values is None and in such a case all events are handled.
        '''
        desired_events = []
        try:
            if games_events and isinstance(games_events[0], F24_Game):
                all_events = list(map(lambda x: x.events, games_events))
            else:
                all_events = games_events
            playerID = self.getPlayerID_Alt(player_name)
            for events in all_events:
                for event in events:
                    if int(playerID[1:]) == event.playerID:
                        desired_events.append(event)
            if desired_events is None:
                print("no events is available")
                return None
            logging.info("all events are collected")
            handler = EventHandler()
            old_team_id = "t-1"
            if oldTeamName is not None:
                old_team_id = self.getTeamID(oldTeamName)
            team_id = "t-1"
            if currentTeamName is not None:
                team_id = self.getTeamID(currentTeamName)
            data = self.preparePlayerDataForHandler(desired_events, all_events,
                                                    self.getPlayerGamesPlayed(currentTeamName, player_name, 34)[
                                                        "total_minutes"],
                                                    playerID, team_id, old_team_id
                                                    )
            if requested_statistics:
                results = handler.handle_single_event_v2(requested_statistics, data)
            else:
                results = handler.handle_all_events_v2(data)
            return results
        except Exception as err:
            print(err)
        return None

    def preparePlayerDataForHandler(self, events, all_events, total_minutes,
                                    player_id, team_id="t-1", old_team_id="t-1"):
        '''
        This function is helper for handlePlayerGames.
        :param events: It is a list of events.
        :param all_events: It is a list of list of events.
        :param total_minutes: It is integer that specify playing time of a player.
        :param player_id: It is a string of player_id.
        :param team_id: It is a string of team_id (If exists).
        :param old_team_id: It is a string of old_team_id (If exists).
        '''

        data = dict()
        data["events"] = events
        data["all_events"] = all_events
        data["total_minutes"] = total_minutes
        data["playerID"] = player_id
        data["teamID"] = team_id
        data["oldTeamID"] = old_team_id
        return data

    def get_both_team(self, player_name):
        '''
        This function returns the name of current and old team (If exist) of a player.
        If there is multiple player with same name it also print warning message.
        :param player_name: It is a string that stands for the player name.
        '''
        current_team_name, is_duplicate = self.get_team_fast(player_name, True)
        old_team_name, is_duplicate2 = self.get_team_fast(player_name, False)
        if is_duplicate or is_duplicate2:
            print("!!! Be careful there are multiple player with this name.")
        return current_team_name, old_team_name

    def getPlayerGamesEvent(self, player_name, game_number, limit_number):
        '''
        This function returns the desired F24_Game objects to get game events of player.
        For example: game_number=4, limit_number=6, then function returns the F24_Game
        week4 to week(4+6) namely week4 to week10.
        :param player_name: It is a string that stands for the player name.
        :param game_number: It is integer to specify starting week.
        :param limit_number: It is integer to specify how many week to get F24_Game
         starting from game_number.
        '''
        current_team_name, old_team_name = self.get_both_team(player_name)
        team_list = []
        if current_team_name:
            team_list.append(current_team_name)
        if old_team_name:
            team_list.append(old_team_name)
        result = []
        for team in team_list:
            temp_result = F24_Game.objects(  # To get multiple games events of team
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=team) | Q(homeTeamName=team))
            ).only(*["ID", "events"]).order_by('+ID', '+events').skip(
                game_number - 1).limit(limit_number)
            result = result + list(temp_result)

        return result, current_team_name, old_team_name

    def getPlayerGamesEventWithGameIDs(self, player_name, game_ids):
        '''
        This function returns the F24_Game objects those with matched game_ids
         to get game events of player.
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        current_team_name, old_team_name = self.get_both_team(player_name)
        team_list = []
        if current_team_name:
            team_list.append(current_team_name)
        if old_team_name:
            team_list.append(old_team_name)
        result = []
        for team in team_list:
            temp_result = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=team) | Q(homeTeamName=team)) &
                (Q(ID__in=game_ids))
            ).only("ID", "events")
            result = result + list(temp_result)

        return result, current_team_name, old_team_name

    def getPlayerGamesEventWithDate(self, player_name, low_date_str, high_date_str):
        '''
        This function returns the desired F24_Game objects to get game events of player.
        For example: low_date_str= "2018-08-11", high_date_str= "2018-10-21", then function returns the
         F24_Game between the given dates.
        :param player_name: It is a string that stands for the player name.
        :param low_date_str: It is string to specify starting date.
        :param high_date_str: It is string to specify ending date.
        '''
        # * low_date_str in form --> "2018-08-11" and if there is match at this date it will be added
        low_date_str = low_date_str + "T00:00:00"
        high_date_str = high_date_str + "T24:59:59"
        current_team_name, old_team_name = self.get_both_team(player_name)
        team_list = []
        if current_team_name:
            team_list.append(current_team_name)
        if old_team_name:
            team_list.append(old_team_name)
        result = []
        for team in team_list:
            temp_result = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=team) | Q(homeTeamName=team)) &
                (Q(periodOneStart__gte=low_date_str) & Q(periodOneStart__lte=high_date_str))
            ).only("events")
            result = result + list(temp_result)

        return result, current_team_name, old_team_name

    def getPlayerGameEventPKs(self, player_name, game_ids):
        '''
        This function returns the all ObjectIds or primary keys of F24_Event documents about given game_ids.
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        current_team_name, old_team_name = self.get_both_team(player_name)
        result = F24_Game.objects(
            Q(competitionID=int(self.competitionID)) &
            Q(seasonID=int(self.seasonID)) &
            (Q(awayTeamName=current_team_name) | Q(homeTeamName=current_team_name)
             | Q(awayTeamName=old_team_name) | Q(homeTeamName=old_team_name)) &
            (Q(ID__in=game_ids))
        ).only("pk", "events")
        eventID_lists = []
        for game in result:
            eventID_lists.append(list(map(lambda x: x.pk, game.events)))
        return eventID_lists

    def getPlayerGamesEventSeperatedHalf(self, player_name, game_ids):
        '''
        This function returns the game events as a separation of first half and second half
        in form of list of list of F24_Events.
        e.g. [firsthalf:[gameID1:[events], gameIDs2:[events]], secondhalf:[gameID1:[events], gameIDs2:[events]]
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        eventID_lists = self.getPlayerGameEventPKs(player_name, game_ids)
        # format: [firsthalf:[gameID1:[events], gameIDs2:[events]], secondhalf:[gameID1:[events], gameIDs2:[events]]
        first_half_events = []
        for eventID_list in eventID_lists:
            first_half_event = F24_Event.objects(
                Q(pk__in=eventID_list) &
                Q(periodID=1)
            )
            first_half_events.append(first_half_event)

        second_half_events = []
        for eventID_list in eventID_lists:
            second_half_event = F24_Event.objects(
                Q(pk__in=eventID_list) &
                Q(periodID=2)
            )
            second_half_events.append(second_half_event)
        return [first_half_events, second_half_events]

    def minute_parser(self, minute_list):
        '''
        This function is a helper function for getTeamGamesStatisticsSeperatedMins function.
        It takes a cutting minutes (like : [25, 75]) as a parameter and returns the list of
        time interval according to given minutes (like: [[0-25], [25-75], [75-120]] for example above).
        :param minute_list: IT is a list of integer to specify cutting minutes.
        '''
        if not minute_list:
            return [[0, 120]]
        # ! consider sorting list if required
        if minute_list[0] != 0:
            minute_list = [0] + minute_list

        minute_list.append(120)

        pair_list = []
        for i in range(len(minute_list) - 1):
            pair = [minute_list[i], minute_list[i + 1]]
            pair_list.append(pair)
        return pair_list

    def getPlayerGamesEventSeperatedMins(self, player_name, game_ids, minute_pairs):  # min_list like: [15, 45, 65, 80]
        '''
        This function returns the game events seperated by given minute pairs
        in form of list of list of F24_Event.
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param minute_pairs: It is a list of list of integer that specify the desired time
        intervals to get game events.
        '''
        eventID_lists = self.getPlayerGameEventPKs(player_name, game_ids)
        result_list = []
        for min_pair in minute_pairs:

            if min_pair[1] < 45:
                temp_events = []
                for eventID_list in eventID_lists:
                    temp_event = F24_Event.objects(
                        Q(pk__in=eventID_list) &
                        Q(periodID=1) &
                        Q(min__gte=min_pair[0]) & Q(min__lt=min_pair[1])
                    )
                    temp_events.append(temp_event)
                result_list.append(temp_events)

            elif min_pair[0] < 45 and min_pair[1] > 45:
                temp_events = []
                for eventID_list in eventID_lists:
                    temp_event = F24_Event.objects(
                        Q(pk__in=eventID_list) &
                        ((Q(periodID=1) & Q(min__gte=min_pair[0])) | (Q(periodID=2) & Q(min__lt=min_pair[1])))
                    )
                    temp_events.append(temp_event)
                result_list.append(temp_events)

            elif min_pair[1] == 45:
                temp_events = []
                for eventID_list in eventID_lists:
                    temp_event = F24_Event.objects(
                        Q(pk__in=eventID_list) &
                        Q(periodID=1) &
                        Q(min__gte=min_pair[0])
                    )
                    temp_events.append(temp_event)
                result_list.append(temp_events)

            elif min_pair[0] == 45:
                temp_events = []
                for eventID_list in eventID_lists:
                    temp_event = F24_Event.objects(
                        Q(pk__in=eventID_list) &
                        Q(periodID=2) &
                        Q(min__lt=min_pair[1])
                    )
                    temp_events.append(temp_event)
                result_list.append(temp_events)

            elif min_pair[0] > 45:
                temp_events = []
                for eventID_list in eventID_lists:
                    temp_event = F24_Event.objects(
                        Q(pk__in=eventID_list) &
                        Q(periodID=2) &
                        Q(min__gte=min_pair[0]) & Q(min__lt=min_pair[1])
                    )
                    temp_events.append(temp_event)
                result_list.append(temp_events)

        return result_list

    def getPlayerGamesEventSeperatedByRedCards(self, player_name, game_id):
        '''
        This function returns the game events seperated by red card event minutes
        in form of list of list of F24_Event.
        :param player_name: It is a string that stands for the player name.
        :param game_id: It is integer to specify game_id of played match.
        '''
        eventID_lists = self.getPlayerGameEventPKs(player_name, [game_id])
        all_card_events = []
        for eventID_list in eventID_lists:
            card_events = F24_Event.objects(
                Q(pk__in=eventID_list) &
                Q(typeID=17)
            )
            all_card_events.append(card_events)

        # print(all_card_events)
        red_card_mins = []
        if all_card_events[0]:
            for event in all_card_events[0]:
                # print(event.qEvents)
                for qEvent in event.qEvents:
                    if qEvent.qualifierID == 33:
                        min = event.min
                        if event.periodID == 1 and min > 45:
                            min = 45
                        else:
                            min += 1
                        red_card_mins.append(min)
        # print(red_card_mins)

        minute_pairs = self.minute_parser(red_card_mins)
        # print(minute_pairs)
        return self.getPlayerGamesEventSeperatedMins(player_name, [game_id], minute_pairs), minute_pairs

    def getPlayerGamesEventSeperatedByGoals(self, player_name, game_id):
        '''
        This function returns the game events seperated by goal event minutes
        in form of list of list of F24_Event.
        :param player_name: It is a string that stands for the player name.
        :param game_id: It is integer to specify game_id of played match.
        '''
        eventID_lists = self.getPlayerGameEventPKs(player_name, [game_id])
        all_goal_events = []
        for eventID_list in eventID_lists:
            goal_events = F24_Event.objects(
                Q(pk__in=eventID_list) &
                Q(typeID=16)
            )
            all_goal_events.append(goal_events)

        goal_mins = []

        if all_goal_events[0]:
            for event in all_goal_events[0]:
                min = event.min
                if event.periodID == 1 and min > 45:
                    min = 45
                else:
                    min += 1
                goal_mins.append(min)

        minute_pairs = self.minute_parser(goal_mins)

        return self.getPlayerGamesEventSeperatedMins(player_name, [game_id], minute_pairs), minute_pairs

    def getPlayerGamesStatistics(self, player_name, game_number, limit_number, requested_statistics=None):
        '''
        This function returns the desired game statistics of a player.
        For example: game_number=4, limit_number=6, then function returns game statistics between
        week 4 to week(4+6) namely week 4 to week 10.
        :param player_name: It is a string that stands for the player name.
        :param game_number: It is integer to specify starting week.
        :param limit_number: It is integer to specify how many game week should we take
         starting from game_number.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        games_events, current_team_name, old_team_name = self.getPlayerGamesEvent(player_name,
                                                                                  game_number, limit_number)
        return self.handlePlayerGames(player_name, games_events, current_team_name, old_team_name, requested_statistics)

    def getPlayerGamesStatisticsWithGameIDs(self, player_name, game_ids, requested_statistics=None):
        '''
        This function returns the game (games that in game_ids list) statistics of a player.
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        games_events, current_team_name, old_team_name = self.getPlayerGamesEventWithGameIDs(player_name, game_ids)
        return self.handlePlayerGames(player_name, games_events, current_team_name, old_team_name, requested_statistics)

    def getPlayerGamesStatisticsWithDate(self, player_name, low_date_str, high_date_str, requested_statistics=None):
        '''
        This function returns the game statistics of a player between given dates.
        :param player_name: It is a string that stands for the player name.
        :param low_date_str: It is string to specify starting date.
        :param high_date_str: It is string to specify ending date.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        games_events, current_team_name, old_team_name = self.getPlayerGamesEventWithDate(player_name, low_date_str,
                                                                                          high_date_str)
        return self.handlePlayerGames(player_name, games_events, current_team_name, old_team_name, requested_statistics)

    def getPlayerGamesStatisticsSeperatedHalf(self, player_name, game_ids, requested_statistics=None):
        '''
        This function returns the game statistics of a player in two seperate halves.
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated = self.getPlayerGamesEventSeperatedHalf(player_name, game_ids)
        current_team_name, old_team_name = self.get_both_team(player_name)
        result = dict()
        result["FirstHalves"] = self.handlePlayerGames(player_name, game_events_seperated[0],
                                                       current_team_name, old_team_name, requested_statistics)
        result["SecondHalves"] = self.handlePlayerGames(player_name, game_events_seperated[1],
                                                        current_team_name, old_team_name, requested_statistics)
        return result

    def getPlayerGamesStatisticsSeperatedMins(self, player_name, game_ids, minute_list, requested_statistics=None):
        '''
        This function returns the game statistics of a player seperated by given minute_list
        :param player_name: It is a string that stands for the player name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param minute_list: IT is a list of integer to specify cutting minutes.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        minute_pairs = self.minute_parser(minute_list)
        current_team_name, old_team_name = self.get_both_team(player_name)
        game_events_seperated = self.getPlayerGamesEventSeperatedMins(player_name, game_ids, minute_pairs)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handlePlayerGames(player_name, game_events_seperated[i],
                                                                            current_team_name, old_team_name,
                                                                            requested_statistics)
        return result

    def getPlayerGamesStatisticsSeperatedByRedCards(self, player_name, game_id, requested_statistics=None):
        '''
        This function returns the game statistics of a player seperated by red card events.
        :param player_name: It is a string that stands for the player name.
        :param game_id: It is integer to specify game_id of played match.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated, minute_pairs = self.getPlayerGamesEventSeperatedByRedCards(player_name, game_id)
        current_team_name, old_team_name = self.get_both_team(player_name)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handlePlayerGames(player_name, game_events_seperated[i],
                                                                            current_team_name, old_team_name,
                                                                            requested_statistics)
        return result

    def getPlayerGamesStatisticsSeperatedByGoals(self, player_name, game_id, requested_statistics=None):
        '''
        This function returns the game statistics of a player seperated by goal events.
        :param player_name: It is a string that stands for the player name.
        :param game_id: It is integer to specify game_id of played match.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated, minute_pairs = self.getPlayerGamesEventSeperatedByGoals(player_name, game_id)
        current_team_name, old_team_name = self.get_both_team(player_name)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handlePlayerGames(player_name, game_events_seperated[i],
                                                                            current_team_name, old_team_name,
                                                                            requested_statistics)
        return result

    def getTotalGoalkeeping(self, team_name):
        team_pks, player_changed_pks, all_pks = self.getSeasonTeamPKs()

        pipeline = [
            {
                "$match": {
                    "name": team_name
                    }
            },
            {
                "$addFields": {
                    "teamName": "$name"
                }
            },
            {
                "$project": {
                    "teamName": 1, "players": 1
                }
            },
            {
                "$unset": "_id"
            },
            {
                "$lookup": {
                    "from": "f40__player",
                    "localField": "players",
                    "foreignField": "_id",
                    "as": "players"
                }
            },
            {
                "$unwind": "$players"
            },
            {
                "$addFields": {
                    "name": "$players.name",
                    "position": "$players.position"
                }
            },
            {
                "$unset": "players"
            },
            {
                "$match": {
                    "position": "Goalkeeper"
                }
            },
            {
                "$lookup": {
                    "from": "player_statistics",
                    "localField": "name",
                    "foreignField": "playerName",
                    "as": "statistics"
                }
            },
            {
                "$lookup": {
                    "from": "goalkeeper_event",
                    "localField": "statistics.goalkeeperEvent",
                    "foreignField": "_id",
                    "as": "goalkeeping"
                }
            },
            {
                "$unwind": "$goalkeeping"
            },
            {
                "$unset": ["statistics", "name", "position", "goalkeeping._id"]
            },
            {
                "$match": {
                    "goalkeeping.crosses_faced": {
                        "$nin": [0],
                    }
                }
            }
        ]
        result = F40_Team.objects(pk__in=all_pks).aggregate(pipeline)
        total_dict = dict()
        total_dict["team_name"] = team_name
        total_dict["stats"] = dict()
        substring = "percentage"
        count = 0
        for doc in result:
            # print(doc)
            count += 1
            print(doc["goalkeeping"])
            for stat in doc["goalkeeping"]:
                if len(total_dict['stats']) < len(doc["goalkeeping"]):
                    total_dict["stats"][stat] = doc["goalkeeping"][stat]
                else:
                    if stat is not None and substring in stat:
                        total_dict["stats"][stat] = ((count-1) * total_dict["stats"][stat] + doc["goalkeeping"][stat]) / (count)
                    else:
                        total_dict["stats"][stat] += doc["goalkeeping"][stat]
        return total_dict

    def callPlayer_Fast(self, player_name, stat_group, detailed_stats=None):  # detailed_stats is list of str like:
        if stat_group == "AerialEvent":                                      # ['fouls_won', 'penalty_won', ...]
            result = self.getAerial_Alt(player_name, detailed_stats)
        elif stat_group == "AssistEvent":
            result = self.getAsist(player_name, detailed_stats)
        elif stat_group == "BallControlEvent":
            result = self.getBallControl(player_name, detailed_stats)
        elif stat_group == "PassEvent":
            result = self.getPass(player_name, detailed_stats)
        elif stat_group == "FoulEvent":
            result = self.getFoul(player_name, detailed_stats)
        elif stat_group == "CardEvent":
            result = self.getCard(player_name, detailed_stats)
        elif stat_group == "TakeOnEvent":
            result = self.getTakeOn(player_name, detailed_stats)
        elif stat_group == "TouchEvent":
            result = self.getTouch(player_name, detailed_stats)
        elif stat_group == "DuelEvent":
            result = self.getDuel(player_name, detailed_stats)
        elif stat_group == "ShotandGoalEvent":
            result = self.getShotAndGoal(player_name, detailed_stats)
        elif stat_group == "GoalkeeperEvent":
            result = self.getGoalKeeping(player_name, detailed_stats)
        else:
            result = None
            print(f"{stat_group} can not found in database.")
        return result

    def callPlayer_Fast_V2(self, player_name, stat_list=None):  # stat_list is list of list like:
        result = dict()                   #  [ ['FoulEvent',['fouls_won']],['AssistEvent',['total_assists']], ...]
        if stat_list is None:
            stat_list = [["AerialEvent"], ["PassEvent"], ["FoulEvent"],  ["CardEvent"],
                  ["BallControlEvent"], ["TakeOnEvent"], ["TouchEvent"], ["DuelEvent"],
                  ["ShotandGoalEvent"], ["AssistEvent"], ["GoalkeeperEvent"]]
        for stat in stat_list:
            if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                continue
            detailed_stat = None
            if len(stat) > 1:
                detailed_stat = stat[1]
            if stat[0] == "AerialEvent":
                temp = self.getAerial_Alt(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "AssistEvent":
                temp = self.getAsist(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "BallControlEvent":
                temp = self.getBallControl(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "PassEvent":
                temp = self.getPass(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "FoulEvent":
                temp = self.getFoul(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "CardEvent":
                temp = self.getCard(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "TakeOnEvent":
                temp = self.getTakeOn(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "TouchEvent":
                temp = self.getTouch(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "DuelEvent":
                temp = self.getDuel(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "ShotandGoalEvent":
                temp = self.getShotAndGoal(player_name, detailed_stat)
                result = {**result, **temp}
            elif stat[0] == "GoalkeeperEvent":
                temp = self.getGoalKeeping(player_name, detailed_stat)
                result = {**result, **temp}
            else:
                print(f"{stat[0]} can not found in database.")
        return result

    def callPlayer_Fast_V3(self, player_name, stat_list=None):  # stat_list is list of list like:
        result = dict()                   # [['FoulEvent',['fouls_won']],['AssistEvent',['total_assists']], ...]
        if stat_list is None:
            stat_list = [["AerialEvent"], ["PassEvent"], ["FoulEvent"],  ["CardEvent"],
                  ["BallControlEvent"], ["TakeOnEvent"], ["TouchEvent"], ["DuelEvent"],
                  ["ShotandGoalEvent"], ["AssistEvent"], ["GoalkeeperEvent"]]
        for stat in stat_list:
            if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                continue
            detailed_stat = None
            if len(stat) > 1:
                detailed_stat = stat[1]
            if stat[0] == "AerialEvent":
                temp = self.getAerial_Alt(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "AssistEvent":
                temp = self.getAsist(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "BallControlEvent":
                temp = self.getBallControl(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "PassEvent":
                temp = self.getPass(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "FoulEvent":
                temp = self.getFoul(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "CardEvent":
                temp = self.getCard(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "TakeOnEvent":
                temp = self.getTakeOn(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "TouchEvent":
                temp = self.getTouch(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "DuelEvent":
                temp = self.getDuel(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "ShotandGoalEvent":
                temp = self.getShotAndGoal(player_name, detailed_stat)
                result[stat[0]] = temp
            elif stat[0] == "GoalkeeperEvent":
                temp = self.getGoalKeeping(player_name, detailed_stat)
                result[stat[0]] = temp
            else:
                print(f"{stat[0]} can not found in database.")
        return result

    def callPlayer_Fast_V4(self, player_name, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the statistics of player from different event_groups like aerial, foul, take on ...
        :param player_name: It is a string that stands for the player name.
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        :param get_translated: it is a flag to get values in a form like : {aerial: ....} instead of {aerialEvent: ....}
        simply this flag helpful for front_end.
        '''
        result = dict()                   # [['foulEvent',['fouls_won']],['assistEvent',['total_assists']], ...]
        if stat_list is None:
            result = self.getPlayerEventGroup(player_name)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getPlayerEventGroup(player_name, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result

    def callPlayer_percentile(self, player_name, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the percentile statistics of player from different event_groups like aerial, foul, take on ...
        :param player_name: It is a string that stands for the player name.
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        :param get_translated: it is a flag to get values in a form like : {aerial: ....} instead of {aerialEvent: ....}
        simply this flag helpful for front_end.
        '''
        result = dict()                   # [['foulEvent',['fouls_won']],['assistEvent',['total_assists']], ...]
        if stat_list is None:
            result = self.getPlayerPercentileEventGroup(player_name)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getPlayerPercentileEventGroup(player_name, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result

    def callPlayerPer90(self, player_name, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the statistics of player from different event_groups like aerial, foul, take on ... as per90
        :param player_name: It is a string that stands for the player name.
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        :param get_translated: it is a flag to get values in a form like : {aerial: ....} instead of {aerialEvent: ....}
        simply this flag helpful for front_end.
        '''
        result = dict()                   # [['foulEvent',['fouls_won']],['assistEvent',['total_assists']], ...]
        if stat_list is None:
            result = self.getPlayerPer90EventGroup(player_name)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getPlayerPer90EventGroup(player_name, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result

    def callSeasonAverage_Fast(self, stat_name, stat_type, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the cumulative average season statistics of players from different event_groups like
        aerial, foul, take on ...
        :param stat_name: It is a string that stands for the stat name like forward_dominant_players.
        :param stat_type: It is a string that stands for the stat type like average, standard_deviation.
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        :param get_translated: it is a flag to get values in a form like : {aerial: ....} instead of {aerialEvent: ....}
        simply this flag helpful for front_end.
        '''
        result = dict()                   # [['foulEvent',['fouls_won']],['assistEvent',['total_assists']], ...]
        if stat_list is None:
            result = self.getPlayerAverageEventGroup(stat_name, stat_type)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getPlayerAverageEventGroup(stat_name, stat_type, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result


    '''
    input like: funct("reference_playerName", ["playerName", "PlayerName", ...], stat_list-> same as callPlayerV3 )
    return type is dict like {"AerialEvent":{"totalDuels": "+5", ... },...}
    positive values mean that player X is greater than reference player in given stat
    negative values mean that player X is less than reference player in given stat
    '''
    def comparePlayers_V2(self, reference_player, player_list, stat_list=None):
        reference_stats = self.callPlayer_Fast_V3(reference_player, stat_list)
        diff_list = list()
        for player in player_list:
            diff_stat = dict()
            diff_stat["playerName"] = player
            diff_stat["referencePlayer"] = reference_player
            temp_stat = self.callPlayer_Fast_V3(player, stat_list)
            for stat in temp_stat:
                diff_detailed_stat = dict()
                for detailed_stat in temp_stat[stat]:
                    diff_detailed_stat[detailed_stat] = temp_stat[stat][detailed_stat] - reference_stats[stat][detailed_stat]
                diff_stat[stat] = diff_detailed_stat
            diff_list.append(diff_stat)
        return diff_list

    def comparePlayers_V3(self, reference_player, player_list, stat_list=None):
        '''
        This function compare the reference_player stats with the all player stats in the player_list
        , and returns the comparison values of stats in stat_list.
        :param reference_player:  It is a string that stands for the reference player name.
        :param player_list: It is a list of string that contain list of players to compare with reference player
        e.g. ["Galatarasaray", "Besiktas", "Akhisarspor", "Trabzonspor"]
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        '''
        reference_stats = self.callPlayer_Fast_V4(reference_player, stat_list)
        diff_list = list()
        for player in player_list:
            diff_stat = dict()
            diff_stat["playerName"] = player
            diff_stat["referencePlayer"] = reference_player
            temp_stat = self.callPlayer_Fast_V4(player, stat_list)
            for stat in temp_stat:
                diff_detailed_stat = dict()
                if temp_stat[stat] is None:
                    continue
                for detailed_stat in temp_stat[stat]:
                    diff_detailed_stat[detailed_stat] = temp_stat[stat][detailed_stat] - reference_stats[stat][detailed_stat]
                diff_stat[stat] = diff_detailed_stat
            diff_list.append(diff_stat)
        return diff_list

    def rankLeaguePlayers_V2(
            self, stat_group: str, detailed_stat: str, limit_number: int = None
    ):
        """
        Description:
            This function returns the top list (in terms of given
            detailed_stat like goals, total_red_cards, total_assists)
            of players with desired limit.

        Example Usage:
            rankLeaguePlayers_V2(
                stat_group="shot", detailed_stat="goals", limit_number=3
            )

        Example Output:
            [
                {
                    "player": "Mbaye Diagne",
                    "stat_value": 30.0
                },
                {
                    "player": "Vedat Muriqi",
                    "stat_value": 17.0
                },
                {
                    "player": "Papiss Demba Ciss\u00e9",
                    "stat_value": 16.0
                }
            ]

        Parameters:
            :param str stat_group: It is a string to specify the desired statistical group.
            :param str detailed_stat: It is a string to specify the desired statistic from event_group.
            :param int limit_number: It is integer that specify length of return list.

        Return:
            :rtype: list
        """

        if not self._check_event_field_existence(
                event=stat_group, field=detailed_stat
        ):
            print("Given statistic field does not match with any field. "
                  "Example; 'card', 'aerial', 'ballControl' etc.")
            return []

        event_collections = [stat_group]
        detailed_stat = stat_group + "." + detailed_stat
        event_params = [detailed_stat]
        sort_query = {"stat_value": -1}
        query_object = self.get_filtered_stats_players(
            event_collections=event_collections,
            event_params=event_params,
            join_f40=False,
            return_pipeline=True
        ).group(
            main_field="playerName",
            max_fields={"stat_value": detailed_stat}
        ).add_field(
            key="player",
            value="_id"
        ).remove(
            "_id"
        ).keep(
            "player",
            "stat_value"
        ).parallelize(
            "stat_value"
        ).sort(
            sort_query
        ).limit(
            limit_number
        )
        players = list(
            query_object.run()
        )
        return players

    def getPlayerEventGroup(self, player_name, event_group=None, params=None):
        '''
        This function can return the whole, specific or more specific statistics of player.
        With just player_name parameter it returns all statistics of player.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param player_name: It is a string that stands for the player name.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = PlayerStatistics.objects(
            Q(playerName=player_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        if stat is not None:
            keys_dict = {}
            if event_group is None:
                event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                          'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
                for group in event_groups:  # TODO make translation like 'CardEvent' --> 'cardEvent'
                    event_obj = getattr(stat, group, "not found")
                    class_name = event_obj.__class__
                    pk = getattr(event_obj, 'id', "not found")
                    if params is None:
                        keys = class_name.objects.exclude("id").get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
                    else:
                        keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
            else:
                event_obj = getattr(stat, event_group, "not found")
                class_name = event_obj.__class__
                pk = getattr(event_obj, 'id', "not fount")
                if pk == "not found" or event_obj == "not found":
                    return None
                if params is None:
                    keys = class_name.objects.exclude("id").get(id=pk)
                else:
                    keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                keys_dict = json.loads(keys.to_json())

            return keys_dict

    def getPlayerPer90EventGroup(self, player_name, event_group=None, params=None):
        '''
        This function can return the whole, specific or more specific per90 statistics of player.
        With just player_name parameter it returns all per90 statistics of player.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param player_name: It is a string that stands for the player name.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = PlayerStatisticsPer90.objects(
            Q(playerName=player_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        if stat is not None:
            keys_dict = {}
            if event_group is None:
                event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                          'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
                for group in event_groups:  # TODO make translation like 'CardEvent' --> 'cardEvent'
                    event_obj = getattr(stat, group, "not found")
                    class_name = event_obj.__class__
                    pk = getattr(event_obj, 'id', "not found")
                    if params is None:
                        keys = class_name.objects.exclude("id").get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
                    else:
                        keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
            else:
                event_obj = getattr(stat, event_group, "not found")
                class_name = event_obj.__class__
                pk = getattr(event_obj, 'id', "not fount")
                if pk == "not found" or event_obj == "not found":
                    return None
                if params is None:
                    keys = class_name.objects.exclude("id").get(id=pk)
                else:
                    keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                keys_dict = json.loads(keys.to_json())

            return keys_dict

    def getPlayerPercentileEventGroup(self, player_name, event_group=None, params=None):
        '''
        This function can return the percentile statistics of player.
        With just player_name parameter it returns all statistics of player.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param player_name: It is a string that stands for the player name.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = PlayerPercentileStatistics.objects(
            Q(playerName=player_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        if stat is not None:
            keys_dict = {}
            if event_group is None:
                event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                          'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
                for group in event_groups:  # TODO make translation like 'CardEvent' --> 'cardEvent'
                    event_obj = getattr(stat, group, "not found")
                    class_name = event_obj.__class__
                    pk = getattr(event_obj, 'id', "not found")
                    if params is None:
                        keys = class_name.objects.exclude("id").get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
                    else:
                        keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
            else:
                event_obj = getattr(stat, event_group, "not found")
                class_name = event_obj.__class__
                pk = getattr(event_obj, 'id', "not fount")
                if pk == "not found" or event_obj == "not found":
                    return None
                if params is None:
                    keys = class_name.objects.exclude("id").get(id=pk)
                else:
                    keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                keys_dict = json.loads(keys.to_json())

            return keys_dict

    def getPlayerAverageEventGroup(self, stat_name, stat_type, event_group=None, params=None):
        '''
        This function can return the whole, specific or more specific average statistics of all noticable players
        in season. With just stat_name and stat_type parameters it returns all statistics of season.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param stat_name: It is a string that stands for the stat name like forward_dominant_players.
        :param stat_type: It is a string that stands for the stat type like average, standard_deviation.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = PlayerSeasonStatistics.objects(
            Q(statType=stat_type)
            & Q(statName=stat_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        if stat is not None:
            keys_dict = {}
            if event_group is None:
                event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                                'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
                for group in event_groups:  # TODO make translation like 'CardEvent' --> 'cardEvent'
                    event_obj = getattr(stat, group, "not found")
                    class_name = event_obj.__class__
                    pk = getattr(event_obj, 'id', "not found")
                    if params is None:
                        keys = class_name.objects.exclude("id").get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
                    else:
                        keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                        keys_dict[group] = json.loads(keys.to_json())
            else:
                event_obj = getattr(stat, event_group, "not found")
                class_name = event_obj.__class__
                pk = getattr(event_obj, 'id', "not fount")
                if pk == "not found" or event_obj == "not found":
                    return None
                if params is None:
                    keys = class_name.objects.exclude("id").get(id=pk)
                else:
                    keys = class_name.objects.exclude("id").only(*params).get(id=pk)
                keys_dict = json.loads(keys.to_json())

            return keys_dict

    def get_all_sub_stat_names(self, stat_name):
        stat_list = EventAPI.EventAPI(
            self.competitionID, self.seasonID
        ).getEventParams(stat_name)
        stat_list.remove('id')
        return stat_list

    # -------------Get player Name and ID---------------------

    def get_player_id(self, player_name: str):
        query_object = self.tapi().fast_lookup_f40_player().keep("players.name", "players.uID").parallelize("players")
        query_object.match({"players.name": str(player_name)})
        result = list(query_object.limit(1).run())
        if 0 < len(result):
            return result[0]["players"]["uID"]
        else:
            return None

    def get_player_name(self, player_id: int):
        query_object = self.tapi().fast_lookup_f40_player().keep("players.name", "players.uID").parallelize("players")
        query_object.match({"players.uID": int(player_id)})
        result = list(query_object.limit(1).run())
        if 0 < len(result):
            return result[0]["players"]["name"]
        else:
            return None

    # -----------------------Get Any Event Statistics----------------- (An old function, it will be deleted soon.)

    def getEventParams(self, teamName, playerName, eventName, params):

        stat = self.getPlayerStatObj(playerName)

        # If the player statistics do not exist in the database,
        # we need to first calculate the statistic and then use the function.
        if stat is None:
            case = self.calculateStatistics(teamName, playerName)
            stat = self.getPlayerStatObj(playerName)

            if stat is None:
                print("The player does not exist. Check team_name and player name.")
                return None

        # Dictionary of all event documents in the database.
        events = self.evapi().getEventDict()

        keys = events[eventName].objects.exclude("id").only(*params).get(id=stat._data[eventName + "Event"].id)
        keys_dict = keys.to_json()
        return keys_dict

    # ------------Some Basic Applications of Query Function of GameMinuteStatistics-----------------

    def get_played_teams_of_player(self, player_id: int):
        """
        Given function takes input as a player uID and returns all team ids,
        where the given player has been played in that team. This operation does not use parser functions, therefore
        it does not require local data for the users to have. It only uses the data saved in the MongoDB,
        to be more specific, it uses F40_Team and F40_Player collections in the database.

        :param int player_id: ex. 66807
        :return: ex. [6796]
        :rtype: list
        """
        query_conditions = {"playerID": player_id}
        result = list(self.get_filtered_total_play_time_stats(
            query_pre_unwind=query_conditions, project=["playerName", "teams_played"], limit=1
        ))
        if result:
            if 0 < len(result):
                result = result[0]["teams_played"]
        return result

    def get_player_games_played(self, player_id: int, team_id: int = None, play_time_non_zero: bool = False):
        """
        Given function takes input as a player uID and team uID (optional), then returns all game ids,
        where the given player has been played. If the team uID specified, then it only returns the game
        ids where the player played only that team. This operation does not use parser functions, therefore
        it does not require local data for the users to have. It only uses the data saved in the MongoDB,
        to be more specific, it uses F40_Team and F40_Player collections in the database.

        :param int player_id: Player ID.
        :param int team_id: Team ID.
        :param bool play_time_non_zero: If the variable is True, the function returns only the games that players total
        play time non-zero. Otherwise, it will return all games where the player did not actually join the game but
        stay as substitute player through whole game.
        :return: List of all the game IDs.
        :rtype: list
        """
        pre_query = {"playerID": player_id}
        after_query = dict()
        if team_id:
            after_query["gamesPlayed.teamID"] = team_id
        if play_time_non_zero:
            after_query["gamesPlayed.game_minute_stats.total_play_time"] = {"$gt": 0}

        if len(after_query) == 0:
            after_query = None
        result = list(self.get_filtered_total_play_time_stats(
            query_pre_unwind=pre_query, query_after_unwind=after_query,
            project=["playerName", "games_played"], limit=1
        ))
        if result:
            if 0 < len(result):
                result = result[0]["games_played"]

        return result

    def get_player_total_play_time(self, player_id: int, team_id: int = None):
        pre_query = {"playerID": player_id}
        after_query = None
        if team_id:
            after_query = {"gamesPlayed.teamID": team_id}

        result = list(self.get_filtered_total_play_time_stats(
            query_pre_unwind=pre_query, query_after_unwind=after_query,
            project=["total_played_time"], limit=1
        ))
        if len(result) == 1:
            return int(list(result)[0]["total_played_time"])
        else:
            return None

    # ----------------Query on GameMinuteStatistics Document from MongoDB-------------------

    def get_filtered_total_play_time_stats(
            self, query_pre_unwind=None, query_after_unwind=None, query_after_group=None, project=None, limit=None
    ):
        root_document = PlayerMinuteStatistics
        query_object = QueryPipeline(root_document)
        query_object.match({
            "competitionID": int(self.competitionID), "seasonID": int(self.seasonID)
        })
        look_up_list = [self.doc_name(GameMinuteStatistics), "gamesPlayed", "_id", "gamesPlayed"]
        query_object.join(*look_up_list)
        if query_pre_unwind:
            query_object.match(query_pre_unwind)
        query_object.parallelize("gamesPlayed")
        if query_after_unwind:
            query_object.match(query_after_unwind)
        query_object.group(
            main_field="$playerID",
            first_fields={"playerName": "playerName", "playerID": "playerID"},
            set_fields={"games_played": "gamesPlayed.gameID", "teams_played": "gamesPlayed.teamID"},
            sum_fields={"total_played_time": "gamesPlayed.game_minute_stats.total_play_time"}
        ).remove("_id")
        if query_after_group:
            query_object.match(query_after_group)
        if project:
            if isinstance(project, str):
                query_object.keep(project)
            elif hasattr(project, "__iter__"):
                query_object.keep(*project)
            else:
                pass
        if limit:
            query_object.limit(limit)
        return query_object.run()

    # -----------Convert and Save PlayerStatistics Document into per90 Statistics----------------

    def convert_stats_into_per90(self, player_id: int):
        candidate_total_time = self.get_player_total_play_time(player_id=player_id)

        if candidate_total_time == 0 or candidate_total_time is None:
            return None
        else:
            total_time = candidate_total_time

        data = list(self.get_filtered_stats_players(query_conditions={"playerID": player_id}))

        if 0 == len(data):
            return None
        else:
            data = data[0]

        event_keys = list(self.evapi().getEventDict().keys())
        results = list()
        for event in event_keys:
            if event in data:
                if 0 < len(data[event]):
                    temp_event_results = dict()
                    for event_parameter, old_value in data[event][0].items():
                        new_value = old_value
                        temp_condition = bool(
                            ("rate" not in event_parameter) and
                            ("ercentage" not in event_parameter) and
                            ("ratio" not in event_parameter)
                        )
                        if temp_condition:
                            new_value = round(float(90*float(old_value)/int(total_time)), 9)
                        temp_event_results[event_parameter] = new_value
                    results.append({event: temp_event_results})
        return results

    def get_players_per90_stats(self, player_id: int, event_collections=None, event_params=None):
        match_player = {"playerID": player_id}
        result = list(self.get_filtered_stats_players(
            event_collections=event_collections, event_params=event_params, per90=True, query_conditions=match_player
        ))
        if 0 == len(result):
            player_name = str(self.get_player_name(player_id=player_id))
            result = self.convert_stats_into_per90(player_id=player_id)
            if result:
                APIHelpers.PlayerEventStatisticsPer90(
                    player_name=player_name,
                    player_id=player_id,
                    competition_id=self.competitionID,
                    season_id=self.seasonID,
                    results=result
                )
        return result

    # -----------Construct and Save PlayerStatistics Document into Percentile Statistics----------------

    def _check_event_field_existence(self, event: str, field: str):
        events = self.evapi().getEventDict()
        if event not in events:
            print("Event could not found: ", event)
            return False
        all_fields = self.evapi().getDocumentFields(events[event])["fields"]
        if field not in all_fields:
            print("Field could not found!: ", field)
            return False
        return True

    def construct_percentile_stats(
            self, event: str, field: str, check_event_field: bool = True,
            print_results: bool = False
    ):
        if check_event_field:
            if not self._check_event_field_existence(event, field):
                return None
        modified_field = event + "." + field
        query_condition = {
            modified_field: {"$ne": None}
        }
        sort_condition = {
            modified_field: -1
        }
        results = list(
            self.get_filtered_stats_players(
                event_collections=[event], query_conditions=query_condition,
                event_params=[modified_field], sort_conditions=sort_condition,
                join_f40=False
            )
        )
        norm = len(results)
        if norm == 0:
            return None
        prev_value = results[0][event][0][field]
        distribution = norm
        for index in range(norm):
            temp_player = results[index]
            next_value = temp_player[event][0][field]
            if next_value != prev_value:
                distribution = norm - index - 1
            temp_percentiles = (distribution / norm) * 100
            results[index][event][0][field] = temp_percentiles
            prev_value = next_value
        if print_results:
            print(json.dumps(results, indent=4))
        return results

    def get_percentile_stats(
            self, event: str, field: str,  player_id: int = None, check_event_field: bool = True
    ):
        if check_event_field:
            if not self._check_event_field_existence(event, field):
                return None

        match_player = None
        if player_id is not None:
            match_player = {"playerID": player_id}

        modified_field = event + "." + field
        percentiles = list(
            self.get_filtered_stats_players(
                event_collections=[event], event_params=[modified_field],
                percentile=True, query_conditions=match_player
            )
        )
        missing_data_flag = bool(0 == len(percentiles))
        if missing_data_flag is False:
            candidate_player = percentiles[0]
            try:
                dummy_variable = candidate_player[event][0][field]
                missing_data_flag = False
            except (KeyError, IndexError):
                missing_data_flag = True
        if missing_data_flag:
            percentiles = self.construct_percentile_stats(event, field, False, False)
            if percentiles is None:
                percentiles = []
            for player in percentiles:
                player_id = player["playerID"]
                player_name = player["playerName"]
                value = player[event][0][field]
                APIHelpers.PlayerPercentileStatistics(
                    player_name=player_name,
                    player_id=player_id,
                    competition_id=self.competitionID,
                    season_id=self.seasonID,
                    event=event,
                    field=field,
                    value=value
                )
        return percentiles

    # --------------Find Specific Players in PlayerStatistics Document with some Conditions-----------------

    def get_filtered_stats_players(
            self, event_collections=None, query_conditions=None, team_names=None, event_params=None,
            sort_conditions=None, limit=None, return_pipeline=False, join_f40=True, per90=False, percentile=False
    ):
        """
        The given function does query operation on the "PlayerStatistics" object on the MongoDB.
        We can access any player in the system by specifying some conditions on some event parameters.
        As an example, in order to obtain all the players in Trabzonspor with aerial won bigger than 37 and
        has more than 3 goals in the desc order wrt goal numbers of players, and showing only these statistics
        of the resulting players, we need to use the function with following way;

        get_filtered_stats_players(
        event_collections=[aerial_event, shotand_goal_event],
        query_conditions={"$and":[{aerial_event.won:{"$gt":37}}, {shotand_goal_event.goals:{"$gt":3}}]},
        team_name=Trabzonspor,
        event_params=[aerial_event.won, shotand_goal_event.goals],
        sort_conditions={shotand_goal_event.goals: -1},
        limit=45)

        :param bool join_f40:
        :param bool percentile:
        :param list event_collections:
        :param dict query_conditions:
        :param list team_names:
        :param list event_params:
        :param dict sort_conditions:
        :param int limit:
        :param bool return_pipeline:
        :param bool per90:
        :return:
        :rtype:
        """

        if join_f40:
            new_fields = {
                "teamName": "name",
                "teamID": "uID",
                "playerName": "players.name",
                "playerID": "players.uID",
                "position": "players.position"
            }

            query_object = self.tapi().fast_lookup_f40_player().keep(
                *list(new_fields.values())
            )

            if team_names:
                if not isinstance(team_names, list):
                    team_names = [team_names]
                query_object.match({"name": {"$in": team_names}})

            query_object.parallelize("players")

            for key, value in new_fields.items():
                query_object.add_field(key, value)

            query_object.remove("name", "uID", "players")

        else:
            new_fields = {"playerName": None, "playerID": None}
            query_object = QueryPipeline(root_document=PlayerStatistics)

        field_names = self.evapi().getEventFieldsDict()
        mongo_db_field_names = self.evapi().getEventCollectionDict()
        if event_collections is None:
            event_collections = list(field_names.keys())

        if per90:
            query_object.join(self.doc_name(PlayerStatisticsPer90), "playerName", "playerName", "statistics")
        elif percentile:
            query_object.join(self.doc_name(PlayerPercentileStatistics), "playerName", "playerName", "statistics")
        else:
            query_object.join(self.doc_name(PlayerStatistics), "playerName", "playerName", "statistics")

        query_object.match({
            "statistics.competitionID": int(self.competitionID), "statistics.seasonID": int(self.seasonID)
        })

        for collection in event_collections:
            query_object.join(
                mongo_db_field_names[collection], "statistics." + field_names[collection], "_id", collection
            ).remove(collection + "._id")

        query_object.remove(["_id", "statistics", "stats"] + list(field_names.values()))

        if query_conditions:
            query_object.match(query_conditions)

        if event_params:
            event_params += list(new_fields.keys())
            query_object.keep(*event_params)

        if sort_conditions:
            query_object.sort(sort_conditions)

        if limit:
            query_object.limit(limit)

        if return_pipeline:
            return query_object

        result = query_object.run()
        return result

    # --------------Find Specific Players in F40_Player Document with some Conditions-----------------

    def get_filtered_personal_players(
            self, query_conditions=None, team_names=None, event_params=None, sort_conditions=None, limit=None
    ):
        """
        Following function does query operation on the "F40_Player" object on the MongoDB.We can access any player
        in the system by specifying some conditions on some personal parameters. Example, obtaining all the players
        with birth_date bigger than "1993-03-02" in the desc order.

        :param query_conditions:
        :param team_names:
        :param event_params:
        :param sort_conditions:
        :param limit:
        :return:
        """

        query_object = self.tapi().fast_lookup_f40_player()

        if team_names:
            query_object.match({"name": {"$in": team_names}})

        query_object.parallelize("players").join(self.doc_name(F40_Stat), "players.stats", "_id", "info")

        add_fields = {
            "teamName": "name",
            "playerName": "players.name",
            "playerID": "players.uID",
            "position": "players.position"
        }

        for key, value in add_fields.items():
            query_object.add_field(key, value)

        query_object.keep(*list(add_fields.keys()), "info").remove("_id", "info._id")

        if query_conditions:
            for logic_key in query_conditions.keys():
                new_condition_list = list()
                for condition in query_conditions[logic_key]:
                    temp_key = list(condition.keys())[0]
                    new_condition_list += [{"info": {"$elemMatch": {"type": temp_key, "value": condition[temp_key]}}}]
                query_conditions[logic_key] = new_condition_list
            query_object.match(query_conditions)

        if event_params:
            project_dict_info_list = list()
            for parameter in event_params:
                temp_project = {"$eq": ["$$info.type", parameter]}
                project_dict_info_list.append(temp_project)

            query_object.keep_with_condition(
                "player_info", "info", {"$or": project_dict_info_list}
            )

        if sort_conditions:
            query_object.sort(sort_conditions)

        if limit:
            query_object.limit(limit)

        result = query_object.run()

        return result

    # --------------Construct General Data of a Season (Mean, Standard Deviation etc.)-----------------

    def calculate_general_player_stats(
            self, event_collections=None, params_names=None, doc_name=None, player_ids=None, per90=False
    ):
        player_match_query = None
        if player_ids:
            player_match_query = {"playerID": {"$in": player_ids}}
        field_names = self.evapi().getEventDict()
        if event_collections is None:
            event_collections = list(field_names.keys())

        event_api = self.evapi()

        results_std = list()
        results_mean = list()
        results_max = list()
        results_min = list()
        for event in event_collections:
            event_results_mean = dict()
            event_results_std = dict()
            event_results_max = dict()
            event_results_min = dict()
            if params_names is None:
                all_params = event_api.getDocumentFields(event_api.getEventDict()[event])["fields"]
                all_params.remove("id")
            else:
                all_params = params_names

            player_query_obj = self.get_filtered_stats_players(
                event_collections=[event], query_conditions=player_match_query,
                return_pipeline=True, per90=per90, join_f40=False
            )

            for param in all_params:
                if "." in param:
                    parsed_param = param.split(".")
                    if parsed_param[0] != event:
                        continue
                    query_param = param
                    param = parsed_param[1]
                else:
                    query_param = event + "." + param

                copy_of_query_object = player_query_obj.copy()
                result = list(copy_of_query_object.keep(query_param).parallelize(event).group(
                    main_field=None, average_fields={"mean": query_param}, std_deviation={"std": query_param},
                    max_fields={"max": query_param}, min_fields={"min": query_param}
                ).remove("_id").run())

                if 0 < len(result):
                    result = result[0]
                    event_results_mean[param] = result["mean"]
                    event_results_std[param] = result["std"]
                    event_results_max[param] = result["max"]
                    event_results_min[param] = result["min"]

            results_std.append({event: event_results_std})
            results_mean.append({event: event_results_mean})
            results_max.append({event: event_results_max})
            results_min.append({event: event_results_min})

        main_result = {
            "mean": results_mean, "std": results_std,
            "max": results_max, "min": results_min
        }

        if doc_name:
            for key, value in main_result.items():
                APIHelpers.PlayerGeneralEventStatistics(
                    stat_name=doc_name, stat_type=key, competition_id=self.competitionID,
                    season_id=self.seasonID, results=value
                )
        return main_result

    def get_general_player_stats(
            self, event_collections=None, params_names=None, doc_name=None, player_ids=None, per90=False
    ):
        pre_match = {"competitionID": int(self.competitionID), "seasonID": int(self.seasonID)}
        main_result = list()
        if doc_name:
            main_document_object = PlayerSeasonStatistics
            main_query_object = QueryPipeline(main_document_object)
            main_query_object.match({**pre_match, "statName": str(doc_name)})

            field_names = self.evapi().getEventFieldsDict()
            mongo_db_field_names = self.evapi().getEventCollectionDict()
            if event_collections is None:
                event_collections = list(field_names.keys())

            for collection in event_collections:
                main_query_object.join(
                    mongo_db_field_names[collection], field_names[collection], "_id", collection
                ).remove(collection + "._id")

            if params_names:
                main_query_object.keep(*params_names, "statName", "statType")

            main_query_object.remove(["_id"] + list(field_names.values()))

            main_result = list(main_query_object.run())

        if len(main_result) == 0 or doc_name is None:
            main_result = self.calculate_general_player_stats(
                event_collections=event_collections, params_names=params_names,
                doc_name=doc_name, player_ids=player_ids, per90=per90
            )

        return main_result

    # ----------------------------------------------------------------------------------

    def getPlayerStatObj(self, player_name):
        stat = PlayerStatistics.objects(
            Q(playerName=player_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        return stat

    def getAerial_Alt(self, player_name, params=None):  #* call like plObj.getAerial_Alt("Adem Ljajic", data["filters"])
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = AerialEvent.objects.exclude("id").get(id=stat.aerialEvent.id)
            else:
                keys = AerialEvent.objects.exclude("id").only(*params).get(id=stat.aerialEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getAsist(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = AssistEvent.objects.exclude("id").get(id=stat.assistEvent.id)
            else:
                keys = AssistEvent.objects.exclude("id").only(*params).get(id=stat.assistEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getBallControl(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = BallControlEvent.objects.exclude("id").get(id=stat.ballControlEvent.id)
            else:
                keys = BallControlEvent.objects.exclude("id").only(*params).get(id=stat.ballControlEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getFoul(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = FoulEvent.objects.exclude("id").get(id=stat.foulEvent.id)
            else:
                keys = FoulEvent.objects.exclude("id").only(*params).get(id=stat.foulEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getCard(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = CardEvent.objects.exclude("id").get(id=stat.cardEvent.id)
            else:
                keys = CardEvent.objects.exclude("id").only(*params).get(id=stat.cardEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getPass(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = PassEvent.objects.exclude("id").get(id=stat.passEvent.id)
            else:
                keys = PassEvent.objects.exclude("id").only(*params).get(id=stat.passEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getTakeOn(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = TakeOnEvent.objects.exclude("id").get(id=stat.takeOnEvent.id)
            else:
                keys = TakeOnEvent.objects.exclude("id").only(*params).get(id=stat.takeOnEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getTouch(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = TouchEvent.objects.exclude("id").get(id=stat.touchEvent.id)
            else:
                keys = TouchEvent.objects.exclude("id").only(*params).get(id=stat.touchEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getDuel(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = DuelEvent.objects.exclude("id").get(id=stat.duelEvent.id)
            else:
                keys = DuelEvent.objects.exclude("id").only(*params).get(id=stat.duelEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getShotAndGoal(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = ShotandGoalEvent.objects.exclude("id").get(id=stat.shotEvent.id)
            else:
                keys = ShotandGoalEvent.objects.exclude("id").only(*params).get(id=stat.shotEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getGoalKeeping(self, player_name, params=None):
        stat = self.getPlayerStatObj(player_name)
        if stat is not None:
            if params is None:
                keys = GoalkeeperEvent.objects.exclude("id").get(id=stat.goalkeeperEvent.id)
            else:
                keys = GoalkeeperEvent.objects.exclude("id").only(*params).get(id=stat.goalkeeperEvent.id)
            keys_dict = json.loads(keys.to_json())
            return keys_dict

    def getSeasonTeamPKs(self):  # * return the primary keys of all F40_Team objects --> normalTeams, transferTeams, All
        '''
        This function returns the primary keys of all F40_Team documents in season.
        '''
        feed = self.connector.getFeed(Parser.Feeds.feed40, self.competitionID, self.seasonID, None)
        teams1 = feed.team
        teams1 = list(map(lambda x: x.pk, teams1))
        teams2 = feed.playerChanges
        teams2 = list(map(lambda x: x.pk, teams2))
        return teams1, teams2, teams1+teams2

    def getSeasonPlayerPKs(self):
        '''
        This function returns the primary keys of all F40_Player documents in season.
        '''
        feed = self.connector.getFeed(Parser.Feeds.feed40, self.competitionID, self.seasonID, None)
        playerPKs = []
        teams1 = feed.team
        for team1 in teams1:
            temp1 = list(map(lambda x: x.pk, team1.players))
            playerPKs += temp1
        teams2 = feed.playerChanges
        for team2 in teams2:
            temp2 = list(map(lambda x: x.pk, team2.players))
            playerPKs += temp2
        return playerPKs

    def get_player_data_fast(self, player_name):
        player_pks = self.getSeasonPlayerPKs()
        pipeline = [
            {
                "$match": {
                    "name": player_name
                }
            },
            {
                "$lookup": {
                    "from": "f40__stat",
                    "localField": "stats",
                    "foreignField": "_id",
                    "as": "player_stats"
                }
            },
            {
                "$project": {
                    "name": 1, "position": 1, "player_stats": 1
                }
            },
            {
                "$unset": "_id",
            },
            {
                "$unset": "player_stats._id",
            }
        ]
        result = F40_Player.objects(pk__in=player_pks).aggregate(pipeline)
        data = {}
        if result is not None:
            player_stats = result.next()["player_stats"]
            # print(player_stats)
            for stat in player_stats:
                data[stat["type"]] = stat["value"]
                # print(stat)
        data["team_name"] = self.get_team_fast(player_name, True)[0]
        return data

    def get_player_all_matches(self, player_name):
        current_team_name, old_team_name = self.get_both_team(player_name)

        player_data = self.get_player_data_fast(player_name)
        join_date = player_data["join_date"]
        join_date = join_date + "T24:59:59"
        if old_team_name is None and current_team_name is not None:  # none_transferred player
            games = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=current_team_name) | Q(homeTeamName=current_team_name)) &
                Q(periodOneStart__gte=join_date)
            ).exclude("id").only(
            *["ID", "awayTeamName", "awayScore", "homeTeamName", "homeScore"])
        elif old_team_name is not None and not current_team_name:  # retired or transferred other team
            leave_date = player_data["leave_date"] + "T00:00:00"
            games = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=old_team_name) | Q(homeTeamName=old_team_name)) &
                Q(periodOneStart__lte=leave_date)
            ).exclude("id").only(
            *["ID", "awayTeamName", "awayScore", "homeTeamName", "homeScore"])
        else:  # transferred to some team in superlig at the half
            games_1 = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=current_team_name) | Q(homeTeamName=current_team_name)) &
                Q(periodOneStart__gte=join_date)
            ).exclude("id").only(
            *["ID", "awayTeamName", "awayScore", "homeTeamName", "homeScore"])
            games_2 = F24_Game.objects(
                Q(competitionID=int(self.competitionID)) &
                Q(seasonID=int(self.seasonID)) &
                (Q(awayTeamName=old_team_name) | Q(homeTeamName=old_team_name)) &
                Q(periodOneStart__lte=join_date)
            ).exclude("id").only(
            *["ID", "awayTeamName", "awayScore", "homeTeamName", "homeScore"])
            games = list(games_2) + list(games_1)
        result = []
        for game in games:
            temp_res = {}
            temp = {}
            temp["homeTeam"] = game.homeTeamName
            temp["homeScore"] = int(game.homeScore)
            temp["awayTeam"] = game.awayTeamName
            temp["awayScore"] = game.awayScore
            temp_res["gameID"] = game.ID
            temp_res["score"] = temp
            result.append(temp_res)
        return result

    def get_player_name_filtered(self, least_total_time=None, team_name=None, position=None):
        pipeline = []
        playerPKs = self.getSeasonPlayerPKs()
        if position:
            pipeline.append({"$match": {"position": position}})

        if team_name:
            temp = {
                "$lookup": {
                    "from": "f40__team",
                    "localField": "_id",
                    "foreignField": "players",
                    "as": "team_players"
                }

            }
            pipeline.append(temp)
            pipeline.append({"$unwind": "$team_players"})
            pipeline.append({"$match": {"team_players.name": team_name}})

        pipeline.append({"$project": {"name": 1}})
        pipeline.append({"$unset": "_id"})

        if least_total_time:
            time_filter_temp = self.get_filtered_total_play_time_stats(
                query_after_group={"total_played_time": {"$gte": least_total_time}},
                project='playerName'
            )
            time_filtered_players = []
            for doc in time_filter_temp:
                time_filtered_players.append(doc["playerName"])
            q_result = F40_Player.objects(Q(name__in=time_filtered_players) & Q(pk__in=playerPKs)).aggregate(pipeline)
        else:
            q_result = F40_Player.objects(pk__in=playerPKs).aggregate(pipeline)

        result = []
        for doc in q_result:
            result.append(doc)

        return result

    def get_season_all_player_and_team_name(self):
        players = F40_Player.objects(pk__in=self.getSeasonPlayerPKs()).only("name")
        # [F40_Player, F40_Player, ...] -> [ {search_type: P, name: P_name}, ... ]
        # F40_Player -> {search_type: P, name: P_name}

        player_list = list(map(lambda x: {"search_type": "P", "name": x.name}, players))
        team_pks,a,b = self.getSeasonTeamPKs()
        teams = F40_Team.objects(pk__in=team_pks).only("name")
        team_list = list((map(lambda x: {"search_type": "T", "name": x.name}, teams)))
        return player_list + team_list

    def get_season_all_player_name(self):
        players = F40_Player.objects(pk__in=self.getSeasonPlayerPKs()).only("name")
        # [F40_Player, F40_Player, ...] -> [ {search_type: P, name: P_name}, ... ]
        # F40_Player -> {search_type: P, name: P_name}
        player_list = list(map(lambda x: {"name": x.name}, players))

        return player_list

    def getPlayerData_Alt(self, playerName, teamName=None):  # * it seem to pass test
        '''
        This function returns the some data (nationality, age, etc.) about player.
        :param playerName: It is a string that stands for the player name.
        :param teamName: It is a string that stands for the team name.
        '''
        feed = self.connector.getFeed(Parser.Feeds.feed40, self.competitionID, self.seasonID, None)
        searchedPlayer = None
        data = {}
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    if player.name == playerName:
                        searchedPlayer = player
                        break  # * to increase performance little bit
                break
        if searchedPlayer is None:
            for team in feed.playerChanges:
                for player in team.players:
                    if player.name == playerName:
                        searchedPlayer = player
        for stat in searchedPlayer.stats:
            data[stat.type] = stat.value
        return data

    def getPlayerID_Alt(self, playerName):  # * it seem to pass test
        playerPKs = self.getSeasonPlayerPKs()  # this takes PKs with season parameter
        playerObjs = F40_Player.objects(Q(name=playerName) & Q(pk__in=playerPKs)).only("uID")
        if playerObjs:
            return playerObjs[0].uID

    def getAllPlayerIDs_Alt(self,teamName, option=None):  # * it seems to pass test
        team, playerChanges, all = self.getSeasonTeamPKs()  # it work with option parameter.
        desiredPKs = []                                     # if option is "left" it returns playerIDs for players left the team
                                                            # if option is "all" it returns all playerIDs
        if option == "left":                                # otherwise it returns the playerIDs for players stay the team.
            desiredPKs = playerChanges
        elif option == "all":
            desiredPKs = all
        else:
            desiredPKs = team

        desired_team = F40_Team.objects(Q(name=teamName) & Q(pk__in=desiredPKs)).fields(players=1)
        if len(desired_team) == 1:
            return list(map(lambda x: x.uID, desired_team[0].players))
        elif len(desired_team) == 2:  # statement for "all" option
            return list(map(lambda x: x.uID, desired_team[0].players + desired_team[1].players))
        return None

    def getTeamID_Alt(self, teamName):  # ? to be tested
        teamPKs, changesPK, allPKs = self.getSeasonTeamPKs()
        team = F40_Team.objects(Q(name= teamName) & Q(pk__in=allPKs)).fields(uID=1).first()
        return team.uID

    def getAllTeamIDs_Alt(self):
        teams = F40_Team.objects(country="Turkey").fields(uID=1)
        return list(map(lambda x : x.uID, teams))
        #* teams = {F40_Team,F40_Team, ...}

    def getAllPlayersInTeam_Alt(self, team_name):
        player_names = self.getTeamAllPlayerNames_Alt(team_name)
        players_events = []
        for name in player_names:
            events = self.getPlayerEvents_Alt(team_name, name)
            players_events.append(events)
        return players_events

    def getTeamAllPlayerNames_Alt(self, teamName, option=None):  # * it seems to pass test
        team, playerChanges, all = self.getSeasonTeamPKs() # it work with option parameter.
                                                           # if option is "left" it returns playerNames left the team
        if option == "left":                               # if option is "all" it returns all playerNames
            desiredPKs = playerChanges                     # otherwise it returns the playerNames stay the team.
        elif option == "all":
            desiredPKs = all
        else:
            desiredPKs = team

        desired_team = F40_Team.objects(Q(name=teamName) & Q(pk__in=desiredPKs)).fields(players=1)
        if len(desired_team) == 1:
            return list(map(lambda x: x.name, desired_team[0].players))
        elif len(desired_team) == 2:  # statement for "all" option
            return list(map(lambda x: x.name, desired_team[0].players + desired_team[1].players))
        return None

    def getPlayerEvents_Alt(self, teamName, playerName):
        teamID = self.getTeamID_Alt(teamName)
        playerID = self.getPlayerID_Alt(playerName)
        events = F24_Event.objects(Q(teamID=int(teamID[1:])) & Q(playerID=int(playerID[1:])))
        return events

    def getDuplicatePlayersID(self):  #this is presumably generic method for finding duplicate players(for now it can detect player duplicate with 2)
        pipeline = [
            {"$group": {"_id": "$uID", "totalIDCount": {"$sum": 1}}},    #this process in pipeline group document with respect to uID and count how many of them
            {"$match": {"totalIDCount": 2}}                              #this process in pipeline filter doc if "totalIDCount" == 2 take element
        ]
        uID_counts = F40_Player.objects.aggregate(pipeline)
        # return format CommandCursor like a iterator in C++ probably

        list_uID = []

        for doc in uID_counts: # format of doc is like -->  { "_id" : "p66807", "totalIDCount" : 2  }
            # print(doc)
            list_uID = list_uID + [doc]

        duplicate_id_list = map(lambda x: x["_id"], list_uID)

        return list(duplicate_id_list)

    def getDuplicatePlayersName(self):  #this is presumably generic method for finding duplicate players(for now it can detect player duplicate with 2)
        pipeline = [
            {"$group": {"_id": "$name", "totalNameCount": {"$sum": 1}}},    #this process in pipeline group document with respect to uID and count how many of them
            {"$match": {"totalNameCount": 2}}                              #this process in pipeline filter doc if "totalIDCount" == 2 take element
        ]
        name_counts = F40_Player.objects.aggregate(pipeline)
        # return format CommandCursor like a iterator in C++ probably

        list_name = []

        for doc in name_counts: # format of doc is like -->  { "_id" : "player name", "totalIDCount" : 2  }
            # print(doc)
            list_name = list_name + [doc]

        duplicate_name_list = map(lambda x: x["_id"], list_name)

        return list(duplicate_name_list)

    def getDiffPlayers(self): # this is not generic method for collecting duplicate player just compare players in first half and second half.
                              # if one player fetched first and second half then it was added to the return list
        playerHalf1 = F40_Team.objects(country="Turkey").fields(name=1, players=1)
        # gives us {team1, team2 , .. } in first half where we can fetch player
        player_ids_h1 = []
        for i in range(len(playerHalf1)):
            temp_playerList = list(map(lambda x: x.uID, playerHalf1[i].players))
            player_ids_h1 = player_ids_h1 + temp_playerList
        # print(len(player_ids_h1))
        # print(player_ids_h1)

        playerHalf2 = F40_Team.objects(country=None).fields(name=1, players=1)
        # gives us {team1, team2 , .. } in second half where we can fetch player
        player_ids_h2 = []
        for i in range(len(playerHalf2)):
            temp_playerList = list(map(lambda x: x.uID, playerHalf2[i].players))
            player_ids_h2 = player_ids_h2 + temp_playerList
        # print(len(player_ids_h2))
        # print(player_ids_h2)

        duplicate_1to2_h = []
        for i in range(len(player_ids_h1)):
            for j in range(len(player_ids_h2)):
                if (player_ids_h1[i] == player_ids_h2[j]):
                    duplicate_1to2_h = duplicate_1to2_h + [player_ids_h2[j]]

        return duplicate_1to2_h

    def getOldTeamWithName(self, playername):  # This function return the team that player has been left from
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        teams = feed.playerChanges
        for team in teams:
            playerNames = list(map(lambda x: x.name, team.players))
            if (playername in playerNames):
                return team.name
        return None

    def getCurrentTeamWithName(self, playername):  # This function return the team where player finished the season
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        teams = feed.team
        for team in teams:
            playerNames = list(map(lambda x: x.name, team.players))
            if(playername in playerNames):
                return team.name
        return None

    def getProblematicPlayers(self):  # !  wrong approach
        players = F40_Player.objects.distinct(field='name')
        # print(players)
        prob_players= []
        for player in players:
            oldTeam = self.getOldTeamWithName(player)
            currentTeam = self.getCurrentTeamWithName(player)
            if(oldTeam is not None) and (currentTeam is None):
                temp = []
                temp.append(player)
                temp.append(oldTeam)
                prob_players.append(temp)
        return prob_players

    def getPlayerBothTeam(self, doublePlayers):                              # give parameter to list of playerName
        oldTeam = list(map(self.getOldTeamWithName, doublePlayers))          # it returns list of list like:
        currentTeam = list(map(self.getCurrentTeamWithName, doublePlayers))  # -->[[player, oldTeam, newTeam],[],[]..]
        transferred_players_list = []
        for i in range(len(doublePlayers)):
            temp = []
            temp = temp + [doublePlayers[i]]
            temp = temp + [oldTeam[i]]
            temp = temp + [currentTeam[i]]
            transferred_players_list = transferred_players_list + [temp]
        return transferred_players_list

    def getPositionPlayer(self, playerName):
        '''
        This function returns the position of given player.
        :param playerName: It is a string that stands for the player name.
        '''
        playerPKs = self.getSeasonPlayerPKs()
        playerObjs = F40_Player.objects(Q(name=playerName) & Q(pk__in=playerPKs)).only("position")
        if playerObjs:
            return playerObjs[0].position

    def getPositionPlayer_Alt(self, playerName, teamName=None):
        '''
        This function returns the position of given player.
        :param playerName: It is a string that stands for the player name.
        :param teamName:  It is a string that stands for the team name.
        '''
        feed = self.connector.getFeed(  # if player left from some team we do not need teamName parameter
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    if player.name == playerName:
                        return player.position

        for first_team in feed.playerChanges:
            for player in first_team.players:
                if player.name == playerName:
                    return player.position

    def printEverythingPlayer(self,playerName):
        print("---------------------------------------------------------{}---------------------------------------------------------".format(playerName))
        position = self.getPositionPlayer(playerName)
        oldTeam = self.getOldTeamWithName(playerName)
        currentTeam = self.getCurrentTeamWithName(playerName)
        print(f"{playerName} is {position}")
        if oldTeam is None and currentTeam is not None:
            print(f"{playerName} most probably played for {currentTeam} whole season.")
            print(f"{playerName} transferred to {currentTeam} from the outside, with the low probability.")
        elif oldTeam is not None and currentTeam is not None:
            print(f"{playerName} transferred from {oldTeam} to {currentTeam}")
        elif oldTeam is not None and currentTeam is None:
            print(f"{playerName} either has been transferred from {oldTeam} to outside or has been retired.")
        else:
            print("There is something wrong with this record or player.")

        if position == "Goalkeeper":
            data20 = {
                "event": "goalkeeping",
                "filters": ['clean_sheet', 'crosses_faced', 'cross_percentage_gk', 'goal_kicks', 'successful_gk_throws',
                            'save_percentage', 'save_1on1', 'saves', 'save_penalty']
            }
            data15 = {
                "event": "card",
                "filters": ['total_cards', 'yellow_card', 'second_yellow_card', 'red_card', 'card_rescinded']
            }
            goalkeeping_stat = self.getGoalKeeping(playerName,data20["filters"])
            if goalkeeping_stat:
                # print(f"save percantage is {goalkeeping_stat['save_percentage']}")
                print(f"goalkeeping statistics are:\n \t{goalkeeping_stat}")
            card_stat = self.getCard(playerName,data15["filters"])
            if card_stat:
                print(f"card statistics are:\n \t{card_stat}")

        else:
            data12 = {
                "event": "asist",
                "filters": ['total_assists', 'assist_for_first_touch_goal', 'key_passes']
            }
            data15 = {
                "event": "card",
                "filters": ['total_cards', 'yellow_card', 'second_yellow_card', 'red_card']
            }
            data19 = {
                "event": "shoot and goal",
                "filters": ['goals', 'goals_outside_the_box', 'non_penalty_goals',
                            'total_shots', 'shooting_percentage']
            }
            asist_stat = self.getAsist(playerName, data12["filters"])
            card_stat = self.getCard(playerName, data15["filters"])
            goal_stat = self.getShotAndGoal(playerName, data19["filters"])
            if asist_stat:
                print(f"asist statistics are:\n \t{asist_stat}")
            if card_stat:
                print(f"card statistics are:\n \t{card_stat}")
            if asist_stat:
                print(f"shoot and goal statistics are:\n \t{goal_stat}")

    # This function returns the goal leaders as a list of dict it needs integer number parameter to know where the stop.
    def getGoalLeaders(self, number):
        stats = PlayerStatistics.objects(Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID)).fields(shotEvent=1, playerName=1)
        goalObjKeys = list(map(lambda x: x.shotEvent.pk, stats))
        goalPLayers = list(map(lambda x: x.playerName, stats))
        print(goalObjKeys)
        print(goalPLayers)
        goals = ShotandGoalEvent.objects(pk__in=goalObjKeys).fields(goals=1, pk=1).order_by('-goals', '+pk').limit(number)
        goalLeaderList = []
        for i in range(number):
            temp = {}
            temp["player"] = goalPLayers[goalObjKeys.index(goals[i].pk)]  # * Note: If we need this type of operations
            temp["goal"] = goals[i].goals                                 # * more we can use hash table structure.
            goalLeaderList.append(temp)
            print(temp)
        return goalLeaderList

    def getAllGames(self):
        '''
        This function returns the all game ids in season
        '''
        playedGames = []
        feed = self.connector.getFeed(Parser.Feeds.feed1, self.competitionID, self.seasonID)
        for mdata in feed.matchData:
            playedGames.append(mdata.uID)
        return playedGames

    def tryLookup(self):
        teamPKs, playerChangedPKs, allPKs = self.getSeasonTeamPKs()
        curosr = F40_Player.objects.aggregate(*[
            {
                '$lookup': {
                    'from': F40_Team._get_collection_name(),
                    'localField': '_id',
                    'foreignField': 'players',
                    'as': 'belongTeam'}
            },
            {"$match": {"name": "Burak Yilmaz"}},
            {
                "$project": {
                    "name": "$name",
                    "teamName": "$belongTeam.name",
                    "teamPK": "$belongTeam._id",
                    # 'inSeason': {'$in': ["$belongTeam._id", allPKs]},

                }
            }
        ])
        print(teamPKs)
        print(type(teamPKs[0]))
        for doc in curosr:
            print(doc)
            print(doc["teamPK"])
            print(type(doc["teamPK"][0]))

#? end of new query based fetch functions

    def getPlayerID(self, playerName, teamName): #! Done
        # print(playerName, teamName)
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    print(player.name)
                    if player.name == playerName:
                        return player.uID

        for first_team in feed.playerChanges:
            for player in first_team.players:
                if player.name == playerName:
                    return player.uID

    def getAllPlayerIDs(self, teamName):  #! Done
        ids = []
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    ids.append(player.uID)
        for team2 in feed.playerChanges:
            if team2.name == teamName:
                for player2 in team2.players:
                    ids.append(player2.uID)
        return ids

    def getAllPlayedGamesBy(self, feed, teamName, playerId):
        gameIds = []
        games = []
        for game in feed.matchData:
            if game.uID is not None:
                game = self.connector.getFeed(
                    Parser.Feeds.feed24, self.competitionID, self.seasonID, game.uID
                )
                gameIds.append(game.gameID)
                games.append(game)

        return self.getGamesPlayedBy(games, gameIds, teamName, playerId)

    def getGamesPlayedBy(self, gameIds, teamName, playerId):
        filteredGameIds = []
        for gameId in gameIds:
            feed = self.connector.getFeed(
                Parser.Feeds.feed9, self.competitionID, self.seasonID, gameId
            )
            teamId = None
            for team in feed.teams:
                if team.name == teamName:
                    teamId = team.uID
                if teamId is not None:
                    for t in feed.matchData.teamData:
                        if t.teamRef == teamId:
                            for item in t.playerLineUp:
                                # print("player", item.playerRef, playerId)
                                if item.playerRef == playerId:
                                    # print("player", item.playerRef, playerId, gameId)
                                    filteredGameIds.append(gameId)
                                    break
        return filteredGameIds

    def getTeamID(self, teamName): #! Done
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        for team in feed.team:
            if team.name == teamName:
                return team.uID

    def getGoalKeeperEvents(self, team_name, player_name):
        """
        Return the all events of a game
        :param gameId:
        :return:
        """
        playerID = self.getPlayerID(player_name, team_name)  # find the player id
        teams_ids = self.getAllTeamIDs()
        events = []
        # player_events = self.getPlayerEventsByIds(self.getTeamID(team_name), playerID)
        player_events, other_events = self.getAllEventsByIds(
            self.getTeamID(team_name), playerID
        )
        # for team_id in teams_ids:
        #     player_events = self.getPlayerEventsByIds(team_id,playerID)
        #     print(len(player_events))
        #     events = events + player_events
        # print("total size of events",len(events))
        return player_events, other_events

    def getAllTeamIDs(self): #! Done
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        teams_ids = []
        for team in feed.team:
            teams_ids.append(team.uID)
        return teams_ids

    def getPlayerEventsByIds(self, teamID, playerID):

        gameIDs = self.getGamesPlayedByTeam(teamID)  # get all played game ids
        events = []
        playerID = playerID[1:]  # player ip includes p character
        for gid in gameIDs:  # read all events where team id is equal to the event id
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if playerID == str(event.playerID):
                    events.append(event)
        return events

    def getAllEventsByIds(self, teamID, playerID):

        gameIDs = self.getGamesPlayedByTeam(teamID)  # get all played game ids
        events = []
        other_events = []
        for gid in gameIDs:  # read all events where team id is equal to the event id
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if teamID[1:] != str(event.teamID):  # ! opposite team is excluded.
                    continue
                if playerID[1:] == str(event.playerID):
                    events.append(event)
                else:
                    other_events.append(event)
        return events, other_events

    def processEvents(self, events, teamName=None, playerName=None, requested_statistics=None):
        handler = EventHandler()
        teamID = self.getTeamID(teamName)
        playerID = self.getPlayerID(playerName, teamName)
        data = dict()
        data["teamID"] = teamID
        data["oldTeamID"] = "t-1"
        oldTeamName = self.getOldTeamWithName(playerName)
        if oldTeamName is not None:
            data["oldTeamID"] = self.getTeamID(oldTeamName)
        data["playerName"] = playerName
        data["total_minutes"] = self.getPlayerGamesPlayed(teamName, playerName, 34)["total_minutes"]
        data["events"] = events
        data["all_events"] = GameAPI.GameAPI(self.competitionID, self.seasonID).getAllSeasonGameEvents(teamID, playerID)

        if requested_statistics:
            if requested_statistics == EventIDs.GamesandMinutesEvents:
                data["playerID"] = playerID[1:]
            else:
                data["playerID"] = playerID
            result = handler.handle_single_event(requested_statistics, data)
        else:
            data["playerID"] = playerID
            result = handler.handle_all_events(data)
        return result

    def getTeamAllPlayerNames(self, teamName): #! Done
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        players = []
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    players.append(player.name)
        return players

    def comparePlayersEventStatistics(self, teams_players):
        """
        expected object should look like this
        [{team:team_name,player:player_name},{team:team_name,player:player_name},..]
        :param teams_players:
        :return:
        """
        players_stats = []
        for player in teams_players:
            result = self.getPlayerStatistics(player["team"], player["player"])
            players_stats.append(json.loads(result))
        return json.dumps(players_stats)

    # --------------Calculate Player Statistics------------------

    def get_player_events(self, player_id: int, team_ids: list, game_ids: list):
        gapi = self.gapi()
        player_events = list()

        for team_id in team_ids:
            events = gapi.get_match_data(
                game_ids=game_ids,
                player_ids=player_id,
                team_ids=team_id,
                get_f24_event_objects=True
            )
            if len(events) != 0:
                for game in events:
                    try:
                        player_events += game["events"][0][team_id][player_id]
                    except KeyError:
                        continue

        return player_events

    def get_game_all_events(self, game_ids: list, team_ids: list):
        gapi = self.gapi()
        events = gapi.get_match_data(
            team_ids=team_ids,
            game_ids=game_ids,
            get_f24_event_objects=True
        )
        all_events = list()
        if len(events) != 0:
            for game in events:
                for played_team in game["events"]:
                    for team_id in team_ids:
                        if team_id in played_team:
                            all_events += played_team[team_id]
        return all_events

    def calculateStatistics(self, player_name: str):
        player_id = self.get_player_id(player_name=player_name)
        team_ids = self.get_played_teams_of_player(player_id)
        game_ids = list()
        for team_id in team_ids:
            game_ids += self.get_player_games_played(
                player_id=player_id, team_id=team_id, play_time_non_zero=True
            )
        for index in range(len(game_ids)):
            game_ids[index] = str(game_ids[index])
        events = self.get_player_events(player_id=player_id, team_ids=team_ids, game_ids=game_ids)
        if events is None:
            print("no events is available")
            return None

        logging.info("all events are collected")
        handler = EventHandler()
        data = dict()
        data["teamID"] = team_ids
        data["playerID"] = player_id
        data["playerName"] = player_name
        total_time = self.get_player_total_play_time(player_id)
        if total_time == 0 or total_time is None:
            return None
        data["total_minutes"] = total_time
        data["events"] = events

        results = handler.handle_all_events(data, print_results=False)
        if player_id:
            player_stat = APIHelpers.PlayerEventStatistics(
                player_name,
                player_id,
                self.competitionID,
                self.seasonID,
                team_ids,
                results.copy(),
            )
            player_stat.storeInDB()
            return True

        return None

    def preparePlayerStatisticsForSeason(self, stat: PlayerStatistics, event_type: list = None):
        team_names = self.get_played_teams_of_player(player_id=stat.playerID)
        st = APIHelpers.PlayerEventStatistics(
            stat.playerName,
            stat.playerID,
            stat.competitionID,
            stat.seasonID,
            team_names,
            None,
        )
        st.eventResults = []

        # Dictionary of all event documents in the database.
        events = {
            "aerial": stat.aerialEvent,
            "pass": stat.passEvent,
            "foul": stat.foulEvent,
            "card": stat.cardEvent,
            "ballControl": stat.ballControlEvent,
            "takeOn": stat.takeOnEvent,
            "touch": stat.touchEvent,
            "duel": stat.duelEvent,
            "shot": stat.shotEvent,
            "assist": stat.assistEvent,
            "goalkeeper": stat.goalkeeperEvent
        }

        if event_type is None:
            event_type = list(events.keys())

        for event in event_type:
            st.eventResults.append({event: events[event]})

        return st

    @staticmethod
    def filter_event_results(obj):
        if obj:
            aobj = json.loads(obj)
            new_aobj = dict()
            new_aobj["event_results"] = {}

            for item in aobj["eventResults"]:
                for key, value in item.items():
                    if value is not None:
                        alist = value["_data"]
                        del alist["_id"]
                        new_aobj["event_results"][key] = alist
            aobj["eventResults"] = new_aobj["event_results"]
            return aobj
        return '{}'

    def getPlayerStatistics(self, player_name: str, event_type: list = None):
        stat = PlayerStatistics.objects(
            Q(playerName=player_name)
            & Q(competitionID=int(self.competitionID))
            & Q(seasonID=int(self.seasonID))
        )

        if stat:
            obj = jsonSerializer(self.preparePlayerStatisticsForSeason(stat[0], event_type))
            return json.dumps(self.filter_event_results(obj))

        else:
            result = self.calculateStatistics(player_name)
            if result:
                stat = PlayerStatistics.objects(
                    Q(playerName=player_name)
                    & Q(competitionID=int(self.competitionID))
                    & Q(seasonID=int(self.seasonID))
                )

                if stat:
                    obj = jsonSerializer(self.preparePlayerStatisticsForSeason(stat[0]))
                    return json.dumps(self.filter_event_results(obj))

                else:
                    return jsonSerializer("{}")
            else:
                return jsonSerializer("{Error: user does not exist}")

    # ----------------------Update Player Statistics----------------

    def updatePlayerStatistics(
            self, data: list = None, mapper: dict = None, file_name: str = None, path_name: str = None
    ):
        stats_fields = list(self.evapi().getEventFieldsDict().values())
        for player in data:
            player_id = player["playerID"]
            player_document = PlayerStatistics.objects(
                Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID) & Q(playerID=player_id)
            ).first()
            if type(player) != dict:
                continue
            for field_name, statistics in player.items():
                if field_name not in stats_fields:
                    continue
                field_document = getattr(player_document, field_name)
                for stat, value in statistics.items():
                    if hasattr(field_document, stat):
                        try:
                            setattr(field_document, stat, value)
                            field_document.save()
                        except ValidationError as err:
                            print("VALIDATION ERROR: ", err)
                            print(f"The new value could not be updated: {value}")
                            continue

    # ------------------------------------------------------------------

    def getPlayerEventsByMinSec(
        self, team_name, player_name, frm_min, to_min, frm_sec=None, to_sec=None
    ):

        playerID = self.getPlayerID(player_name, team_name)  # find the player id
        teamID = self.getTeamID(team_name)  # find team id
        gameIDs = self.getGamesPlayedByTeam(teamID)  # get all played game ids
        events = []
        start = False
        for gid in gameIDs:  # read all events where team id is equal to the event id
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if playerID == str(event.playerID) and (frm_min <= event.min <= to_min):
                    if frm_sec is not None and to_sec is not None:
                        if not start:
                            if event.sec >= frm_sec:
                                start = True
                        if start:
                            if event.min == to_min:
                                if event.sec > to_sec:
                                    break
                            events.append(event)
                    else:
                        events.append(event)

        return events

    def getPlayerEventsInterval(self, team_name, player_name, frm_eventid, to_eventid):

        playerID = self.getPlayerID(player_name, team_name)  # find the player id
        teamID = self.getTeamID(team_name)  # find team id
        gameIDs = self.getGamesPlayedByTeam(teamID)  # get all played game ids
        events = []
        for gid in gameIDs:  # read all events where team id is equal to the event id
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if playerID == str(event.playerID) and (
                    frm_eventid <= event.eventID < to_eventid
                ):
                    events.append(event)

        return events

    def calculateMeanStatistics(self, stats):
        pass

    def getGamesPlayedByTeam(self, teamId):
        playedGames = []
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID
        )
        for mdata in feed.matchData:
            for item in mdata.teamData:
                if item.teamRef == teamId:
                    playedGames.append(mdata.uID)
        return playedGames

    def getPlayerGamesPlayed(self, team_name, player_name, fixtures):
        print("Inside getPlayerGamesPlayed")
        player_list = self.getPlayerKeys(team_name)
        transferred_list = self.getTransferredPlayerKeys(team_name)
        player_key = self.getChosenPlayerKey(player_list, transferred_list, player_name)
        team_id = self.getTeamKey(team_name)
        active_game_keys = self.getGameKeys(team_id, fixtures)

        team_id = self.getTeamID(team_name)
        data = dict()
        data["events"] = self.getEvents(active_game_keys)
        data["teamID"] = int(team_id.strip("t"))
        data["playerID"] = player_key
        data["playerName"] = player_name

        event_handler = GamesandMinutesEvents()
        result = event_handler.callEventHandler(data)

        return result

    def getGameKeys(self, team_id, fixtures):
        self.game_keys = ["" for x in range(fixtures)]
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID
        )
        counter = 0
        for mdata in feed.matchData:
            for item in mdata.teamData:
                if counter == fixtures:
                    break
                if item.teamRef[1:] == team_id:
                    self.game_keys[counter] = mdata.uID
                    counter += 1
        active_game_keys = []
        for i in range(fixtures):
            active_game_keys.append(self.game_keys[i])
        return active_game_keys

    def getPlayerKeys(self, team_name):
        feed = self.connector.getFeed("feed40", self.competitionID, self.seasonID, None)
        self.player_IDs = {}
        player_IDs_array = []
        for team in feed.team:
            if team.name == team_name:
                for p in team.players:
                    self.player_IDs["name"] = p.name
                    self.player_IDs["player_id"] = p.uID
                    player_IDs_array.append(self.player_IDs)
                    self.player_IDs = {"name": "", "player_id": ""}
        return player_IDs_array

    def getTransferredPlayerKeys(self, team_name):
        feed = self.connector.getFeed("feed40", self.competitionID, self.seasonID, None)
        player_IDs_array = []
        for team in feed.playerChanges:
            if team.name == team_name:
                for p in team.players:
                    self.player_IDs["name"] = p.name
                    self.player_IDs["player_id"] = p.uID
                    player_IDs_array.append(self.player_IDs)
                    self.player_IDs = {"name": "", "player_id": ""}
        return player_IDs_array

    def getTeamKey(self, team_name):
        feed = self.connector.getFeed("feed1", self.competitionID, self.seasonID, None)
        team_ID = str(0)
        for team in feed.teams:
            if team.name == team_name:
                team_ID = team.uID
        team_key = str(team_ID).strip("t")
        return team_key

    def getChosenPlayerKey(self, playerlist, transferredlist, player_name):
        for i in range(len(playerlist)):
            if player_name == playerlist[i]["name"]:
                player_id = playerlist[i]["player_id"]
                break
        for i in range(len(transferredlist)):
            if player_name == transferredlist[i]["name"]:
                player_id = transferredlist[i]["player_id"]
                break
        player_key = str(player_id).strip("p")
        return player_key

    def getEvents(self, gameIDs):
        """
        Returns an event list obtained by the given game Ids
        :param gameIDs:
        :return:
        """
        events = []
        for gid in gameIDs:  # read all events where team id is equal to the event id
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                events.append(event)
        return events


event_name_translation = {
            "aerialEvent": "aerial",
            "passEvent": "pass",
            "foulEvent": "foul",
            "cardEvent": "card",
            "ballControlEvent": "ballControl",
            "takeOnEvent": "takeon",
            "touchEvent": "touch",
            "duelEvent": "duel",
            "shotEvent": "shot",
            "assistEvent": "assist",
            "goalkeeperEvent": "goalkeeper"
        }
name_event_translation = {
            "aerial": "aerialEvent",
            "pass": "passEvent",
            "foul": "foulEvent",
            "card": "cardEvent",
            "ballControl": "ballControlEvent",
            "takeon": "takeOnEvent",
            "touch": "touchEvent",
            "duel": "duelEvent",
            "shot": "shotEvent",
            "assist": "assistEvent",
            "goalkeeper": "goalkeeperEvent"
        }

formations = {
    "2": "442",
    "3": "41212",
    "4": "433",
    "5": "451",
    "6": "4411",
    "7": "4141",
    "8": "4231",
    "9": "4321",
    "10": "532",
    "11": "541",
    "12": "352",
    "13": "343",
    "15": "4222",
    "16": "3511",
    "17": "3421",
    "18": "3412",
    "19": "3142",
    "20": "343d",
    "21": "4132",
    "22": "4240",
    "23": "4312",
    "24": "3241",
    "25": "3331",
}
detailed_position_id = {
    "1": "Goalkeeper",
    "2": "Wing Back",
    "3": "Full Back",
    "4": "Central Defender",
    "5": "Defensive Midfielder",
    "6": "Attacking Midfielder",
    "7": "Central Midfielder",
    "8": "Winger",
    "9": "Striker",
    "10": "Second Striker",
}
detailed_position_442 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Left Midfielder",
}
detailed_position_41212_diamond = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Defensive Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Centre Attacking Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Left Midfielder",
}
detailed_position_433 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Defensive Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Right Winger",
    "11": "Left Winger",
}
detailed_position_451 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Defensive Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Central Midfielder",
    "11": "Left Midfielder",
}
detailed_position_4411 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Centre Attacking Midfielder",
    "11": "Left Midfielder",
}
detailed_position_4141 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Defensive Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Central Midfielder",
    "11": "Left Midfielder",
}
detailed_position_4231 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Attacking Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Centre Attacking Midfielder",
    "11": "Left Attacking Midfielder",
}
detailed_position_4321 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Defensive Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Left Midfielder",
    "8": "Right Midfielder",
    "9": "Striker",
    "10": "Centre Attacking Midfielder",
    "11": "Centre Attacking Midfielder",
}
detailed_position_532 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Central Midfielder",
}
detailed_position_541 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Central Midfielder",
    "11": "Left Midfielder",
}
detailed_position_352 = {
    "1": "Goalkeeper",
    "2": "Right Wing Back",
    "3": "Left Wing Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Central Midfielder",
}
detailed_position_343 = {
    "1": "Goalkeeper",
    "2": "Right Wing Back",
    "3": "Left Wing Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Right Winger",
    "11": "Left Winger",
}
detailed_position_4222 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Centre Attacking Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Centre Attacking Midfielder",
}
detailed_position_3511 = {
    "1": "Goalkeeper",
    "2": "Right Wing Back",
    "3": "Left Wing Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Centre Attacking Midfielder",
    "11": "Central Midfielder",
}
detailed_position_3421 = {
    "1": "Goalkeeper",
    "2": "Right Wing Back",
    "3": "Left Wing Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Centre Attacking Midfielder",
    "11": "Centre Attacking Midfielder",
}
detailed_position_3412 = {
    "1": "Goalkeeper",
    "2": "Right Wing Back",
    "3": "Left Wing Back",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Central Midfielder",
    "8": "Central Midfielder",
    "9": "Centre Attacking Midfielder",
    "10": "Striker",
    "11": "Striker",
}
detailed_position_3142 = {
    "1": "Goalkeeper",
    "2": "Right Attacking Midfielder",
    "3": "Left Attacking Midfielder",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Centre Attacking Midfielder",
    "8": "Defensive Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Centre Attacking Midfielder",
}
detailed_position_343d = {
    "1": "Goalkeeper",
    "2": "Right Midfielder",
    "3": "Left Midfielder",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Centre Attacking Midfielder",
    "8": "Defensive Midfielder",
    "9": "Striker",
    "10": "Right Winger",
    "11": "Left Winger",
}
detailed_position_4132 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Attacking Midfielder",
    "8": "Centre Attacking Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Left Attacking Midfielder",
}
detailed_position_4240 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Attacking Midfielder",
    "8": "Central Midfielder",
    "9": "Centre Attacking Midfielder",
    "10": "Centre Attacking Midfielder",
    "11": "Left Attacking Midfielder",
}
detailed_position_4321 = {
    "1": "Goalkeeper",
    "2": "Right Back",
    "3": "Left Back",
    "4": "Central Midfielder",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Right Midfielder",
    "8": "Centre Attacking Midfielder",
    "9": "Striker",
    "10": "Second Striker",
    "11": "Left Midfielder",
}
detailed_position_3241 = {
    "1": "Goalkeeper",
    "2": "Defensive Midfielder",
    "3": "Defensive Midfielder",
    "4": "Left Back",
    "5": "Central Defender",
    "6": "Right Back",
    "7": "Centre Attacking Midfielder",
    "8": "Centre Attacking Midfielder",
    "9": "Striker",
    "10": "Right Attacking Midfielder",
    "11": "Left Attacking Midfielder",
}
detailed_position_3331 = {
    "1": "Goalkeeper",
    "2": "Central Midfielder",
    "3": "Central Midfielder",
    "4": "Central Defender",
    "5": "Central Defender",
    "6": "Central Defender",
    "7": "Centre Attacking Midfielder",
    "8": "Central Midfielder",
    "9": "Striker",
    "10": "Right Attacking Midfielder",
    "11": "Left Attacking Midfielder",
}
formations_played = []
positions_played = []
exact_position = []
