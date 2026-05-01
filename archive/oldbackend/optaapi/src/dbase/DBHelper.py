# mongodb url tutorial: https://www.mongodb.com/blog/post/getting-started-with-python-and-mongodb
# https://realpython.com/introduction-to-mongodb-and-python/

"""
Author: Cem Akpolat

"""

from mongoengine import *
import datetime

dbref = False

#################
# Feed1 Tables
#################


class F1_Goal(Document):
    period = StringField(required=False, max_length=200)
    playerRef = IntField(required=False)
    type = StringField(required=False, max_length=200)


class F1_Schedule(Document):
    type = StringField(required=True, max_length=200)
    value = StringField(required=True, max_length=200)


class F1_Team(Document):
    name = StringField(required=True, max_length=200)
    uID = IntField(required=True)


class F1_MatchOfficial(Document):
    first = StringField(required=True, max_length=200)
    last = StringField(required=True, max_length=200)
    uID = IntField(required=True)
    type = StringField(required=True, max_length=200)


class F1_MatchInfo(Document):
    date = StringField()
    # date = DateTimeField(default=datetime.datetime.now)
    matchWinner = IntField(required=False)
    TZ = StringField(required=False, max_length=200)
    venueID = IntField()
    matchDay = IntField()
    matchType = StringField(required=False, max_length=200)
    period = StringField()
    status = StringField(max_length=200)
    teamRef = IntField(required=False)
    playerRef = IntField(required=False)
    timestamp = DateTimeField(default=datetime.datetime.now)
    varReason = StringField(required=False, max_length=200)
    leg = StringField(required=False, max_length=200)
    firstLegID = IntField()
    legWinner = IntField()
    nextMatch = IntField(required=False)
    nextMatchLoser = IntField(required=False)
    roundNumber = IntField()
    roundType = StringField(required=False, max_length=200)
    groupName = StringField(required=False, max_length=200)
    gameWinner = IntField(required=False)
    gameWinnerType = StringField(required=False, max_length=200)


class F1_TeamData(Document):
    score = IntField()
    halfScore = StringField(max_length=200)
    ninetyScore = IntField()
    extraScore = IntField()
    penaltyScore = IntField()
    side = StringField(required=True, max_length=200)
    teamRef = IntField(required=True)
    goal = ListField(ReferenceField(F1_Goal))


class F1_MatchData(Document):
    timingID = IntField()
    matchInfo = ReferenceField(F1_MatchInfo)
    uID = IntField(required=True)
    matchOfficials = ListField(ReferenceField(F1_MatchOfficial))
    detailID = IntField()
    lastModified = StringField()
    schedule = ReferenceField(F1_Schedule)
    teamData = ListField(ReferenceField(F1_TeamData))


class F1_DetailType(Document):
    detailID = IntField()
    name = StringField()


class F1_TimestampAccuracyType(Document):
    name = StringField()
    timestampAccuracyID = StringField()


class F1_TimingType(Document):
    name = StringField()
    timingID = IntField()


class F1_TimingTypes(Document):
    detailTypes = ListField(ReferenceField(F1_DetailType))
    timingTypes = ListField(ReferenceField(F1_TimingType))
    timestampAccuracyTypes = ListField(ReferenceField(F1_TimestampAccuracyType))


# Feed 1
class F1_Root(Document):
    matchData = ListField(ReferenceField(F1_MatchData))
    type = StringField()
    competitionCode = StringField()
    competitionID = IntField()
    competitionName = StringField()
    gameSystemID = IntField()
    seasonID = IntField()
    seasonName = StringField()
    timestamp = DateTimeField()
    teams = ListField(ReferenceField(F1_Team))
    timingTypes = ReferenceField(F1_TimingTypes)


############
#### Feed9 Tables
############


class F9_Stat(Document):
    """
    @param: value
    @param: type
    """

    value = StringField(required=True, max_length=200)
    type = StringField(required=True, max_length=200)


class F9_Schedule(Document):
    type = StringField(required=True, max_length=200)
    value = StringField(required=True, max_length=200)


class F9_Competition(Document):
    """
    :param country: required string value
    :param name: required string value
    :param uID: id
    :param competitionID: competition unique id required
    :param competitionName: competion name required
    :param pool:
    :param stats: list of stats
    :param roundNumber: optional string
    :Example:

    """

    country = StringField(required=True, max_length=200)
    name = StringField(required=True, max_length=200)
    uID = StringField(required=True, max_length=200)
    competitionID = IntField()
    competitionName = StringField(required=False, max_length=200)
    pool = StringField()
    stats = ListField(ReferenceField(F9_Stat))
    roundNumber = IntField()


class F9_Season(Document):
    """
    :param country: required string value
    :param name: required string value
    :param uID: id
    """

    year = IntField()
    seasonID = IntField()
    seasonName = StringField(required=False, max_length=200)


class F9_TeamStat(Document):
    """
    :param value
    :param type
    :param sh
    :param fh
    """

    value = StringField(required=True, max_length=200)
    type = StringField(required=True, max_length=200)
    sh = StringField(max_length=200)
    fh = StringField(max_length=200)


