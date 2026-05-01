# class SB_LineUp(Document):
#     team_id = StringField(required=True, max_length=200)
#     team_name = StringField(required=True, max_length=200)
#     lineups = ListField(ReferenceField(SB_Player))
#
# class SB_Player(Document):
#     player_id = StringField(required=True, max_length=200)
#     player_name = StringField(required=True, max_length=200)
#     jersey_number = IntField(required=True)
#     country = IntField(required=True)
#     countryName = StringField( max_length=200)
#     player_nickname =StringField( max_length=200)
class Event:
    """
      "id":"3b32ec0b-3336-4821-a6b0-065c67470f47",
      "index":1,
      "period":1,
      "timestamp":"00:00:00.000",
      "minute":0,
      "second":0,
      "type":{
         "id":35,
         "name":"Starting XI"
      },
      "possession":1,
      "possession_team":{
         "id":762,
         "name":"Houston Dash"
      },
      "play_pattern":{
         "id":1,
         "name":"Regular Play"
      },
      "team":{
         "id":762,
         "name":"Houston Dash"
      },
      "duration":0.0,
      "tactics":{
         "formation":442,
         "lineup":[
            {
               "player":{
                  "id":5056,
                  "name":"Jane Campbell"
               },
               "position":{
                  "id":1,
                  "name":"Goalkeeper"
               },
               "jersey_number":1
            },
            {
               "player":{
                  "id":4959,
                  "name":"Taylor Comeau"
               },
               "position":{
                  "id":2,
                  "name":"Right Back"
               },
               "jersey_number":21
            },
            {
               "player":{
                  "id":5045,
                  "name":"Amber Brooks"
               },
               "position":{
                  "id":3,
                  "name":"Right Center Back"
               },
               "jersey_number":22
            },
            {
               "player":{
                  "id":8382,
                  "name":"Clare Polkinghorne"
               },
               "position":{
                  "id":5,
                  "name":"Left Center Back"
               },
               "jersey_number":8
            },
            {
               "player":{
                  "id":5038,
                  "name":"Allysha Chapman"
               },
               "position":{
                  "id":6,
                  "name":"Left Back"
               },
               "jersey_number":4
            },
            {
               "player":{
                  "id":5053,
                  "name":"Linda Maserame Motlhalo"
               },
               "position":{
                  "id":10,
                  "name":"Center Defensive Midfield"
               },
               "jersey_number":10
            },
            {
               "player":{
                  "id":5051,
                  "name":"Kealia Ohai"
               },
               "position":{
                  "id":13,
                  "name":"Right Center Midfield"
               },
               "jersey_number":7
            },
            {
               "player":{
                  "id":5039,
                  "name":"Veronica Latsko"
               },
               "position":{
                  "id":15,
                  "name":"Left Center Midfield"
               },
               "jersey_number":12
            },
            {
               "player":{
                  "id":5105,
                  "name":"Sofia Huerta"
               },
               "position":{
                  "id":19,
                  "name":"Center Attacking Midfield"
               },
               "jersey_number":23
            },
            {
               "player":{
                  "id":5043,
                  "name":"Nichelle Prince"
               },
               "position":{
                  "id":22,
                  "name":"Right Center Forward"
               },
               "jersey_number":14
            },
            {
               "player":{
                  "id":5058,
                  "name":"Rachel Daly"
               },
               "position":{
                  "id":24,
                  "name":"Left Center Forward"
               },
               "jersey_number":3
            }
         ]
      },
      "match_id":7494
    """


    """
    "ea3810fc-32d0-4e13-a5a0-1201f0507d11":{
      "id":"ea3810fc-32d0-4e13-a5a0-1201f0507d11",
      "index":3,
      "period":1,
      "timestamp":"00:00:00.000",
      "minute":0,
      "second":0,
      "type":{
         "id":18,
         "name":"Half Start"
      },
      "possession":1,
       "under_pressure":true,
      "possession_team":{
         "id":762,
         "name":"Houston Dash"
      },
      "play_pattern":{
         "id":1,
         "name":"Regular Play"
      },
      "team":{
         "id":767,
         "name":"Utah Royals"
      },
      "duration":0.0,
      "related_events":[
         "43628ea9-9928-4b9d-b143-6d48f7b3ee78"
      ],
       "carry":{
         "end_location":[
            63.0,
            74.0
         ]
      },
      "duel":{
         "type":{
            "id":10,
            "name":"Aerial Lost"
         }
      },
        "counterpress":true,
         "ball_receipt":{
         "outcome":{
            "id":9,
            "name":"Incomplete"
         }
      },
      "pass":{
         "recipient":{
            "id":5051,
            "name":"Kealia Ohai"
         },
         "length":22.472204,
         "angle":0.36397895,
         "height":{
            "id":3,
            "name":"High Pass"
         },
              "aerial_won":true,
         "end_location":[
            49.0,
            71.0
         ],
            "cross":true,
              "switch":true,
         "body_part":{
            "id":37,
            "name":"Head"
         },
         "type":{
            "id":66,
            "name":"Recovery"
         },
          "outcome":{
            "id":9,
            "name":"Incomplete"
         }
      },
      "match_id":7494
   }
   """
    def __init__(self):
        pass
class Season:
    def __init__(self, id, name):
        self.season_id = id
        self.season_name = name
