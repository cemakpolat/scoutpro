"""
Author: Cem Akpolat

"""
PeriodID = {
    "1": "First half",
    "2": "Second Half",
    "3": "First period of extra time",
    "4": "Second period of extra time",
    "5": "Penalty shoot out",
    "10": "Half-time",
    "14": "Post-game",
    "15": "Pre-game",
    "16": "Pre-match",
}

EventTypes = {
    "1": "Pass",  # outcome: 0 - unsuccessful: pass did not find team mate, outcome: 1 - successful pass
    "2": "Offside Pass",  # outcome is always set to 1
    "3": "Take On",  # 0 - player lost possession or was tackled, 1 - successful take on
    "4": "Foul",  # outcome:0 - player who committed the foul, outcome: 1 - player who was fouled
    "5": "Out",  # 0 - the team that put the ball out, 1: the team that won the corner
    "6": "Corner Awarded",  # 0 - team that conceded the corner, 1 - team that won the corner
    "7": "Tackle",  # 0 - attempted taclked/ challenge from this team to the team on te ball, 1 - sucessfull tackle
    "8": "Interception",  # outcome is always set to 1
    "9": "Turnover",  # n.a.
    "10": "Save",  # outcome is always set to 1
    "11": "Claim",
    # 0 - keeper drops the ball after an attempted catch from a cross, 1- keeper catches the cross in one attempt ie no drop
    "12": "Clearance",  # outcome is always set to 1
    "13": "Miss",  # outcome: 1
    "14": "Post",  # outcome: 1
    "15": "Attempt Saved",  # outcome: 1
    "16": "Goal",  # outcome: 1
    "17": "Card",  # outcome: 1
    "18": "Player Off",  # outcome: 1
    "19": "Player on",  # outcome: 1
    "20": "Player retired",  # outcome: 1
    "21": "Player returns",  # outcome: 1
    "22": "Player becomes goalkeeper",  # outcome: 1
    "23": "Goalkeeper becomes player",  # outcome: 1
    "24": "Condition change",  # outcome: 1
    "25": "Official change",  # outcome: 1
    "27": "Start delay",  # outcome: 1
    "28": "End delay",  # outcome: 1
    "30": "End",  # outcome: 1
    "32": "Start",  # outcome: 1
    "34": "Team set up",  # outcome: 1
    "35": "Player changed position",  # outcome: 1
    "36": "Player changed jersey number",  # outcome: 1
    "37": "Collection End",  # outcome: 1
    "38": "Temp_Goal",  # outcome: 1
    "39": "Temp_Attempt",  # outcome: 1
    "40": "Formation change",  # outcome: 1
    "41": "Punch",  # outcome: 1
    "42": "Good skill",  # outcome: 1
    "43": "Deleted event",  # outcome: 1
    "44": "Aerial",  # outcome: 0 - player lost aerial duel, 1 - player won the aerial duel
    "45": "Challenge",  # outcome: 0, unsuccessful challenge
    "47": "Rescinded card",  # outcome: 1
    "49": "Ball recovery",  # outcome: 1
    "50": "Dispossessed",  # outcome: 1
    "51": "Error",  # outcome: 1
    "52": "Keeper pick-up",  # outcome: 1
    "53": "Cross not claimed",  # outcome: 1
    "54": "Smother",  # outcome: 1
    "55": "Offside provoked",  # outcome: 1
    "56": "Shield ball opp",  # outcome: 1
    "57": "Foul throw-in",  # 0 - player who conceded the foul throw, 1 - player who won the foul throw
    "58": "Penalty faced",  # outcome: 0
    "59": "Keeper sweeper",
    # 0 - goalkeeper comes off the line and clears ball but possession switches to other team, 1 - goalkeepr comes off the line and either clears bal to another tam mate or ...
    "60": "Chance missed",  # outcome: 0
    "61": "Ball touch",  # 0 - player unsuccessfully controlled the ball, 1 - ball simply hit player unintentionally
    "63": "Temp_Save",  # # outcome: 1
    "64": "Resume",
    "65": "Contentious referee decision",
    "66": "Possession data",
    "67": "50/50",  # 0 - player lost 50/50 duel, 1 - player won 50/50 duel
    "68": "Referee Drop Ball",  # outcome: 1
    "69": "Failed to Block",  # outcome: 1
    "70": "Injury Time Announcement",  # outcome: 1
    "71": "Coach Setup",  # outcome: 1
    "72": "Caught Offside",  # outcome: 1
    "73": "Other Ball Contact",  # outcome: 1
    "74": "Blocked Pass",
    "75": "Delayed Start",
    "76": "Early end",
    "77": "Player Off Pitch",
    "79": "Coverage Interruption",
    "80": "Assist",
    "81": "First touch assist",
    "83": "Key pass dribble",
    "84": "Key pass",
    "85": "Chances set play",
    "86": "Chances open play",
    "87": "First touch key pass",
    "90": "Shot against",
    "92": "Goal against",
    "94": "Shot on target against",
    "96": "Cross against",
    "101": "Clean sheet"
}


