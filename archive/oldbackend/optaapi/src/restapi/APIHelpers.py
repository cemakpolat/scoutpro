"""
Author: Cem Akpolat

"""
import sys

sys.path.append("..")  # Adds higher directory to python modules path.
from datetime import datetime
from mongoengine import *
from src.dbase import DBHelper
from src.utils import Utils
from src.feedAPI import EventAPI
from src.feedAPI import Connector
from src.utils import Utils
import json

converter = Utils.convert_id


class Competition(object):
    def __init__(self, country, name, uID):
        self.country = country
        self.name = name
        self.stats = []
        self.uID = uID
        self.pool = None
        self.roundNumber = None

    def setStats(self, stats):
        self.stat = stats

    def addStat(self, Stat):
        self.stats.append(Stat)

    def toString(self):
        print(self.country + self.name + self.uID)

    def setFeature(self, featureName, featureValue):
        if featureName == "country":
            self.country = featureValue
        elif featureName == "Name":
            self.name = featureValue
        elif featureName == "Stat":
            self.stats = featureValue
        elif featureName == "RoundNumber":
            self.roundNumber = featureValue
        elif featureName == "uID":
            self.uID = featureValue
        elif featureName == "Pool":
            self.pool = featureValue
        else:
            print("feature " + featureName + " could not be found in Competition")
        return self


# Team Stat or Stat
class Stat(object):
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def toString(self):
        print(self.type + " " + self.value)


class Kit(object):
    def __init__(self, id, colour1, type):
        self.id = id
        self.colour1 = colour1
        self.colour2 = None
        self.type = type

    def setSecondColour(self, color):
        self.colour2 = color


class Stadium(object):
    def __init__(self, name, uID):
        self.name = name
        self.capacity = None
        self.uID = converter(uID)

    def setCapacity(self, capacity):
        self.capacity = capacity


class PersonalInfo(object):
    def __init__(self, first, last, type, uID):
        self.first = first
        self.last = last
        self.type = type
        self.uID = converter(uID)
        self.leaveDate = None
        self.joinDate = None
        self.birthDate = None


class TeamOfficial(object):
    def __init__(self, first, last, type, uID):
        self.first = first
        self.last = last
        self.type = type
        self.uID = converter(uID)
        self.leaveDate = None
        self.joinDate = None
        self.birthDate = None
        self.birthPlace = None
        self.country = None
        # self.known = None

    def setFeature(self, featureName, featureValue):
        if featureName == "leave_date":
            self.leaveDate = featureValue
        elif featureName == "join_date":
            self.joinDate = featureValue
        elif featureName == "BirthDate":
            self.birthDate = featureValue
        elif featureName == "BirthPlace":
            self.birthPlace = featureValue
        elif featureName == "country" or featureName == "Country":
            self.country = featureValue
        # elif featureName == 'Known':
        #     self.known = featureValue
        else:
            print("feature " + featureName + " could not be found in TeamOfficial")
        return self


class Player(object):
    def __init__(self, position):
        self.name = None
        self.first = None
        self.last = None
        self.type = None
        self.uID = None
        self.position = position
        self.known = None
        self.captain = None
        self.playerData = None
        self.stats = None
        self.playerLoan = None

    def setFeature(self, feature, value):
        if feature == "Name":
            self.name = value
        elif feature == "uID":
            self.uID = converter(value)
        elif feature == "Known":
            self.known = value
        elif feature == "Type":
            self.type = type
        elif feature == "First":
            self.first = value
        elif feature == "Last":
            self.last = value
        elif feature == "PlayerData":
            self.playerData = value
        elif feature == "Stat":
            self.stats = value
        elif feature == "Captain":
            self.captain = value
        elif feature == "PlayerLoan":
            self.playerLoan = value
        else:
            print("feature " + feature + " is not found!")
        return self


class Team(object):
    def __init__(self, name, uID):
        self.name = name
        self.uID = converter(uID)
        self.country = None
        self.countryISO = None
        self.countryID = None
        self.regionName = None
        self.regionID = None
        self.officialClubName = None
        self.stadium = None
        self.kits = None
        self.teamOfficials = None
        self.players = None
        self.shortClubName = None
        self.founded = None
        self.symid = None
        self.fifaRank = None
        self.city = None
        self.postalCode = None
        self.street = None
        self.webAddress = None

    def setFeature(self, feature, value):

        if feature == "name":
            self.kits = value
        elif feature == "uID":
            self.kits = value
        elif feature == "Kit":
            self.kits = value
        elif feature == "country" or feature == "Country":
            self.country = value
        elif feature == "country_id":
            self.countryID = converter(value)
        elif feature == "country_iso":
            self.countryISO = value
        elif feature == "official_club_name":
            self.officialClubName = value
        elif feature == "region_id":
            self.regionID = converter(value)
        elif feature == "region_name":
            self.regionName = value
        elif feature == "short_club_name":
            self.shortClubName = value
        elif feature == "Player":
            self.players = value
        elif feature == "TeamOfficial":
            self.teamOfficials = value
        elif feature == "Stadium":
            self.stadium = value
        elif feature == "Founded":
            self.founded = value
        elif feature == "SYMID":
            self.symid = value
        elif feature == "FifaRank":
            self.fifaRank = value
        elif feature == "City":
            self.city = value
        elif feature == "postal_code":
            self.postalCode = value
        elif feature == "Street":
            self.street = value
        elif feature == "web_address":
            self.webAddress = value
        elif feature == "FifaRank":
            self.founded = value
        else:
            print("feature " + feature + " could not be found in Team!")

        return self


class Result(object):
    def __init__(self, type):
        self.type = type
        self.minutes = None
        self.reason = None
        self.winner = None

    def setWinner(self, winner):
        self.winner = winner
        return self

    def setMinutes(self, min):
        self.minutes = min
        return self

    def setReason(self, reason):
        self.reason = reason
        return self


class MatchInfo(object):
    def __init__(self, date):
        self.result = None
        self.date = date
        self.matchWinner = None
        self.TZ = None
        self.venueID = None
        self.matchDay = None
        self.matchType = None
        self.matchWinner = None
        self.period = None
        self.status = None
        self.teamRef = None
        self.playerRef = None
        self.timestamp = None
        self.varReason = None
        self.leg = None
        self.firstLegID = None
        self.legWinner = None
        self.nextMatch = None
        self.nextMatchLoser = None
        self.roundNumber = None
        self.roundType = None
        self.groupName = None
        self.gameWinner = None
        self.gameWinnerType = None
        self.timestamp = None

    def setResult(self, result):
        self.result = result

    def setFeature(self, featureName, featureValue):
        if featureName == "TZ":
            self.TZ = featureValue
        elif featureName == "MatchType":
            self.matchType = featureValue
        elif featureName == "MatchDay":
            self.matchDay = featureValue
        elif featureName == "MatchWinner":
            self.matchWinner = converter(featureValue)
        elif featureName == "PlayerRef":
            self.playerRef = converter(featureValue)
        elif featureName == "Status":
            self.status = featureValue
        elif featureName == "Period":
            self.period = featureValue
        elif featureName == "Venue_id":
            self.venueID = converter(featureValue)
        elif featureName == "TeamRef":
            self.teamRef = converter(featureValue)
        elif featureName == "TimeStamp":
            self.timestamp = featureValue
        elif featureName == "VAR_Reason":
            self.varReason = featureValue
        elif featureName == "leg":
            self.leg = featureValue
        elif featureName == "FirstLegId":
            self.firstLegID = converter(featureValue)
        elif featureName == "LegWinner":
            self.legWinner = featureValue
        elif featureName == "NextMatch":
            self.nextMatch = featureValue
        elif featureName == "NextMatchLoser":
            self.nextMatchLoser = featureValue
        elif featureName == "RoundNumber":
            self.roundNumber = converter(featureValue)
        elif featureName == "RoundType":
            self.roundType = featureValue
        elif featureName == "GroupName":
            self.groupName = featureValue
        elif featureName == "GameWinner":
            self.gameWinner = converter(featureValue)
        elif featureName == "GameWinnerType":
            self.gameWinnerType = featureValue
        else:
            print(
                "feature "
                + featureName
                + " "
                + featureValue
                + " could not be found in MatchInfo"
            )
        return self


class AssistantOfficial(object):
    def __init__(self, first, last, uID, type):
        self.first = first
        self.last = last
        self.uID = converter(uID)
        self.type = type


class MatchOfficial(object):
    def __init__(self, firstname, lastname, uID, type):
        self.first = firstname
        self.last = lastname
        self.uID = converter(uID)
        self.type = type
        self.officialRef = None
        self.officialData = None

    def setFeature(self, featureName, featureValue):
        if featureName == "OfficialRef":
            self.officialRef = featureValue
        elif featureName == "OfficialData":
            self.officialData = featureValue
        else:
            print("feature isn't found!")
        return self


class VARData(object):
    def __init__(
            self,
            decision,
            eventID,
            eventNumber,
            min,
            outcome,
            period,
            playerRef,
            reason,
            sec,
            teamRef,
    ):
        self.decision = decision
        self.eventID = eventID
        self.eventNumber = eventNumber
        self.min = min
        self.outcome = outcome
        self.period = period
        self.playerRef = converter(playerRef)
        self.reason = reason
        self.sec = sec
        self.teamRef = converter(teamRef)


class MatchState(object):
    def __init__(self, value, type):
        self.type = type
        self.value = value


class MatchPlayer(object):
    def __init__(self, playerRef, position, shirtnumber, status):
        self.playerRef = converter(playerRef)
        self.position = position
        self.shirtNumber = converter(shirtnumber)
        self.status = status
        self.stats = None
        self.subPosition = None
        self.captain = None

    def setCaptain(self, captain):
        self.captain = captain

    def setStat(self, stat):
        self.stats = stat

    def setFeature(self, featureName, featureValue):
        if featureName == "Stat":
            self.stats = featureValue
        elif featureName == "Captain":
            self.captain = featureValue
        elif featureName == "PlayerRef":
            self.playerRef = converter(featureValue)
        elif featureName == "Position":
            self.position = featureValue
        elif featureName == "ShirtNumber":
            self.shirtNumber = converter(featureValue)
        elif featureName == "Status":
            self.status = featureValue
        elif featureName == "SubPosition":
            self.subPosition = featureValue
        else:
            print("feature " + featureName + " could not be found in MatchPlayer")
        return self


class Substitution(object):
    def __init__(self, eventID, eventNumber, period, timeStamp, uID):
        self.eventID = eventID
        self.eventNumber = eventNumber
        self.min = None
        self.period = period
        self.reason = None
        self.suboff = None
        self.subon = None
        self.substitutePosition = None
        self.sec = None
        self.time = None
        self.timestamp = timeStamp
        self.type = None
        self.uID = uID
        self.retired = None

    def setFeature(self, featureName, featureValue):
        if featureName == "Time":
            self.time = featureValue
        elif featureName == "Min":
            self.min = featureValue
        elif featureName == "Sec":
            self.sec = featureValue
        elif featureName == "Type":
            self.type = featureValue
        elif featureName == "Retired":
            self.retired = featureValue
        elif featureName == "Reason":
            self.reason = featureValue
        elif featureName == "SubOn":
            self.subon = featureValue
        elif featureName == "SubOff":
            self.suboff = featureValue
        elif featureName == "SubstitutePosition":
            self.substitutePosition = featureValue

        else:
            print("feature " + featureName + " could not be found in Substitution")


class MissedPenalty(object):
    def __init__(self):
        self.period = None
        self.time = None
        self.playerRef = None
        self.eventNumber = None
        self.type = None
        self.uID = None

    def setFeature(self, featureName, featureValue):
        if featureName == "period":
            self.period = featureValue
        elif featureName == "time":
            self.time = featureValue
        elif featureName == "playerRef":
            self.playerRef = featureValue
        elif featureName == "eventNumber":
            self.eventNumber = featureValue
        elif featureName == "type":
            self.type = featureValue
        elif featureName == "uID":
            self.uID = featureValue
        return self


class Goal(object):
    def __init__(self):
        self.eventID = None
        self.eventNumber = None
        self.min = None
        self.period = None
        self.playerRef = None
        self.sec = None
        self.time = None
        self.timeStamp = None
        self.type = type
        self.uID = None
        self.assist = None
        self.secondAssist = None
        self.soloRun = None
        self.VARReviewed = None
        self.originalDecision = None

    def setAssist(self, goalAssist):
        self.assist = goalAssist

    def setFeature(self, featureName, featureValue):
        if featureName == "Card":
            self.card = featureValue
        elif featureName == "CardType":
            self.cardType = featureValue
        elif featureName == "EventID":
            self.eventID = featureValue
        elif featureName == "EventNumber":
            self.eventNumber = featureValue
        elif featureName == "Min":
            self.min = featureValue
        elif featureName == "Period":
            self.period = featureValue
        elif featureName == "PlayerRef":
            self.playerRef = converter(featureValue)
        elif featureName == "Sec":
            self.sec = featureValue
        elif featureName == "Time":
            self.time = featureValue
        elif featureName == "Type":
            self.type = featureValue
        elif featureName == "TimeStamp":
            self.timeStamp = featureValue
        elif featureName == "Time":
            self.time = featureValue
        elif featureName == "uID":
            self.uID = converter(featureValue)
        elif featureName == "SecondAssist":
            self.secondAssist = featureValue
        elif featureName == "SoloRun":
            self.soloRun = featureValue
        elif featureName == "VARReviewed":
            self.VARReviewed = featureValue
        elif featureName == "OriginalDecision":
            self.originalDecision = featureValue
        else:
            print("object could not be found!")

        return self


