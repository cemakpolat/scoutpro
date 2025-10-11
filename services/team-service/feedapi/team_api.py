# What is the purpose ? Team statistics comparison
# select a year and country lig
# get all players and their statistics from events
# sum all player statistics for all games
# Migrated to microservices - imports updated to use shared libraries
import json
from datetime import *
import sys

# Add shared libraries to path
sys.path.append('/app')

# Shared library imports
from shared.connectors import Connector, main_conn
from shared.parsers.parser import Parser
from shared.events.event_handler import EventHandler
from shared.events.Events import EventTypes, EventIDs
from shared.events.QTypes import QTypes_PassEvents, QTypes_ShortLocationDescriptor, QTypes_FoulCardEvents
from shared.utils.opta_utils import *
from shared.models.mongoengine.feed_models import *
from shared.utils.query_pipeline import QueryPipeline


class TeamAPI:
    def __init__(self, competitionID, seasonID):
        self.competitionID = int(competitionID)
        self.seasonID = int(seasonID)
        self.connector = main_conn
        self.doc_name = get_doc_name
        self.online = False
        self.event_api_connection = False
        self.game_api_connection = False
        self.db_port = 27017
        self.host = "localhost"
        self.connector.connect()

    def evapi(self):
        # TODO: In microservices, this should call match-service API instead
        # Temporarily disabled - cross-service dependencies need HTTP calls
        raise NotImplementedError("EventAPI now in match-service - use HTTP API instead")

    def gapi(self):
        # TODO: In microservices, this should call match-service API instead
        # Temporarily disabled - cross-service dependencies need HTTP calls
        raise NotImplementedError("GameAPI now in match-service - use HTTP API instead")

    def lookup_f40_root(self):
        query_object = QueryPipeline(F40_Root)

        add_filed_dict = dict()
        for doc_field in self.evapi().getDocumentFields(F40_Team)["fields"]:
            add_filed_dict[doc_field] = "team." + str(doc_field)

        query_object.match({
            "competitionID": self.competitionID, "seasonID": self.seasonID
        }).keep("team", "playerChanges").join(
            self.doc_name(F40_Team), "team", "_id", "team"
        ).join(
            self.doc_name(F40_Team), "playerChanges", "_id", "playerChanges"
        ).parallelize("team").parallelize("playerChanges").match(
            {"$expr": {"$eq": ["$team.uID", "$playerChanges.uID"]}}
        )

        for key, value in add_filed_dict.items():
            query_object.add_field(key, value)
        query_object.remove("team").set_union(
            "players", "players", "playerChanges.players"
        ).remove("playerChanges")

        return query_object

    def fast_lookup_f40_player(self):
        query_object = self.lookup_f40_root()
        query_object.keep("name", "uID", "players").join(
            self.doc_name(F40_Player), "players", "_id", "players"
        )
        return query_object

    def lookup_f1_root_match_data(self):
        query_object = QueryPipeline(F1_Root)

        add_filed_dict = dict()
        for doc_field in self.evapi().getDocumentFields(F1_MatchData)["fields"]:
            add_filed_dict[doc_field] = "matchData." + str(doc_field)

        query_object.match({
            "competitionID": self.competitionID, "seasonID": self.seasonID
        }).keep("matchData").join(
            self.doc_name(F1_MatchData), "matchData", "_id", "matchData"
        ).parallelize("matchData")

        for key, value in add_filed_dict.items():
            query_object.add_field(key, value)
        query_object.remove("matchData").join(
            self.doc_name(F1_TeamData), "teamData", "_id", "teamData"
        )

        return query_object

    def fast_lookup_f1_root(self):
        query_object = QueryPipeline(F1_Root)
        query_object.match({
            "competitionID": self.competitionID, "seasonID": self.seasonID
        }).keep("teams").join(
            self.doc_name(F1_Team), "teams", "_id", "teams"
        ).parallelize("teams").add_field("name", "teams.name").add_field("uID", "teams.uID").remove("teams", "_ids")
        return query_object

    def getSeasonTeamsEvents(self):
        """
        Return the all events of a game
        :param gameId:
        :return:
        """
        teams_ids = self.getAllTeamIDs()
        events = []
        for id in teams_ids:
            events = events + self.getTeamEventsByTeamID(id)
        return events

    def getAllTeamNames(self):
        feed = self.connector.getFeed(Parser.Feeds.feed40, self.competitionID, self.seasonID)
        teams_names = []
        for team in feed.team:
            teams_names.append(team.name)
        return teams_names

    def getAllTeamIDs(self):
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        teams_ids = []
        print(len(feed.team))
        for team in feed.team:
            teams_ids.append(team.uID)
        return teams_ids

    def getTeamAllPlayers(self, teamName):
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        players = []
        for team in feed.team:
            if team.name == teamName:
                for player in team.players:
                    p = APIHelpers.Player(player.position)
                    p.name = player.name
                    p.position = player.position
                    p.uID = player.uID
                    p.stats = player.stats
                    p.stats = []
                    for stat in player.stats:
                        p.stats.append({stat.type: stat.value})
                    p.playerLoan = player.playerLoan

                    players.append(p)

        return jsonSerializer(players)

    def getTeamID(self, teamName):
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        for team in feed.team:
            if team.name == teamName:
                return team.uID

    def getTeamEvents(self, team_name):
        # find team id
        teamID = self.getTeamID(team_name)
        # get all played game ids
        gameIDs = self.getGamesPlayedByTeam(teamID)
        events = []
        # read all events where team id is equal to the event id
        for gid in gameIDs:
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if teamID.split("t")[1] == str(event.teamID):
                    events.append(event)

        return events

    def get_team_events(self, team_id: int, game_ids: list):
        gapi = self.gapi()

        team_ids = [team_id]

        events = gapi.get_match_data(
            game_ids=game_ids,
            team_ids=team_ids,
            get_f24_event_objects=True
        )
        team_events = list()
        if len(events) != 0:
            for game in list(events):
                team_events += game["events"][0][team_ids[0]]
        return team_events

    def getTeamEventsByTeamID(self, teamID):
        # get all played game ids
        gameIDs = self.getGamesPlayedByTeam(teamID)
        events = []
        # read all events where team id is equal to the event id
        for gid in gameIDs:
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if teamID.split("t")[1] == str(event.teamID):
                    events.append(event)

        return events

    def getTeamEventsByMinSec(
        self, team_name, frm_min, to_min, frm_sec=None, to_sec=None
    ):
        # find team id
        teamID = self.getTeamID(team_name)
        # get all played game ids
        gameIDs = self.getGamesPlayedByTeam(teamID)
        events = []
        # read all events where team id is equal to the event id
        start = False
        for gid in gameIDs:
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if teamID.split("t")[1] == str(event.teamID) and (
                    frm_min <= event.min <= to_min
                ):
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

    def getTeamEventsInterval(self, team_name, frm_eventid, to_eventid):
        # find team id
        teamID = self.getTeamID(team_name)
        # get all played game ids
        gameIDs = self.getGamesPlayedByTeam(teamID)
        events = []
        # read all events where team id is equal to the event id
        for gid in gameIDs:
            feed = self.connector.getFeed(
                Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
            )
            for event in feed.game.events:
                if teamID.split("t")[1] == str(event.teamID) and (
                    frm_eventid <= event.eventID < to_eventid
                ):
                    events.append(event.to_json())

        return events

    def getGamesPlayedByTeam(self, teamId):
        # teamId = "t" + str(teamId).replace("t", "").strip()
        playedGames = []
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID
        )
        for mdata in feed.matchData:
            for item in mdata.teamData:
                if item.teamRef == teamId:
                    playedGames.append(mdata.uID)
        return playedGames

    def getGamesPlayedIntervalByTeam(self, teamId, frm_date, to_date):
        playedGames = []
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID
        )
        for mdata in feed.matchData:
            date_time_obj = datetime.strptime(mdata.matchInfo.date, "%Y-%m-%d %H:%M:%S")
            if frm_date <= date_time_obj <= to_date:
                for item in mdata.teamData:
                    if item.teamRef == teamId:
                        playedGames.append(mdata.uID)
        return playedGames

    def getAllTeams(self):
        pass

    def getTeamsEvents(self, *teams_names):
        result = []
        for team_name in teams_names:
            result.append(self.getTeamEvents(team_name))
        return result

    def getTeamData(self, teamName):
        """
        # - team, GET
        competition / season / match / matchid / teams
        {
            name: "",
            uId: "",
            country: "",
            kit: {
                id: "",
                colour1: "",
                colour2: "",
                type: "home"
            },
            players: [
                {
                    first: "",
                    last: "",
                    position: "",
                    uID: ""
                }, {..}
        ]
        """

        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        for team in feed.team:
            if team.name == teamName:
                t = APIHelpers.Team(team.name, team.uID)
                t.stadium = APIHelpers.Stadium(team.stadium.name, team.stadium.uID)
                t.stadium.capacity = team.stadium.capacity
                t.country = team.country
                t.city = team.city
                t.countryISO = team.countryISO
                t.countryID = team.countryID
                t.postalCode = team.postalCode
                t.regionName = team.regionName
                t.regionID = team.regionID
                t.symid = team.symid
                t.shortClubName = team.shortClubName

                t.players = []
                for player in team.players:
                    p = APIHelpers.Player(player.position)
                    p.name = player.name
                    p.position = player.position
                    p.uID = player.uID
                    p.stats = []
                    for stat in player.stats:
                        p.stats.append({stat.type: stat.value})
                    p.playerLoan = player.playerLoan
                    t.players.append(p)

                t.kits = []
                for kit in team.kits:
                    k = APIHelpers.Kit(kit.id, kit.colour1, kit.type)
                    if kit.colour2:
                        k.colour2 = kit.colour2
                    t.kits.append(k)

                t.teamOfficials = []
                for tof in team.teamOfficials:
                    to = APIHelpers.TeamOfficial(
                        tof.personalInfo.first, tof.personalInfo.last, tof.type, tof.uID
                    )
                    to.country = tof.country
                    if tof.personalInfo.birthDate:
                        to.birthDate = tof.personalInfo.birthDate
                    if tof.personalInfo.joinDate:
                        to.joinDate = tof.personalInfo.joinDate
                    if tof.personalInfo.leaveDate:
                        to.leaveDate = tof.personalInfo.leaveDate
                    if tof.personalInfo.birthPlace:
                        to.birthPlace = tof.personalInfo.birthPlace
                    t.teamOfficials.append(to)

                return jsonSerializer(t)

        return []

    def getPlayerChanges(self, teamID):
        # return the whole object of the teamID
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        for team in feed.playerChanges:
            if team.uID == teamID:
                t = APIHelpers.Team(team.name, team.uID)
                t.name = team.name

                t.players = []
                for player in team.players:
                    p = APIHelpers.Player(player.position)
                    p.uID = player.uID
                    p.name = player.name
                    p.position = player.position
                    p.stats = []
                    for stat in player.stats:
                        p.stats.append({stat.type: stat.value})
                    t.players.append(p)

                t.teamOfficials = []
                for tof in team.teamOfficials:
                    tofficial = APIHelpers.TeamOfficial(
                        tof.personalInfo.first, tof.personalInfo.last, tof.type, tof.uID
                    )
                    tofficial.leaveDate = tof.personalInfo.leaveDate
                    tofficial.joinDate = tof.personalInfo.joinDate
                    tofficial.birthDate = tof.personalInfo.birthDate
                    tofficial.birthPlace = tof.personalInfo.birthPlace
                    tofficial.country = tof.country
                    t.teamOfficials.append(tofficial)

                return jsonSerializer(t)

    @staticmethod
    def filter_event_results(obj):
        '''
            This function is helper for getTeamStatistics functions.
        '''
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

    def get_all_sub_stat_names(self, stat_name):
        stat_list = EventAPI.EventAPI(
            self.competitionID, self.seasonID
        ).getEventParams(stat_name)
        stat_list.remove('id')
        return stat_list

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

    def getTeamEventGroup(self, team_name, event_group=None, params=None):
        '''
        This function can return the whole, specific or more specific statistics of team.
        With just team_name parameter it returns all statistics of team.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param team_name: It is a string that stands for the team name.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = TeamStatistics.objects(
            Q(teamName=team_name)
            & Q(competitionID=self.competitionID)
            & Q(seasonID=self.seasonID)
        ).first()
        if stat is not None:
            keys_dict = dict()
            if event_group is None:
                event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                                'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
                for group in event_groups:
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

    def getTeamAverageEventGroup(self, stat_name, stat_type, event_group=None, params=None):
        '''
        This function can return the whole, specific or more specific average statistics of all teams
        in season. With just stat_name and stat_type parameters it returns all statistics of season.
        Additional event_group and params parameter allow function to return more specific statistics.
        :param stat_name: It is a string that stands for the stat name like all_teams.
        :param stat_type: It is a string that stands for the stat type like average, standard_deviation.
        :param event_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param params: It is a list of string to specify the desired statistics from event_group.
         e.g. ["goals", "total_shots", "shots_on_target"] while event_group == "shotEvent"
        '''
        stat = TeamSeasonStatistics.objects(
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

    def callTeam(self, team_name, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the statistics of team from different event_groups like aerial, foul, take on ...
        :param team_name: It is a string that stands for the team name.
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
            result = self.getTeamEventGroup(team_name)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getTeamEventGroup(team_name, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result

    def callTeamSeasonAverage(self, stat_name, stat_type, stat_list=None, get_translated=None):  # stat_list is list of list like:
        '''
        This function returns the cumulative average season statistics of teams from different event_groups like
        aerial, foul, take on ...
        :param stat_name: It is a string that stands for the stat name like all_teams.
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
            result = self.getTeamAverageEventGroup(stat_name, stat_type)
        else:
            for stat in stat_list:
                if not isinstance(stat, (list, tuple)) or len(stat) < 1:
                    continue
                detailed_stat = None
                if len(stat) > 1:
                    detailed_stat = stat[1]
                temp = self.getTeamAverageEventGroup(stat_name, stat_type, stat[0], detailed_stat)
                if temp is not None:
                    if get_translated:
                        result[event_name_translation[stat[0]]] = temp
                    else:
                        result[stat[0]] = temp
        return result

    def compareTeams(self, reference_team, team_list, stat_list=None):
        '''
        This function compare the reference_team stats with the all team stats in the team_list
        , and returns the comparison values of stats in stat_list.
        :param reference_team:  It is a string that stands for the reference team name.
        :param team_list: It is a list of string that contain list of teams to compare with reference team
        e.g. ["Galatarasaray", "Besiktas", "Akhisarspor", "Trabzonspor"]
        :param stat_list: It is a list of list in form of [event_group,[desired_stat1,desiredstat2...],...]
        example format: [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                  ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                  ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                  ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
                  ["aerialEvent"]]
        Note: it also allows tuple instead of list.
        '''
        reference_stats = self.callTeam(reference_team, stat_list)
        diff_list = list()
        for team in team_list:
            diff_stat = dict()
            diff_stat["team_name"] = team
            diff_stat["reference_team"] = reference_team
            temp_stat = self.callTeam(team, stat_list)
            for stat in temp_stat:
                diff_detailed_stat = dict()
                if temp_stat[stat] is None:
                    continue
                for detailed_stat in temp_stat[stat]:
                    diff_detailed_stat[detailed_stat] = temp_stat[stat][detailed_stat] - reference_stats[stat][detailed_stat]
                diff_stat[stat] = diff_detailed_stat
            diff_list.append(diff_stat)
        return diff_list

    def rankLeagueTeams(self, stat_group, detailed_stat, limit_number, get_translated=None):
        '''
        This function returns the top list (in terms of given detailed_stat like goals, total_red_cards, total_assists)
        of teams with desired limit.
        :param stat_group: It is a string to specify the desired statistical group. e.g. "shotEvent", "foulEvent"
        :param detailed_stat: It is a string to specify the desired statistic from event_group. e.g. "goals"
        :param limit_number: It is integer that specify length of return list.
        '''
        if get_translated:
            stat_group = name_event_translation[stat_group]
        stat = TeamStatistics.objects(Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID)).first()
        event_group_obj = getattr(stat, stat_group, "event not found")
        class_name = event_group_obj.__class__
        stats = TeamStatistics.objects(Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID)).only(
            *["teamName", stat_group])

        event_obj_keys = list(map(lambda x: getattr(
            getattr(x, stat_group, "name not found"), 'id', "id not found"), stats))

        event_obj_teams = list(map(lambda x: getattr(x, "teamName", "name not found"), stats))

        event_groups = class_name.objects(pk__in=event_obj_keys).only(
            *["pk", detailed_stat]).order_by('-' + detailed_stat, '+pk').limit(limit_number)

        event_leaders_list = []
        total_stat = 0
        for i in range(limit_number):
            temp = dict()
            temp["team"] = event_obj_teams[event_obj_keys.index(event_groups[i].pk)]
            stat = getattr(event_groups[i], detailed_stat, detailed_stat + " not found")
            if get_translated:
                temp["stat_value"] = stat
            else:
                temp[detailed_stat] = stat
            total_stat += stat
            event_leaders_list.append(temp)
            # print(temp)
        if not get_translated:
            temp2 = dict()
            temp2["team"] = "All_Teams"
            temp2[detailed_stat] = total_stat
            # print(temp2)
            event_leaders_list.append(temp2)
        return event_leaders_list

    def getTeamName(self, team_id):
        '''
        This function returns the name of team with given team_id.
        :param team_id: It is a string of team_id.
        '''
        teamPKs, x, y = self.getSeasonTeamPKs()  # this takes PKs with season parameter
        team_name = F40_Team.objects(Q(uID=team_id) & Q(pk__in=teamPKs)).only("name").first()
        print(team_name)
        if team_name:
            return team_name.name

    def getTeamAllPlayerNames(self, teamName, option=None):  # * it seems to pass test
        '''
        This function returns the name of all player in team.
        Additionally there is 3 option for selecting player_name. If "left" is selected
        it returns the player who transferred from team. If "all" is selected it
        returns all players who have been in team in specified season. If option is None
        it returns the name of non_transferred players.
        :param teamName: It is a string that stands for the team name.
        :param option: It is string of option. All values rather then "left" and "all"
        make function returns the non_transferred players.
        '''
        team, playerChanges, all = self.getSeasonTeamPKs()   # it work with option parameter.
        # if option is "left" it returns playerNames left the team
        if option == "left":                                 # if option is "all" it returns all playerNames
            desiredPKs = playerChanges                       # otherwise it returns the playerNames stay the team.
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

    def getTransferredPlayerNames(self, team_name):
        '''
        This functions returns the name of all transferred players in given team.
        :param team_name: It is a string that stands for the team name.
        '''
        return self.getTeamAllPlayerNames(team_name, "left")

    def compareTeamEventStatistics(self, teams):
        """
        expected object should look like this
        [team_name, team_name, ..]
        :param teams:
        :return:
        """
        team_stats = []
        for team in teams:
            result = self.getTeamStatistics(team)
            team_stats.append(json.loads(result))
        return json.dumps(team_stats)

    def getTeamKey(self, team_name):  # * kinda unnecessary There is getTeamID functions.
        feed = self.connector.getFeed("feed1", self.competitionID, self.seasonID, None)
        team_ID = str(0)
        for team in feed.teams:
            if team.name == team_name:
                team_ID = team.uID
        team_key = str(team_ID).strip("t")
        return team_key

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

    def getTeamGameEventWithPipe(self, team_name, game_number):

        pipeline = [
            {
                "$match": {
                    "competitionID": int(self.competitionID),
                    "seasonID": int(self.seasonID),
                    "$or": [{"awayTeamName": team_name}, {"homeTeamName": team_name}]
                }
            },
            {
                "$addFields": {
                    "team": team_name
                }
            },
            {
                "$project": {
                    "ID": 1, "team": 1, "events": 1
                }
            },
            {
                "$unset": "_id"
            },
            {
                "$sort": {"ID": 1}
            },
            {
                "$skip": game_number-1
            },
            {
                "$limit": 1
            },
            {
                "$lookup": {
                    "from": "f24__event",
                    "localField": "events",
                    "foreignField": "_id",
                    "as": "game_events"
                }
            }
        ]

        result = F24_Game.objects.aggregate(pipeline)

        for doc in result:
            print(doc)
            print(f"**{doc['game_events'][0]['qEvents'][0]}")

    def handleTeamGames(self, team_name, games_events, requested_statistics=None):
        '''
        This function take the games_event of given team and handle those events and
        returns the statistics about those events. This is a helper function for game
        analysis of team.
        :param team_name: It is a string that stands for the team name.
        :param games_events: It is a list of F24_Game or list of list of F24_Event that contain
        mainly all events to be handled.
        e.g. [F24_Game, F24_Game, F24_Game...] or [[F24_Event, F24_Event, ..], [], [], ...]
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        Default values is None and in such a case all events are handled.
        '''
        desired_events = []
        try:
            if games_events and isinstance(games_events[0], F24_Game):
                all_events = list(map(lambda x: x.events, games_events))
            else:
                all_events = games_events
            teamID = self.get_team_id(team_name)
            for events in all_events:
                for event in events:
                    if teamID == event.teamID:
                        desired_events.append(event)
            if desired_events is None:
                print("no events is available")
                return None
            logging.info("all events are collected")
            handler = EventHandler.EventHandler()
            data = self.prepareTeamDataForHandler(desired_events, all_events, teamID)
            if requested_statistics:
                results = handler.handle_single_event_v2(requested_statistics, data, False)
            else:
                results = handler.handle_all_events_v2(data, False)
            return results
            # TODO add DB part later to speed up if required

        except Exception as err:
            print(err)
        return None

    def prepareTeamDataForHandler(self, events, all_events, team_id):
        '''
        This function is helper for handleTeamGames.
        :param events: It is a list of events.
        :param all_events: It is a list of list of events.
        :param team_id: It is a string of team_id.
        '''

        data = dict()
        data["events"] = events
        data["all_events"] = all_events
        data["teamID"] = team_id
        data["total_minutes"] = 90 * 34
        data["playerID"] = "p-1"
        data["oldTeamID"] = "t-1"
        return data

    def getTeamGamesEvent(self, team_name, game_number, limit_number):
        '''
        This function returns the desired F24_Game objects to get game events of team.
        For example: game_number=4, limit_number=6, then function returns the F24_Game
        week4 to week(4+6) namely week4 to week10.
        :param team_name: It is a string that stands for the team name.
        :param game_number: It is integer to specify starting week.
        :param limit_number: It is integer to specify how many week to get F24_Game
         starting from game_number.
        '''
        result = F24_Game.objects(   # To get multiple games events of team
            Q(competitionID=int(self.competitionID)) &
            Q(seasonID=int(self.seasonID)) &
            (Q(awayTeamName=team_name) | Q(homeTeamName=team_name))
        ).only("ID", "events").order_by('+ID', '+events').skip(
            game_number-1).limit(limit_number)

        return result

    def getTeamGamesEventWithGameIDs(self, team_name, game_ids):
        '''
        This function returns the F24_Game objects those with matched game_ids
         to get game events of team.
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        result = F24_Game.objects(
            Q(competitionID=int(self.competitionID)) &
            Q(seasonID=int(self.seasonID)) &
            (Q(awayTeamName=team_name) | Q(homeTeamName=team_name)) &
            (Q(ID__in=game_ids))
        ).order_by("+periodID", "+min", "+sec", "+eventID").only("ID", "events")

        return result

    def getTeamGamesEventWithDate(self, team_name, low_date_str, high_date_str):
        '''
        This function returns the desired F24_Game objects to get game events of team.
        For example: low_date_str= "2018-08-11", high_date_str= "2018-10-21", then function returns the
         F24_Game between the given dates.
        :param team_name: It is a string that stands for the team name.
        :param low_date_str: It is string to specify starting date.
        :param high_date_str: It is string to specify ending date.
        '''
        # * low_date_str in form --> "2018-08-11" and if there is match at this date it will be added
        low_date_str = low_date_str + "T00:00:00"
        high_date_str = high_date_str + "T24:59:59"
        result = F24_Game.objects(
            Q(competitionID=int(self.competitionID)) &
            Q(seasonID=int(self.seasonID)) &
            (Q(awayTeamName=team_name) | Q(homeTeamName=team_name)) &
            (Q(periodOneStart__gte=low_date_str) & Q(periodOneStart__lte=high_date_str))
        ).only("events")

        return result

    def getTeamGameEventPKs(self, team_name, game_ids):
        '''
        This function returns the all ObjectIds or primary keys of F24_Event documents about given game_ids.
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        result = F24_Game.objects(
            Q(competitionID=int(self.competitionID)) &
            Q(seasonID=int(self.seasonID)) &
            (Q(awayTeamName=team_name) | Q(homeTeamName=team_name)) &
            (Q(ID__in=game_ids))
        ).only("pk", "events")
        eventID_lists = []
        for game in result:
            eventID_lists.append(list(map(lambda x: x.pk, game.events)))
        return eventID_lists

    def getTeamGameEventBetweenTimes(self, team_id, eventIDs_lists, start_time, end_time):
        '''
        This function returns the game events between specified times with given
        F24_Event primary keys.
        :param team_id: It is a string that stands for the team name.
        :param eventIDs_lists: list of primary key of F24_Event documents. It can be got
        by calling getTeamGameEventPKs
        :param start_time: It is a tuple of min, sec pair like (min, sec) to specify starting time of desired events
        :param end_time: It is a tuple of min, sec pair like (min, sec) to specify ending time of desired events
        '''
        result = F24_Event.objects(
            Q(pk__in=eventIDs_lists) &
            Q(teamID=team_id) &
            (Q(min__gt=start_time[0]) | (Q(min=start_time[0]) & Q(sec__gte=start_time[1]))) &
            (Q(min__lt=end_time[0]) | (Q(min=end_time[0]) & Q(sec__lte=end_time[1])))
        )
        return result

    def getTeamGamesEventSeperatedHalf(self, team_name, game_ids):
        '''
        This function returns the game events as a separation of first half and second half
        in form of list of list of F24_Events.
        e.g. [firsthalf:[gameID1:[events], gameIDs2:[events]], secondhalf:[gameID1:[events], gameIDs2:[events]]
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        '''
        eventID_lists = self.getTeamGameEventPKs(team_name, game_ids)
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

    def getTeamGamesEventSeperatedMins(self, team_name, game_ids, minute_pairs):  # min_list like: [15, 45, 65, 80]
        '''
        This function returns the game events seperated by given minute pairs
        in form of list of list of F24_Event.
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param minute_pairs: It is a list of list of integer that specify the desired time
        intervals to get game events.
        '''
        eventID_lists = self.getTeamGameEventPKs(team_name, game_ids)
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

    def getTeamGamesEventSeperatedByRedCards(self, team_name, game_id):
        '''
        This function returns the game events seperated by red card event minutes
        in form of list of list of F24_Event.
        :param team_name: It is a string that stands for the team name.
        :param game_id: It is integer to specify game_id of played match.
        '''
        eventID_lists = self.getTeamGameEventPKs(team_name, [game_id])
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
        return self.getTeamGamesEventSeperatedMins(team_name, [game_id], minute_pairs), minute_pairs

    def getTeamGamesEventSeperatedByGoals(self, team_name, game_id):
        '''
        This function returns the game events seperated by goal event minutes
        in form of list of list of F24_Event.
        :param team_name: It is a string that stands for the team name.
        :param game_id: It is integer to specify game_id of played match.
        '''
        eventID_lists = self.getTeamGameEventPKs(team_name, [game_id])
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

        return self.getTeamGamesEventSeperatedMins(team_name, [game_id], minute_pairs), minute_pairs

    def getTeamGamesStatistics(self, team_name, game_number, limit_number, requested_statistics=None):
        '''
        This function returns the desired game statistics of a team.
        For example: game_number=4, limit_number=6, then function returns game statistics between
        week 4 to week(4+6) namely week 4 to week 10.
        :param team_name: It is a string that stands for the team name.
        :param game_number: It is integer to specify starting week.
        :param limit_number: It is integer to specify how many game week should we take
         starting from game_number.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        games_events = self.getTeamGamesEvent(team_name, game_number, limit_number)
        return self.handleTeamGames(team_name, games_events, requested_statistics)

    def getTeamGamesStatisticsWithGameIDs(self, team_name, game_ids, requested_statistics=None):
        '''
        This function returns the game (games that in game_ids list) statistics of a team.
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events = self.getTeamGamesEventWithGameIDs(team_name, game_ids)
        return self.handleTeamGames(team_name, game_events, requested_statistics)

    def getTeamGamesStatisticsWithDate(self, team_name, low_date_str, high_date_str, requested_statistics=None):
        '''
        This function returns the game statistics of a team between given dates.
        :param team_name: It is a string that stands for the team name.
        :param low_date_str: It is string to specify starting date.
        :param high_date_str: It is string to specify ending date.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events = self.getTeamGamesEventWithDate(team_name, low_date_str, high_date_str)
        return self.handleTeamGames(team_name, game_events, requested_statistics)

    def getTeamGamesStatisticsSeperatedHalf(self, team_name, game_ids, requested_statistics=None):
        '''
        This function returns the game statistics of a team in two seperate halves.
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated = self.getTeamGamesEventSeperatedHalf(team_name, game_ids)
        result = dict()
        result["FirstHalves"] = self.handleTeamGames(team_name, game_events_seperated[0], requested_statistics)
        result["SecondHalves"] = self.handleTeamGames(team_name, game_events_seperated[1], requested_statistics)
        return result

    def getTeamGamesStatisticsSeperatedMins(self, team_name, game_ids, minute_list, requested_statistics=None):
        '''
        This function returns the game statistics of a team seperated by given minute_list
        :param team_name: It is a string that stands for the team name.
        :param game_ids: It is list of integer to specify game_ids of played matches.
        :param minute_list: IT is a list of integer to specify cutting minutes.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        minute_pairs = self.minute_parser(minute_list)
        game_events_seperated = self.getTeamGamesEventSeperatedMins(team_name, game_ids, minute_pairs)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handleTeamGames(team_name, game_events_seperated[i], requested_statistics)
        return result

    def getTeamGamesStatisticsSeperatedByRedCards(self, team_name, game_id, requested_statistics=None):
        '''
        This function returns the game statistics of a team seperated by red card events.
        :param team_name: It is a string that stands for the team name.
        :param game_id: It is integer to specify game_id of played match.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated, minute_pairs = self.getTeamGamesEventSeperatedByRedCards(team_name, game_id)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handleTeamGames(team_name, game_events_seperated[i],
                                                                          requested_statistics)
        return result

    def getTeamGamesStatisticsSeperatedByGoals(self, team_name, game_id, requested_statistics=None):
        '''
        This function returns the game statistics of a team seperated by goal events.
        :param team_name: It is a string that stands for the team name.
        :param game_id: It is integer to specify game_id of played match.
        :param requested_statistics: It is a string or integer that can be reachable with EventIDs
        '''
        game_events_seperated, minute_pairs = self.getTeamGamesEventSeperatedByGoals(team_name, game_id)
        result = dict()
        for i in range(len(game_events_seperated)):
            result["mins:" + str(minute_pairs[i])] = self.handleTeamGames(team_name, game_events_seperated[i],
                                                                          requested_statistics)
        return result

    def attack_sequence_analysis(self, team_name, game_id):
        game_event = self.getTeamGamesEventWithGameIDs(team_name, [game_id])
        teamID = int(self.getTeamID(team_name)[1:])
        events = []
        start_events = []
        end_events = []
        for event in game_event[0].events:
            if event.teamID == teamID:
                event_type = EventTypes[str(event.typeID)]
                event_outcome = event.outcome

                if event_type in ["Attempt Saved", "Miss", "Post", "Goal"]:
                    end_events.append((event_type, event))
                    events.append(["End", event_type, event, event.min, event.sec])

                elif event_type == "Pass":
                    x_end = 0
                    is_throw_in = False
                    is_gk_throw = False
                    is_long_ball = False
                    is_cross = False
                    for qEvent in event.qEvents:
                        if qEvent.qualifierID == 140:
                            x_end = int(float(qEvent.value))
                        elif qEvent.qualifierID == 107:
                            is_throw_in = True
                        elif qEvent.qualifierID == 123:
                            is_gk_throw = True
                        elif qEvent.qualifierID == 1:
                            is_long_ball = True
                        elif qEvent.qualifierID == 2:
                            is_cross = True
                    if not is_gk_throw and not is_throw_in and event.x < 66 and x_end >= 66 and event_outcome == 1:
                        if is_long_ball:
                            event_type = "Long Pass"
                        if is_cross:
                            event_type = "Cross"
                        start_events.append((event_type, event))
                        events.append(["Start", event_type, event, event.min, event.sec])
                    elif is_throw_in and event.x >= 66:
                        start_events.append(("Throw-in", event))
                        events.append(["Start", "Throw-in", event, event.min, event.sec])
                    elif is_gk_throw:
                        start_events.append(("Keeper Throw", event))
                        events.append(["Start", "Keeper Throw", event, event.min, event.sec])

                elif event_outcome == 1 and event_type == "Ball recovery":
                    start_events.append((event_type, event))
                    events.append(["Start", event_type, event, event.min, event.sec])

                elif event_outcome == 1 and event_type in ["Tackle", "Clearance", "Interception"]:
                    start_events.append((event_type, event))
                    events.append(["Start", event_type, event, event.min, event.sec])

                elif event_outcome == 1 and event_type == "Take On" and event.x >= 66.6:
                    start_events.append((event_type, event))
                    events.append(["Start", event_type, event, event.min, event.sec])

                elif event_outcome == 1 and event_type == "Foul":
                    start_events.append((event_type, event))
                    events.append(["Start", event_type, event, event.min, event.sec])

                elif event_type == "Corner Awarded":
                    start_events.append((event_type, event))
                    events.append(["Start", event_type, event, event.min, event.sec])
        start_end_pairs = []
        last_start_index = -1
        if len(events) > 0:
            if events[0][0] == "Start":
                last_start_index = 0

        if last_start_index == -1:
            print("Something went wrong!!!")

        length = len(events)

        if last_start_index != -1:
            for i in range(1, length):
                if events[i][0] == "Start" and events[i-1][0] == "Start":
                    last_start_index = i
                elif events[i][0] == "Start" and events[i-1][0] == "End":
                    temp = [events[last_start_index], events[i-1]]
                    last_start_index = i
                    start_end_pairs.append(temp)

        if events[length-1][0] == "End":
           temp = [events[last_start_index], events[length-1]]
           start_end_pairs.append(temp)

        eventIDs_lists = self.getTeamGameEventPKs(team_name, [game_id])[0]
        attack_times = []
        result_events = []
        for pair in start_end_pairs:
            between_time_events = list(self.getTeamGameEventBetweenTimes(teamID, eventIDs_lists,
                                                                        (pair[0][3], pair[0][4]),
                                                                        (pair[1][3], pair[1][4])))
            attack_times.append([(pair[0][3], pair[0][4]), (pair[1][3], pair[1][4])])
            result_events = result_events + between_time_events

        result = self.handleTeamGames(team_name, [result_events])
        return result

    def calculateTeamStatistics(self, team_name, match_duration_min=90):
        try:
            team_id = self.get_team_id(team_name=team_name)
            all_game_ids = self.get_all_team_played_games(team_id=team_id)
            events = self.get_team_events(team_id=team_id, game_ids=all_game_ids)
            if events is None:
                print("no events is available")
                return None

            total_number_of_games_played = len(all_game_ids)
            total_minutes = total_number_of_games_played * match_duration_min

            data = dict()
            data["events"] = events
            data["teamID"] = team_id
            data["playerID"] = self.get_all_players_ids(team_name)
            data["playerName"] = self.get_all_players_name(team_name)
            data["total_minutes"] = total_minutes
            handler = EventHandler.EventHandler()
            results = handler.handle_all_events(data=data)
            if team_name:
                team_stat = APIHelpers.TeamEventStatistics(
                    team_name,
                    team_id,
                    self.competitionID,
                    self.seasonID,
                    results.copy(),
                )
                team_stat.storeInDB()
                return True

        except Exception as err:
            print(err)
            return None

    def prepareTeamStatisticsForSeason(self, stat, team_name, event_type=None):
        st = APIHelpers.TeamEventStatistics(
            team_name,
            self.getTeamID(team_name),
            self.competitionID,
            self.seasonID,
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

    def getTeamStatistics(self, team_name: str, event_type=None):
        """
            This function takes team_name and returns the all statistics about team.
            If values in DB call prepareTeamStatisticsForSeason and get data directly from DB
            else call calculateStatistics then call prepareTeamStatisticsForSeason.

            :param event_type:
            :param team_name: It is a string that stands for the team name.

        """
        team_id = self.get_team_id(team_name=team_name)
        stat = TeamStatistics.objects(
            Q(teamName=team_name)
            & Q(teamID=team_id)
            & Q(competitionID=int(self.competitionID))
            & Q(seasonID=int(self.seasonID))
        ).first()

        if stat is not None:
            obj = jsonSerializer(self.prepareTeamStatisticsForSeason(stat, team_name, event_type))
            return json.dumps(PlayerAPI.PlayerAPI(self.competitionID, self.seasonID).filter_event_results(obj))

        else:
            result = self.calculateTeamStatistics(team_name)
            if result:
                stat = TeamStatistics.objects(
                    Q(teamName=team_name)
                    & Q(competitionID=int(self.competitionID))
                    & Q(seasonID=int(self.seasonID))
                ).first()

                if stat is not None:
                    obj = jsonSerializer(self.prepareTeamStatisticsForSeason(stat, team_name))
                    return json.dumps(PlayerAPI.PlayerAPI(self.competitionID, self.seasonID).filter_event_results(obj))

                else:
                    return jsonSerializer("{}")
            else:
                return jsonSerializer("{Error: user does not exist}")

    # ---------------------Check Team Exists in DataBase-------------------

    def does_team_exist(self, team_id: int = None, team_name: str = None):
        query_object = self.lookup_f40_root().keep("uID", "name")
        if team_id is None and team_name is None:
            print("Both team_id and team_name can not be empty at the same time.")
            return None
        if team_id:
            query_object.match({"uID": team_id})
        if team_name:
            query_object.match({"name": team_name})

        result_bool = 0 < len(list(query_object.run()))

        return result_bool

    # --------------Construct General Data of a Season (Mean, Standard Deviation etc.)-----------------

    def calculate_general_team_stats(
            self, event_collections=None, params_names=None, doc_name=None, team_ids=None
    ):

        field_names = self.evapi().getEventDict()
        if event_collections is None:
            event_collections = list(field_names.keys())
        if team_ids is None:
            team_ids = self.get_all_team_ids()
        team_match_query = {"teamID": {"$in": team_ids}}
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

            player_query_obj = self.get_filtered_stats_teams(
                event_collections=[event], query_conditions=team_match_query, return_pipeline=True
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
                APIHelpers.TeamGeneralEventStatistics(
                    stat_name=doc_name, stat_type=key, competition_id=self.competitionID,
                    season_id=self.seasonID, results=value
                )
        return main_result

    def get_general_team_stats(
            self, event_collections=None, params_names=None, doc_name=None, team_ids=None
    ):
        pre_match = {"competitionID": int(self.competitionID), "seasonID": int(self.seasonID)}
        main_result = list()
        if doc_name is not None:
            main_document_object = TeamSeasonStatistics
            main_query_object = QueryPipeline(main_document_object)
            mongo_db_obj = main_query_object.match({**pre_match, "statName": str(doc_name)})

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

            main_result = list(mongo_db_obj.run())

        if len(main_result) == 0:
            main_result = self.calculate_general_team_stats(
                event_collections=event_collections, params_names=params_names, doc_name=doc_name, team_ids=team_ids
            )

        return main_result

    # -------------Preparation Functions for Querying-------------------------

    def get_team_id(self, team_name: str):
        query_object = self.fast_lookup_f1_root()
        query_object.match({"name": team_name}).keep("uID")
        result = list(query_object.run())
        if 0 < len(result):
            return result[0]["uID"]
        else:
            return None

    def get_team_name(self, team_id: int):
        query_object = self.fast_lookup_f1_root()
        query_object.match({"uID": team_id}).keep("name")
        result = list(query_object.run())
        if 0 < len(result):
            return result[0]["name"]

    def get_player_id(self, player_name: str):
        query_object = self.fast_lookup_f40_player().keep("players.name", "players.uID").parallelize("players")
        query_object.match({"players.name": player_name})
        result = list(query_object.limit(1).run())
        if 0 < len(result):
            return result[0]["players"]["uID"]
        else:
            return None

    def get_player_name(self, player_id: int):
        query_object = self.fast_lookup_f40_player().keep("players.name", "players.uID").parallelize("players")
        query_object.match({"players.uID": player_id})
        result = list(query_object.limit(1).run())
        if 0 < len(result):
            return result[0]["players"]["name"]
        else:
            return None

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
            self.get_filtered_stats_teams(
                event_collections=[event], query_conditions=query_condition,
                event_params=[modified_field], sort_conditions=sort_condition
            )
        )
        norm = len(results)
        if norm == 0:
            return None
        prev_value = results[0][event][0][field]
        distribution = norm
        for index in range(norm):
            temp_team = results[index]
            next_value = temp_team[event][0][field]
            if next_value != prev_value:
                distribution = norm - index - 1
            temp_percentiles = (distribution / norm) * 100
            results[index][event][0][field] = temp_percentiles
            prev_value = next_value
        if print_results:
            print(json.dumps(results, indent=4))
        return results

    def get_percentile_stats(
            self, event: str, field: str,  team_id: int = None, check_event_field: bool = True
    ):
        if check_event_field:
            if not self._check_event_field_existence(event, field):
                return None

        match_team = None
        if team_id is not None:
            match_team = {"teamID": team_id}

        modified_field = event + "." + field
        percentiles = list(
            self.get_filtered_stats_teams(
                event_collections=[event], event_params=[modified_field],
                percentile=True, query_conditions=match_team
            )
        )
        missing_data_flag = bool(0 == len(percentiles))
        if missing_data_flag is False:
            candidate_team = percentiles[0]
            try:
                dummy_variable = candidate_team[event][0][field]
                missing_data_flag = False
            except (KeyError, IndexError):
                missing_data_flag = True
        if missing_data_flag:
            percentiles = self.construct_percentile_stats(event, field, False, False)
            if percentiles is None:
                percentiles = []
            for team in percentiles:
                team_id = team["teamID"]
                team_name = team["teamName"]
                value = team[event][0][field]
                APIHelpers.TeamPercentileStatistics(
                    team_name=team_name,
                    team_id=team_id,
                    competition_id=self.competitionID,
                    season_id=self.seasonID,
                    event=event,
                    field=field,
                    value=value
                )
        return percentiles

    # -------------Get All Player uID's ID's or Names in a Team-------------------------

    def _get_general_function(self, team_name: str = None, team_id: int = None, keep_field: list = None):
        if keep_field is None:
            keep_field = ["players.uID", "players.name"]
        query_object = self.fast_lookup_f40_player().keep("name", "uID", *keep_field)
        if team_name:
            query_object.match({"name": team_name})
        elif team_id:
            query_object.match({"uID": team_id})
        else:
            return None
        result = query_object.run()
        return result

    def get_all_players_ids(self, team_name: str = None, team_id: int = None):
        result = self._get_general_function(
            team_name=team_name, team_id=team_id, keep_field=["players.uID"]
        )
        if result is None:
            return None

        all_players = list()
        for team in list(result):
            if "players" in team:
                for player in team["players"]:
                    if "uID" in player:
                        all_players.append(player["uID"])
        return all_players

    def get_all_players_name(self, team_name: str = None, team_id: int = None):
        result = self._get_general_function(
            team_name=team_name, team_id=team_id, keep_field=["players.name"]
        )
        if result is None:
            return None

        all_players = list()
        for team in list(result):
            if "players" in team:
                for player in team["players"]:
                    if "name" in player:
                        all_players.append(player["name"])
        return all_players

    # -------------------------Get All Team Names------------------------

    def get_all_team_names(self):
        team_name_list = list()
        query_object = self.fast_lookup_f1_root()
        query_object.keep("name")
        result = list(query_object.run())
        if 0 < len(result):
            for query_doc in result:
                team_name_list.append(query_doc["name"])
        return team_name_list

    def get_all_team_ids(self):
        team_id_list = list()
        query_object = self.fast_lookup_f1_root()
        query_object.keep("uID")
        result = list(query_object.run())
        if 0 < len(result):
            for query_doc in result:
                team_id_list.append(query_doc["uID"])
        return team_id_list

    # ----------------Get All Played Games of a Team------------------

    def get_all_team_played_games(self, team_id: int = None, team_name: str = None):
        query_object = self.lookup_f1_root_match_data()
        if team_id is None and team_name is None:
            print("Both team_id and team_name con not be None at the same time.")
            return list()

        if team_id is None:
            team_id = self.get_team_id(team_name=team_name)
            if team_id is None:
                if not self.does_team_exist(team_name=team_name):
                    print("Given Team Does Not Exists.")
                else:
                    print("Something went wrong.")
                return list()

        result = list(
            query_object.match(
                {"teamData.teamRef": team_id}
            ).keep("uID").group(
                main_field=None, push_fields={"uID": "uID"}
            ).run()
        )

        if 0 < len(result):
            result = result[0]["uID"]

        return result

    # ----------Get All Players Personal Info in a Team------------------

    def get_all_personal_info(self, team_name):

        team_id = str(self.get_team_id(team_name))

        if team_id is None:
            print("Team name does not exists in the database.")
            return None

        look_up_dict = {
            "f40__player": "players",
            "f40__stat": "players.stats",
            "f40__stadium": "stadium",
            "f40__kit": "kits",
            "f40__team_official": "teamOfficials"
        }

        main_fields = ["uID", "stadium", "kits", "teamOfficials", "players"]
        unnecessary_fields = [
            e for e in EventAPI.EventAPI().getDocumentFields(F40_Team)["fields"] if e not in main_fields
        ]
        def_unwind = [{"$unset": unnecessary_fields}, {"$match": {"uID": team_id}}, {"$unwind": "$players"}]

        def_look_up = list()
        def_unset = list()
        for key in list(look_up_dict.keys()):
            def_look_up.append({
                "$lookup": {
                    "from": key,
                    "localField": look_up_dict[key],
                    "foreignField": "_id",
                    "as": look_up_dict[key]
                }})
            def_unset.append({
                "$unset": [look_up_dict[key]+"._id"]
            })

        def_group = [{
                "$group": {
                    "_id": "$_id",
                    "stadium": {"$addToSet": "$stadium"},
                    "kits": {"$addToSet": "$kits"},
                    "team_officials": {"$addToSet": "$teamOfficials"},
                    "players": {"$push": "$players.stats"}
                }
            }, {
                "$unset": ["_id"]
            }]

        pipeline = def_unwind + def_look_up + def_unset + def_group

        result = list(F40_Team.objects().aggregate(pipeline))

        if len(result) == 0:
            return None
        else:
            return result

    # ----------Get All Played Match Info of a Team------------------

    def get_all_match_info(self, team_name, convert_reference_ids=True):

        team_id = str(self.get_team_id(team_name))

        if team_id is None:
            print("Team name does not exists in the database.")
            return None

        look_up_dict = {
            "f1__match_info": "matchInfo",
            "f1__match_official": "matchOfficials",
            "f1__team_data": "teamData"
        }

        def_look_up = list()
        def_unset = [{"$unset": ["timingID", "detailID", "lastModified"]}]
        for key in list(look_up_dict.keys()):
            def_look_up.append({
                "$lookup": {
                    "from": key,
                    "localField": look_up_dict[key],
                    "foreignField": "_id",
                    "as": look_up_dict[key]
                }})
            def_unset.append({
                "$unset": [look_up_dict[key]+"._id"]
            })

        def_unwind = [{
            "$match": {"teamData.teamRef": {"$eq": team_id}}
        }, {
            "$unwind": "$teamData"
        }, {
            "$lookup": {
                "from": "f1__goal",
                "localField": "teamData.goal",
                "foreignField": "_id",
                "as": "teamData.goal"
            }
        }, {
            "$unset": ["teamData.goal._id", ]
        }]

        def_group = [{
            "$group": {
                "_id": "$_id",
                "u_id": {"$first": "$uID"},
                "matchInfo": {"$addToSet": "$matchInfo"},
                "matchOfficials": {"$addToSet": "$matchOfficials"},
                "teamData": {"$push": "$teamData"}
            }
        }, {
            "$unset": ["_id"]
        }]

        pipeline = def_look_up + def_unset + def_unwind + def_group

        result = list(F1_MatchData.objects().aggregate(pipeline))

        if convert_reference_ids:
            for match in result:
                try:
                    if int(match["teamData"][0]["score"]) != int(match["teamData"][-1]["score"]):
                        temp_winner = match["matchInfo"][0][0]["matchWinner"]
                        match["matchInfo"][0][0]["matchWinner"] = self.get_team_name(temp_winner)
                except KeyError:
                    print("Winner could not changed. The game uID; ", match["u_id"])
                try:
                    temp_first_team = match["teamData"][0]["teamRef"]
                    match["teamData"][0]["teamRef"] = self.get_team_name(temp_first_team)
                    for goal in match["teamData"][0]["goal"]:
                        goal["playerRef"] = self.get_player_name(goal["playerRef"])
                except KeyError:
                    print("Player names could not changed. The game uID; ", match["u_id"])
                try:
                    temp_first_team = match["teamData"][-1]["teamRef"]
                    match["teamData"][-1]["teamRef"] = self.get_team_name(temp_first_team)
                    for goal in match["teamData"][-1]["goal"]:
                        goal["playerRef"] = self.get_player_name(goal["playerRef"])
                except KeyError:
                    print("Player names could not changed. The game uID; ", match["u_id"])

        return result

    # --------------Find Specific Teams in TeamStatistics Document with some Conditions-----------------

    # Following function does query operation on the "TeamStatistics" object on the MongoDB.
    # We can access any team in the system by specifying some conditions on some event parameters.
    # Example, obtaining all the teams with aerial_event.won bigger than 370 in the desc order.
    # Here aerial_event corresponding to another MongoDB collection, "won" on the other hand
    # corresponding to the aerial event's "won" field in the database.
    def get_filtered_stats_teams(
            self, event_collections=None, query_conditions=None, event_params=None,
            sort_conditions=None, limit=None, return_pipeline=False, percentile=False
    ):
        if percentile:
            root_document = TeamPercentileStatistics
        else:
            root_document = TeamStatistics
        query_object = QueryPipeline(root_document=root_document)

        field_names = self.evapi().getEventFieldsDict()
        mongo_db_field_names = self.evapi().getEventCollectionDict()

        if event_collections is None:
            event_collections = list(field_names.keys())

        for collection in event_collections:
            query_object.join(
                mongo_db_field_names[collection], field_names[collection], "_id", collection
            ).remove(collection + "._id")

        query_object.remove(["_id"] + list(field_names.values()))

        if query_conditions:
            query_object.match(query_conditions)

        if event_params:
            event_params += ["teamID", "teamName"]
            query_object.keep(*event_params)

        if sort_conditions:
            query_object.sort(sort_conditions)

        if limit:
            query_object.limit(limit)

        if return_pipeline:
            return query_object

        result = query_object.run()

        return result

    def get_team_matches(self, team_name):
        # team_id = self.getTeamID(team_name)
        team_id = self.get_team_id(team_name)
        print(team_id)
        game_ids = self.getGamesPlayedByTeam(team_id)
        # game_ids = list(map(lambda x: int(x.replace("g", "")), game_ids))
        game_ids = list(game_ids)
        # print(game_ids)
        game_list = F24_Game.objects(ID__in=game_ids).exclude("id").only(
            *["ID", "awayTeamName", "awayScore", "homeTeamName", "homeScore"])
        result = []
        # print(game_list)
        for game in game_list:
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

    def get_team_data(self, team_name):
        teamPKs,a,b = self.getSeasonTeamPKs()
        team = F40_Team.objects(Q(name=team_name) & Q(pk__in=teamPKs)).first()
        data = []
        data.append({"stat_type": "name", "stat_value": team.name})
        data.append({"stat_type": "country", "stat_value": team.country})
        data.append({"stat_type": "stadium name", "stat_value": team.stadium.name})
        data.append({"stat_type": "stadium capacity", "stat_value": team.stadium.capacity})
        data.append({"stat_type": "founding date", "stat_value": team.founded})
        for person in team.teamOfficials:
            data.append({"stat_type": person.type,
                         "stat_value": person.personalInfo.first + " " + person.personalInfo.last})
        for kit in team.kits:
            if kit.type == "home":
                data.append({"stat_type": "color_1", "stat_value": kit.colour1})
                if kit.colour2 is not None:
                    data.append({"stat_type": "color_2", "stat_value": kit.colour2})
        return data

    def get_season_team_name(self):
        team_pks,a,b = self.getSeasonTeamPKs()
        teams = F40_Team.objects(pk__in=team_pks).only("name")
        team_list = list((map(lambda x: {"name": x.name}, teams)))
        return team_list


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