class Events:
    ID_1_Pass_Events = {"typeID": "1", "name": "Pass"}
    ID_2_Offside_Pass = {"typeID": "2", "name": "Offside Pass"}
    ID_3_Take_On = {"typeID": "2", "name": "Take On"}
    ID_4_Foul = {"typeID": "3", "name": "Foul"}
    ID_5_Out = {"typeID": "4", "name": "Out"}
    ID_6_Corner_Awarded = {"typeID": "5", "name": "Corner Awarded"}
    ID_7_Tackle = {"typeID": "6", "name": "Tackle"}
    ID_8_Interception = {"typeID": "7", "name": "Interception"}
    ID_9_Turnover = {"typeID": "8", "name": "Turnover"}
    ID_10_Save = {"typeID": "9", "name": "Save"}
    ID_11_Claim = {"typeID": "10", "name": "Claim"}
    ID_12_Clearance = {"typeID": "11", "name": "Clearance"}
    ID_13_Miss = {"typeID": "12", "name": "Miss"}
    ID_14_Post = {"typeID": "13", "name": "Post"}
    ID_15_Attempt_Saved = {"typeID": "14", "name": "Attempt Saved"}
    ID_16_Goal = {"typeID": "15", "name": "Goal"}
    ID_17_Card = {"typeID": "16", "name": "Goal"}
    ID_18_Player_Off = {"typeID": "17", "name": "Player Off"}
    ID_19_Player_on = {"typeID": "18", "name": "Player on"}
    ID_20_Player_retired = {"typeID": "19", "name": "Player retired"}
    ID_21_Player_returns = {"typeID": "20", "name": "Player returns"}
    ID_22_Player_becomes_goalkeeper = {
        "typeID": "21",
        "name": "Player becomes goalkeeper",
    }
    ID_23_Goalkeeper_becomes_player = {"typeID": "22", "name": "Player becomes player"}
    ID_24_Condition_change = {"typeID": "23", "name": "Condition change"}
    ID_25_Official_change = {"typeID": "24", "name": "Official change"}
    ID_27_Start_delay = {"typeID": "27", "name": "Start delay"}
    ID_28_End_delay = {"typeID": "28", "name": "End delay"}
    ID_30_End = {"typeID": "30", "name": "Official change"}
    ID_32_Start = {"typeID": "32", "name": "Start"}
    ID_34_Team_set_up = {"typeID": "34", "name": "Team set up"}
    ID_35_Player_changed_position = {"typeID": "35", "name": "Player changed position"}
    ID_36_Player_changed_jersey_number = {
        "typeID": "36",
        "name": "Player changed jersey number",
    }
    ID_37_Collection_End = {"typeID": "37", "name": "Collection End"}
    ID_38_Temp_Goal = {"typeID": "38", "name": "Temp_Goal"}
    ID_39_Temp_Attempt = {"typeID": "39", "name": "Temp_Attempt"}
    ID_40_Formation_change = {"typeID": "40", "name": "change"}
    ID_41_Punch = {"typeID": "41", "name": "Punch"}
    ID_42_Good_skill = {"typeID": "42", "name": "Good skill"}
    ID_43_Deleted_event = {"typeID": "43", "name": "Deleted event"}
    ID_44_Aerial = {"typeID": "44", "name": "Aerial"}
    ID_45_Challenge = {"typeID": "45", "name": "Challenge"}
    ID_47_Rescinded_card = {"typeID": "47", "name": "Rescinded card"}
    ID_49_Ball_recovery = {"typeID": "49", "name": "Ball recovery"}
    ID_50_Dispossessed = {"typeID": "50", "name": "Dispossessed"}
    ID_51_Error = {"typeID": "51", "name": "Error"}
    ID_52_Keeper_pick_up = {"typeID": "52", "name": "Keeper pick-up"}
    ID_53_Cross_not_claimed = {"typeID": "53", "name": "Cross not claimed"}
    ID_54_Smother = {"typeID": "54", "name": "Smother"}
    ID_55_Offside_provoked = {"typeID": "55", "name": "Offside provoked"}
    ID_56_Shield_ball_opp = {"typeID": "56", "name": "Shield ball opp"}
    ID_57_Foul_throw_in = {"typeID": "57", "name": "Foul throw-in"}
    ID_58_Penalty_faced = {"typeID": "58", "name": "Penalty faced"}
    ID_59_Keeper_sweeper = {"typeID": "59", "name": "Keeper sweeper"}
    ID_60_Chance_missed = {"typeID": "60", "name": "Chance missed"}
    ID_61_Ball_touch = {"typeID": "61", "name": "Ball touch"}
    ID_63_Temp_Save = {"typeID": "63", "name": "Temp_Save"}
    ID_64_Resume = {"typeID": "64", "name": "Resume"}
    ID_65_Contentious_referee_decision = {
        "typeID": "65",
        "name": "Contentious referee decision",
    }
    ID_66_Possession_data = {"typeID": "66", "name": "Possession data"}
    ID_67_50_50 = {"typeID": "67", "name": "50/50"}
    ID_68_Referee_Drop_Ball = {"typeID": "68", "name": "Referee Drop Ball"}
    ID_69_Failed_to_Block = {"typeID": "69", "name": "Failed to Block"}
    ID_70_Injury_Time_Announcement = {
        "typeID": "70",
        "name": "Injury Time Announcement",
    }
    ID_71_Coach_Setup = {"typeID": "71", "name": "Coach Setup"}
    ID_72_Caught_Offside = {"typeID": "72", "name": "Caught Offside"}
    ID_73_Other_Ball_Contact = {"typeID": "73", "name": "Other Ball Contact"}
    ID_74_Blocked_Pass = {"typeID": "74", "name": "Blocked Pass"}
    ID_75_Delayed_Start = {"typeID": "75", "name": "Delayed Start"}
    ID_76_Early_end = {"typeID": "76", "name": "Early end"}
    ID_77_Player_Off_Pitch = {"typeID": "77", "name": "Player Off Pitch"}
    ID_79_Coverage_Interruption = {"typeID": "79", "name": "Coverage Interruption"}