class F9_Assist(Document):
    """
    :param playerRef
    """

    playerRef = StringField(required=True, max_length=200)


class F9_MissedPenalty(Document):
    """
    :param period
    :param time
    :param playerRef
    :param eventNumber
    :param type
    :param uID
    """

    period = StringField(max_length=200)
    time = DateField()
    playerRef = StringField(max_length=200)
    eventNumber = IntField()
    type = StringField(max_length=200)
    uID = IntField()


class F9_Substitution(Document):
    """
    :param eventID
    :param eventNumber
    :param min
    :param sec
    :param time
    :param timestamp
    :param retired
    :param uID
    :param period
    :param reason
    :param suboff
    :param subon
    :param substitutePosition
    """

    eventID = LongField()
    eventNumber = IntField()
    min = IntField()
    sec = IntField()
    time = IntField()
    timestamp = StringField()
    # timestamp = DateField()
    retired = IntField()
    uID = StringField(max_length=200)
    period = StringField(max_length=200)
    reason = StringField(max_length=200)
    suboff = StringField(max_length=200)
    subon = StringField(max_length=200)
    substitutePosition = StringField(max_length=200)


class F9_ShootOut(Document):
    """
    :param firstPenalty
    """

    firstPenalty = IntField()


class F9_SecondAssist(Document):
    """
    :param playerRef
    """

    playerRef = StringField(required=True, max_length=200)


class F9_Goal(Document):
    eventID = LongField()
    eventNumber = StringField(max_length=200)
    min = IntField()
    period = StringField(required=True, max_length=200)
    playerRef = StringField(required=True, max_length=200)
    sec = IntField()
    time = DateTimeField()
    timeStamp = DateTimeField()
    type = StringField(required=True, max_length=200)
    uID = StringField(max_length=200)
    assist = ReferenceField(F9_Assist)
    secondAssist = ReferenceField(F9_SecondAssist)
    soloRun = IntField()
    VARReviewed = StringField(max_length=200)
    originalDecision = StringField(max_length=200)


class F9_AssistantOfficial(Document):
    first = StringField(required=True, max_length=200)
    last = StringField(required=True, max_length=200)
    uID = StringField(required=True, max_length=200)
    type = StringField(required=True, max_length=200)


class F9_PenaltyShot(Document):
    outcome = StringField(required=True, max_length=200)
    eventNumber = IntField()
    playerRef = StringField(required=True, max_length=200)
    uID = IntField()


class F9_MatchType(Document):
    type = StringField(required=True, max_length=200)


class F9_PreviousMatch(Document):
    matchRef = StringField(required=True, max_length=200)
    matchType = StringField(required=True, max_length=200)  # ReferenceField(MatchType)
    venueRef = StringField(required=True, max_length=200)


class F9_Venue(Document):
    country = StringField(max_length=200)
    name = StringField(max_length=200)
    uID = StringField(max_length=200)


class F9_Result(Document):
    type = StringField(required=True, max_length=200)
    minutes = IntField()
    reason = StringField(max_length=200)
    winner = StringField(max_length=200)


class F9_MatchState(Document):
    type = StringField(required=True, max_length=200)
    timestamp = DateTimeField()


class F9_VARData(Document):
    eventID = LongField()
    eventNumber = IntField()
    period = StringField()
    min = IntField()
    sec = IntField()
    reason = StringField()
    decision = StringField()
    outcome = StringField()
    teamRef = StringField()
    playerRef = StringField()


class F9_MatchInfo(Document):
    result = ReferenceField(F9_Result)
    date = StringField()
    # date = DateTimeField(default=datetime.datetime.now)
    matchWinner = StringField(required=False, max_length=200)
    TZ = StringField(required=False, max_length=200)
    venueID = IntField()
    matchDay = IntField()
    matchType = StringField(required=False, max_length=200)
    period = StringField()
    status = StringField(max_length=200)
    teamRef = StringField(required=False, max_length=200)
    playerRef = StringField(required=False, max_length=200)
    timestamp = DateTimeField(default=datetime.datetime.now)
    varReason = StringField(required=False, max_length=200)
    leg = StringField(required=False, max_length=200)
    firstLegID = IntField()
    legWinner = IntField()
    nextMatch = IntField()
    nextMatchLoser = IntField()
    roundNumber = IntField()
    roundType = StringField(required=False, max_length=200)
    groupName = StringField(required=False, max_length=200)
    gameWinner = StringField(required=False, max_length=200)
    matchWinner = IntField()
    gameWinnerType = StringField(required=False, max_length=200)


class F9_MatchOfficial(Document):
    first = StringField(required=True, max_length=200)
    last = StringField(required=True, max_length=200)
    uID = StringField(required=True, max_length=200)
    type = StringField(required=True, max_length=200)
    officialRef = StringField(max_length=200)
    officialData = StringField(max_length=200)