class Assist(object):
    def __init__(self, playerRef):
        self.playerRef = playerRef


class SecondAssist(object):
    def __init__(self, playerRef):
        self.playerRef = playerRef


class TeamStat(object):
    def __init__(self, value, type):
        self.value = value
        self.FH = None
        self.SH = None
        self.type = type

    def setFeature(self, featureName, featureValue):
        if featureName == "SH":
            self.SH = featureValue
        elif featureName == "FH":
            self.FH = featureValue
        return self


class ShootOut(object):
    def __init__(self, penalty):
        self.firstPenalty = penalty


class PenaltyShot(object):
    def __init__(self, outcome, eventNumber, playerRef, uId):
        self.outcome = outcome
        self.eventNumber = eventNumber
        self.playerRef = playerRef
        self.uID = uId


class TeamData(object):
    def __init__(self, teamRef):
        self.score = None
        self.side = None
        self.teamRef = converter(teamRef)
        self.halfScore = None
        self.goals = None
        self.teamStats = None
        self.missedPenalty = None
        self.substitutions = None
        self.playerLineUp = None
        self.shootOutScore = None
        self.booking = None

        self.ninetyScore = None
        self.extraScore = None
        self.penaltyScore = None

    def setGoals(self, goals):
        self.goals = goals

    # def setPlayerLineUp(self,matchPlayer):
    #   self.mplayers = matchPlayer

    def setStats(self, stats):
        self.teamStats = stats

    def setSubstitution(self, subs):
        self.substitutions = subs

    def setBooking(self, booking):
        self.booking = booking

    def setFeature(self, featureName, featureValue):
        if featureName == "Score":
            self.score = featureValue
        elif featureName == "Side":
            self.side = featureValue
        elif featureName == "TeamRef":
            self.teamRef = converter(featureValue)
        elif featureName == "HalfScore":
            self.halfScore = featureValue
        elif featureName == "NinetyScore":
            self.ninetyScore = featureValue
        elif featureName == "ExtraScore":
            self.extraScore = featureValue
        elif featureName == "PenaltyScore":
            self.penaltyScore = featureValue
        elif featureName == "MissedPenalty":
            self.missedPenalty = featureValue
        elif featureName == "TeamRef":
            self.teamRef = converter(featureValue)
        elif featureName == "Stat":
            self.teamStats = featureValue
        elif featureName == "Goal":
            self.goals = featureValue
        elif featureName == "Substution":
            self.substitutions = featureValue
        elif featureName == "PlayerLineUp":
            self.playerLineUp = featureValue
        elif featureName == "Booking":
            self.booking = featureValue
        elif featureName == "ShootOutScore":
            self.shootOutScore = featureValue
        else:
            print("feature " + featureName + " could not be found in TeamData")
        return self


class Booking(object):
    def __init__(self):
        self.eventNumber = None
        self.reason = None
        self.period = None
        self.eventID = None
        self.time = None
        self.uID = None
        self.card = None
        self.cardType = None
        self.sec = None
        self.min = None
        self.playerRef = None
        self.timestamp = None

    def setFeature(self, featureName, featureValue):
        if featureName == "EventNumber":
            self.eventNumber = featureValue
        elif featureName == "Reason":
            self.reason = featureValue
        elif featureName == "Period":
            self.period = featureValue
        elif featureName == "EventID":
            self.eventID = featureValue
        elif featureName == "Time":
            self.time = featureValue
        elif featureName == "uID":
            self.uID = featureValue
        elif featureName == "Card":
            self.card = featureValue
        elif featureName == "CardType":
            self.cardType = featureValue
        elif featureName == "Sec":
            self.sec = featureValue
        elif featureName == "Min":
            self.min = featureValue
        elif featureName == "PlayerRef":
            self.playerRef = converter(featureValue)
        elif featureName == "TimeStamp":
            self.timestamp = featureValue

        else:
            print("feature " + featureName + " could not be found in Booking")
        return self


class Schedule(object):
    def __init__(self):
        self.type = None
        self.value = None

    def setFeature(self, featureName, featureValue):
        if featureName == "Type":
            self.type = featureValue
        elif featureName == "Value":
            self.value = featureValue
        else:
            print("feature doesn't exist")
        return self


class TeamScore(object):
    def __init__(self):
        self.halfScore = None
        self.score = None
        self.goal = None
        self.teamRef = None
        self.side = None
        self.ninetyScore = None
        self.extraScore = None
        self.penaltyScore = None

    def setFeature(self, featureName, featureValue):
        if featureName == "HalfScore":
            self.halfScore = featureValue
        elif featureName == "Score":
            self.score = featureValue
        elif featureName == "Goal":
            self.goal = featureValue
        elif featureName == "TeamRef":
            self.teamRef = converter(featureValue)
        elif featureName == "Side":
            self.side = featureValue
        elif featureName == "NinetyScore":
            self.ninetyScore = featureValue
        elif featureName == "ExtraScore":
            self.extraScore = featureValue
        elif featureName == "PenaltyScore":
            self.penaltyScore = featureValue
        else:
            print("feature " + featureName + " could not be found in TeamScore")
        return self


class PreviousMatch(object):
    def __init__(self, matchRef, matchType, venueRef):
        self.matchRef = matchRef
        self.matchType = matchType
        self.venueRef = venueRef


class MatchData(object):
    def __init__(self):
        self.uID = None
        self.stats = None
        self.matchOfficials = None
        self.teamData = None
        self.matchInfo = None
        self.detailID = None
        self.lastModified = None
        self.schedule = None
        self.timingID = None
        self.assistantOfficials = None
        self.shootOut = None
        self.penaltyShot = None
        self.previousMatch = None
        self.VARData = None
        self.schedule = None
        self.teamScore = None
        self.timestampAccuracyID = None

    def setFeature(self, featureName, featureValue):
        if featureName == "detail_id":
            self.detailID = featureValue
        elif featureName == "Schedule":
            self.schedule = featureValue
        elif featureName == "TeamScore":
            self.teamScore = featureValue
        elif featureName == "last_modified":
            self.lastModified = featureValue
        elif featureName == "timestamp_accuracy_id":
            self.timestampAccuracyID = featureValue
        elif featureName == "timing_id":
            self.timingID = featureValue
        elif featureName == "Stat":
            self.stats = featureValue
        elif featureName == "MatchOfficials":
            self.matchOfficials = featureValue
        elif featureName == "TeamData":
            self.teamData = featureValue
        elif featureName == "MatchInfo":
            self.matchInfo = featureValue
        elif featureName == "uID":
            self.uID = converter(featureValue)
        elif featureName == "Schedule":
            self.schedule = featureValue
        elif featureName == "AssistantOfficials":
            self.assistantOfficials = featureValue
        elif featureName == "ShootOut":
            self.shootOut = featureValue
        elif featureName == "PenaltyShot":
            self.penaltyShot = featureValue
        elif featureName == "PreviousMatch":
            self.previousMatch = featureValue
        elif featureName == "VARData":
            self.VARData = featureValue
        else:
            print("feature " + featureName + "is not known in MatchData!")
        return self


class Game(object):
    def __init__(self, id):
        self.id = converter(id)
        self.events = None
        self.awayScore = None
        self.awayTeamID = None
        self.awayTeamName = None
        self.competitionID = None
        self.competitionName = None
        self.seasonID = None
        self.seasonName = None
        self.periodOneStart = None
        self.matchDay = None
        self.homeTeamID = None
        self.homeTeamName = None
        self.homeScore = None
        self.periodSecondStart = None
        self.gameDate = None
        self.periodThirdStart = None
        self.periodFourthStart = None
        self.periodFifthStart = None

    def setFeature(self, featureName, featureValue):
        if featureName == "Event":
            self.events = featureValue
        elif featureName == "away_score":
            self.awayScore = converter(featureValue)
        elif featureName == "away_team_id":
            self.awayTeamID = converter(featureValue)
        elif featureName == "away_team_name":
            self.awayTeamName = featureValue
        elif featureName == "competition_id":
            self.competitionID = converter(featureValue)
        elif featureName == "competition_name":
            self.competitionName = featureValue
        elif featureName == "season_id":
            self.seasonID = converter(featureValue)
        elif featureName == "season_name":
            self.seasonName = featureValue
        elif featureName == "period_1_start":
            self.periodOneStart = featureValue
        elif featureName == "game_date":
            self.gameDate = featureValue
        elif featureName == "matchday":
            self.matchDay = converter(featureValue)
        elif featureName == "home_team_id":
            self.homeTeamID = converter(featureValue)
        elif featureName == "home_team_name":
            self.homeTeamName = featureValue
        elif featureName == "home_score":
            self.homeScore = converter(featureValue)
        elif featureName == "period_2_start":
            self.periodSecondStart = featureValue
        elif featureName == "period_3_start":
            self.periodThirdStart = featureValue
        elif featureName == "period_4_start":
            self.periodFourthStart = featureValue
        elif featureName == "period_5_start":
            self.periodFifthStart = featureValue
        else:
            print("Feature " + featureName + " is unknown!")
        return self


class QEvent(object):
    def __init__(self, id, qualifierID, value=None):
        self.ID = id
        self.qualifierID = qualifierID
        self.value = value

    def setValue(self, value):
        self.value = value


class Event(object):
    def __init__(self, id, eventId):
        self.ID = id
        self.eventID = eventId
        self.qEvents = None
        self.periodID = None
        self.sec = None
        self.timestamp = None
        self.min = None
        self.teamID = None
        self.typeID = None
        self.outcome = None
        self.x = None
        self.y = None
        self.lastModified = None
        self.version = None
        self.playerID = None
        self.assist = None
        self.keypass = None

    def setFeature(self, feature, value):
        if feature == "QEvent":
            self.qEvents = value
        elif feature == "period_id":
            self.periodID = value
        elif feature == "type_id":
            self.typeID = value
        elif feature == "min":
            self.min = value
        elif feature == "sec":
            self.sec = value
        elif feature == "player_id":
            self.playerID = value
        elif feature == "team_id":
            self.teamID = value
        elif feature == "outcome":
            self.outcome = value
        elif feature == "x":
            self.x = value
        elif feature == "y":
            self.y = value
        elif feature == "TimeStamp":
            self.timestamp = value
        elif feature == "last_modified":
            self.lastModified = value
        elif feature == "version":
            self.version = value
        elif feature == "assist":
            self.assist = value
        elif feature == "keypass":
            self.keypass = value
        elif feature == "id":
            self.ID = value
        elif feature == "event_id":
            self.eventID = value
        else:
            print("Feature, " + feature + ", is unknown!")
        return self


# The following class might be used later
class FeedDocument(object):
    def __init__(self):
        self.matchData = None
        self.type = None
        self.competitionCode = None
        self.competitionID = None
        self.competitionName = None
        self.gameSystemID = None
        self.seasonID = None
        self.seasonName = None
        self.timeStamp = None
        self.team = None
        self.timingTypes = None

    def setFeature(self, featureName, featureValue):
        if featureName == "MatchData":
            self.matchData = featureValue
        elif featureName == "Type":
            self.type = featureValue
        elif featureName == "competition_code":
            self.competitionCode = featureValue
        elif featureName == "competition_id":
            self.competitionID = featureValue
        elif featureName == "competition_name":
            self.competitionName = featureValue
        elif featureName == "gameSystemID":
            self.gameSystemID = featureValue
        elif featureName == "season_id":
            self.seasonID = featureValue
        elif featureName == "TimeStamp":
            self.timeStamp = featureValue
        elif featureName == "season_name":
            self.seasonName = featureValue
        elif featureName == "team":
            self.team = featureValue
        elif featureName == "timingTypes":
            self.timingTypes = featureValue
        else:
            print("Feature," + featureName + ", is unknown!")
        return self


class TimingTypes(object):
    def __init__(self):
        self.detailTypes = None
        self.tsAccuracyTypes = None
        self.timingTypes = None

    def setDetailTypes(self, ttype):
        self.detailTypes = ttype

    def setTSAccuracyTypes(self, ttype):
        self.tsAccuracyTypes = ttype

    def setTimingTypes(self, ttype):
        self.timingTypes = ttype


class TimingType(object):
    def __init__(self, name, timing_id):
        self.name = name
        self.timingID = timing_id