class EventIDs:
    # event completion is successful or not
    SUCCESSFUL = 1
    UNSUCCESSFUL = 0

    # multi event definitions
    ALL = "ALLEVENTS"
    AerialDuelEvents = "AerialDuelEvents"
    AssistEvents = "AssistEvents"
    BallControlEvents = "BallControlEvents"
    CardEvents = "CardEvents"
    DuelEvents = "DuelEvents"
    FoulEvents = "FoulEvents"
    GamesandMinutesEvents = "GamesandMinutesEvents"
    GoalkeeperEvents = "GoalkeeperEvents"
    PassEvents = "PassEvents"
    ShotandGoalEvents = "ShotandGoalEvents"
    TakeOnEvents = "TakeOnEvents"
    TouchEvents = "TouchEvents"
    EventMinutes = "EventMinutes"

    # single event definitions

    ID_1_Pass_Events = 1
    ID_2_Offside_Pass = 2
    ID_3_Take_On = 3
    ID_4_Foul = 4
    ID_5_Out = 5
    ID_6_Corner_Awarded = 6
    ID_7_Tackle = 7
    ID_8_Interception = 8
    ID_9_Turnover = 9
    ID_10_Save = 10
    ID_11_Claim = 11
    ID_12_Clearance = 12
    ID_13_Miss = 13
    ID_14_Post = 14
    ID_15_Attempt_Saved = 15
    ID_16_Goal = 16
    ID_17_Card = 17
    ID_18_Player_Off = 18
    ID_19_Player_on = 19
    ID_20_Player_retired = 20
    ID_21_Player_returns = 21
    ID_22_Player_becomes_goalkeeper = 22
    ID_23_Goalkeeper_becomes_player = 23
    ID_24_Condition_change = 24
    ID_25_Official_change = 25
    ID_27_Start_delay = 27
    ID_28_End_delay = 28
    ID_30_End = 30
    ID_32_Start = 32
    ID_34_Team_set_up = 34
    ID_35_Player_changed_position = 35
    ID_36_Player_changed_jersey_number = 36
    ID_37_Collection_End = 37
    ID_38_Temp_Goal = 38
    ID_39_Temp_Attempt = 39
    ID_40_Formation_change = 40
    ID_41_Punch = 41
    ID_42_Good_skill = 42
    ID_43_Deleted_event = 43
    ID_44_Aerial = 44
    ID_45_Challenge = 45
    ID_47_Rescinded_card = 47
    ID_49_Ball_recovery = 49
    ID_50_Dispossessed = 50
    ID_51_Error = 51
    ID_52_Keeper_pick_up = 52
    ID_53_Cross_not_claimed = 53
    ID_54_Smother = 54
    ID_55_Offside_provoked = 55
    ID_56_Shield_ball_opp = 56
    ID_57_Foul_throw_in = 57
    ID_58_Penalty_faced = 58
    ID_59_Keeper_sweeper = 59
    ID_60_Chance_missed = 60
    ID_61_Ball_touch = 61
    ID_63_Temp_Save = 63
    ID_64_Resume = 64
    ID_65_Contentious_referee_decision = 65
    ID_66_Possession_data = 66
    ID_67_50_50 = 67
    ID_68_Referee_Drop_Ball = 68
    ID_69_Failed_to_Block = 69
    ID_70_Injury_Time_Announcement = 70
    ID_71_Coach_Setup = 71
    ID_72_Caught_Offside = 72
    ID_73_Other_Ball_Contact = 73
    ID_74_Blocked_Pass = 74
    ID_75_Delayed_Start = 75
    ID_76_Early_end = 76
    ID_77_Player_Off_Pitch = 77
    ID_79_Coverage_Interruption = 79
    ID_Ball_Control = 1000  # todo: the number is not important here
    # NEW EVENTS
    ID_80_Assist = 80
    ID_81_First_Touch_Assist = 81
    ID_83_Key_Pass_Dribble = 83
    ID_84_Key_Pass = 84
    ID_85_Chances_Set_Play = 85
    ID_86_Chances_Open_Play = 86
    ID_87_First_Touch_Key_Pass = 87
    ID_90_Shot_Against = 90
    ID_92_Goal_Against = 92
    ID_94_Shot_On_Target_Against = 94
    ID_96_Crosses_Against = 96
    ID_101_Clean_Sheet = 101