class F9_Booking(Document):
    """
    :param eventNumber
    :param reason
    :param period
    :param eventID
    :param time
    :param uID
    :param card
    :param cardType
    """

    eventNumber = IntField()
    reason = StringField(max_length=200)
    period = StringField(required=True, max_length=200)
    eventID = LongField()
    time = IntField()
    uID = StringField()
    card = StringField(required=True, max_length=200)
    cardType = StringField(required=True, max_length=200)
    min = IntField()
    timestamp = StringField()
    playerRef = StringField(required=True, max_length=200)
    sec = IntField()


class F9_MatchPlayer(Document):
    playerRef = StringField(required=True, max_length=200)
    position = StringField(required=True, max_length=200)
    shirtNumber = StringField(required=True, max_length=200)
    status = StringField(required=True, max_length=200)
    stats = ListField(ReferenceField(F9_Stat))
    subPosition = StringField(max_length=200)
    captain = BooleanField()


class F9_TeamData(Document):
    score = IntField()
    halfScore = StringField(max_length=200)
    ninetyScore = IntField()
    extraScore = IntField()
    penaltyScore = IntField()
    side = StringField(required=True, max_length=200)
    teamRef = StringField(max_length=200)
    goal = ListField(ReferenceField(F9_Goal))
    teamStats = ListField(ReferenceField(F9_TeamStat))
    missedPenalty = ReferenceField(F9_MissedPenalty)
    substitutions = ListField(ReferenceField(F9_Substitution))
    playerLineUp = ListField(ReferenceField(F9_MatchPlayer))
    shootOutScore = ReferenceField(F9_ShootOut)
    booking = ListField(ReferenceField(F9_Booking))


class F9_MatchData(Document):
    timingID = IntField()
    matchInfo = ReferenceField(F9_MatchInfo)
    matchStats = ListField(ReferenceField(F9_Stat))
    uID = StringField(max_length=200)
    matchOfficials = ListField(ReferenceField(F9_MatchOfficial))
    teamData = ListField(ReferenceField(F9_TeamData))
    detailID = IntField()
    lastModified = StringField()
    # lastModified = DateTimeField(default=datetime.datetime.now)
    schedule = ReferenceField(F9_Schedule)
    assistantOfficials = ListField(ReferenceField(F9_AssistantOfficial))
    shootOut = ReferenceField(F9_ShootOut)
    penaltyShot = ReferenceField(F9_PenaltyShot)
    previousMatch = ReferenceField(F9_PreviousMatch)
    VARData = ReferenceField(F9_VARData)


class F9_TeamOfficial(Document):
    """
    :param first
    :param last
    :param type
    :param uID
    :param country
    :param personalInfo
    """

    first = StringField(max_length=200)
    last = StringField(max_length=200)
    type = StringField(max_length=200)
    uID = StringField(max_length=200)
    country = StringField(max_length=200)


class F9_Player(Document):
    """
    :param stats
    :param name
    :param first
    :param last
    :param type
    :param uID
    :param position
    :param known
    :param captain
    :param playerLoan
    """

    stats = ListField(ReferenceField(F9_Stat))
    name = StringField(max_length=200)
    first = StringField(max_length=200)
    last = StringField(max_length=200)
    type = StringField(max_length=200)
    uID = IntField(required=True)
    position = StringField(required=True, max_length=200)
    known = StringField(max_length=200)
    captain = BooleanField()
    playerLoan = IntField()


class F9_Kit(Document):
    """
    :param kitID
    :param colour1
    :param colour2
    :param type
    """

    kitID = IntField()
    colour1 = StringField()
    colour2 = StringField()
    type = StringField()


class F9_TeamOfficial(Document):
    """
    :param first
    :param last
    :param type
    :param uID
    :param country
    :param personalInfo
    """

    first = StringField(max_length=200)
    last = StringField(max_length=200)
    type = StringField(max_length=200)
    uID = StringField(max_length=200)
    country = StringField(max_length=200)  # ?


class F9_Team(Document):
    name = StringField(required=True, max_length=200)
    uID = IntField(required=True)
    players = ListField(ReferenceField(F9_Player))
    country = StringField()
    teamOfficials = ListField(ReferenceField(F9_TeamOfficial))
    kits = ListField(ReferenceField(F9_Kit))


class F9_Root(Document):
    matchData = ReferenceField(F9_MatchData)
    venue = ReferenceField(F9_Venue)
    type = StringField(max_length=200)
    teams = ListField(ReferenceField(F9_Team))
    detailID = IntField()
    uID = StringField(required=True, max_length=200)
    competition = ReferenceField(F9_Competition)
    competitionID = IntField()
    seasonID = IntField()
    timestamp = StringField()
    # timestamp = DateTimeField()


##############
#### Feed24 Tables
##############


class F24_Assist(Document):
    """
    :param playerRef
    """

    playerRef = StringField(required=True, max_length=200)


class F24_QEvent(Document):
    ID = IntField(required=True)
    qualifierID = IntField()
    value = StringField(max_length=200)