class DetailType(object):
    def __init__(self, id, name):
        self.detailID = id
        self.name = name


class TimestampAccuracyType(object):
    def __init__(self, id, name):
        self.timestampAccuracyID = id
        self.name = name


class Venue(object):
    def __init__(self):
        self.country = None
        self.uID = None
        self.name = None

    def setFeature(self, featureName, featureValue):
        if featureName == "country" or featureName == "Country":
            self.country = featureValue
        elif featureName == "uID":
            self.uID = featureValue
        elif featureName == "Name":
            self.name = featureValue
        else:
            print("Feature is unknown! FeedDocument", featureName, featureValue)
        return self


###### Feeds


class Feed(object):
    def __init__(self, ts, feed):
        self.timestamp = ts
        self.feedName = feed


class Feed1(Feed):
    def __init__(
            self, mdata, type, c_code, c_id, c_name, g_s_id, s_id, s_name, team, ttypes
    ):
        self.feedName = "feed1"
        self.matchData = mdata
        self.type = type
        self.competitionCode = c_code
        self.competitionID = c_id
        self.competitionName = c_name
        self.gameSystemID = g_s_id
        self.seasonID = s_id
        self.seasonName = s_name
        self.timestamp = None
        self.teams = team
        self.timingTypes = ttypes

    def connectToDB(self):
        Connector.main_conn.connect()

    def storeInDB(self):
        self.connectToDB()

        mdataList = []
        for mdata in self.matchData:
            teamDataList = []
            res = 0
            for teamd in mdata.teamData:
                goals = []
                if isinstance(teamd.goals, list):
                    for goal in teamd.goals:
                        tgoal = DBHelper.F1_Goal(
                            period=goal.period, playerRef=goal.playerRef, type=goal.type
                        )
                        tgoal.save()
                        goals.append(tgoal)
                elif teamd.goals is not None:
                    tgoal = DBHelper.F1_Goal(
                        period=teamd.goals.period,
                        playerRef=teamd.goals.playerRef,
                        type=teamd.goals.type,
                    )
                    tgoal.save()
                    goals.append(tgoal)

                teamData = DBHelper.F1_TeamData(
                    halfScore=teamd.halfScore,
                    score=teamd.score,
                    goal=goals,
                    teamRef=converter(teamd.teamRef),
                    side=teamd.side,
                    ninetyScore=teamd.ninetyScore,
                    extraScore=teamd.extraScore,
                    penaltyScore=teamd.penaltyScore,
                )
                teamData.save()
                teamDataList.append(teamData)

            mofficialList = []
            if mdata.matchOfficials != None:
                if isinstance(mdata.matchOfficials, list):
                    for mOfficial in mdata.matchOfficials:
                        official = DBHelper.F1_MatchOfficial(
                            first=mOfficial.first,
                            last=mOfficial.last,
                            type=mOfficial.type,
                            uID=mOfficial.uID,
                        )
                        official.save()
                        mofficialList.append(official)
                elif mdata.matchOfficials is not None:
                    official = DBHelper.F1_MatchOfficial(
                        first=mdata.matchOfficials.first,
                        last=mdata.matchOfficials.last,
                        type=mdata.matchOfficials.type,
                        uID=mdata.matchOfficials.uID,
                    )
                    official.save()
                    mofficialList.append(official)

            # schedule = DBHelper.Schedule(
            #     type = mdata.schedule.type,
            #     value = mdata.schedule.value
            # )
            matchInfo = mdata.matchInfo
            if not isinstance(matchInfo.date, str):
                continue
            minfo = DBHelper.F1_MatchInfo(
                date=matchInfo.date,
                TZ=matchInfo.TZ,
                period=matchInfo.period,
                matchWinner=matchInfo.matchWinner,
                matchType=matchInfo.matchType,
                venueID=matchInfo.venueID,
                matchDay=matchInfo.matchDay,
                leg=matchInfo.leg,
                firstLegID=matchInfo.firstLegID,
                legWinner=matchInfo.legWinner,
                nextMatch=matchInfo.nextMatch,
                nextMatchLoser=matchInfo.nextMatchLoser,
                roundNumber=matchInfo.roundNumber,
                roundType=matchInfo.roundType,
                groupName=matchInfo.groupName,
                gameWinner=matchInfo.gameWinner,
                gameWinnerType=matchInfo.gameWinnerType,
            )
            minfo.save()

            matchData = DBHelper.F1_MatchData(
                matchInfo=minfo,
                uID=mdata.uID,
                detailID=mdata.detailID,
                # timestampAccuracyID = mdata.timestamp_accuracy_id,
                lastModified=mdata.lastModified,
                # schedule = schedule,
                teamData=teamDataList,
                matchOfficials=mofficialList,
                timingID=mdata.timingID,
            )
            matchData.save()
            mdataList.append(matchData)

        teamList = []
        for team in self.teams:
            tdata = DBHelper.F1_Team(name=team.name, uID=team.uID)
            tdata.save()
            teamList.append(tdata)
        # add here timing types

        dtypeList = []
        tsAccList = []
        tTypes = []

        for dtype in self.timingTypes.detailTypes:
            dt = DBHelper.F1_DetailType(detailID=dtype.detailID, name=dtype.name)
            dt.save()
            dtypeList.append(dt)

        for tsAccType in self.timingTypes.tsAccuracyTypes:
            tst = DBHelper.F1_TimestampAccuracyType(
                name=tsAccType.name, timestampAccuracyID=tsAccType.timestampAccuracyID
            )
            tst.save()
            tsAccList.append(tst)

        for ttype in self.timingTypes.timingTypes:
            tt = DBHelper.F1_TimingType(name=ttype.name, timingID=ttype.timingID)
            tt.save()
            tTypes.append(tt)

        timingTypesObject = DBHelper.F1_TimingTypes(
            detailTypes=dtypeList, timingTypes=tTypes, timestampAccuracyTypes=tsAccList
        )
        timingTypesObject.save()

        feed = DBHelper.F1_Root(
            type=self.type,
            competitionCode=self.competitionCode,
            competitionID=self.competitionID,
            competitionName=self.competitionName,
            gameSystemID=self.gameSystemID,
            seasonID=self.seasonID,
            seasonName=self.seasonName,
            timestamp=self.timestamp,
            teams=teamList,
            matchData=mdataList,
            timingTypes=timingTypesObject,
        )
        feed.save()
        # self.closeDBConnection()