# find an item in the class an get its key
class EventTypesHelper:
    def __init__(self):
        self.event_types = EventTypes

    def getEventNumber(self, eventName):
        for (
                number,
                value,
        ) in (
                self.event_types.items()
        ):  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if value == eventName:
                print(number)
                return number

    def getEventName(self, eventNumber):
        for (
                number,
                value,
        ) in (
                self.event_types.items()
        ):  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if number == eventNumber:
                print(value)
                return value


class Event:
    def __init__(self):
        print()


Event_QTypes = {
    "1": {
        1,
        2,
        4,
        5,
        6,
        15,
        22,
        23,
        25,
        26,
        29,
        31,
        55,
        56,
        96,
        97,
        106,
        107,
        123,
        124,
        138,
        140,
        141,
        152,
        154,
        155,
        156,
        157,
        160,
        168,
        195,
        196,
        198,
        199,
        210,
        212,
        213,
        214,
        218,
        223,
        224,
        225,
        236,
        237,
        238,
        240,
        241,
        266,
        278,
        279,
        287,
        307,
    },
    "2": {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        23,
        55,
        56,
        107,
        123,
        124,
        140,
        141,
        152,
        241,
        297,
        298,
        307,
    },
    "3": {56, 211, 285, 286, 307, 312},
    "4": {
        9,
        10,
        11,
        12,
        13,
        34,
        40,
        56,
        95,
        132,
        152,
        184,
        241,
        242,
        264,
        265,
        285,
        286,
        289,
        294,
        295,
        296,
        307,
        313,
    },
    "5": {56},
    "6": {56, 73, 219, 220, 221, 222},
    "7": {14, 56, 167, 285, 286, 307, 312},
    "8": {13, 14, 15, 31, 32, 56, 307, 312},
    "9": {},
    "10": {
        1,
        2,
        9,
        14,
        15,
        17,
        21,
        25,
        29,
        55,
        56,
        82,
        88,
        90,
        91,
        92,
        93,
        94,
        101,
        102,
        103,
        137,
        139,
        173,
        174,
        175,
        176,
        177,
        178,
        179,
        180,
        181,
        182,
        183,
        190,
        239,
        267,
        268,
        269,
        270,
        271,
        272,
        273,
        274,
        275,
        284,
        307,
        312,
    },
    "11": {1, 2, 56, 88, 307, 312},
    "12": {1, 2, 14, 15, 56, 91, 128, 167, 185},
    "13": {
        1,
        2,
        9,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        29,
        55,
        56,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        83,
        84,
        85,
        86,
        87,
        89,
        96,
        97,
        100,
        102,
        103,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        115,
        116,
        117,
        118,
        119,
        120,
        121,
        122,
        133,
        137,
        146,
        147,
        153,
        154,
        160,
        188,
        214,
        215,
        249,
        250,
        251,
        252,
        253,
        263,
        266,
        276,
        307,
        314,
    },
    "14": {
        5,
        9,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        29,
        55,
        56,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        81,
        89,
        96,
        97,
        102,
        103,
        108,
        109,
        111,
        112,
        113,
        114,
        116,
        117,
        118,
        119,
        120,
        121,
        122,
        133,
        146,
        147,
        154,
        160,
        214,
        215,
        230,
        231,
        249,
        250,
        251,
        252,
        253,
        263,
        266,
        307,
    },
    "15": {
        1,
        2,
        9,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        29,
        55,
        56,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        83,
        84,
        85,
        86,
        87,
        89,
        96,
        97,
        100,
        101,
        102,
        103,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        115,
        116,
        117,
        118,
        119,
        120,
        121,
        122,
        133,
        138,
        139,
        146,
        147,
        154,
        160,
        192,
        214,
        215,
        249,
        250,
        251,
        252,
        253,
        263,
        266,
        284,
        301,
        307,
        314,
    },
    "16": {
        2,
        9,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        28,
        29,
        40,
        55,
        56,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        83,
        84,
        85,
        86,
        87,
        89,
        96,
        97,
        102,
        103,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        117,
        118,
        119,
        120,
        121,
        122,
        133,
        136,
        138,
        146,
        147,
        216,
        217,
        230,
        231,
        249,
        250,
        251,
        252,
        253,
        254,
        261,
        262,
        263,
        266,
        280,
        281,
        282,
        300,
        307,
    },
    "17": {
        10,
        11,
        12,
        13,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        56,
        95,
        132,
        158,
        159,
        161,
        162,
        163,
        164,
        165,
        166,
        171,
        172,
        184,
        191,
        243,
        244,
        245,
        283,
    },
    "18": {41, 42, 44, 55, 59, 83, 227},
    "19": {41, 42, 44, 55, 59, 145, 227},
    "20": {},
    "21": {45},
    "22": {},
    "23": {44},
    "24": {45, 46, 47, 48, 49, 255, 256, 257, 258, 259, 260},
    "25": {50, 51},
    "27": {41, 53, 200, 201, 202, 203, 204, 205, 206, 207, 208, 246, 299, 303},
    "28": {299},
    "30": {54, 57, 209, 226, 227, 308, 309},
    "32": {127},
    "34": {30, 44, 59, 130, 131, 194, 197, 227},
    "35": {44},
    "36": {59},
    "37": {229},
    "38": {9, 16, 17, 18, 19, 22, 26, 56, 60, 61, 62, 63, 64, 65, 66, 69, 70, 71},
    "39": {
        9,
        16,
        17,
        18,
        19,
        20,
        22,
        26,
        56,
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
    },
    "40": {30, 44, 59, 130, 131, 227},
    "41": {56, 307},
    "42": {56, 307},
    "43": {},
    "44": {9, 13, 55, 56, 285, 286},
    "45": {31, 56, 285, 286},
    "47": {13, 31, 32, 33, 34},
    "49": {14, 56},
    "50": {56, 307},
    "51": {169, 170},
    "52": {},
    "53": {},
    "54": {232, 285, 286, 307, 312},
    "55": {},
    "56": {56},
    "57": {56},
    "58": {9, 56, 73, 75, 138, 178, 179, 186, 187, 188},
    "59": {56},
    "60": {55, 56, 89, 154},
    "61": {56, 138, 228, 238, 307},
    "63": {56, 173, 178, 182},
    "64": {},
    "65": {9, 26, 33, 40, 167, 247, 248},
    "66": {234, 235, 288},
    "67": {285, 286},
    "68": {},
    "69": {285, 286},
    "70": {277},
    "71": {290},
    "72": {},
    "73": {291},
    "74": {56, 285, 233, 307, 312},
    "76": {54, 226, 227},
    "77": {41, 304, 305, 306, 310, 311},
}