class F24_Event(Document):
    ID = IntField()
    eventID = LongField()
    qEvents = ListField(ReferenceField(F24_QEvent))
    periodID = IntField()
    sec = IntField()
    # timestamp = DateTimeField()
    min = IntField()
    teamID = IntField()
    typeID = IntField()
    outcome = IntField()
    x = DecimalField()
    y = DecimalField()
    lastModified = StringField(max_length=200)
    # lastModified = DateTimeField()
    version = StringField(max_length=200)
    playerID = IntField()
    assist = ReferenceField(
        F24_Assist
    )  # playerRef? if this is ref, then it is indeed string
    keypass = StringField(max_length=200)


class F24_Game(Document):
    ID = IntField(required=True)
    events = ListField(ReferenceField(F24_Event))
    awayScore = IntField()
    awayTeamID = IntField(required=True)
    awayTeamName = StringField(max_length=200)
    competitionID = IntField(required=True)
    competitionName = StringField(required=True, max_length=200)
    seasonID = IntField(required=True)
    seasonName = StringField(required=True, max_length=200)
    periodOneStart = StringField(required=True, max_length=200)
    matchDay = IntField()
    homeTeamID = IntField(required=True)
    homeTeamName = StringField(max_length=200)
    homeScore = IntField()
    periodSecondStart = StringField(max_length=200)
    gameDate = DateField()
    periodThirdStart = StringField(max_length=200)
    periodFourthStart = StringField(max_length=200)
    periodFifthStart = StringField(max_length=200)


# Feed 24, Indeed we have only a single game for each gameId
class F24_Root(Document):
    timestamp = DateTimeField()
    game = ReferenceField(F24_Game)
    competitionID = IntField(required=True)
    seasonID = IntField(required=True)
    gameID = IntField(required=True)


#### Feed40 Tables


class F40_Kit(Document):
    """
    :param kitID
    :param colour1
    :param colour2
    :param type
    """

    kitID = IntField()
    colour1 = StringField()
    colour2 = StringField()
    type = StringField()


class F40_PersonalInfo(Document):
    """
    :param first
    :param last
    :param type
    :param uID
    :param leaveDate
    :param joinDate
    :param birthDate
    :param birthPlace

    """

    first = StringField(required=True, max_length=200)
    last = StringField(required=True, max_length=200)
    type = StringField(max_length=200)
    uID = IntField(required=True)
    leaveDate = DateTimeField()
    joinDate = DateTimeField()
    birthDate = DateField()
    birthPlace = StringField(max_length=200)  # ?


class F40_TeamOfficial(Document):
    """
    :param first
    :param last
    :param type
    :param uID
    :param country
    :param personalInfo
    """

    type = StringField(max_length=200)
    uID = IntField(required=True)
    country = StringField(max_length=200)
    personalInfo = ReferenceField(F40_PersonalInfo)


class F40_Stat(Document):
    """
    @param: value
    @param: type
    """

    value = StringField(required=True, max_length=200)
    type = StringField(required=True, max_length=200)


class F40_Player(Document):
    """
    :param stats
    :param name
    :param first
    :param last
    :param type
    :param uID
    :param position
    :param known
    :param captain
    :param playerLoan
    """

    stats = ListField(ReferenceField(F40_Stat))
    name = StringField(max_length=200)
    uID = IntField(required=True)
    position = StringField(required=True, max_length=200)
    playerLoan = IntField()


class F40_Stadium(Document):
    name = StringField(required=True, max_length=200)
    uID = IntField(required=True)
    capacity = IntField()


class F40_Team(Document):
    name = StringField(required=True, max_length=200)
    uID = IntField(required=True)
    country = StringField(max_length=200)
    countryISO = StringField(max_length=200)
    countryID = IntField()
    regionName = StringField(max_length=200)
    regionID = IntField()
    stadium = ReferenceField(F40_Stadium)
    officialClubName = StringField(max_length=200)
    shortClubName = StringField(max_length=200)
    kits = ListField(ReferenceField(F40_Kit))
    teamOfficials = ListField(ReferenceField(F40_TeamOfficial))
    players = ListField(ReferenceField(F40_Player))
    founded = IntField()
    symid = StringField()
    fifaRank = StringField(max_length=200)
    city = StringField(max_length=200)
    postalCode = IntField()
    street = StringField(max_length=200)
    webAddress = StringField(max_length=200)


class F40_Root(Document):
    team = ListField(ReferenceField(F40_Team))
    type = StringField(max_length=200)
    competitionID = IntField()
    competitionName = StringField(max_length=200)
    competitionCode = StringField(max_length=200)
    seasonID = IntField()
    seasonName = StringField(max_length=200)
    playerChanges = ListField(ReferenceField(F40_Team))  # TODO: This is not true
    timestamp = DateTimeField()


############
###########


class FeedTable(Document):
    feedID = IntField(required=True)
    seasonID = IntField(required=True)
    competitionID = IntField(required=True)
    gameID = IntField()


class AerialEvent(Document):
    totalDuels = FloatField()
    won = FloatField()
    lost = FloatField()
    wonPercentage = FloatField()
    attackingHalf = FloatField()
    wonPercentageInAttackingHalf = FloatField()
    defendingHalf = FloatField()
    wonPercentageInDefendingHalf = FloatField()
    attackingThird = FloatField()
    wonPercentageInAttackingThird = FloatField()
    middleThird = FloatField()
    wonPercentageInMiddleThird = FloatField()
    defendingThird = FloatField()
    wonPercentageInDefendingThird = FloatField()