class Feed9(Feed):
    def __init__(
            self, ts, mdata, venue, type, teams, uid, competition, competitionId, seasonId
    ):
        self.feedName = "feed9"
        self.timestamp = ts
        self.matchData = mdata
        self.venue = venue
        self.type = type
        self.teams = teams
        self.detailID = None
        self.uID = uid
        self.competition = competition
        self.competitionId = competitionId
        self.seasonID = seasonId

    def setFeature(self, featureName, featureValue):
        if featureName == "detail_id":
            self.detailID = featureValue

    def connectToDB(self):
        print("connection == being established!")
        Connector.main_conn.connect()

    def closeDBConnection(self):
        print("connection is being closed!")
        Connector.main_conn.disconnect()

    def storeInDB(self):
        # self.connectToDB()
        assistantOfficialList = []
        matchOfficialList = []
        mData = self.matchData

        # asisstant
        if hasattr(mData, "assistantOfficials"):
            for assistant in mData.assistantOfficials:
                assistantObj = DBHelper.F9_AssistantOfficial(
                    first=assistant.first,
                    last=assistant.last,
                    type=assistant.type,
                    uID=assistant.uID,
                )
                assistantObj.save()
                assistantOfficialList.append(assistantObj)

        # match official
        if hasattr(mData, "matchOfficials"):

            if isinstance(mData.matchOfficials, list):
                for mofficial in mData.matchOfficials:
                    mofficialObj = DBHelper.F9_MatchOfficial(
                        first=mofficial.first,
                        last=mofficial.last,
                        officialData=mofficial.officialData,
                        officialName=mofficial.officialName,
                        uID=mofficial.uID,
                    )
                    mofficialObj.save()
                    matchOfficialList.append(mofficialObj)
            elif mData.matchOfficials is not None:
                mofficialObj = DBHelper.F9_MatchOfficial(
                    first=mData.matchOfficials.first,
                    last=mData.matchOfficials.last,
                    officialData=mData.matchOfficials.officialData,
                    officialName=mData.matchOfficials.officialName,
                    uID=mData.matchOfficials.uID,
                )
                mofficialObj.save()
                matchOfficialList.append(mofficialObj)

        # mstate
        mstatList = []
        for mstat in mData.stats:
            mstatObj = DBHelper.F9_Stat(type=mstat.type, value=mstat.value)
            mstatObj.save()
            mstatList.append(mstatObj)

        shootOut = None
        if hasattr(mData, "shootOut"):
            if mData.shootOut is not None:
                shootOutObj = DBHelper.F9_ShootOut(
                    firstPenalty=mData.shootOut.firstPenalty
                )
                shootOutObj.save()
                shootOut = shootOutObj

        penaltyShot = None
        if hasattr(mData, "penaltyShot"):
            if mData.penaltyShot:
                penaltyShotObj = DBHelper.F9_PenaltyShot(
                    outcome=mData.penaltyShot.outcome,
                    eventNumber=mData.penaltyShot.eventNumber,
                    playerRef=mData.penaltyShot.playerRef,
                    uID=mData.penaltyShot.uID,
                )
                penaltyShotObj.save()
                penaltyShot = penaltyShotObj

        ### Teams
        teams = []

        for t in self.teams:
            tPlayers = []

            for p in t.players:
                player = DBHelper.F9_Player(
                    first=p.first,
                    known=p.known,
                    last=p.last,
                    uID=p.uID,
                    captain=p.captain,
                    position=p.position,
                )
                player.save()
                tPlayers.append(player)

            # team officials
            tOfficials = []
            if isinstance(t.teamOfficials, list):
                for tt in t.teamOfficials:
                    tOfficial = DBHelper.F9_TeamOfficial(
                        first=tt.first,
                        last=tt.last,  # known=tt.known,
                        uID=tt.uID,
                        type=tt.type,
                    )
                    tOfficial.save()
                    tOfficials.append(tOfficial)
            elif t.teamOfficials is not None:
                tOfficial = DBHelper.F9_TeamOfficial(
                    first=tt.first,
                    last=tt.last,  # known=tt.known,
                    uID=tt.uID,
                    type=tt.type,
                )
                tOfficial.save()
                tOfficials.append(tOfficial)
            # kits
            kits = []
            if isinstance(t.kits, list):
                for t in t.kits:
                    kit = DBHelper.F9_Kit(
                        id=t.kit.id,
                        colour1=t.kit.colour1,
                        colour2=t.kit.colour2,
                        type=t.kit.type,
                    )
                    kit.save()
                    kits.append(kit)
            elif t.kits is not None:
                kit = DBHelper.F9_Kit(
                    id=t.kit.id,
                    colour1=t.kit.colour1,
                    colour2=t.kit.colour2,
                    type=t.kit.type,
                )
                kit.save()
                kits.append(kit)


            team = DBHelper.F9_Team(
                name=t.name,
                uID=t.uID,
                players=tPlayers,
                country=t.country,
                teamOfficials=tOfficials,
                kits=kits,
            )
            team.save()
            teams.append(team)

        # minfo
        # if mData.matchInfo.result == NaN
        # check whether the result == available!

        result = DBHelper.F9_Result(
            type=mData.matchInfo.result.type,
            winner=mData.matchInfo.result.winner,
            minutes=mData.matchInfo.result.minutes,
            reason=mData.matchInfo.result.reason,
        )
        result.save()

        minfoObj = DBHelper.F9_MatchInfo(
            date=str(mData.matchInfo.date),
            TZ=mData.matchInfo.TZ,
            period=mData.matchInfo.period,
            result=result,
            varReason=mData.matchInfo.varReason,
            timestamp=mData.matchInfo.timestamp,
            matchType=mData.matchInfo.matchType,
            playerRef=mData.matchInfo.playerRef,
            teamRef=mData.matchInfo.teamRef,
            status=mData.matchInfo.status,
            matchDay=mData.matchInfo.matchDay,
        )
        minfoObj.save()
        # previous match
        previousMatch = None
        if hasattr(mData.previousMatch, "matchRef"):
            previousMatchObj = DBHelper.F9_PreviousMatch(
                matchRef=mData.previousMatch.matchRef,
                matchType=mData.previousMatch.matchType,
                venueRef=mData.previousMatch.venueRef,
            )
            previousMatchObj.save()
            previousMatchObj = previousMatchObj
        # var data
        if mData.VARData is not None:
            varDataObj = DBHelper.F9_VARData(
                eventID=mData.VARData.eventID,
                eventNumber=mData.VARData.eventNumber,
                period=mData.VARData.period,
                min=mData.VARData.min,
                sec=mData.VARData.sec,
                reason=mData.VARData.reason,
                decision=mData.VARData.decision,
                outcome=mData.VARData.outcome,
                teamRef=mData.VARData.teamRef,
                playerRef=mData.VARData.playerRef,
            )
            varDataObj.save()
        else:
            varDataObj = DBHelper.F9_VARData(
                eventID=None,
                eventNumber=None,
                period=None,
                min=None,
                sec=None,
                reason=None,
                decision=None,
                outcome=None,
                teamRef=None,
                playerRef=None,
            )
            varDataObj.save()
        teamDataList = []
        for tData in mData.teamData:

            if hasattr(tData, "missedPenalty"):
                missedPenaltyObj = DBHelper.F9_MissedPenalty(
                    period=None, playerRef=None, type=None
                )
                missedPenaltyObj.save()
            teamStatList = []
            for stat in tData.teamStats:
                tStat = DBHelper.F9_TeamStat(
                    value=stat.value, type=stat.type, fh=stat.FH, sh=stat.SH
                )
                tStat.save()
                teamStatList.append(tStat)

            substitions = []
            # if hasattr(tData, "substitutions"):
            if isinstance(tData.substitutions, list):
                for subs in tData.substitutions:
                    tSub = DBHelper.F9_Substitution(
                        eventID=subs.eventID,
                        period=subs.period,
                        time=subs.time,
                        eventNumber=subs.eventNumber,
                        sec=subs.sec,
                        uID=subs.uID,
                        min=subs.min,
                        suboff=subs.suboff,
                        subon=subs.subon,
                        reason=subs.reason,
                        substitutePosition=subs.substitutePosition,
                        retired=subs.retired,
                        timestamp=subs.timestamp,
                    )
                    tSub.save()
                    substitions.append(tSub)

            # match Player List
            matchPlayerList = []

            for mp in tData.playerLineUp:
                mpStatList = []
                if isinstance(mp.stats, list):
                    for mstat in mp.stats:
                        mstatObj = DBHelper.F9_Stat(type=mstat.type, value=mstat.value)
                        mstatObj.save()
                        mpStatList.append(mstatObj)
                elif mp.stats is not None:
                    mstatObj = DBHelper.F9_Stat(type=mstat.type, value=mstat.value)
                    mstatObj.save()
                    mpStatList = mstatObj

                mPlayer = DBHelper.F9_MatchPlayer(
                    stats=mpStatList,
                    captain=mp.captain,
                    playerRef=mp.playerRef,
                    position=mp.position,
                    shirtNumber=mp.shirtNumber,
                    status=mp.status,
                    subPosition=mp.subPosition,
                )
                mPlayer.save()
                matchPlayerList.append(mPlayer)

            # goal
            assistObj = None
            secondAssistObj = None
            goalObj = None
            if hasattr(tData, "goal"):
                assistObj = DBHelper.F9_Assist(playerRef=tData.goal.assist.playerRef)
                assistObj.save()
                secondAssistObj = DBHelper.F9_SecondAssist(
                    playerRef=tData.goal.secondAssist.playerRef
                )
                secondAssistObj.save()

                goalObj = DBHelper.F9_Goal(
                    eventID=tData.goal.eventID,
                    period=tData.goal.period,
                    time=tData.goal.time,
                    playerRef=tData.goal.playerRef,
                    eventNumber=tData.goal.eventNumber,
                    sec=tData.goal.sec,
                    uID=tData.goal.uID,
                    min=tData.goal.min,
                    type=tData.goal.type,
                    timestamp=tData.goal.timestamp,
                    assist=assistObj,
                    secondAssist=secondAssistObj,
                    soloRun=tData.goal.soloRun,
                    VARReviewed=tData.goal.VARReviewed,
                    originalDecision=tData.goal.originalDecision,
                )
                goalObj.save()
            bookings = []
            if hasattr(tData, "booking"):
                if isinstance(tData.booking, list):
                    for booking in tData.booking:
                        bookingObj = DBHelper.F9_Booking(
                            eventNumber=booking.eventNumber,
                            eventID=booking.eventID,
                            period=booking.period,
                            time=booking.time,
                            uID=booking.uID,
                            card=booking.card,
                            cardType=booking.cardType,
                            sec=booking.sec,
                            min=booking.min,
                            playerRef=booking.playerRef,
                            timestamp=booking.timestamp,
                        )
                        bookingObj.save()
                        bookings.append(bookingObj)
                elif tData.booking is not None:
                    bookingObj = DBHelper.F9_Booking(
                        eventNumber=tData.booking.eventNumber,
                        eventID=tData.booking.eventID,
                        period=tData.booking.period,
                        time=tData.booking.time,
                        uID=tData.booking.uID,
                        card=tData.booking.card,
                        cardType=tData.booking.cardType,
                        sec=booking.sec,
                        min=booking.min,
                        playerRef=booking.playerRef,
                        timestamp=booking.timestamp,
                    )
                    bookingObj.save()
                    bookings = bookingObj

            teamDataObj = DBHelper.F9_TeamData(
                teamStats=teamStatList,
                missedPenalty=missedPenaltyObj,
                side=tData.side,
                score=tData.score,
                substitutions=substitions,
                playerLineUp=matchPlayerList,
                goal=goalObj,
                teamRef=tData.teamRef,
                shootOutScore=tData.shootOutScore,
                booking=bookings,
            )
            teamDataObj.save()
            teamDataList.append(teamDataObj)
        ###

        mDataObj = DBHelper.F9_MatchData(
            assistantOfficials=assistantOfficialList,
            matchOfficials=matchOfficialList,
            matchStats=mstatList,
            shootOut=shootOut,
            penaltyShot=penaltyShot,
            teamData=teamDataList,
            matchInfo=minfoObj,
            previousMatch=previousMatch,
            VARData=varDataObj,
        )
        mDataObj.save()
        ### venue
        venueObj = DBHelper.F9_Venue(
            country=self.venue.country, name=self.venue.name, uID=self.venue.uID
        )
        venueObj.save()
        ## competition
        compStats = []
        for stat in self.competition.stats:
            statobj = DBHelper.F9_Stat(value=stat.value, type=stat.type)
            statobj.save()
            compStats.append(statobj)

        competitionObj = DBHelper.F9_Competition(
            country=self.competition.country,
            name=self.competition.name,
            pool=self.competition.pool,
            stats=compStats,
            roundNumber=self.competition.roundNumber,
            uID=self.competition.uID,
        )
        competitionObj.save()

        feed = DBHelper.F9_Root(
            type=self.type,
            venue=venueObj,
            detailID=self.detailID,
            uID=self.uID,
            competition=competitionObj,
            timestamp=self.timestamp,
            matchData=mDataObj,
            teams=teams,
            competitionID=self.competitionId,
            seasonID=self.seasonID,
        )
        feed.save()
        # self.closeDBConnection()


class Feed24(Feed):
    def __init__(self, c_id, s_id, game):
        self.feedName = "feed24"
        self.timestamp = None
        self.competitionID = c_id
        self.seasonID = s_id
        self.game = game
        self.gameID = game.id

    def connectToDB(self):
        Connector.main_conn.connect()

    def closeDBConnection(self):
        Connector.main_conn.disconnect()

    def storeInDB(self):
        # self.connectToDB()
        eventList = []
        for event in self.game.events:

            if hasattr(event, "qEvents"):
                qList = []
                if isinstance(event.qEvents, list):
                    for q in event.qEvents:
                        qObj = DBHelper.F24_QEvent(
                            ID=q.ID, qualifierID=q.qualifierID, value=q.value
                        )
                        qObj.save()
                        qList.append(qObj)
                elif event.qEvents is not None:
                    qObj = DBHelper.F24_QEvent(
                        ID=q.ID, qualifierID=q.qualifierID, value=q.value
                    )
                    qObj.save()
                    qList.append(qObj)

                eventObj = DBHelper.F24_Event(
                    qEvents=qList,
                    ID=event.ID,
                    periodID=event.periodID,
                    sec=event.sec,
                    # timestamp = event.timestamp,
                    min=event.min,
                    eventID=event.eventID,
                    teamID=event.teamID,
                    typeID=event.typeID,
                    outcome=event.outcome,
                    x=event.x,
                    y=event.y,
                    lastModified=event.lastModified,
                    version=event.version,
                    playerID=event.playerID,
                    assist=event.assist,
                    keypass=event.keypass,
                )
                eventObj.save()
                eventList.append(eventObj)

        gameObj = DBHelper.F24_Game(
            events=eventList,
            ID=converter(self.game.id),
            awayScore=self.game.awayScore,
            awayTeamID=converter(self.game.awayTeamID),
            awayTeamName=self.game.awayTeamName,
            competitionID=self.game.competitionID,
            competitionName=self.game.competitionName,
            seasonID=self.game.seasonID,
            seasonName=self.game.seasonName,
            homeTeamID=converter(self.game.homeTeamID),
            homeTeamName=self.game.homeTeamName,
            homeScore=self.game.homeScore,
            matchDay=self.game.matchDay,
            periodOneStart=self.game.periodOneStart,
            periodSecondStart=self.game.periodSecondStart,
            periodThirdStart=self.game.periodThirdStart,
            periodFourthStart=self.game.periodFourthStart,
            periodFifthStart=self.game.periodFifthStart,
        )
        gameObj.save()
        feed = DBHelper.F24_Root(
            timestamp=self.timestamp,
            game=gameObj,
            competitionID=self.competitionID,
            seasonID=self.seasonID,
            gameID=converter(self.gameID),
        )
        feed.save()
        # self.closeDBConnection()


class Feed40(Feed):
    def __init__(
            self, teams, pchanges, type, c_id, c_name, c_code, s_id, s_name, ts=None
    ):
        self.feedName = "feed40"
        self.timestamp = ts
        # self.name = name
        self.teams = teams
        self.playerChanges = pchanges
        self.type = type
        self.competitionID = c_id
        self.competitionName = c_name
        self.competitionCode = c_code
        self.seasonID = s_id
        self.seasonName = s_name

    def connectToDB(self):
        Connector.main_conn.connect()

    def closeDBConnection(self):
        Connector.main_conn.disconnect()

    def storeInDB(self):
        # self.connectToDB() # For saving the object in the databasem, comment out this line

        ### Teams
        teamList = []

        # Teams
        for t in self.teams:

            # team stadium
            stadiumObj = DBHelper.F40_Stadium(
                name=t.stadium.name, capacity=t.stadium.capacity, uID=t.stadium.uID
            )
            stadiumObj.save()

            # team players
            tPlayerList = []
            for p in t.players:
                stats = []
                for stat in p.stats:
                    statObj = DBHelper.F40_Stat(type=stat.type, value=stat.value)
                    statObj.save()
                    stats.append(statObj)
                #
                playerObj = DBHelper.F40_Player(
                    name=p.name,
                    uID=p.uID,
                    position=p.position,
                    stats=stats,
                    playerLoan=p.playerLoan,  # this might be null!
                    # playerData = playerDataObj
                )
                playerObj.save()
                tPlayerList.append(playerObj)

            ## team officials
            teamOfficialList = []
            for tofficial in t.teamOfficials:
                personalInfoObj = DBHelper.F40_PersonalInfo(
                    first=tofficial.first,
                    last=tofficial.last,
                    uID=tofficial.uID,
                    leaveDate=tofficial.leaveDate,
                    joinDate=tofficial.joinDate,
                    birthDate=tofficial.birthDate,
                )

                personalInfoObj.save()
                tOfficialObj = DBHelper.F40_TeamOfficial(
                    personalInfo=personalInfoObj,
                    uID=tofficial.uID,
                    type=tofficial.type,
                    country=tofficial.country,
                )
                tOfficialObj.save()
                teamOfficialList.append(tOfficialObj)

            # team kits

            kitList = []

            if isinstance(t.kits, list):
                for kit in t.kits:
                    kitObj = DBHelper.F40_Kit(
                        kitID=kit.id,
                        colour1=kit.colour1,
                        colour2=kit.colour2,
                        type=kit.type,
                    )
                    kitObj.save()
                    kitList.append(kitObj)
            elif t.kits is not None:
                kit = DBHelper.F40_Kit(
                    id=t.kits.id,
                    colour1=t.kits.colour1,
                    colour2=t.kits.colour2,
                    type=t.type,
                )
                kit.save()
                kitList.append(kit)

            team = DBHelper.F40_Team(
                name=t.name,
                uID=t.uID,
                country=t.country,
                countryISO=t.countryISO,
                countryID=t.countryID,
                regionName=t.regionName,
                regionID=t.regionID,
                stadium=stadiumObj,
                officialClubName=t.officialClubName,
                shortClubName=t.shortClubName,
                kits=kitList,
                teamOfficials=teamOfficialList,
                players=tPlayerList,
                founded=t.founded,
                fifaRank=t.fifaRank,
                symid=t.symid,
                city=t.city,
                postalCode=t.postalCode,
                street=t.street,
                webAddress=t.webAddress,
            )
            team.save()
            teamList.append(team)

        pChangesList = []

        # Player Changes
        for team in self.playerChanges:

            # player object
            players = []
            for p in team.players:
                stats = []
                for stat in p.stats:
                    statObj = DBHelper.F40_Stat(type=stat.type, value=stat.value)
                    statObj.save()
                    stats.append(statObj)
                #
                playerObj = DBHelper.F40_Player(
                    name=p.name,
                    uID=p.uID,
                    position=p.position,
                    stats=stats,
                    # playerData = playerDataObj
                )
                playerObj.save()
                players.append(playerObj)

            ### team official

            teamOfficialList = []

            for tofficial in team.teamOfficials:
                personalInfoObj = DBHelper.F40_PersonalInfo(
                    first=tofficial.first,
                    last=tofficial.last,
                    uID=tofficial.uID,
                    leaveDate=tofficial.leaveDate,
                    joinDate=tofficial.joinDate,
                    birthDate=tofficial.birthDate,
                )
                personalInfoObj.save()
                tOfficialObj = DBHelper.F40_TeamOfficial(
                    personalInfo=personalInfoObj,
                    uID=tofficial.uID,
                    type=tofficial.type,
                    country=tofficial.country,
                )
                tOfficialObj.save()
                teamOfficialList.append(tOfficialObj)

            # team object
            teamObj = DBHelper.F40_Team(
                uID=team.uID,
                name=team.name,
                players=players,
                teamOfficials=teamOfficialList,
            )

            teamObj.save()
            pChangesList.append(teamObj)

        feed = DBHelper.F40_Root(
            timestamp=self.timestamp,
            team=teamList,
            playerChanges=pChangesList,
            type=self.type,
            competitionID=self.competitionID,
            competitionName=self.competitionName,
            competitionCode=self.competitionCode,
            seasonID=self.seasonID,
            seasonName=self.seasonName,
        )
        feed.save()
        # self.closeDBConnection()