# EVENT - Goal, Attempt Saved
# Qualifier #end_y #end_z
# todo: go ove the parameters below, turn them to a format like end_y: min, max (has a meaning of inbetween)
Goal_Attempt_Saved = {
    # "Low Left": {"end_y:51.8,54.8","end_z:0,20"}, example for inbetween
    "Low Left": {"51.8 <= end_y <= 54.8", "0 <= end_z <= 20"},
    "High Left": {"51.8 <= end_y <= 54.8", "20 <= end_z <= 38"},
    "Low Centre": {"48.2 <= end_y <= 51.8", "0 <= end_z <= 20"},
    "High Centre": {"48.2 <= end_y <= 51.8", "20 <= end_z <= 38"},
    "Low Right": {"45.2 <= end_y <= 48.2", "0 <= end_z <= 20"},
    "High Right": {"45.2 <= end_y <= 48.2", "20 <= end_z <= 38"},
}

Post = {
    "Left": {"54.8 <= end_y <= 55.8", "0 <= end_z <= 38"},
    "High": {"44.2 <= end_y <= 55.8", "38 <= end_z <= 42"},
    "Right": {"44.2 <= end_y <= 45.2", "0 <= end_z <= 38"},
}

Miss = {
    "Close left": {"55.8 <= end_y <= 59.3", "0 <= end_z <= 40"},
    "Close High Left": {"55.8 <= end_y <= 59.3", "40 <= end_z <= 60"},
    "Close Right": {"40.7 <= end_y <= 44.2", "0 <= end_z <= 40"},
    "Close High Right": {"40.7 <= end_y <= 44.2", "40 <= end_z <= 60"},
    "Close High": {"44.2 <= end_y <= 55.8", "42 <= end_z <= 60"},
    "Left": {"59.3 <= end_y <= 100", "0 <= end_z <= 40"},
    "Right": {"0 <= end_y <= 40.7", "0 <= end_z <= 40"},
    "HighLeft": {"55.8 <= end_y <= 100", "60 <= end_z <= 100"},
    "HighRight": {"0 <= end_y <= 44.2", "60 <= end_z <= 100"},
    "High": {"44.2 <= end_y <= 55.8", "60 <= end_z <= 100"},
}