class PassEvent(Document):
    attempted = FloatField()
    averagePassDistance = FloatField()
    passAttemptedInDefensiveThird = FloatField()
    passAttemtedInMiddleThird = FloatField()
    passAttemptedInAttackingThird = FloatField()
    passAttemptedIntoDefensiveThird = FloatField()
    passAttemptedIntoDefensiveThirdOwnBox = FloatField()
    passAttemtedIntoMiddleThird = FloatField()
    passAttemptedIntoAttackingThird = FloatField()
    passAttemptedIntoBox = FloatField()
    passAttemptedIntoBoxWithCrosses = FloatField()
    passAttemptedForward = FloatField()


class AssistEvent(Document):
    total_assists = FloatField()
    intentional_assists = FloatField()
    assists_from_open_play = FloatField()
    open_play_assist_rate = FloatField()
    assists_from_set_play = FloatField()
    assists_from_free_kick = FloatField()
    assists_from_corners = FloatField()
    assists_from_throw_in = FloatField()
    assists_from_goal_kick = FloatField()
    assist_for_first_touch_goal = FloatField()
    assist_and_key_passes = FloatField()
    key_passes = FloatField()
    key_pass_free_kick = FloatField()
    key_pass_corner = FloatField()
    key_pass_throw_in = FloatField()
    key_pass_goal_kick = FloatField()
    key_passes_after_dribble = FloatField()
    minutes_per_chance = FloatField()
    chances_created_from_open_play = FloatField()
    keypass_for_first_touch_shot = FloatField()
    chances_created_from_set_play = FloatField()


class BallControlEvent(Document):
    total_dispossessed = FloatField()
    errors = FloatField()
    error_led_to_goal = FloatField()
    error_led_to_shot = FloatField()
    caught_offside = FloatField()
    ball_touch = FloatField()
    ball_hit_the_player = FloatField()
    unsuccessful_control = FloatField()


class CardEvent(Document):
    total_cards = FloatField()
    yellow_card = FloatField()
    second_yellow_card = FloatField()
    red_card = FloatField()
    card_rescinded = FloatField()


class FoulEvent(Document):
    # simple foul event counters
    fouls_total = FloatField()
    fouls_won = FloatField()
    fouls_conceded = FloatField()
    handball_conceded = FloatField()
    penalty_conceded = FloatField()
    penalty_won = FloatField()
    fouls_won_in_defending_third = FloatField()
    fouls_won_in_middle_third = FloatField()
    fouls_won_in_attacking_third = FloatField()
    fouls_committed_in_defending_third = FloatField()
    fouls_committed_in_middle_third = FloatField()
    fouls_committed_in_attacking_third = FloatField()


class DuelEvent(Document):
    # duel counters
    total_duels = FloatField()
    successful_duels = FloatField()
    unsuccessful_duels = FloatField()
    total_ground_duels = FloatField()
    successful_ground_duels = FloatField()
    unsuccessful_ground_duels = FloatField()
    defensive_duels = FloatField()
    offensive_duels = FloatField()

    # duel regions
    duels_in_attacking_third = FloatField()
    duels_in_middle_third = FloatField()
    duels_in_defending_third = FloatField()

    # successful duel regions
    successful_duels_attacking_third = FloatField()
    successful_duels_middle_third = FloatField()
    successful_duels_defensive_third = FloatField()

    # unsuccessful duel regions
    unsuccessful_duels_attacking_third = FloatField()
    unsuccessful_duels_middle_third = FloatField()
    unsuccessful_duels_defensive_third = FloatField()

    # aerial duel success rate
    duel_success_rate = FloatField()
    duel_success_attacking_third = FloatField()
    duel_success_middle_third = FloatField()
    duel_success_defending_third = FloatField()