class AerialEvent:
    def __init__(self):
        self.totalDuels = 0
        self.won = 0
        self.lost = 0
        self.wonPercentage = 0
        self.attackingHalf = 0
        self.wonPercentageInAttackingHalf = 0
        self.defendingHalf = 0
        self.wonPercentageInDefendingHalf = 0
        self.attackingThird = 0
        self.wonPercentageInAttackingThird = 0
        self.middleThird = 0
        self.wonPercentageInMiddleThird = 0
        self.defendingThird = 0
        self.wonPercentageInDefendingThird = 0


class AssistEvents:
    def __init__(self):
        self.total_assists = 0
        self.intentional_assists = 0
        self.assists_from_open_play = 0
        self.open_play_assist_rate = 0
        self.assists_from_set_play = 0
        self.assists_from_free_kick = 0
        self.assists_from_corners = 0
        self.assists_from_throw_in = 0
        self.assists_from_goal_kick = 0
        self.assist_for_first_touch_goal = 0
        self.assist_and_key_passes = 0
        self.key_passes = 0
        self.key_pass_free_kick = 0
        self.key_pass_corner = 0
        self.key_pass_throw_in = 0
        self.key_pass_goal_kick = 0
        self.key_passes_after_dribble = 0


class BallControlEvents:
    def __init__(self):
        self.total_dispossessed = 0
        self.errors = 0
        self.error_led_to_goal = 0
        self.error_led_to_shot = 0
        self.caught_offside = 0
        self.ball_touch = 0
        self.ball_hit_the_player = 0
        self.unsuccessful_control = 0


class CardEvents:
    def __init__(self):
        self.total_cards = 0
        self.yellow_card = 0
        self.second_yellow_card = 0
        self.red_card = 0
        self.card_rescinded = 0


class FoulEvents:
    def __init__(self):
        # simple foul event counters
        self.fouls_total = 0
        self.fouls_won = 0
        self.fouls_conceded = 0
        self.handball_conceded = 0
        self.penalty_conceded = 0
        self.penalty_won = 0
        self.fouls_won_in_defending_third = 0
        self.fouls_won_in_middle_third = 0
        self.fouls_won_in_attacking_third = 0
        self.fouls_committed_in_defending_third = 0
        self.fouls_committed_in_middle_third = 0
        self.fouls_committed_in_attacking_third = 0


class DuelEvents:
    def __init__(self):
        # duel counters
        self.total_duels = 0
        self.successful_duels = 0
        self.unsuccessful_duels = 0
        self.total_ground_duels = 0
        self.successful_ground_duels = 0
        self.unsuccessful_ground_duels = 0
        self.defensive_duels = 0
        self.offensive_duels = 0

        # duel regions
        self.duels_in_attacking_third = 0
        self.duels_in_middle_third = 0
        self.duels_in_defending_third = 0

        # successful duel regions
        self.successful_duels_attacking_third = 0
        self.successful_duels_middle_third = 0
        self.successful_duels_defensive_third = 0

        # unsuccessful duel regions
        self.unsuccessful_duels_attacking_third = 0
        self.unsuccessful_duels_middle_third = 0
        self.unsuccessful_duels_defensive_third = 0

        # aerial duel success rate
        self.duel_success_rate = 0
        self.duel_success_attacking_third = 0
        self.duel_success_middle_third = 0
        self.duel_success_defending_third = 0


class ShotandGoalEvents:
    def __init__(self):
        # goal counters
        self.goals = 0
        self.goals_inside_the_box = 0
        self.goals_outside_the_box = 0
        self.left_footed_goals = 0
        self.right_footed_goals = 0
        self.non_penalty_goals = 0
        self.goals_from_penalties = 0
        self.goals_from_set_play = 0
        self.goals_from_set_piece_cross = 0
        self.goals_from_set_piece_throw_in = 0
        self.goals_from_open_play = 0
        self.goals_from_volleys = 0
        self.goals_from_corners = 0
        self.goals_from_fast_break = 0
        self.goals_from_regular_play = 0
        self.goals_deflected = 0
        self.goals_from_direct_free_kicks = 0
        self.headed_goals = 0
        self.goals_with_other_part_of_body = 0
        self.own_goal = 0
        self.minutes_per_goal = 0
        self.goals_unassisted = 0

        # goal after dribble
        self.dribble_event_id = 0
        self.dribble_check = 0
        self.event_id = 0
        self.shots_after_dribble = 0

        # total shots
        self.total_shots = 0
        self.total_shots_with_blocks = 0
        self.penalty_shots_taken = 0
        self.left_footed_shots = 0
        self.right_footed_shots = 0
        self.shots_inside_box = 0
        self.shots_outside_box = 0
        self.total_headed_shots = 0
        self.shots_with_first_touch = 0
        self.total_big_chances = 0
        self.total_direct_free_kicks = 0
        self.shot_cleared_off_line = 0
        self.shots_deflected = 0
        self.shots_from_set_play = 0
        self.shots_from_fast_break = 0
        self.shots_unassisted = 0
        self.shots_cleared_off_the_line_inside_box = 0
        self.shots_cleared_off_the_line_outside_box = 0

        # blocked shots
        self.blocked_shot = 0
        self.blocked_shot_left = 0
        self.blocked_shot_right = 0
        self.shots_blocked_inside_box = 0
        self.shots_blocked_outside_box = 0
        self.headed_shots_blocked = 0
        self.blocked_shots_with_other_part_of_body = 0
        self.shots_blocked_from_big_chances = 0
        self.blocked_direct_free_kicks = 0
        self.shots_blocked_from_set_play = 0

        # shots off target
        self.shots_off_target = 0
        self.shots_off_target_inside_box = 0
        self.shots_off_target_outside_box = 0
        self.shots_off_target_from_set_piece_cross = 0
        self.shots_off_target_from_set_play = 0
        self.shots_off_target_from_set_piece_throw_in = 0
        self.shots_off_target_from_corners = 0
        self.shots_off_target_from_regular_play = 0
        self.shots_off_target_from_fast_break = 0
        self.shots_off_target_from_open_play = 0
        self.shots_off_target_from_penalties = 0
        self.headed_shots_off_target = 0
        self.left_footed_shots_off_target = 0
        self.right_footed_shots_off_target = 0
        self.shots_hit_woodwork = 0
        self.shots_hit_the_post_from_big_chances = 0
        self.shots_off_target_from_big_chances = 0
        self.direct_free_kicks_off_target = 0

        # shots on target
        self.shots_on_target = 0
        self.headed_shots_on_target = 0
        self.shots_on_target_from_set_piece_cross = 0
        self.shots_on_target_from_set_play = 0
        self.shots_on_target_from_set_piece_throw_in = 0
        self.shots_on_target_from_corners = 0
        self.shots_on_target_from_regular_play = 0
        self.shots_on_target_from_fast_break = 0
        self.shots_on_target_from_open_play = 0
        self.shots_on_target_from_penalties = 0
        self.shots_on_target_inside_box = 0
        self.shots_on_target_outside_box = 0
        self.left_footed_shots_on_target = 0
        self.right_footed_shots_on_target = 0
        self.penalty_shots_saved = 0
        self.shots_on_target_from_direct_free_kicks = 0

        # big chances
        self.goals_from_big_chances = 0
        self.shots_on_target_from_big_chances = 0
        self.chance_missed = 0

        # goal percentages
        self.headed_goals_rate = 0
        self.open_play_goals_rate = 0
        self.headed_shots_rate = 0
        self.inside_the_box_shots_rate = 0
        self.outside_the_box_shots_rate = 0
        self.left_foot_shots_rate = 0
        self.right_foot_shots_rate = 0
        self.shots_on_target_rate = 0
        self.blocked_shots_rate = 0
        self.shooting_percentage = 0
        self.no_block_shooting_percentage = 0
        self.big_chance_conversion_rate = 0
        self.free_kick_on_target_rate = 0
        self.unassisted_goals_shots_rate = 0


class TakeOnEvents:
    def __init__(self):
        # simple card event counters
        self.total_take_ons = 0
        self.take_ons_successful = 0
        self.take_ons_unsuccessful = 0
        self.take_on_success_rate = 0
        self.take_on_overrun = 0
        self.take_on_in_attacking_third = 0
        self.take_on_in_attacking_third_uns = 0
        self.take_on_success_rate_attacking_third = 0
        self.take_ons_in_box = 0
        self.successful_take_ons_in_box = 0
        self.tackled = 0


class TouchEvents:
    def __init__(self):
        # simple ball control event counters
        self.total_touches = 0
        self.total_touches_in_attacking_third = 0
        self.total_touches_in_middle_third = 0
        self.total_touches_in_defensive_third = 0
        self.total_touches_in_box = 0
        self.turnover = 0
        self.turnover_percentage = 0
        self.take_on_overrun = 0
        self.defensive_touches = 0

        # save
        self.save_by_outfield_player = 0

        # tackles
        self.total_tackles = 0
        self.total_successful_tackles = 0
        self.tackle_made_percentage = 0
        self.total_tackles_in_attacking_third = 0
        self.total_tackles_in_middle_third = 0
        self.total_tackles_in_defensive_third = 0
        self.challenges = 0
        self.tackle_attempts = 0
        self.tackle_success_percentage = 0
        self.last_man_tackles = 0

        # ball recoveries
        self.total_ball_recovery = 0
        self.total_recoveries_in_defensive_third = 0
        self.total_recoveries_in_middle_third = 0
        self.total_recoveries_in_attacking_third = 0

        # interceptions
        self.total_interceptions = 0
        self.total_interceptions_in_defensive_third = 0
        self.total_interceptions_in_middle_third = 0
        self.total_interceptions_in_attacking_third = 0

        # clearances
        self.total_clearances = 0
        self.total_clearances_in_defensive_third = 0
        self.total_clearances_in_middle_third = 0
        self.total_clearances_in_attacking_third = 0
        self.blocked_cross = 0
        self.headed_clearance = 0
        self.total_real_clearances = 0
        self.clearances_off_the_line = 0

        # offsides provoked
        self.total_offsides_provoked = 0