class Country:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Competition:
    """
    "Champions League",
   "2016/2017",
   "male"")":{
      "competition_id":16,
      "season_id":2,
      "country_name":"Europe",
      "competition_name":"Champions League",
      "competition_gender":"male",
      "season_name":"2016/2017",
      "match_updated":"2020-08-26T12:33:15.869622",
      "match_available":"2020-07-29T05:00"
   },
    """
    def __init__(self, id, co_name, comp_name):
        self.competition_id = id
        self.country_name = co_name
        self.competition_name = comp_name

class Manager:
    def __init__(self, id, name):
        self.id = id
        self.name =  name
        self.nickname= None
        self.dob: None
        self.country = None

class CompetitionStage:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Stadium:
    def __init__(self,id,name):
        self.id = id
        self.name = name
        self.country = None

class Referee:
    def __init__(self,id,name):
        self.id = id
        self.name = name

class Team:
    """
    "home_team":{
         "home_team_id":785,
         "home_team_name":"Croatia",
         "home_team_gender":"male",
         "home_team_group":"None",
         "country":{
            "id":56,
            "name":"Croatia"
         },
         "managers":[
            {
               "id":307,
               "name":"Zlatko Dalić",
               "nickname":"None",
               "dob":"None",
               "country":{
                  "id":56,
                  "name":"Croatia"
               }
            }
         ]
      },
      "away_team":{
         "away_team_id":776,
         "away_team_name":"Denmark",
         "away_team_gender":"male",
         "away_team_group":"None",
         "country":{
            "id":61,
            "name":"Denmark"
         },
         "managers":[
            {
               "id":641,
               "name":"Åge Fridtjof Hareide",
               "nickname":"Åge Hareide",
               "dob":"None",
               "country":{
                  "id":171,
                  "name":"Norway"
               }
            }
         ]
      },
    """
    def __init__(self,id,name,gender):
        self.team_id= id
        self.team_name= name
        self.team_gender= gender
        self.team_group= None
        self.country = None
        self.managers=[]
    def setFeature(self, featureName, featureValue):
        if featureName == "country":
            self.country = featureValue["id"]
            self.countryName = featureValue["name"]

class Match:
    """
    "match_id":7581,
      "match_date":"2018-07-01",
      "kick_off":"20:00:00.000",
      "competition":{
         "competition_id":43,
         "country_name":"International",
         "competition_name":"FIFA World Cup"
      },
      "season":{
         "season_id":3,
         "season_name":"2018"
      },
      "home_team":{
         "home_team_id":785,
         "home_team_name":"Croatia",
         "home_team_gender":"male",
         "home_team_group":"None",
         "country":{
            "id":56,
            "name":"Croatia"
         },
         "managers":[
            {
               "id":307,
               "name":"Zlatko Dalić",
               "nickname":"None",
               "dob":"None",
               "country":{
                  "id":56,
                  "name":"Croatia"
               }
            }
         ]
      },
      "away_team":{
         "away_team_id":776,
         "away_team_name":"Denmark",
         "away_team_gender":"male",
         "away_team_group":"None",
         "country":{
            "id":61,
            "name":"Denmark"
         },
         "managers":[
            {
               "id":641,
               "name":"Åge Fridtjof Hareide",
               "nickname":"Åge Hareide",
               "dob":"None",
               "country":{
                  "id":171,
                  "name":"Norway"
               }
            }
         ]
      },
     "home_score":1,
      "away_score":1,
      "match_status":"available",
      "match_status_360":"unscheduled",
      "last_updated":"2020-07-29T05:00",
      "last_updated_360":"None",
      "metadata":{
         "data_version":"1.0.2"
      },
      "match_week":4,
      "competition_stage":{
         "id":33,
         "name":"Round of 16"
      },
      "stadium":{
         "id":4263,
         "name":"Stadion Nizhny Novgorod",
         "country":{
            "id":188,
            "name":"Russia"
         }
      },
      "referee":{
         "id":730,
         "name":"N. Pitana"
      }
    """
    def __init__(self,mid, mdate,ko):
        self.match_id = mid
        self.match_data = mdate
        self.kick_off = ko
        self.competion = None
        self.season = None
        self.home_team = None
        self.away_team = None
        self.home_score = None
        self.away_score = None
        self.match_status = None
        self.match_status_360 = None
        self.last_updated = None
        self.last_updated_360 = None
        self.metdata = None
        self.match_week = None
        self.competion_state = None
        self.stadium = None
        self.referee = None
    def setFeature(self, featureName, featureValue):
        if featureName == "country":
            self.country = featureValue["id"]
            self.countryName = featureValue["name"]

class Player:
    def __init__(self, pid, name):
        self.player_id = pid
        self.player_name = name
        self.jersey_number = None
        self.country = None
        self.countryName = None
        self.player_nickname = None

    def setFeature(self, featureName, featureValue):
        if featureName == "country":
            self.country = featureValue["id"]
            self.countryName = featureValue["name"]
        elif featureName == "player_nickname":
            self.name = featureValue
        elif featureName == "jersey_number":
            self.jersey_number = featureValue
        return self

    def to_string(self):
        return {"player_id":self.player_id,"player_name":self.player_name,"jersey_number":self.jersey_number, "country":self.countryName}

class LineUp:
    def __init__(self, tid, tname):
        self.team_id = tid
        self.team_name = tname
        self.lineup = []

    def add_players(self, data):
        for player in data:
            player = Player(player["player_id"], player["player_name"]).setFeature("jersey_number",player["jersey_number"]).\
                setFeature("country",player["country"]).setFeature("player_nickname",player["player_nickname"])
            self.lineup.append(player)