class ShotandGoalEvent(Document):
    # goal counters
    goals = FloatField()
    goals_inside_the_box = FloatField()
    goals_outside_the_box = FloatField()
    left_footed_goals = FloatField()
    right_footed_goals = FloatField()
    non_penalty_goals = FloatField()
    goals_from_penalties = FloatField()
    goals_from_set_play = FloatField()
    goals_from_set_piece_cross = FloatField()
    goals_from_set_piece_throw_in = FloatField()
    goals_from_open_play = FloatField()
    goals_from_volleys = FloatField()
    goals_from_corners = FloatField()
    goals_from_fast_break = FloatField()
    goals_from_regular_play = FloatField()
    goals_deflected = FloatField()
    goals_from_direct_free_kicks = FloatField()
    headed_goals = FloatField()
    goals_with_other_part_of_body = FloatField()
    own_goal = FloatField()
    minutes_per_goal = FloatField()
    goals_unassisted = FloatField()

    # goal after dribble
    dribble_event_id = FloatField()
    dribble_check = FloatField()
    event_id = FloatField()
    shots_after_dribble = FloatField()

    # total shots
    total_shots = FloatField()
    total_shots_with_blocks = FloatField()
    penalty_shots_taken = FloatField()
    left_footed_shots = FloatField()
    right_footed_shots = FloatField()
    shots_inside_box = FloatField()
    shots_outside_box = FloatField()
    total_headed_shots = FloatField()
    shots_with_first_touch = FloatField()
    total_big_chances = FloatField()
    total_direct_free_kicks = FloatField()
    shot_cleared_off_line = FloatField()
    shots_deflected = FloatField()
    shots_from_set_play = FloatField()
    shots_from_fast_break = FloatField()
    shots_unassisted = FloatField()
    shots_cleared_off_the_line_inside_box = FloatField()
    shots_cleared_off_the_line_outside_box = FloatField()

    # blocked shots
    blocked_shot = FloatField()
    blocked_shot_left = FloatField()
    blocked_shot_right = FloatField()
    shots_blocked_inside_box = FloatField()
    shots_blocked_outside_box = FloatField()
    headed_shots_blocked = FloatField()
    blocked_shots_with_other_part_of_body = FloatField()
    shots_blocked_from_big_chances = FloatField()
    blocked_direct_free_kicks = FloatField()
    shots_blocked_from_set_play = FloatField()

    # shots off target
    shots_off_target = FloatField()
    shots_off_target_inside_box = FloatField()
    shots_off_target_outside_box = FloatField()
    shots_off_target_from_set_piece_cross = FloatField()
    shots_off_target_from_set_play = FloatField()
    shots_off_target_from_set_piece_throw_in = FloatField()
    shots_off_target_from_corners = FloatField()
    shots_off_target_from_regular_play = FloatField()
    shots_off_target_from_fast_break = FloatField()
    shots_off_target_from_open_play = FloatField()
    shots_off_target_from_penalties = FloatField()
    headed_shots_off_target = FloatField()
    left_footed_shots_off_target = FloatField()
    right_footed_shots_off_target = FloatField()
    shots_hit_woodwork = FloatField()
    shots_hit_the_post_from_big_chances = FloatField()
    shots_off_target_from_big_chances = FloatField()
    direct_free_kicks_off_target = FloatField()

    # shots on target
    shots_on_target = FloatField()
    headed_shots_on_target = FloatField()
    shots_on_target_from_set_piece_cross = FloatField()
    shots_on_target_from_set_play = FloatField()
    shots_on_target_from_set_piece_throw_in = FloatField()
    shots_on_target_from_corners = FloatField()
    shots_on_target_from_regular_play = FloatField()
    shots_on_target_from_fast_break = FloatField()
    shots_on_target_from_open_play = FloatField()
    shots_on_target_from_penalties = FloatField()
    shots_on_target_inside_box = FloatField()
    shots_on_target_outside_box = FloatField()
    left_footed_shots_on_target = FloatField()
    right_footed_shots_on_target = FloatField()
    penalty_shots_saved = FloatField()
    shots_on_target_from_direct_free_kicks = FloatField()

    # big chances
    goals_from_big_chances = FloatField()
    shots_on_target_from_big_chances = FloatField()
    chance_missed = FloatField()

    # goal percentages
    headed_goals_rate = FloatField()
    open_play_goals_rate = FloatField()
    headed_shots_rate = FloatField()
    inside_the_box_shots_rate = FloatField()
    outside_the_box_shots_rate = FloatField()
    left_foot_shots_rate = FloatField()
    right_foot_shots_rate = FloatField()
    shots_on_target_rate = FloatField()
    blocked_shots_rate = FloatField()
    shooting_percentage = FloatField()
    no_block_shooting_percentage = FloatField()
    big_chance_conversion_rate = FloatField()
    free_kick_on_target_rate = FloatField()
    unassisted_goals_shots_rate = FloatField()


class TakeOnEvent(Document):
    # simple card event counters
    total_take_ons = FloatField()
    take_ons_successful = FloatField()
    take_ons_unsuccessful = FloatField()
    take_on_success_rate = FloatField()
    take_on_overrun = FloatField()
    take_on_in_attacking_third = FloatField()
    take_on_in_attacking_third_uns = FloatField()
    take_on_success_rate_attacking_third = FloatField()
    take_ons_in_box = FloatField()
    successful_take_ons_in_box = FloatField()
    tackled = FloatField()