class EventStatistics:
    def __init__(self, c_id, s_id, results):
        self.competitionID = c_id
        self.seasonID = s_id
        self.eventResults = results
        # self.storeInDB()

    def handleAerialEvent(self, item):
        return DBHelper.AerialEvent(
            totalDuels=item["total aerial duels"],
            won=item["aerial duels won"],
            lost=item["aerial duels lost"],
            wonPercentage=item["aerial duels won percentage"],
            attackingHalf=item["aerial duels in attacking half"],
            wonPercentageInAttackingHalf=item[
                "aerial duels won percentage in attacking half"
            ],
            defendingHalf=item["aerial duels won percentage in defending half"],
            wonPercentageInDefendingHalf=item[
                "aerial duels won percentage in defending half"
            ],
            attackingThird=item["aerial duels in attacking third"],
            wonPercentageInAttackingThird=item[
                "aerial duels won percentage in attacking third"
            ],
            middleThird=item["aerial duels in middle third"],
            wonPercentageInMiddleThird=item[
                "aerial duels won percentage in middle third"
            ],
            defendingThird=item["aerial duels in defending third"],
            wonPercentageInDefendingThird=item[
                "aerial duels won percentage in defending third"
            ],
        )

    def handlePassEvent(self, item):
        print("pass event")
        return DBHelper.PassEvent(
            passes_total=item["Total passes attempted"],
            total_passes_in_defensive_third=item[
                "Total passes attempted in defensive third"],
            total_passes_in_middle_third=item["Total passes attempted in middle third"],
            total_passes_in_attacking_third=item["Total passes attempted in attacking third"],
            total_passes_into_defensive_third=item[
                "Total passes attempted into defensive third"
            ],
            total_passes_into_defensive_third_from_own_box=item[
                "Total passes attempted into defensive third from own box"
            ],
            total_passes_into_middle_third=item[
                "Total passes attempted into middle third"],
            total_passes_into_attacking_third=item["Total passes attempted into attacking third"],
            total_passes_into_box=item["Total passes attempted into the box"],
            total_passes_into_box_with_cross=item["Total passes attempted into the box (with crosses)"],
            total_passes_forward=item["Total passes attempted forward"],
            pass_originate_and_end_in_opponent_half=item[
                "Total passes attempted in opponent half (both originate and end)"
            ],
            pass_originate_and_end_in_own_half=item[
                "Total passes attempted in own half (both originate and end)"
            ],
            forward_pass_attempt_rate=item["Forward pass attempt percentage"],
            passes_successful=item["Total passes completed"],
            total_passes_successful_in_defensive_third=item[
                "Total passes completed from defensive third"
            ],
            total_passes_successful_in_middle_third=item[
                "Total passes completed from middle third"
            ],
            total_passes_successful_in_attacking_third=item[
                "Total passes completed from attacking third"
            ],
            total_passes_successful_in_box=item[
                "Total passes completed inside the box"
            ],
            total_passes_successful_into_defensive_third=item[
                "Total passes completed into defensive third"
            ],
            total_passes_successful_into_middle_third=item[
                "Total passes completed into middle third"
            ],
            total_passes_successful_into_attacking_third=item[
                "Total passes completed into attacking third"
            ],
            total_passes_successful_into_box=item[
                "Total passes completed into the box"
            ],
            successful_passes_into_box_with_cross=item[
                "Total passes completed into the box (including crosses)"
            ],
            total_passes_into_opponent_half=item[
                "Total passes attempted into opponent half"
            ],
            total_passes_into_own_half=item["Total passes attempted into own half"],
            total_passes_successful_into_opponent_half=item[
                "Total passes completed into opponent half"
            ],
            total_passes_successful_into_own_half=item[
                "Total passes completed into own half"
            ],
            pass_originate_and_end_in_opponent_half_successful=item[
                "Total passes completed in opponent half (both originate and end)"
            ],
            pass_originate_and_end_in_own_half_successful=item[
                "Total passes completed in own half (both originate and end)"
            ],
            pass_success_rate=item["Passes completion percentage"],
            pass_completion_percentage_in_the_defensive_third=item[
                "Passes completion percentage in defensive third"
            ],
            pass_completion_percentage_in_the_middle_third=item[
                "Passes completion percentage in middle third"
            ],
            pass_completion_percentage_in_the_final_third=item[
                "Passes completion percentage in attacking third"
            ],
            pass_completion_percentage_into_middle_third=item[
                "Passes completion percentage into middle third"
            ],
            pass_completion_percentage_into_attacking_third=item[
                "Passes completion percentage into attacking third"
            ],
            pass_completion_percentage_in_opponent_half=item[
                "Passes completion percentage in opponent half (both originate and end)"
            ],
            passes_unsuccessful=item["Unsuccessful passes"],
            unsuccessful_passes_in_opponent_half=item[
                "Unsuccessful passes in opponent half"
            ],
            unsuccessful_passes_in_own_half=item["Unsuccessful passes in own half"],
            long_passes=item["Total attempted long passes"],
            successful_long_passes=item["Total completed long passes"],
            long_pass_success_rate=item["Pass completion ratio on long passes"],
            long_pass_ratio=item["Long ball percentage"],
            offensive_passes=item["Total offensive passes"],
            successful_offensive_passes=item["Total successful offensive passes"],
            unsuccessful_offensive_passes=item["Total unsuccessful offensive passes"],
            headed_pass=item["Total headed passes attempted"],
            headed_pass_successful=item["Total headed passes completed"],
            through_ball=item["Total through balls attempted"],
            through_ball_successful=item["Total through balls completed"],
            chipped_passes=item["Chipped passes attempted"],
            chipped_passes_successful=item["Chipped passes completed"],
            lay_off_passes=item["Lay-off passes"],
            lay_off_passes_successful=item["Successful lay-off passes"],
            lay_off_passes_unsuccessful=item["Unsuccessful lay-off passes"],
            flick_on_passes=item["Flick-on passes"],
            flick_on_passes_successful=item["Flick-on passes successful"],
            flick_on_passes_unsuccessful=item["Flick-on passes unsuccessful"],
            flick_on_passes_success_ratio=item["Flick-on passes success percentage"],
            pull_back_passes=item["Pull back passes"],
            switch_play_passes=item["Switch play passes attempted"],
            switch_play_passes_successful=item["Switch play passes completed"],
            blocked_passes=item["Blocked passes"],
            indirect_free_kick=item["Indirect free kicks taken"],
            goal_kick=item["Total goal kicks"],
            total_crosses=item["Total crosses attempted"],
            crosses_from_left_third=item["Total crosses attempted from left third"],
            crosses_from_right_third=item["Total crosses attempted from right third"],
            successful_crosses=item["Crosses completed"],
            unsuccessful_crosses=item["Unsuccessful crosses"],
            cross_success_rate=item["Cross accuracy percentage"],
            overhit_cross=item["Overhit cross"],
            crosses_from_free_kicks=item["Total crosses attempted from free kicks"],
            successful_crosses_from_free_kicks=item["Total crosses completed from free kicks"],
            crosses_from_open_play=item["Total crosses attempted from open play"],
            successful_crosses_from_open_play=item["Total crosses completed from open play"],
            unsuccessful_crosses_from_open_play=item["Total crosses unsuccessful from open play"],
            cross_success_rate_open_play=item["Cross accuracy percentage from open play"],
            cross_pass_ratio_in_attacking_third=item["Cross pass ratio in attacking third"],
            throw_in=item["Total throw ins"],
            successful_throw_in=item["Total throw ins to own player"],
            unsuccessful_throw_in=item["Total throw ins to opponent player"],
            total_corners=item["Total corners"],
            short_corners=item["Short corners"],
            crosses_from_corners=item["Crosses from corners"],
            successful_corner=item["Successful corners"],
            successful_crosses_from_corners=item["Successful crosses from corners"],
            unsuccessful_corner=item["Unsuccessful corners"],
            corners_into_box_successful=item["Successful corners into box"],
            successful_corner_left=item["Successful corners from left"],
            successful_corner_right=item["Successful corners from right"],
            unsuccessful_corner_left=item["Unsuccessful corners from left"],
            unsuccessful_corner_right=item["Unsuccessful corners from right"],
            corner_cross_accuracy_percentage=item["Cross accuracy percentage on corners"],
            corner_success_percentage_left=item["Percentage of successful corners from left"],
            corner_success_percentage_right=item["Percentage of successful corners from right"]
        )

    def handleFoulEvent(self, item):
        return DBHelper.FoulEvent(
            fouls_won=item["total fouls suffered"],
            fouls_conceded=item["total fouls committed"],
            handball_conceded=item["total handballs conceded"],
            penalty_conceded=item["total penalties conceded"],
            penalty_won=item["total penalties won"],
            fouls_won_in_defending_third=item["total fouls suffered in defending third"],
            fouls_won_in_middle_third=item["total fouls suffered in middle third"],
            fouls_won_in_attacking_third=item["total fouls suffered in attacking third"],
            fouls_committed_in_defending_third=item["total fouls committed in defending third"],
            fouls_committed_in_middle_third=item["total fouls committed in middle third"],
            fouls_committed_in_attacking_third=item["total fouls committed in attacking third"]
        )

    def handleAssistEvents(self, item):
        return DBHelper.AssistEvent(
            total_assists=item["total assists"],
            intentional_assists=item["total intentional assists"],
            assists_from_open_play=item["total assists from open play"],
            open_play_assist_rate=item["open play assist percentage"],
            assists_from_set_play=item["total assists from set play"],
            assists_from_free_kick=item["total assists from free kicks"],
            assists_from_corners=item["total assists from corners"],
            assists_from_throw_in=item["total assists from throw in"],
            assists_from_goal_kick=item["total assists from goal kicks"],
            assist_for_first_touch_goal=item["total assists for first touch goals"],
            assist_and_key_passes=item["total assists and key passes"],
            key_passes=item["total key passes"],
            key_pass_free_kick=item["total key passes from free kicks"],
            key_pass_corner=item["total key passes from corners"],
            key_pass_throw_in=item["total key passes from throw ins"],
            key_pass_goal_kick=item["total key passes from goal kicks"],
            chances_created_from_set_play=item["total key passes from set plays"],
            chances_created_from_open_play=item["total key passes from open plays"],
            keypass_for_first_touch_shot=item["total key passes for first touch shot"],
            minutes_per_chance=item["minutes per chance"],
        )

    def handleDuelEvents(self, item):
        return DBHelper.DuelEvent(
            total_duels=item["total duels"],
            defensive_duels=item["defensive duels"],
            offensive_duels=item["offensive duels"],
            successful_duels=item["total successful duels"],
            unsuccessful_duels=item["total unsuccessful duels"],
            duel_success_rate=item["duel success percentage"],
            duels_in_attacking_third=item["duels in attacking third"],
            duels_in_middle_third=item["duels in middle third"],
            duels_in_defending_third=item["duels in defending third"],
            duel_success_attacking_third=item["duel success percentage in attacking third"],
            duel_success_middle_third=item["duel success percentage in middle third"],
            duel_success_defending_third=item["duel success percentage in defending third"],
            successful_ground_duels=item["total ground duels won"],
            unsuccessful_ground_duels=item["total ground duels lost"]
        )

    def handleBallControlEvents(self, item):
        return DBHelper.BallControlEvent(
            total_dispossessed=item["total dispossessed"],
            errors=item["total errors"],
            error_led_to_goal=item["total errors led to goal"],
            error_led_to_shot=item["total errors led to shot"],
            caught_offside=item["total offsides"],
            ball_touch=item["bad ball touches"],
            ball_hit_the_player=item["ball hit the player"],
            unsuccessful_control=item["unsuccessful ball controls"]
        )

    def handleShotandGoalEvents(self, item):
        return DBHelper.ShotandGoalEvent(
            goals=item["Goals"],
            left_footed_goals=item["Left footed Goals"],
            right_footed_goals=item["Right footed goals"],
            non_penalty_goals=item["Non-penalty goals"],
            goals_inside_the_box=item["Goals from inside the box"],
            goals_outside_the_box=item["Goals from outside the box"],
            goals_from_open_play=item["Goals from open play"],
            goals_from_regular_play=item["Goals from regular play"],
            goals_from_fast_break=item["Goals from fast breaks"],
            goals_from_set_play=item["Goals from set plays"],
            goals_from_set_piece_cross=item["Goals from set piece cross"],
            goals_from_set_piece_throw_in=item["Goals from throw in"],
            goals_from_corners=item["Goals from corners"],
            goals_from_penalties=item["Goals from penalties"],
            goals_from_volleys=item["Goals with volleys"],
            headed_goals=item["Headed goals"],
            goals_with_other_part_of_body=item["Goals with other part of body"],
            goals_deflected=item["Deflected goals"],
            own_goal=item["Own goals"],
            goals_unassisted=item["goals unassisted"],

            total_shots=item["otal shots (excluding blocks)"],
            total_shots_with_blocks=item[
                "Total shots (including blocks)"
            ],
            shots_from_set_play=item["Total shots from set play"],
            shots_from_fast_break=item["Total shots from fast break"],
            shots_inside_box=item["Shots from inside the box"],
            shots_outside_box=item["Shots from outside the box"],
            left_footed_shots=item["Left footed shots"],
            right_footed_shots=item["Right footed shots"],
            total_headed_shots=item["Headed shots"],
            penalty_shots_taken=item["Penalty shots taken"],
            shots_with_first_touch=item["Shots attempted first time without another touch"],
            shot_cleared_off_line=item["Shots cleared off line"],
            shots_cleared_off_the_line_inside_box=item["Shots cleared off line inside the box"],
            shots_cleared_off_the_line_outside_box=item[
                "Shots cleared off line ourside the box"
            ],
            shots_deflected=item["Deflected shots"],
            shots_unassisted=item["shots unassisted"],
            shots_after_dribble=item["Total shots after dribble"],

            blocked_shot=item["Blocked shots"],
            blocked_shot_left=item["Blocked shots left"],
            blocked_shot_right=item["Blocked shots right"],
            headed_shots_blocked=item["Blocked shots headed"],
            blocked_shots_with_other_part_of_body=item[
                "Blocked shots with other parts of body"
            ],
            shots_blocked_inside_box=item[
                "Blocked shots from inside the box"
            ],
            shots_blocked_outside_box=item[
                "Blocked shots from outside the box"
            ],

            shots_on_target=item["Total shots on target"],
            shots_on_target_inside_box=item[
                "Shots on target from inside the box"
            ],
            shots_on_target_outside_box=item[
                "Shots on target from outside the box"
            ],
            headed_shots_on_target=item["Headed shots on target"],
            left_footed_shots_on_target=item[
                "Left footed shots on target"
            ],
            right_footed_shots_on_target=item[
                "Right footed shots on target"
            ],
            shots_on_target_from_set_play=item[
                "Shots on target from set plays"
            ],
            shots_on_target_from_open_play=item[
                "Shots on target from open play"
            ],
            shots_on_target_from_penalties=item[
                "Shots on target from penalties"
            ],
            penalty_shots_saved=item["Penalty shots saved (shooter)"],
            shots_on_target_from_corners=item[
                "Shots on target from corners"
            ],
            shots_on_target_from_set_piece_throw_in=item[
                "Shots on target from throw ins"
            ],

            # TODO: continue from here
            shots_off_target=item["Total shots off target"],
            shots_off_target_inside_box=item[
                "Shots off target from inside the box"
            ],
            shots_off_target_outside_box=item[
                "Shots off target from outside the box"
            ],
            headed_shots_off_target=item["Headed shots off target"],
            left_footed_shots_off_target=item[
                "Left footed shots off target"
            ],
            right_footed_shots_off_target=item[
                "Right footed shots off target"
            ],
            shots_off_target_from_set_play=item[
                "Shots off target from set plays"
            ],
            shots_off_target_from_open_play=item[
                "Shots off target from open play"
            ],
            shots_hit_woodwork=item["Shots hit woodwork"],
            shots_off_target_from_penalties=item[
                "Shots off target from penalties"
            ],
            shots_off_target_from_corners=item[
                "Shots off target from corners"
            ],
            shots_off_target_from_set_piece_throw_in=item[
                "Shots off target from throw ins"
            ],

            total_direct_free_kicks=item[
                "Shot attempts from direct free kicks"
            ],
            goals_from_direct_free_kicks=item[
                "Goals from direct free kicks"
            ],
            shots_on_target_from_direct_free_kicks=item[
                "Shot attempts from free kicks on target"
            ],
            direct_free_kicks_off_target=item[
                "Shot attempts from free kicks off target"
            ],
            blocked_direct_free_kicks=item["Blocked direct free kicks"],
            free_kick_on_target_rate=item[
                "Percentage of free kicks on target"
            ],

            total_big_chances=item["Total big chances"],
            goals_from_big_chances=item["Goals from big chances"],
            shots_on_target_from_big_chances=item[
                "Shots on target from big chances"
            ],
            shots_off_target_from_big_chances=item[
                "Shots off target from big chances"
            ],
            shots_blocked_from_big_chances=item[
                "Blocked shots from big chances"
            ],
            chance_missed=item["Chances missed"],
            big_chance_conversion_rate=item[
                "Big chance conversion percentage"
            ],

            minutes_per_goal=item["Minutes per goal"],
            shots_on_target_rate=item["Percentage of shots on target"],
            headed_goals_rate=item["Percentage of goals headed"],
            headed_shots_rate=item["Percentage of shots headed"],
            open_play_goals_rate=item[
                "Percentage of goals from open play"
            ],
            inside_the_box_shots_rate=item[
                "Percentage of shots inside the box"
            ],
            outside_the_box_shots_rate=item[
                "Percentage of shots outside the box"
            ],
            left_foot_shots_rate=item[
                "Percentage of shots via left foot"
            ],
            right_foot_shots_rate=item[
                "Percentage of shots via right foot"
            ],
            blocked_shots_rate=item["Percentage of shots blocked"],
            no_block_shooting_percentage=item[
                "Shooting percentage (goals per shot excluding blocks)"
            ],
            shooting_percentage=item[
                "Shot conversion rate (goals per shot including blocks)"
            ],
            unassisted_goals_shots_rate=item[
                "goals unassisted / shots unassisted"
            ]
        )

    def handleTakeOnEvents(self, item):
        return DBHelper.TakeOnEvent(
            total_take_ons=item["total take ons"],
            take_ons_successful=item["successful take ons"],
            take_ons_unsuccessful=item["unsuccessful take ons"],
            take_on_success_rate=item["take on success rate"],
            take_on_overrun=item["total overrun take ons"],
            take_on_in_attacking_third=item["successful take ons in attacking third"],
            take_on_success_rate_attacking_third=item["successful take on percentage in attacking third"],
            take_ons_in_box=item["take on attempts in box"],
            successful_take_ons_in_box=item["successful take ons in box"],
            tackled=item["tackled"]
        )

    def handleCardEvents(self, item):
        return DBHelper.CardEvent(
            total_cards=item["total cards"],
            yellow_card=item["total yellow cards"],
            second_yellow_card=item["total second yellow cards"],
            red_card=item["total red cards"],
            card_rescinded=item["total rescinded cards"]
        )

    def handleGoalKeeperEvents(self, item):
        return DBHelper.GoalkeeperEvent(
            clean_sheet=item["clean sheets"],
            gk_sweeper=item["goalkeeper sweepers"],
            crosses_faced=item["crosses faced"],
            cross_percentage_gk=item["cross percentage (GK)"],
            crosses_claimed=item["crosses claimed"],
            crosses_punched=item["crosses punched"],
            goals_against=item["goals against"],
            gk_pick_ups=item["goalkeeper pick ups"],
            successful_goal_kicks=item["successful goal kicks"],
            goal_kicks=item["goal kicks"],
            gk_catch_on_cross=item["goalkeeper catches on crosses"],
            gk_drop_on_cross=item["goalkeeper drops on crosses"],
            successful_gk_throws=item["successful goalkeeper throws"],
            gk_throws=item["goalkeeper throws"],
            crosses_not_claimed=item["crosses not claimed"],
            save_percentage=item["save percentage"],
            save_1on1=item["Save When Attacker Was 1 On 1 With GK"],
            save_caught_or_collected=item["Saves Caught Or Collected By GK"],
            saves=item["Saves"],
            gk_smother=item["Goalkeeper smother"],
            save_body=item["Saves body"],
            save_caught=item["Saves caught"],
            save_collected=item["Saves collected"],
            save_diving=item["Saves diving"],
            save_feet=item["Saves feet"],
            save_fingertip=item["Saves fingertip"],
            save_hands=item["Saves hands"],
            save_inside_box=item["Saves inside box"],
            save_outside_box=item["Saves outside box"],
            save_penalty=item["Saves penalty"],
            save_parried_danger=item["Saves parried danger"],
            save_parried_safe=item["Saves parried safe"],
            save_reaching=item["Saves reaching"],
            save_standing=item["Saves standing"],
            save_stooping=item["Saves stooping"],
            accurate_keeper_sweeper=item["Accurate keeper sweepers"],
            shots_against=item["Shots against"],
            shots_on_target_against=item["Shots on target against"],
            team_own_goals=item["Team own goals"],
            penalty_faced=item["penalties faced"],
            penalties_scored=item["penalties opponent scored"],
            penalties_saved=item["penalties saved by keeper"],
            penalties_missed=item["penalties missed by opponent"],
        )

    def handleTouchEvents(self, item):
        return DBHelper.TouchEvent(
            total_touches=item["total touches"],
            total_touches_in_defensive_third=item["touches in defensive third"],
            total_touches_in_middle_third=item["touches in middle third"],
            total_touches_in_attacking_third=item["touches in attacking third"],
            total_touches_in_box=item["touches in opponent box"],
            total_tackles=item["total tackles"],
            total_successful_tackles=item["total successful tackles"],
            tackle_attempts=item["total tackle attempts"],
            tackle_made_percentage=item["tackle made percentage"],
            tackle_success_percentage=item["tackle success percentage"],
            total_tackles_in_defensive_third=item["tackles in defensive third"],
            total_tackles_in_middle_third=item["tackles in middle third"],
            total_tackles_in_attacking_third=item["tackles in attacking third"],
            last_man_tackles=item["last man tackles"],
            total_challenges=item["total challenges lost"],  # TODO: item name differs from the parameter name
            total_ball_recovery=item["total ball recoveries"],
            total_recoveries_in_defensive_third=item["recoveries in defensive third"],
            total_recoveries_in_middle_third=item["recoveries in middle third"],
            total_recoveries_in_attacking_third=item["recoveries in attacking third"],
            total_interceptions=item["total interceptions"],
            total_interceptions_in_defensive_third=item["interceptions in defensive third"],
            total_interceptions_in_middle_third=item["interceptions in middle third"],
            total_interceptions_in_attacking_third=item["interceptions in attacking third"],
            total_clearances=item["total clearances"],
            total_clearances_in_defensive_third=item["clearances in defensive third"],
            total_clearances_in_middle_third=item["clearances in middle third"],
            total_clearances_in_attacking_third=item["clearances in attacking third"],
            blocked_cross=item["total blocked crosses"],
            headed_clearance=item["total headed clearances"],
            total_offsides_provoked=item["total offsides provoked"],
            defensive_touches=item["total defensive touches"],
            clearances_off_the_line=item["total clearances off the line"],
        )