Team_Formation = {
    "1": "not in use",
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
    "14": "not in use",
    "15": "4222",
    "16": "3511",
    "17": "3421",
    "18": "3412",
    "19": "3142",
    "20": "343d",  # (Diamond) ?
    "21": "4132",
    "22": "4240",
    "23": "4312",
    "24": "3241",
    "25": "3331",
}

EventIdList = {
    "AerialDuelEvents": [EventIDs.ID_44_Aerial, EventIDs.ID_4_Foul],

    "AssistEvents": [EventIDs.ID_80_Assist, EventIDs.ID_81_First_Touch_Assist, EventIDs.ID_83_Key_Pass_Dribble,
                     EventIDs.ID_84_Key_Pass, EventIDs.ID_85_Chances_Set_Play,
                     EventIDs.ID_86_Chances_Open_Play, EventIDs.ID_87_First_Touch_Key_Pass],

    "BallControlEvents": [EventIDs.ID_50_Dispossessed, EventIDs.ID_51_Error,
                          EventIDs.ID_61_Ball_touch, EventIDs.ID_2_Offside_Pass],

    "CardEvents": [EventIDs.ID_17_Card],

    "DuelEvents": [EventIDs.ID_44_Aerial, EventIDs.ID_3_Take_On, EventIDs.ID_4_Foul,
                   EventIDs.ID_7_Tackle, EventIDs.ID_54_Smother, EventIDs.ID_45_Challenge,
                   EventIDs.ID_50_Dispossessed],

    "FoulEvents": [EventIDs.ID_4_Foul],

    "GamesandMinutesEvents": [EventIDs.ID_34_Team_set_up, EventIDs.ID_18_Player_Off,
                              EventIDs.ID_19_Player_on, EventIDs.ID_17_Card],

    "GoalkeeperEvents": [EventIDs.ID_10_Save, EventIDs.ID_11_Claim, EventIDs.ID_41_Punch,
                         EventIDs.ID_52_Keeper_pick_up, EventIDs.ID_54_Smother, EventIDs.ID_1_Pass_Events,
                         EventIDs.ID_59_Keeper_sweeper, EventIDs.ID_53_Cross_not_claimed,
                         EventIDs.ID_58_Penalty_faced, EventIDs.ID_90_Shot_Against,
                         EventIDs.ID_92_Goal_Against, EventIDs.ID_94_Shot_On_Target_Against,
                         EventIDs.ID_96_Crosses_Against, EventIDs.ID_101_Clean_Sheet],

    "PassEvents": [EventIDs.ID_74_Blocked_Pass, EventIDs.ID_1_Pass_Events],

    "ShotandGoalEvents": [EventIDs.ID_16_Goal, EventIDs.ID_13_Miss, EventIDs.ID_14_Post,
                          EventIDs.ID_15_Attempt_Saved, EventIDs.ID_60_Chance_missed, EventIDs.ID_3_Take_On],

    "TakeOnEvents": [EventIDs.ID_3_Take_On],

    "TouchEvents": [EventIDs.ID_1_Pass_Events, EventIDs.ID_2_Offside_Pass, EventIDs.ID_3_Take_On,
                    EventIDs.ID_4_Foul, EventIDs.ID_7_Tackle, EventIDs.ID_10_Save, EventIDs.ID_12_Clearance,
                    EventIDs.ID_16_Goal, EventIDs.ID_13_Miss, EventIDs.ID_14_Post, EventIDs.ID_15_Attempt_Saved,
                    EventIDs.ID_42_Good_skill, EventIDs.ID_50_Dispossessed, EventIDs.ID_61_Ball_touch,
                    EventIDs.ID_73_Other_Ball_Contact, EventIDs.ID_74_Blocked_Pass, EventIDs.ID_45_Challenge,
                    EventIDs.ID_49_Ball_recovery, EventIDs.ID_55_Offside_provoked],

    "EventMinutes": [EventIDs.ID_16_Goal, EventIDs.ID_17_Card, EventIDs.ID_18_Player_Off,
                     EventIDs.ID_19_Player_on, EventIDs.ID_30_End]
}


event_names_statistics = [
            "aerial",
            "aerial_event",
            "pass",
            "pass_event",
            "foul",
            "foul_event",
            "card",
            "card_event",
            "ballControl",
            "ballControl_event",
            "takeOn",
            "takeOn_event",
            "takeon",
            "touch",
            "touch_event",
            "duel",
            "duel_event",
            "shot",
            "shotand_goal_event",
            "assist",
            "assist_event",
            "goalkeeper",
            "goalkeeper_event",
            "minutes",
            "minutes_event"
        ]