class TouchEvent(Document):
    # simple ball control event counters
    total_touches = FloatField()
    total_touches_in_attacking_third = FloatField()
    total_touches_in_middle_third = FloatField()
    total_touches_in_defensive_third = FloatField()
    total_touches_in_box = FloatField()
    turnover = FloatField()
    turnover_percentage = FloatField()
    take_on_overrun = FloatField()
    defensive_touches = FloatField()

    # save
    save_by_outfield_player = FloatField()

    # tackles
    total_tackles = FloatField()
    total_successful_tackles = FloatField()
    tackle_made_percentage = FloatField()
    total_tackles_in_attacking_third = FloatField()
    total_tackles_in_middle_third = FloatField()
    total_tackles_in_defensive_third = FloatField()
    total_challenges = FloatField()
    tackle_attempts = FloatField()
    tackle_success_percentage = FloatField()
    last_man_tackles = FloatField()

    # ball recoveries
    total_ball_recovery = FloatField()
    total_recoveries_in_defensive_third = FloatField()
    total_recoveries_in_middle_third = FloatField()
    total_recoveries_in_attacking_third = FloatField()

    # interceptions
    total_interceptions = FloatField()
    total_interceptions_in_defensive_third = FloatField()
    total_interceptions_in_middle_third = FloatField()
    total_interceptions_in_attacking_third = FloatField()

    # clearances
    total_clearances = FloatField()
    total_clearances_in_defensive_third = FloatField()
    total_clearances_in_middle_third = FloatField()
    total_clearances_in_attacking_third = FloatField()
    blocked_cross = FloatField()
    headed_clearance = FloatField()
    total_real_clearances = FloatField()
    clearances_off_the_line = FloatField()

    # offsides provoked
    total_offsides_provoked = FloatField()


class PassEvent(Document):
    # simple pass counters
    passes_total = FloatField()
    passes_successful = FloatField()
    passes_unsuccessful = FloatField()
    forward_passes = FloatField()
    offensive_passes = FloatField()
    successful_offensive_passes = FloatField()
    unsuccessful_offensive_passes = FloatField()
    backward_passes = FloatField()
    sideway_passes = FloatField()
    total_passes_in_defensive_third = FloatField()
    total_passes_in_middle_third = FloatField()
    total_passes_in_attacking_third = FloatField()
    total_passes_successful_in_defensive_third = FloatField()
    total_passes_successful_in_middle_third = FloatField()
    total_passes_successful_in_attacking_third = FloatField()
    total_passes_successful_in_box = FloatField()
    pass_completion_percentage_in_the_final_third = FloatField()
    pass_completion_percentage_in_the_defensive_third = FloatField()
    pass_completion_percentage_in_the_middle_third = FloatField()
    total_passes_into_defensive_third = FloatField()
    total_passes_into_middle_third = FloatField()
    total_passes_into_attacking_third = FloatField()
    total_passes_into_box = FloatField()
    passes_into_box_with_cross = FloatField()
    total_passes_into_opponent_half = FloatField()
    pass_success_rate = FloatField()
    total_passes_successful_into_defensive_third = FloatField()
    total_passes_successful_into_middle_third = FloatField()
    total_passes_successful_into_attacking_third = FloatField()
    total_passes_successful_into_box = FloatField()
    pass_completion_percentage_into_defensive_third = FloatField()
    pass_completion_percentage_into_middle_third = FloatField()
    pass_completion_percentage_into_attacking_third = FloatField()
    total_passes_into_own_half = FloatField()
    total_passes_successful_into_opponent_half = FloatField()
    total_passes_successful_into_own_half = FloatField()
    total_passes_forward = FloatField()
    forward_pass_attempt_rate = FloatField()

    total_pass_length = FloatField()
    average_pass_length = FloatField()

    successful_passes_into_box_with_cross = FloatField()
    pass_originate_and_end_in_opponent_half = FloatField()
    pass_originate_and_end_in_opponent_half_successful = FloatField()
    pass_completion_percentage_in_opponent_half = FloatField()
    pass_originate_and_end_in_own_half = FloatField()
    pass_originate_and_end_in_own_half_successful = FloatField()
    total_passes_into_defensive_third_from_own_box = FloatField()
    total_crosses_into_box = FloatField()
    total_passes_into_box_with_cross = FloatField()
    unsuccessful_passes_in_opponent_half = FloatField()
    unsuccessful_passes_in_own_half = FloatField()

    # cross counters
    total_crosses = FloatField()
    successful_crosses = FloatField()
    unsuccessful_crosses = FloatField()
    crosses_from_free_kicks = FloatField()
    successful_crosses_from_free_kicks = FloatField()
    crosses_from_right_third = FloatField()
    crosses_from_left_third = FloatField()
    crosses_from_open_play = FloatField()
    successful_crosses_from_open_play = FloatField()
    overhit_cross = FloatField()
    unsuccessful_crosses_from_open_play = FloatField()
    cross_success_rate = FloatField()
    cross_success_rate_open_play = FloatField()
    cross_pass_ratio_in_attacking_third = FloatField()
    successful_crosses_into_box = FloatField()

    # free kick counters
    total_free_kicks_taken = FloatField()
    successful_free_kick = FloatField()
    unsuccessful_free_kick = FloatField()
    direct_free_kick = FloatField()
    indirect_free_kick = FloatField()

    # corner counters
    total_corners = FloatField()
    successful_corner = FloatField()
    unsuccessful_corner = FloatField()
    corners_into_box_successful = FloatField()
    corner_left = FloatField()
    corner_right = FloatField()
    successful_corner_left = FloatField()
    successful_corner_right = FloatField()
    unsuccessful_corner_left = FloatField()
    unsuccessful_corner_right = FloatField()
    corner_cross_accuracy_percentage = FloatField()
    corner_success_percentage_left = FloatField()
    corner_success_percentage_right = FloatField()
    crosses_from_corners = FloatField()
    successful_crosses_from_corners = FloatField()
    short_corners = FloatField()

    # keeper throws
    keeper_throw = FloatField()
    successful_keeper_throw = FloatField()
    unsuccessful_keeper_throw = FloatField()
    goal_kick = FloatField()

    # throw_ins
    throw_in = FloatField()
    successful_throw_in = FloatField()
    unsuccessful_throw_in = FloatField()

    # long passes
    long_passes = FloatField()
    successful_long_passes = FloatField()
    unsuccessful_long_passes = FloatField()
    long_pass_ratio = FloatField()
    long_pass_success_rate = FloatField()

    # pass types
    headed_pass = FloatField()
    headed_pass_successful = FloatField()
    through_ball = FloatField()
    through_ball_successful = FloatField()
    chipped_passes = FloatField()
    chipped_passes_successful = FloatField()
    lay_off_passes = FloatField()
    lay_off_passes_successful = FloatField()
    lay_off_passes_unsuccessful = FloatField()
    launch_passes = FloatField()
    successful_launch_passes = FloatField()
    flick_on_passes = FloatField()
    flick_on_passes_successful = FloatField()
    flick_on_passes_unsuccessful = FloatField()
    flick_on_passes_success_ratio = FloatField()
    pull_back_passes = FloatField()
    switch_play_passes = FloatField()
    switch_play_passes_successful = FloatField()
    blocked_passes = FloatField()

    # assists and key passes
    assist_and_key_passes = FloatField()
    second_assist = FloatField()