class PlayerEventStatistics(EventStatistics):
    """
    Player statistics event class aims at collecting all events from the event classes.
    it can collect season events, which means the statistical data of a season.
    This class should support also the data of the all seasons and
    the last x game season (for this, we need to find out when the given player played.)

    """

    def __init__(self, playerName, playerId, c_id, s_id, team, results):
        EventStatistics.__init__(self, c_id, s_id, results)
        self.playerName = playerName
        self.playerId = converter(playerId)
        self.team = team
        # self.storeInDB()

    def storeInDB(self):
        print(f"events to be saved ", len(self.eventResults))
        aerial = None
        pass_ = None
        foul = None
        card = None
        ballControl = None
        takeOn = None
        touch = None
        duel = None
        shot = None
        assist = None
        goalKeeper = None
        for item in self.eventResults:
            if "aerial" in item:
                aerial = self.handleAerialEvent(item["aerial"])
                aerial.save()
            if "pass" in item:
                pass_ = self.handlePassEvent(item["pass"])
                pass_.save()
            if "foul" in item:
                foul = self.handleFoulEvent(item["foul"])
                foul.save()
            if "card" in item:
                card = self.handleCardEvents(item["card"])
                card.save()
            if "ballControl" in item:
                ballControl = self.handleBallControlEvents(item["ballControl"])
                ballControl.save()
            if "takeOn" in item:
                takeOn = self.handleTakeOnEvents(item["takeOn"])
                takeOn.save()
            if "touch" in item:
                touch = self.handleTouchEvents(item["touch"])
                touch.save()
            if "duel" in item:
                duel = self.handleDuelEvents(item["duel"])
                duel.save()
            if "shot" in item:
                shot = self.handleShotandGoalEvents(item["shot"])
                shot.save()
            if "assist" in item:
                assist = self.handleAssistEvents(item["assist"])
                assist.save()
            if "goalKeeper" in item:
                goalKeeper = self.handleGoalKeeperEvents(item["goalKeeper"])
                goalKeeper.save()
        ps = DBHelper.PlayerStatistics(
            playerName=self.playerName,
            playerID=self.playerId,
            competitionID=self.competitionID,
            seasonID=self.seasonID,
            aerialEvent=aerial,
            passEvent=pass_,
            foulEvent=foul,
            cardEvent=card,
            ballControlEvent=ballControl,
            takeOnEvent=takeOn,
            touchEvent=touch,
            duelEvent=duel,
            shotEvent=shot,
            assistEvent=assist,
            goalkeeperEvent=goalKeeper
        )
        ps.save()
        print("PLAYER DATA SAVED!")


