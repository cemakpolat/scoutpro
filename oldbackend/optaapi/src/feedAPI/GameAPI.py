import sys

import feedAPI.QueryPipeline

sys.path.append("..")  # Adds higher directory to python modules path.

from src.dbase.DBHelper import *
from src.parse import Parser
from src.restapi.APIHelpers import *
from src.restapi import APIHelpers
from src.feedAPI import Connector
from src.feedAPI import PlayerAPI
from src.feedAPI import EventAPI
from src.feedAPI import EventHandler
from src.feedAPI import TeamAPI
from src.feedAPI import QueryPipeline
from src.events import Events
from src.events import GamesandMinutesEvents
from src.utils.Utils import *

"""
Feed1 returns all matches played and non played
Feed9 returns the result of single match.
"""


class GameAPI:
    def __init__(self, competitionID=None, seasonID=None):
        self.competitionID = int(competitionID)
        self.seasonID = int(seasonID)
        self.connector = Connector.main_conn
        self.doc_name = get_doc_name
        self.online = False
        self.event_api_connection = False
        self.player_api_connection = False
        self.team_api_connection = False
        self.db_port = 27017
        self.host = "localhost"
        self.connector.connect()

    def setCompetitionSeason(self, competition_id, season_id):
        self.competitionID = competition_id
        self.seasonID = season_id

    def evapi(self):
        if self.event_api_connection is False:
            self.event_api_connection = EventAPI.EventAPI(competition_id=self.competitionID, season_id=self.seasonID)
            return self.event_api_connection
        else:
            return self.event_api_connection

    def papi(self):
        if self.player_api_connection is False:
            self.player_api_connection = PlayerAPI.PlayerAPI(competitionID=self.competitionID, seasonID=self.seasonID)
            return self.player_api_connection
        else:
            return self.player_api_connection

    def tapi(self):
        if self.team_api_connection is False:
            self.team_api_connection = TeamAPI.TeamAPI(competitionID=self.competitionID, seasonID=self.seasonID)
            return self.team_api_connection
        else:
            return self.team_api_connection

    def getGameDataById(self, id):
        """
        :param int id: Game ID should be integer.
        :return:
        """
        game = F24_Game.objects(Q(ID=id)).to_json()
        return game

    def getGameDataByOId(self, id):
        """

        :param int id: Game ID should be integer.
        :return:
        """
        game = F24_Game.objects(Q(ID=id)).to_json()
        return game

    ## Feed 1

    def prepareStat_Feed1(self, stats):
        list = []
        for stat in stats:
            list.append(Stat(stat.value, stat.type))
        return list

    def prepareMatchOfficials_Feed1(self, mofficials):
        list = []
        for moff in mofficials:
            list.append(MatchOfficial(moff.first, moff.last, moff.uID, moff.type))
        return list

    def prepareTeamData_Feed1(self, tdata):
        # there is only goals
        list = []
        for item in tdata:
            t = TeamData(item.teamRef)
            t.halfScore = item.halfscore
            t.score = item.score
            t.side = item.side
            t.goals = []
            for goal in item.goals:
                g = Goal()
                g.period = goal.period
                g.playerRef = goal.playerRef
                g.type = goal.type
                t.goals.append(g)
            list.append(t)
        return list

    def prepareTeamData_Feed1(self, mdata, teamRef):
        pass

    def prepareMatchData_Feed1(self, mdata):
        self.prepareMatchOfficials_Feed1(mdata)
        self.prepareMatchInfo_Feed1(mdata)
        self.prepareStat_Feed1(mdata)
        self.prepareTeamData_Feed1(mdata)
        # matchinfo
        # match officials
        # stat
        # teamdata
        # attributes

        pass

    def getSeasonPlannedGames(self):
        feed = self.connector.getFeed(Parser.Feeds.feed1, self.competitionID, self.seasonID, None)
        return feed.matchData

    def prepareMatchInfo_Feed1(self, info):
        minfo = MatchInfo(info.date)
        minfo.TZ = info.TZ
        minfo.matchDay = info.matchDay
        minfo.matchType = info.matchType
        minfo.matchWinner = info.matchWinner
        minfo.period = info.period
        minfo.venueID = info.venueID
        return minfo

    def prepareMatchInfo_Feed1(self, info):

        minfo = MatchInfo(info.date)
        minfo.matchWinner = info.matchWinner
        minfo.TZ = info.TZ
        minfo.venueID = info.venueID
        minfo.matchDay = info.matchDay
        minfo.matchType = info.matchType
        minfo.period = info.period
        minfo.status = info.status
        minfo.teamRef = info.teamRef
        minfo.playerRef = info.playerRef
        minfo.timestamp = info.timestamp
        minfo.varReason = info.varReason
        minfo.leg = info.leg
        minfo.firstLegID = info.firstLegID
        minfo.legWinner = info.legWinner
        minfo.nextMatch = info.nextMatch
        minfo.nextMatchLoser = info.nextMatchLoser
        minfo.roundNumber = info.roundNumber
        minfo.roundType = info.roundType
        minfo.groupName = info.groupName

        minfo.gameWinner = info.gameWinner
        minfo.gameWinnerType = info.gameWinnerType

        return minfo

        ##### F9 rest api

    def getMatchInfo_Feed1(self, matchId):
        """
        - matchinfo, GET / competition / season / match / id / info
        {
            matchday: "",
            matchtype: "",
            matchwinner: "",
            period:,
            venue_id: "",
            tz: "",
            date: ""
        }
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID, None
        )
        for i in range(len(feed.matchData)):
            if feed.matchData[i].uID == matchId:
                minfo = self.prepareMatchInfo_Feed1(feed.matchData.matchInfo)
                return jsonSerializer(minfo)
        return None

    ##### F9 rest api
    def getMatchInfo(self, matchId):
        """
        - matchinfo, GET / competition / season / match / id / info
        {
            matchday: "",
            matchtype: "",
            matchwinner: "",
            period:,
            venue_id: "",
            tz: "",
            date: ""
        }
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, id
        )
        stats = self.prepareMatchInfo(feed.matchData.matchInfo)
        return jsonSerializer(stats)
        # mdata = F1_MatchData.objects(Q(uID=matchId)).to_json()
        # return mdata.matchInfo

    def getMatchOfficials(self, matchId):
        """
        - matchofficials, `GET / competition / season / match / id / officials
        [
            firstname: "",
            lastname: "",
            type: "",
            uId: "o44476"
        ]
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, id
        )
        tdata = self.prepareMatchOfficials(feed.matchData.matchOfficials)
        return jsonSerializer(tdata)

    def getTeamData(self, matchId):
        """ "
        - teamdata, GET / competition / season / match / id / teamdata
        {
            halfscore: "",
            score: "",
            side: "",
            teamref {t_208}
            goals: {
                period: "",
                playerRef: "",
                type: ""
            }
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, id
        )
        tdata = self.prepareTeamData(feed.matchData.teamData)
        return jsonSerializer(tdata)

    def getTeamNames(self):
        # return only teams
        feed = self.connector.getFeed(
            Parser.Feeds.feed1, self.competitionID, self.seasonID, id
        )
        teams = []
        for team in feed.teams:
            teams.append(Team(team.name, team.uID))
        return teams

    def getAllMatchData(self):
        feed = F1_Root.objects(
            Q(competitionID=self.competitionID) and Q(seasonID=self.seasonID)
        ).to_json()
        return feed.matchData

    ##### F9 rest api
    def getMatchStats(self, id):
        """
        - matchstats, GET / competition / season / match / id / stats
        {
            venue: "",
            city: "",
            ...
        }
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, id
        )
        stats = self.prepareMatchStats(feed.matchData.matchStats)
        return jsonSerializer(stats)

    def getFeed9Root(self, uid):
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uid
        )
        # add the whole feed

        return F9_Root.objects(
            Q(competitionID=self.competitionID) and Q(seasonID=self.seasonID)
        ).to_json()

    def prepareBooking(self, bookings):
        """
        - booking
           [
               {
                   card: "yellow",
                   cardtype: "yellow",
                   eventId: "",
                   eventnumber: "",
                   min: "",
                   period: "",
                   playerRef: "",
                   reason: "foul",
                   sec: "",
                   time: "",
                   timestamp: "",
                   uID: "b2136-1"
               }, {
               ...
           }
        """
        bsk = []
        for i in range(len(bookings)):
            bk = Booking()
            bk.uID = bookings[i].uID
            bk.eventNumber = bookings[i].eventNumber
            bk.period = bookings[i].period
            bk.eventID = bookings[i].eventID
            bk.card = bookings[i].card
            bk.cardType = bookings[i].cardType
            bk.min = bookings[i].min
            bk.sec = bookings[i].sec
            bk.timestamp = bookings[i].timestamp
            bk.playerRef = bookings[i].playerRef
            bsk.append(bk)
        # return bk
        return bsk

    def prepareSubstitutions(self, substitutions):
        """ "
        # - substitiution:
        {
            eventId: 2323,
            eventNumber: 1427,
            min: "41",
            period: "1",
            reason: "tactical",
            sec: 21,
            suboff: "p8489",
            subon: "p166070",
            substitutePosition: 2,
            time: 42,
            timestamp: ""
            uId: "s2136-1"
        }
        """

        bsk = []
        for i in range(len(substitutions)):
            subs = substitutions[i]
            bk = Substitution(
                subs.eventID, subs.eventNumber, subs.period, subs.timestamp, subs.uID
            )
            bk.period = subs.period
            bk.time = subs.time
            bk.min = subs.min
            bk.sec = subs.sec
            bk.reason = subs.reason
            bk.suboff = subs.suboff
            bk.subon = subs.subon
            bk.substitutePosition = subs.substitutePosition
            bsk.append(bk)
        return bsk

    def preparePlayerLineUp(self, plineups):
        """
        # - playerlineup
        [
            {
                playerref: "",
                position: "goalkeeper",
                shirtnumber: 13,
                status: "start",
                stats: [
                    {
                        type: "diving_save",
                        value: 1
                    }, {
                        type: "leftside_pass",
                        value: 4
                    }, {
                        type: "accurate_pass",
                        value: 10
                    },
                    ...
                ]
            }
        ]
        """
        players = []
        for i in range(len(plineups)):
            mp = MatchPlayer(
                plineups[i].playerRef,
                plineups[i].position,
                plineups[i].shirtNumber,
                plineups[i].status,
            )
            mp.stats = plineups[i].stats  # TODO: This is not handled
            mp.subPosition = plineups[i].subPosition
            mp.captain = plineups[i].captain
            players.append(mp)
        return players

    def prepareTeamStats(self, stats):
        tstats = []
        for i in range(len(stats)):
            element = TeamStat(stats[i].value, stats[i].type)
            tstats.append(element)
        return tstats

    def prepareGoals(self, goals):
        """
        # - goal
        [
            {
                assist: {
                    playerref: "p84.."
                },
                eventID: "",
                eventNumber: "",
                min: "",
                period: "",
                sec: "",
                time: "",
                timestamp: "",
                type: "Goal",
                uID: "",
            }, {
            ...
        }
        ]

        """

        tgoals = []
        for i in range(len(goals)):
            element = Goal()
            element.eventID = goals[i].eventID
            element.eventNumber = goals[i].eventNumber
            element.min = goals[i].min
            element.period = goals[i].period
            element.playerRef = goals[i].playerRef
            element.sec = goals[i].sec
            element.time = goals[i].time
            element.timeStamp = goals[i].timeStamp
            element.type = goals[i].type
            element.uID = goals[i].uID

            if goals[i].assist is not None:
                element.assist = goals[i].assist.playerRef  # TODO: is more than one assist possible?
            if goals[i].secondAssist is not None:
                element.secondAssist = goals[i].secondAssist.playerRef

            element.soloRun = goals[i].soloRun
            element.VARReviewed = goals[i].VARReviewed
            element.originalDecision = goals[i].originalDecision
            tgoals.append(element)
        return tgoals

    def prepareTeamData(self, teamData):
        """ " """
        tData = []
        for i in range(len(teamData)):
            element = TeamData(teamData[i].teamRef)
            element.score = teamData[i].score
            # add team stats
            element.teamStats = self.prepareTeamStats(teamData[i].teamStats)
            # add subs
            element.substitutions = self.prepareSubstitutions(teamData[i].substitutions)
            # add playerlineup
            element.playerLineUp = self.preparePlayerLineUp(teamData[i].playerLineUp)
            # add goals
            element.goal = self.prepareGoals(teamData[i].goal)
            # add bookings
            element.booking = self.prepareBooking(teamData[i].booking)
            # add missed penalty
            element.missedPenalty = self.prepareMissedPenalty(teamData[i].missedPenalty)

            tData.append(element)

        return tData

    def prepareMissedPenalty(self, missedPenalty):

        mp = MissedPenalty()
        mp.uID = missedPenalty.uID
        mp.type = missedPenalty.type
        mp.playerRef = missedPenalty.playerRef
        mp.period = missedPenalty.period
        mp.eventNumber = missedPenalty.eventNumber
        mp.time = missedPenalty.time
        return mp

    def prepareMatchInfo(self, matchInfo):

        result = Result(matchInfo.result.type)
        result.winner = matchInfo.result.winner
        result.reason = matchInfo.result.reason
        result.minutes = matchInfo.result.minutes

        minfo = MatchInfo(matchInfo.date)
        minfo.result = result
        minfo.period = matchInfo.period
        minfo.matchDay = matchInfo.matchDay
        minfo.timestamp = matchInfo.timestamp
        return minfo

    def prepareSchedule(self, schedule):
        if schedule:
            sch = Schedule()
            sch.type = schedule.type
            sch.value = schedule.value
            return sch
        return None

    def prepareShootOut(self, shootOut):  # TODO: to be test. What should return ?
        if shootOut:                      # ? variable changed list to listt
            if isinstance(shootOut, list):  # ! shootOut is list of ShootOut
                listt = []
                for i in range(len(shootOut)):  # ? comment line changed
                    # listt.append(ShootOut(shootOut.firstPenalty))
                    listt.append(ShootOut(shootOut[i].firstPenalty))
                return listt
            else:
                return ShootOut(shootOut.firstPenalty)
        return None

    def preparePenaltyShot(self, prePenalty):  # TODO: to be test. What should return ?
        if prePenalty:                         # ? variable changed list to listt
            if isinstance(prePenalty, list):   # ! prePenalty is list of PenaltyShot
                listt = []
                for i in range(len(prePenalty)):
                    listt.append(
                        PenaltyShot(
                            prePenalty[i].outcome,
                            prePenalty[i].eventNumber,
                            prePenalty[i].playerRef,
                            prePenalty[i].uID,
                        )
                    )
                return listt
        else:
            return PenaltyShot(
                prePenalty.outcome,
                prePenalty.eventNumber,
                prePenalty.playerRef,
                prePenalty.uID,
            )
        return None

    def prepareMatchOfficials(self, mofficials):
        moffs = []
        for i in range(len(mofficials)):
            moff = MatchOfficial()
            moff.first = mofficials[i].first
            moff.last = mofficials[i].last
            moff.uID = mofficials[i].uID
            moff.type = mofficials[i].type
            moff.officialRef = mofficials[i].officialRef
            moff.officialData = mofficials[i].officialData
            moffs.append(moff)
        return moffs

    def prepareAssistantOfficials(self, aofficials):
        """
        # - assistantofficials
        [
            {
                firstname: "",
                secondname: "",
                type: "",
                uID: "043856"
            },
            {...}
        ]
        """
        aoffs = []
        for i in range(len(aofficials)):
            aoff = AssistantOfficial(
                aofficials[i].first,
                aofficials[i].last,
                aofficials[i].uID,
                aofficials[i].type,
            )
            aoffs.append(aoff)
        return aoffs

    def prepareVARData(self, varData):  # TODO: to be tested
        if isinstance(varData, list):
            listt = []                  # * var changed list to listt
            for i in range(len(varData)):
                listt.append(
                    VARData(
                        varData[i].decision,
                        varData[i].eventID,
                        varData[i].eventNumber,
                        varData[i].min,
                        varData[i].outcome,
                        varData[i].period,
                        varData[i].playerRef,
                        varData[i].reason,
                        varData[i].sec,
                        varData[i].teamRef,
                    )
                )
            return listt
        else:
            return VARData(
                varData.decision,
                varData.eventID,
                varData.eventNumber,
                varData.min,
                varData.outcome,
                varData.period,
                varData.playerRef,
                varData.reason,
                varData.sec,
                varData.teamRef,
            )
        # return None

    def preparePreviousMatch(self, prematch):
        if prematch:
            return PreviousMatch(
                prematch.matchRef, prematch.matchType, prematch.venueRef
            )
        return None

    def prepareMatchStats(self, stats):
        """
        # - stats
            [
                {
                    type: "total flickon",
                    value: 4,
                    fh: 4,
                    sh: 0
                },
                {
                    type: "leftside_pass",
                    value: 110,
                    fh: 56,
                    sh: 54
                },
        """
        allstats = []
        for i in range(len(stats)):
            allstats.append(MatchState(stats[i].value, stats[i].type))
        return allstats

    def getMatchData(self, uid):

        """
        url competition / season / match / matchid / matchdata
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uid
        )
        mData = MatchData()
        mData.uID = feed.uID
        mData.detailID = feed.matchData.detailID
        mData.timingID = feed.matchData.timingID
        mData.lastModified = feed.matchData.lastModified
        mData.stats = self.prepareMatchStats(feed.matchData.matchStats)
        mData.matchOfficials = self.prepareMatchOfficials(feed.matchData.matchOfficials)
        mData.teamData = self.prepareTeamData(feed.matchData.teamData)
        mData.matchInfo = self.prepareMatchInfo(feed.matchData.matchInfo)
        mData.schedule = self.prepareSchedule(feed.matchData.schedule)

        mData.assistantOfficials = self.prepareAssistantOfficials(
            feed.matchData.assistantOfficials
        )
        mData.shootOut = self.prepareShootOut(feed.matchData.shootOut)
        mData.penaltyShot = self.preparePenaltyShot(feed.matchData.penaltyShot)
        mData.previousMatch = self.preparePreviousMatch(feed.matchData.previousMatch)
        mData.VARData = self.prepareVARData(feed.matchData.VARData)

        return mData

    def prepareStats(self, data):
        """
        - stats
        [
            {
                type: "match_time",
                value: "71"
            },
        ]
        """
        stats = []
        for i in range(len(data)):
            st = Stat(data[i].value, data[i].type)
            stats.append(st)
        return stats

    # def getMatchTeams(self,uId):
    #     feed = self.connector.getFeed(Parser.Feeds.feed9, self.competitionID, self.seasonID, uId)
    #     # available = self.connector.isFeedAvailable(Parser.Feeds.feed9,self.competitionID,self.seasonID,uId)
    #
    #     feed = F9_Root.objects(Q(uID="f"+uId))
    #     return self.prepareTeamData(feed)

    def getMatchTeamOfficials(self, uId, teamId):
        """
        teamofficial: {
            first: "",
            last: "",
            type: "manager",
            uID: ""
        }
        """
        feed = F9_Root.objects(
            Q(uID=uId)
        )  # TODO: Assumption is the match is already stored in the database, this might fail!
        for item in feed.teams:
            if item.uID == teamId:
                return item.teamOfficials

    # F9 teams data under the F9_root
    def getTeamData(self, teams):

        teamsData = []

        for i in range(len(teams)):
            # team = TeamData()
            team = TeamData
            team.score = teams[i].score
            team.side = teams[i].side
            team.teamRef = teams[i].teamRef
            team.goals = self.prepareGoals(teams.goals)
            team.teamStats = self.prepareTeamStats(teams.teamStats)
            team.missedPenalty = self.prepareMissedPenalty(teams.missedPenalty)
            team.substitutions = self.prepareSubstitutions(teams.substitutions)
            team.playerLineUp = self.preparePlayerLineUp(teams.playerLineUp)
            team.booking = self.prepareBooking(teams.booking)
            teamsData.append(team)

        return teamsData

    def prepareKits(self, kits):
        ks = []
        for i in range(len(kits)):
            # kit = Kit()
            kit = Kit
            kit.id = kits[i].id
            kit.colour1 = kits[i].colour1
            kit.colour2 = kits[i].colour2
            kit.type = kits[i].type
            ks.append(kit)
        return ks

    def prepareTeamOfficials(self, tofficals):
        """
            teamofficial: {
            first: "",
            last: "",
            type: "manager",
            uID: ""
        }
        """
        tofs = []
        for i in range(len(tofficals)):
            tof = TeamOfficial(
                tofficals[i].first,
                tofficals[i].last,
                tofficals[i].type,
                tofficals[i].uID,
            )
            tof.country = tofficals[i].country
            tofs.append(tof)
        return tofs

    def preparePlayers(self, players):
        ps = []
        for i in range(len(players)):
            player = Player(players[i].position)
            player.uID = players[i].uID
            player.first = players[i].first
            player.last = players[i].last
            ps.append(player)
        return ps

    def getTeams(self, teams):
        tes = []
        for i in range(len(teams)):
            t = F9_Team()
            t.uID = teams[i].uID
            t.name = teams[i].name
            t.country = teams[i].country
            t.kits = self.prepareKits(teams[i].kits)
            t.teamOfficials = self.prepareTeamOfficials(teams[i].teamOfficials)
            t.players = self.preparePlayers(teams[i].players)
            tes.append(t)
        return tes

    def getTeamBookings(self, uId, teamId):
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uId
        )
        for i in range(len(feed.matchData.teamData)):
            if feed.matchData.teamData.teamRef == teamId:  # t2141
                return self.prepareBooking(feed.matchData.teamData[i].booking)
        return None

    def getTeamStats(self, uId, teamName):
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uId
        )
        feed40 = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID, None
        )
        tuid = None
        for i in range(len(feed40.teams)):
            if feed40.team[i].name == teamName:
                tuid = feed40.team[i].uID
                break
        # t2141
        for i in range(len(feed.matchData.teamData)):
            if feed.matchData.teamData.teamRef == tuid:
                return self.prepareTeamStats(feed.matchData.teamData[i].teamStats)
        return None

    def getTeamStats(self, uId, teamId):
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uId
        )
        for i in range(len(feed.matchData.teamData)):
            if feed.matchData.teamData.teamRef == teamId:  # t2141
                return self.prepareTeamStats(feed.matchData.teamData[i].teamStats)

        return None

    def getCompetition(self, uID):
        """
        # - competition, GET
            competition / season / match / matchid / competition
            {
                country: "",
                name: "",
                uID: "",
                stats: [
                    season_id: "",
            season_name: "",
            symid: "",
            matchday: ""
            ]
            }
        """
        pass

    def getVenue(self, uID):

        """
        # - venue, GET
        competition / season / match / matchid / venue
        {
            country: "",
            name: "",
            uID: ""
        }
        """
        feed = self.connector.getFeed(
            Parser.Feeds.feed9, self.competitionID, self.seasonID, uID
        )
        venue = Venue()
        venue.country = feed.venue.country
        venue.name = feed.venue.name
        venue.uID = feed.venue.uID

        return jsonSerializer(venue)

    def getAllSeasonGameEvents(self, teamID, playerID="p-1"):

        game_ids = []
        if playerID != "p-1":
            papi = self.papi()
            player_name = papi.get_player_name(int(playerID))  # find the player id
            old_team_name = papi.getOldTeamWithName(player_name)
            gameIDs = papi.getGamesPlayedByTeam(teamID)  # get all played game ids
            old_game_ids = None
            if old_team_name:
                old_game_ids = papi.getGamesPlayedByTeam(papi.getTeamID(old_team_name))
            if old_game_ids:
                for tempGame in old_game_ids:
                    if tempGame not in gameIDs:
                        gameIDs.append(tempGame)
            for gid in gameIDs:
                feed = self.connector.getFeed(
                    Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
                )
                events = []
                for event in feed.game.events:
                    events.append(event)
                game_ids.append(events)
        else:
            gameIDs = self.getGamesPlayedByTeam(teamID)  # get all played game ids

            for gid in gameIDs:  # read all events where team id is equal to the event id
                feed = self.connector.getFeed(
                    Parser.Feeds.feed24, self.competitionID, self.seasonID, gid
                )
                events = []
                for event in feed.game.events:
                    # if teamID[1:] != str(event.teamID):  # ! opposite team is excluded.
                    #     continue
                    events.append(event)
                game_ids.append(events)
        print(f"****{len(game_ids)}")
        leng = 0
        for x in game_ids:
            leng += len(x)
        print(leng)
        return game_ids

    def getGameEvents(self, gameId):
        """
        Return the all events of a game
        :param gameId:
        :return:
        """
        events = []
        feed = self.connector.getFeed(
            Parser.Feeds.feed24, self.competitionID, self.seasonID, gameId
        )
        for event in feed.game.events:
            events.append(event)
        return events

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

    # 1002148 smallest gameID

    def getTeamID(self, teamName):
        feed = self.connector.getFeed(
            Parser.Feeds.feed40, self.competitionID, self.seasonID
        )
        for team in feed.team:
            if team.name == teamName:
                return team.uID

    def get_season_all_game_ids(self):
        query = feedAPI.QueryPipeline.QueryPipeline(
            root_document=F1_Root
        ).match(
            {
                "competitionID": {"$eq": int(self.competitionID)},
                "seasonID": {"$eq": int(self.seasonID)},
            }
        ).keep("matchData").join(
            self.doc_name(F1_MatchData), "matchData", "_id", "matchData"
        ).parallelize("matchData").group(
            main_field=None,
            set_fields={
                "games": "matchData.uID"
            }
        )
        games = None
        for result in query.run():
            games = result["games"]

        return games

    def get_random_game_ids(self, k: int = 10):
        games = self.get_season_all_game_ids()
        selected = random.choices(population=games, k=k)
        return selected

    # --------------Construct and Save the Game and Minute Statistics of Players-----------------

    def get_total_game_minutes_stats(self, game_id: int = None, player_id: int = None, team_id: int = None):
        tapi = self.tapi()

        def re_format_data(old_dict_object):
            if "total_minutes" not in old_dict_object:
                print("Dict object does not have the key 'total_minutes'.")
                return None

            if "starting11" in old_dict_object:
                if int(old_dict_object["starting11"]) == 1:
                    starting_in_11 = True
                else:
                    starting_in_11 = False
            else:
                starting_in_11 = None

            if "used_sub" in old_dict_object:
                if int(old_dict_object["used_sub"]) == 1:
                    used_sub = True
                else:
                    used_sub = False
            else:
                used_sub = None

            if "games_played" in old_dict_object:
                if int(old_dict_object["games_played"]) == 1:
                    in_game = True
                else:
                    in_game = False
            else:
                in_game = None

            new_dict_object = {
                "starting_in_11": starting_in_11,
                "used_sub": used_sub,
                "in_game": in_game,
                "total_play_time": old_dict_object["total_minutes"]
            }

            return new_dict_object

        def _parse_raw_event_objects():
            minute_parser = GamesandMinutesEvents.GamesandMinutesEvents()
            parsed_result = dict()
            match_result = self.get_match_data(
                game_ids=[game_id],
                event_names=["minutes"],
                get_f24_event_objects=True
            )
            match_data = dict()
            for match in match_result:
                match_data = match
                break

            if "events" in match_data:
                for dict_object in match_data["events"]:
                    for temp_team_id, f24_event_objects in dict_object.items():
                        temp_team_players_list = list()
                        temp_data = {"events": f24_event_objects, "teamID": temp_team_id}
                        for temp_player_id, parsed_events in minute_parser.callEventHandler(data=temp_data).items():
                            temp_team_players_list.append({
                                temp_player_id: re_format_data(parsed_events)
                            })
                        parsed_result[temp_team_id] = temp_team_players_list

            return parsed_result

        def _calculate_total_game_minute_stats():
            parsed_result = _parse_raw_event_objects()
            for temp_team_id in parsed_result:
                if team_id:
                    if temp_team_id != team_id:
                        continue
                for temp_player_info_dict in parsed_result[temp_team_id]:
                    temp_player_id, temp_results = list(temp_player_info_dict.items())[0]
                    if player_id:
                        if temp_player_id != player_id:
                            continue
                    APIHelpers.PlayerGameMinuteStatistics(
                        game_id=game_id,
                        player_name=tapi.get_player_name(player_id=temp_player_id),
                        player_id=temp_player_id,
                        competition_id=self.competitionID,
                        season_id=self.seasonID,
                        team_name=tapi.get_team_name(team_id=temp_team_id),
                        team_id=temp_team_id,
                        results=temp_results
                    )

        if player_id:
            match_season_league_player = {
                "competitionID": self.competitionID, "seasonID": self.seasonID, "playerID": player_id
            }
            look_up_list = [self.doc_name(doc=GameMinuteStatistics), "gamesPlayed", "_id", "gamesPlayed"]
            unnecessary_fields = ["_id", "gamesPlayed._id"]
            query_object = feedAPI.QueryPipeline.QueryPipeline(PlayerMinuteStatistics)
            query_object.match(match_season_league_player).join(*look_up_list).remove(*unnecessary_fields)
            if team_id:
                if tapi.does_team_exist(team_id=team_id) is None:
                    print("Given team_id does not exists, please check it again.")
                    return None
                query_object.match({"gamesPlayed.teamID": team_id})

            result = list(query_object.run())

            if 0 != len(result):
                return result
            else:
                _calculate_total_game_minute_stats()

        elif game_id:
            match_season_league_game = {"gameID": game_id}
            query_object = feedAPI.QueryPipeline.QueryPipeline(GameMinuteStatistics)
            result = query_object.match(match_season_league_game).limit(1).run()

            if 0 != len(list(result)):
                return _parse_raw_event_objects()
            else:
                _calculate_total_game_minute_stats()

        else:
            print("Both of the game_id and player_id can not be None.")
            return None


    # --------------Application of Game Minute Stats for Querying-----------------
    def get_game_minutes_stats(
            self, game_id: int, team_id: int = None, player_id: int = None
    ):
        match_conditions = {"gameID": int(game_id)}
        if team_id is not None:
            match_conditions["teamID"] = int(team_id)
        look_up_list = [
            self.doc_name(doc=PlayerMinuteStatistics),
            "_id",
            "gamesPlayed",
            "temp"
        ]
        unnecessary_fields = ["_id", "temp"]
        add_player_id = ("playerID", "temp.playerID", 0)
        add_player_name = ("playerName", "temp.playerName", 0)
        query_object = QueryPipeline.QueryPipeline(
            root_document=GameMinuteStatistics
        )
        query_object.match(
            match_conditions
        ).join(
            *look_up_list
        ).add_field_from_array(
            *add_player_id
        ).add_field_from_array(
            *add_player_name
        ).remove(
            *unnecessary_fields
        )
        if player_id:
            query_object.match(
                {"playerID": player_id}
            )
        result = query_object.run()
        return result


    # -----------------------Get Match Data---------------------------
    def get_match_data(
            self,
            game_ids: list = None,
            team_ids: list = None,
            player_ids: list = None,
            event_names: list = None,
            time_interval: dict = None,
            limit: int = None,
            parse: bool = True,
            all_games_bool: bool = False,
            show_events: bool = False,
            show_event_time: bool = False,
            get_only_games: bool = False,
            get_f24_event_objects: bool = False,
            event_times_converter: bool = True
    ):

        game_ids, team_ids, player_ids = Utils.convert_input_into_list(game_ids, team_ids, player_ids)
        player_ids, team_ids = Utils.convert_input_into_int_list(player_ids, team_ids)

        if all_games_bool:
            if team_ids is not None and player_ids is not None:
                if len(team_ids) == 1 and len(player_ids) == 1:
                    game_ids = self.papi().get_player_games_played(
                        player_id=int(player_ids[0]), team_id=int(team_ids[0])
                    )
                else:
                    print("The operation only supports getting ",
                          "all the match data for just ONE team and ONE player at a time.")
                    return None
            elif team_ids is not None:
                if len(team_ids) == 1:
                    game_ids = self.tapi().get_all_team_played_games(team_id=int(team_ids[0]))
                else:
                    print("The operation only supports getting ",
                          "all the match data for just ONE team at a time.")
                    return None

            elif player_ids is not None:
                if len(player_ids) == 1:
                    game_ids = self.papi().get_player_games_played(player_id=int(player_ids[0]))
                else:
                    print("The operation only supports getting ",
                          "all the match data for just ONE player at a time.")
                    return None
            else:
                print("Both player_ids and team_ids can not be None at the same time, while all_games input is True.")
                return None
        game_ids, = Utils.convert_input_into_str_list(game_ids, remove_char="g")
        game_ids, = Utils.convert_input_into_int_list(game_ids)

        root_object = F24_Root
        query_object = feedAPI.QueryPipeline.QueryPipeline(root_document=root_object, allow_disk_usage=True).match(
            {
                "competitionID": {"$eq": int(self.competitionID)}, "seasonID": {"$eq": int(self.seasonID)},
            }
        )

        if game_ids:
            query_object.match({"gameID": {"$in": game_ids}})

        query_object.join(self.doc_name(doc=F24_Game), "game", "_id", "game")

        if get_only_games:
            result = query_object.remove("game.events", "_id", "game._id").run()
            return result

        query_object.join(
            self.doc_name(doc=F24_Event), "game.events", "_id", "events"
        ).remove("game.events").parallelize("events")

        if time_interval:
            query_object.match(time_interval)

        # If we add these conditions, then there will be inconsistencyGoalkeeper and Pass events.
        if team_ids:
            query_object.match({"events.teamID": {"$in": team_ids}})
        if player_ids:
            query_object.match({"events.playerID": {"$in": player_ids}})

        if show_event_time:
            query_object.match({"events.typeID": {"$in": Events.EventIdList["EventMinutes"]}})

        elif event_names:
            all_event_ids = set()
            event_dict = self.evapi().multi_event_dict()
            converted_events = list()
            for event in event_names:
                if event in event_dict:
                    event = event_dict[event]
                all_event_ids = all_event_ids.union(set(Events.EventIdList[event]))
                converted_events.append(event)
            query_object.match({"events.typeID": {"$in": list(all_event_ids)}})
            event_names = converted_events

        query_object.join(
            self.doc_name(doc=F24_QEvent),
            "events.qEvents",
            "_id",
            "events.qEvents"
        ).group(
            main_field="gameID",
            first_fields={"game": "game"},
            push_fields={"events": "events"}
        ).remove(
            "_id",
            "game._id",
            "events._id",
            "events.qEvents._id"
        ).sort(
            {"game.matchDay": 1}
        )

        if limit:
            query_object.limit(max_limit=limit)

        result = list(
            query_object.run()
        )

        if show_event_time:
            return self.get_match_data_event_times(
                result=result, player_ids=player_ids, team_ids=team_ids,
                event_times_converter=event_times_converter
            )
        elif parse:
            if player_ids and team_ids:
                return self.get_match_data_players(
                    result=result, player_ids=player_ids, event_names=event_names,
                    get_f24_event_objects=get_f24_event_objects
                )
            elif team_ids:
                return self.get_match_data_teams(
                    result=result,
                    team_ids=team_ids,
                    event_names=event_names,
                    get_f24_event_objects=get_f24_event_objects
                )
            elif player_ids:
                return self.get_match_data_players(
                    result=result,
                    player_ids=player_ids,
                    event_names=event_names,
                    get_f24_event_objects=get_f24_event_objects
                )
            elif game_ids:
                return self.get_match_data_teams(
                    result=result, event_names=event_names,
                    get_f24_event_objects=get_f24_event_objects
                )
            else:
                print("All of the followings can not be empty at the same time: ",
                      "player name, team name, and games.")
                return dict()
        else:
            if show_events:
                print("It is not recommended to show more than one game's all events!",
                      "Therefore, only the first game from the result will be shown.")
                for mongo_db_document in result:
                    return mongo_db_document
            else:
                for mongo_db_document in result:
                    del mongo_db_document["events"]
                return result

    @staticmethod
    def get_match_data_f24_object_def(event):
        q_list = []
        if isinstance(event["qEvents"], list):
            for q in event["qEvents"]:
                q_obj = F24_QEvent(**q)
                q_list.append(q_obj)
        elif isinstance(event["qEvents"], dict):
            q_obj = F24_QEvent(**event["qEvents"])
            q_list.append(q_obj)
        else:
            pass
        event["qEvents"] = q_list
        event_obj = F24_Event(**event)
        return event_obj

    def get_match_data_teams(
            self,
            result,
            team_ids=None,
            event_names=None,
            get_f24_event_objects=False
    ):
        tapi = self.tapi()
        for index, mongo_db_document in enumerate(result):
            teams = dict()
            for field_name in ["away", "home"]:
                temp_team_id = mongo_db_document["game"][0][field_name + "TeamID"]
                if team_ids is not None:
                    if temp_team_id not in team_ids:
                        continue
                temp_team_name = mongo_db_document["game"][0][field_name + "TeamName"]
                teams[int(temp_team_id)] = str(temp_team_name)

            event_objects = list()

            for event in mongo_db_document["events"]:
                event_obj = self.get_match_data_f24_object_def(event)
                event_objects.append(event_obj)

            data = dict()
            mongo_db_document["events"] = list()
            for team in teams:
                if get_f24_event_objects:
                    temp_dict = {
                        team: event_objects
                    }
                    mongo_db_document["events"].append(temp_dict)
                else:
                    data["teamID"] = team
                    data["playerID"] = tapi.get_all_players_ids(
                        team_id=data["teamID"]
                    )
                    data["playerName"] = tapi.get_all_players_name(
                        team_id=data["teamID"]
                    )
                    data["total_minutes"] = None
                    data["events"] = event_objects
                    event_handler = EventHandler.EventHandler()
                    if event_names:
                        results = event_handler.handleMultipleEvent(
                            eventTypes=event_names,
                            data=data,
                            print_results=False
                        )
                    else:
                        results = event_handler.handle_all_events(
                            data=data, print_results=False
                        )
                    all_event_stats = {
                        "teamName": teams[team],
                    }
                    if results:
                        for event_stats in results:
                            if event_stats:
                                all_event_stats = {**all_event_stats, **event_stats}
                    mongo_db_document["events"].append(all_event_stats)
                result[index] = mongo_db_document
        return result

    def get_match_data_players(
            self,
            result,
            player_ids,
            event_names=None,
            get_f24_event_objects=False
    ):
        tapi = self.tapi()
        papi = self.papi()
        all_documents = list()
        for mongo_db_document in result:
            event_objects = list()
            game_id = mongo_db_document["game"][0]["ID"]
            for event in mongo_db_document["events"]:
                event_obj = self.get_match_data_f24_object_def(event)
                event_objects.append(event_obj)

            data = dict()
            mongo_db_document["events"] = list()

            players = dict()
            for player in player_ids:
                team_ids = papi.get_played_teams_of_player(player_id=player)
                players[player] = team_ids

            for player, team_ids in players.items():
                for team in team_ids:
                    player_played = list(
                        self.get_game_minutes_stats(
                            game_id=game_id, team_id=team, player_id=player
                        )
                    )
                    if len(player_played) == 1:
                        if player_played[0]["game_minute_stats"]["in_game"]:
                            total_minutes = player_played[0]["game_minute_stats"]["total_play_time"]
                        else:
                            continue
                    else:
                        continue

                    if get_f24_event_objects:
                        temp_dict = {
                            team: {player: event_objects}
                        }
                        mongo_db_document["events"].append(temp_dict)
                        continue

                    data["teamID"] = team
                    data["playerID"] = player
                    data["playerName"] = tapi.get_player_name(data["playerID"])
                    data["total_minutes"] = total_minutes
                    data["events"] = event_objects
                    event_handler = EventHandler.EventHandler()

                    if event_names:
                        results = event_handler.handleMultipleEvent(
                            eventTypes=event_names, data=data, print_results=False
                        )
                    else:
                        results = event_handler.handle_all_events(data=data, print_results=False)

                    all_event_stats = {
                        "playerName": data["playerName"],
                        "teamName": tapi.get_team_name(data["teamID"]),
                        "totalMin": total_minutes
                    }

                    if results:
                        for event_stats in results:
                            if event_stats:
                                all_event_stats = {**all_event_stats, **event_stats}

                    mongo_db_document["events"].append(all_event_stats)

            if 0 < len(mongo_db_document["events"]):
                all_documents.append(mongo_db_document)

        return all_documents

    def get_match_data_event_times(self, result, team_ids=None, player_ids=None, event_times_converter=True):
        for mongo_db_document in result:
            all_event_objects = list()

            for event in mongo_db_document["events"]:
                event_obj = self.get_match_data_f24_object_def(event)
                all_event_objects.append(event_obj)

            data = dict()
            data["teamID"] = team_ids
            data["playerID"] = player_ids
            data["events"] = all_event_objects
            data["converter"] = event_times_converter
            data["competitionID"] = int(self.competitionID)
            data["seasonID"] = int(self.seasonID)

            event_handler = EventHandler.EventHandler()
            results = event_handler.handle_single_event(eventType="EventMinutes", data=data, print_results=False)

            mongo_db_document["events"] = results

        return result

    # -----------------------Applications of Get Match Data---------------------------

    def get_season_all_games_summary(self):
        result = self.get_match_data(
            parse=False, get_only_games=True
        )
        return result

    def get_season_all_games_ids(self):
        result = self.get_season_all_games_summary()
        game_ids = list()
        for game in result:
            try:
                game_ids.append(game["game"][0]["ID"])
            except (KeyError, IndexError) as err:
                print("Some game ids could not added into resulting list!")
                print(f"The error: {err}")
                print(f",The Objective dictionary: {game}")
                continue
        return game_ids

if __name__ == "__main__":
    api = GameAPI(115, 2018)
    test_result = api.get_match_data(
        game_ids=[1002148],
        event_names=["minutes"],
        get_f24_event_objects=True
    )

    for test_match_data in test_result:
        print(test_match_data)
        break