class GoalkeeperEvent(Document):
    clean_sheet = FloatField()
    gk_sweeper = FloatField()
    crosses_faced = FloatField()
    cross_percentage_gk = FloatField()
    crosses_claimed = FloatField()
    crosses_punched = FloatField()
    goals_against = FloatField()
    gk_pick_ups = FloatField()
    successful_goal_kicks = FloatField()
    goal_kicks = FloatField()
    gk_catch_on_cross = FloatField()
    gk_drop_on_cross = FloatField()
    successful_gk_throws = FloatField()
    gk_throws = FloatField()
    crosses_not_claimed = FloatField()
    save_percentage = FloatField()
    save_1on1 = FloatField()
    save_caught_or_collected = FloatField()
    saves = FloatField()
    gk_smother = FloatField()
    save_body = FloatField()
    save_caught = FloatField()
    save_collected = FloatField()
    save_diving = FloatField()
    save_feet = FloatField()
    save_fingertip = FloatField()
    save_hands = FloatField()
    save_inside_box = FloatField()
    save_outside_box = FloatField()
    save_penalty = FloatField()
    save_parried_danger = FloatField()
    save_parried_safe = FloatField()
    save_reaching = FloatField()
    save_standing = FloatField()
    save_stooping = FloatField()
    accurate_keeper_sweeper = FloatField()
    shots_against = FloatField()
    shots_on_target_against = FloatField()
    team_own_goals = FloatField()
    penalty_faced = FloatField()
    penalties_scored = FloatField()
    penalties_saved = FloatField()
    penalties_missed = FloatField()


class PlayerStatistics(Document):
    playerName = StringField()
    playerID = IntField()
    competitionID = IntField()
    seasonID = IntField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class PlayerStatisticsPer90(Document):
    playerName = StringField()
    playerID = IntField()
    competitionID = IntField()
    seasonID = IntField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class PlayerPercentileStatistics(Document):
    playerName = StringField()
    playerID = IntField()
    competitionID = IntField()
    seasonID = IntField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class TeamStatistics(Document):
    teamName = StringField()
    teamID = IntField()
    competitionID = IntField()
    seasonID = IntField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class TeamPercentileStatistics(Document):
    teamName = StringField()
    teamID = IntField()
    competitionID = IntField()
    seasonID = IntField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class GameMinuteStatistics(Document):
    gameID = IntField()
    teamName = StringField()
    teamID = IntField()
    game_minute_stats = DictField()


class PlayerMinuteStatistics(Document):
    competitionID = IntField()
    seasonID = IntField()
    playerID = IntField()
    playerName = StringField()
    gamesPlayed = ListField(ReferenceField(GameMinuteStatistics))


class PlayerSeasonStatistics(Document):
    competitionID = IntField()
    seasonID = IntField()
    statType = StringField()
    statName = StringField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)


class TeamSeasonStatistics(Document):
    competitionID = IntField()
    seasonID = IntField()
    statType = StringField()
    statName = StringField()
    aerialEvent = ReferenceField(AerialEvent)
    passEvent = ReferenceField(PassEvent)
    foulEvent = ReferenceField(FoulEvent)
    cardEvent = ReferenceField(CardEvent)
    ballControlEvent = ReferenceField(BallControlEvent)
    takeOnEvent = ReferenceField(TakeOnEvent)
    touchEvent = ReferenceField(TouchEvent)
    duelEvent = ReferenceField(DuelEvent)
    shotEvent = ReferenceField(ShotandGoalEvent)
    assistEvent = ReferenceField(AssistEvent)
    goalkeeperEvent = ReferenceField(GoalkeeperEvent)