class TeamEventStatistics(EventStatistics):
    """
    Team statistics event class aims at collecting all events from the event classes.
    it can collect season events, which means the statistical data of a season.
    This class should support also the data of the all seasons and
    the last x game season (for this, we need to find out when the given team played.)

    """

    def __init__(self, teamName, teamId, c_id, s_id, results):

        EventStatistics.__init__(self, c_id, s_id, results)
        self.teamName = teamName
        self.teamId = teamId
        # self.storeInDB()

    def storeInDB(self):
        print(f"events to be saved ", len(self.eventResults))
        aerial = None
        pass_ = None
        foul = None
        card = None
        ballControl = None
        takeOn = None
        touch = None
        duel = None
        shot = None
        assist = None
        goalKeeper = None
        for item in self.eventResults:
            if "aerial" in item:
                aerial = self.handleAerialEvent(item["aerial"])
                aerial.save()
            if "pass" in item:
                pass_ = self.handlePassEvent(item["pass"])
                pass_.save()
            if "foul" in item:
                foul = self.handleFoulEvent(item["foul"])
                foul.save()
            if "card" in item:
                card = self.handleCardEvents(item["card"])
                card.save()
            if "ballControl" in item:
                ballControl = self.handleBallControlEvents(item["ballControl"])
                ballControl.save()
            if "takeOn" in item:
                takeOn = self.handleTakeOnEvents(item["takeOn"])
                takeOn.save()
            if "touch" in item:
                touch = self.handleTouchEvents(item["touch"])
                touch.save()
            if "duel" in item:
                duel = self.handleDuelEvents(item["duel"])
                duel.save()
            if "shot" in item:
                shot = self.handleShotandGoalEvents(item["shot"])
                shot.save()
            if "assist" in item:
                assist = self.handleAssistEvents(item["assist"])
                assist.save()
            if "goalKeeper" in item:
                goalKeeper = self.handleGoalKeeperEvents(item["goalKeeper"])
                goalKeeper.save()

        ps = DBHelper.TeamStatistics(
            teamName=self.teamName,
            teamID=self.teamId,
            competitionID=self.competitionID,
            seasonID=self.seasonID,
            aerialEvent=aerial,
            passEvent=pass_,
            foulEvent=foul,
            cardEvent=card,
            ballControlEvent=ballControl,
            takeOnEvent=takeOn,
            touchEvent=touch,
            duelEvent=duel,
            shotEvent=shot,
            assistEvent=assist,
            goalkeeperEvent=goalKeeper
        )
        ps.save()
        print("TEAM DATA SAVED!")


class MongoDBEventStatistics:
    """
    MongoDBEventStatistics class is a general parent class for the classes where its results input comes from already
    saved files from MongoDB. These results have been collected with querying in the database, therefore while parsing
    the result, we need to define new function, different from EventStatistics class.
    """

    def __init__(self, competition_id, season_id, results):
        self.competitionID = competition_id
        self.seasonID = season_id
        self.eventResults = results
        self.all_events = {
            "aerialEvent": "aerial", "passEvent": "pass", "foulEvent": "foul", "cardEvent": "card",
            "ballControlEvent": "ballControl", "takeOnEvent": "takeOn", "touchEvent": "touch",
            "duelEvent": "duel", "shotEvent": "shot", "assistEvent": "assist", "goalkeeperEvent": "goalkeeper"
        }
        self.all_events_inv = {value: key for key, value in self.all_events.items()}
        self.all_event_handlers = {
            "aerial": DBHelper.AerialEvent, "pass": DBHelper.PassEvent, "foul": DBHelper.FoulEvent,
            "card": DBHelper.CardEvent, "ballControl": DBHelper.BallControlEvent,
            "takeOn": DBHelper.TakeOnEvent, "touch": DBHelper.TouchEvent,
            "duel": DBHelper.DuelEvent, "shot": DBHelper.ShotandGoalEvent,
            "assist": DBHelper.AssistEvent, "goalkeeper": DBHelper.GoalkeeperEvent
        }

    def parse_results(self):
        for item in self.eventResults:
            for the_item_key in item.keys():
                for key, value in self.all_events.items():
                    if value == the_item_key:
                        temp_event = self.all_event_handlers[value](**item[the_item_key])
                        self.all_events[key] = temp_event
                        temp_event.save()
        return self


class PlayerEventStatisticsPer90(MongoDBEventStatistics):
    def __init__(self, player_name, player_id, competition_id, season_id, results):
        MongoDBEventStatistics.__init__(self, competition_id, season_id, results)
        self.playerName = player_name
        self.playerID = player_id
        self.store_in_db()

    def generate_player_stats_document(self):
        self.parse_results()
        all_inputs = {
            "competitionID": self.competitionID, "seasonID": self.seasonID, "playerName": self.playerName,
            "playerID": self.playerID, **self.all_events
        }
        ps = DBHelper.PlayerStatisticsPer90(**all_inputs)
        ps.save()
        print("data is saved")
        return self

    def store_in_db(self):
        self.generate_player_stats_document()
        return self


class PlayerPercentileStatistics(MongoDBEventStatistics):
    def __init__(
            self, player_name: str, player_id: int, competition_id: int,
            season_id: int, event: str, field: str, value: float, results: list = None
    ):
        MongoDBEventStatistics.__init__(self, competition_id, season_id, results)
        self.playerName = player_name
        self.playerID = player_id
        self.event_raw = event
        if self.event_raw in self.all_events_inv:
            self.event = self.all_events_inv[self.event_raw]
        else:
            self.event = self.event_raw
            self.event_raw = self.all_events[self.event_raw]
        self.field = field
        self.event_obj = self.all_event_handlers[self.event_raw]
        self.value = value
        self.store_in_db()

    def generate_event_doc(self):
        temp_event_obj = self.event_obj()
        setattr(temp_event_obj, self.field, self.value)
        temp_event_obj.save()
        # print("New event document has been generated.")
        return temp_event_obj

    def generate_player_doc(self, event_doc):
        mongo_db_object = DBHelper.PlayerPercentileStatistics(
            playerName=self.playerName,
            playerID=self.playerID,
            competitionID=self.competitionID,
            seasonID=self.seasonID
        )
        setattr(mongo_db_object, self.event, event_doc)
        mongo_db_object.save()
        # print("New player document has been generated.")

    def find_player_document(self):
        player_document = DBHelper.PlayerPercentileStatistics.objects(
            Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID) &
            Q(playerID=self.playerID) & Q(playerName=self.playerName)
        ).first()
        return player_document

    def update_player_doc(self, player_document, event_doc):
        if hasattr(player_document, self.event):
            setattr(player_document, self.event, event_doc)
            player_document.save()
            # print("Player document has been updated with a new event document.")
        return self

    def find_event_document(self, player_document):
        if hasattr(player_document, self.event):
            event_obj = getattr(player_document, self.event)
            return event_obj

    def update_event_doc(self, event_doc):
        if hasattr(event_doc, self.field):
            setattr(event_doc, self.field, self.value)
            event_doc.save()
            # print("Event document has been updated with a new field.")
        return self

    def store_in_db(self):
        candidate_player_document = self.find_player_document()
        if candidate_player_document is None:
            event_doc = self.generate_event_doc()
            return self.generate_player_doc(event_doc)
        else:
            candidate_event_document = self.find_event_document(candidate_player_document)
            if candidate_event_document is None:
                event_doc = self.generate_event_doc()
                return self.update_player_doc(candidate_player_document, event_doc)
            else:
                return self.update_event_doc(candidate_event_document)


class PlayerGeneralEventStatistics(MongoDBEventStatistics):
    def __init__(self, stat_name, stat_type, competition_id, season_id, results):

        MongoDBEventStatistics.__init__(self, competition_id, season_id, results)
        self.statName = stat_name
        self.statType = stat_type
        self.store_in_db()

    def generate_player_stats_document(self):
        self.parse_results()
        all_inputs = {
            "competitionID": self.competitionID, "seasonID": self.seasonID, "statName": self.statName,
            "statType": self.statType, **self.all_events
        }
        ps = DBHelper.PlayerSeasonStatistics(**all_inputs)
        ps.save()
        print("data is saved")
        return self

    def store_in_db(self):
        self.generate_player_stats_document()
        return self


class TeamPercentileStatistics(MongoDBEventStatistics):
    def __init__(
            self, team_name: str, team_id: int, competition_id: int,
            season_id: int, event: str, field: str, value: float, results: list = None
    ):
        MongoDBEventStatistics.__init__(self, competition_id, season_id, results)
        self.teamName = team_name
        self.teamID = team_id
        self.event_raw = event
        if self.event_raw in self.all_events_inv:
            self.event = self.all_events_inv[self.event_raw]
        else:
            self.event = self.event_raw
            self.event_raw = self.all_events[self.event_raw]
        self.field = field
        self.event_obj = self.all_event_handlers[self.event_raw]
        self.value = value
        self.store_in_db()

    def generate_event_doc(self):
        temp_event_obj = self.event_obj()
        setattr(temp_event_obj, self.field, self.value)
        temp_event_obj.save()
        # print("New event document has been generated.")
        return temp_event_obj

    def generate_team_doc(self, event_doc):
        mongo_db_object = DBHelper.TeamPercentileStatistics(
            teamName=self.teamName,
            teamID=self.teamID,
            competitionID=self.competitionID,
            seasonID=self.seasonID
        )
        setattr(mongo_db_object, self.event, event_doc)
        mongo_db_object.save()
        # print("New player document has been generated.")

    def find_team_document(self):
        team_document = DBHelper.TeamPercentileStatistics.objects(
            Q(competitionID=self.competitionID) & Q(seasonID=self.seasonID) &
            Q(teamID=self.teamID) & Q(teamName=self.teamName)
        ).first()
        return team_document

    def update_team_doc(self, team_document, event_doc):
        if hasattr(team_document, self.event):
            setattr(team_document, self.event, event_doc)
            team_document.save()
            # print("Player document has been updated with a new event document.")
        return self

    def find_event_document(self, team_document):
        if hasattr(team_document, self.event):
            event_obj = getattr(team_document, self.event)
            return event_obj

    def update_event_doc(self, event_doc):
        if hasattr(event_doc, self.field):
            setattr(event_doc, self.field, self.value)
            event_doc.save()
            # print("Event document has been updated with a new field.")
        return self

    def store_in_db(self):
        candidate_team_document = self.find_team_document()
        if candidate_team_document is None:
            event_doc = self.generate_event_doc()
            return self.generate_team_doc(event_doc)
        else:
            candidate_event_document = self.find_event_document(candidate_team_document)
            if candidate_event_document is None:
                event_doc = self.generate_event_doc()
                return self.update_team_doc(candidate_team_document, event_doc)
            else:
                return self.update_event_doc(candidate_event_document)


class TeamGeneralEventStatistics(MongoDBEventStatistics):
    def __init__(self, stat_name, stat_type, competition_id, season_id, results):

        MongoDBEventStatistics.__init__(self, competition_id, season_id, results)
        self.statName = stat_name
        self.statType = stat_type
        self.store_in_db()

    def generate_team_stats_document(self):
        self.parse_results()
        all_inputs = {
            "competitionID": self.competitionID, "seasonID": self.seasonID, "statName": self.statName,
            "statType": self.statType, **self.all_events
        }
        ps = DBHelper.TeamSeasonStatistics(**all_inputs)
        ps.save()
        print("data is saved")
        return self

    def store_in_db(self):
        self.generate_team_stats_document()
        return self


class PlayerGameMinuteStatistics:

    def __init__(self, game_id, player_name, player_id, competition_id, season_id, team_name, team_id, results):
        self.game_id = int(game_id)
        self.player_name = str(player_name)
        self.player_id = int(player_id)
        self.competition_id = int(competition_id)
        self.season_id = int(season_id)
        self.team_name = str(team_name)
        self.team_id = int(team_id)
        self.event_results = results
        self.store_in_db()

    def generate_minute_statistics(self):
        mongo_db_game_minute_stats_object = DBHelper.GameMinuteStatistics(
            gameID=self.game_id,
            teamName=self.team_name,
            teamID=self.team_id,
            game_minute_stats=self.event_results
        )
        mongo_db_game_minute_stats_object.save()

        return mongo_db_game_minute_stats_object

    def generate_player_minute_statistics(self):
        all_played_games = [self.generate_minute_statistics()]
        if 0 < len(all_played_games):
            mongo_db_object = DBHelper.PlayerMinuteStatistics(
                playerName=self.player_name,
                playerID=self.player_id,
                competitionID=self.competition_id,
                seasonID=self.season_id,
                gamesPlayed=all_played_games
            )
            mongo_db_object.save()
            print("New data has been saved.")

    def find_player_document(self):
        player_document = DBHelper.PlayerMinuteStatistics.objects(
            Q(competitionID=self.competition_id) & Q(seasonID=self.season_id) &
            Q(playerID=self.player_id) & Q(playerName=self.player_name)
        ).first()

        # Following code will prevent multiple save of same document,
        # but it may cause the code to run slower.
        if player_document is not None:
            for games in player_document.gamesPlayed:
                if games.gameID == self.game_id:
                    return False

        return player_document

    def update_in_db(self, player_document):
        if hasattr(player_document, "gamesPlayed"):
            new_game_minute_stats = self.generate_minute_statistics()
            player_document.gamesPlayed.append(new_game_minute_stats)
            player_document.save()
            print("Data has been updated.")
        return self

    def store_in_db(self):
        candidate_player_document = self.find_player_document()
        if candidate_player_document is False:
            return self
        elif candidate_player_document is None:
            self.generate_player_minute_statistics()
        else:
            self.update_in_db(player_document=candidate_player_document)
