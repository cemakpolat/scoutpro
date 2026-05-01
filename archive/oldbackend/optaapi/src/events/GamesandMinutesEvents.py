# This class checks the following Opta F24 events:
#     "17":"Cards"
# author: Doruk Sahinel, Cem Akpolat

from src.events.Events import *
from src.events.QTypes import *
import pandas as pd


class GamesandMinutesEvents:
    def __init__(self):

        self.games_played = 0
        self.games_started = 0
        self.total_minutes = 0
        self.actual_minutes_on_field = 0
        self.minutes_per_game = 0
        self.substitute_off = 0
        self.substitute_on = 0
        self.age_at_match_time = 0

        self.player_off = 0
        self.player_on = 0
        self.player_retired = 0
        self.player_changed_position = 0
        self.team_setup = 0
        self.formation = 0
        self.player_in_game = 0
        self.player_starting11 = 0
        self.substitute = 0
        self.player_injured = 0
        self.tactical_substitution = 0
        self.player_position = str(0)
        self.player_substitute = 0
        self.player_counter = 0
        self.total90 = 0
        self.total_on = 0
        self.total_off = 0
        self.total_off_sec = 0
        self.total_on_sec = 0
        self.second_yellow_card = 0
        self.second_yellow_card_min = 0
        self.red_card = 0
        self.red_card_min = 0
        self.not_played = 0
        self.InGame = None

        self.exact_position = []
        self.formations_played = []
        self.positions_played = []

        self.formations = {
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
        self.formations_played = []
        self.event_results = {}

        self.all_players_in_game = set()

    def determine_all_players_in_game(self, events: list, team_id: int):
        self.all_players_in_game = set()
        for event in events:
            if event.typeID == EventIDs.ID_34_Team_set_up and event.teamID == team_id:
                for q in event.qEvents:
                    if q.qualifierID == QTypes.ID_30:
                        lineup = q.value.split(",")
                        for temp_player_id in lineup:
                            self.all_players_in_game.add(int(temp_player_id))

            elif event.typeID == EventIDs.ID_19_Player_on:
                self.all_players_in_game.add(event.playerID)

        result = dict()
        for player_id in self.all_players_in_game:
            temp_data = {
                "events": events,
                "teamID": team_id,
                "playerID": player_id,
            }
            temp_new_object = GamesandMinutesEvents()
            result[player_id] = temp_new_object.callEventHandler(data=temp_data)
        return result

    def callEventHandler(self, data, print_results=False):
        events = data["events"]
        team_id = data["teamID"]

        if "playerID" in data:
            player_key = data["playerID"]
        else:
            player_key = None

        if "playerName" in data:
            player_name = data["playerName"]
        else:
            player_name = None

        if player_key is None:
            return self.determine_all_players_in_game(
                events=events, team_id=team_id
            )

        for event in events:
            if event.typeID == EventIDs.ID_34_Team_set_up and event.teamID == team_id:
                for q in event.qEvents:
                    if q.qualifierID == QTypes.ID_30:
                        lineup = q.value.split(",")
                        for i in range(len(lineup)):
                            if player_key is None:
                                self.all_players_in_game.add(int(lineup[i]))
                            elif int(lineup[i]) == int(player_key):
                                self.InGame = True
                                # print("player found")
                                self.player_in_game += 1
                                player_counter = i + 1
                                self.exact_position.append(player_counter)
                                if i < 11:
                                    # print("player in starting 11")
                                    self.player_starting11 += 1
                                else:
                                    self.substitute += 1
                        if q.qualifierID == QTypes.ID_130:
                            formation = q.value.split(",")
                            formation_key = (
                                str(formation).strip("[").strip("]").replace("'", "")
                            )
                            for key, val in self.formations.items():
                                # print(" inside formation: " + str(val))
                                if key == formation_key:
                                    self.formations_played.append(val)
                                    self.formations_played.count(val)
                        if q.qualifierID == QTypes.ID_131:
                            pass
                self.InGame = False
                self.player_counter = 0
        for event in events:
            if event.playerID is None:
                continue
            if event.typeID == EventIDs.ID_18_Player_Off and event.playerID == int(player_key):
                # print("inside player off")
                self.player_off += 1
                if event.min >= 90:
                    self.total_off += 89
                else:
                    self.total_off += event.min
                    self.total_off_sec += event.min
                    if self.total_off_sec > 0:
                        self.total_off = self.total_off + 1
                for q in event.qEvents:
                    if q.qualifierID == str(41):
                        self.player_in_game += 1
                    if q.qualifierID == str(42):
                        self.tactical_substitution += 1

            if event.typeID == EventIDs.ID_19_Player_on and event.playerID == int(
                    player_key
            ):
                self.player_on += 1
                self.total_on += 90 - event.min
                self.total_on_sec += 60 - event.sec
                if self.total_on_sec > 0:
                    self.total_on = self.total_on - 1
                for q in event.qEvents:
                    if q.qualifierID == QTypes.ID_292:
                        pass
                        # print("player position ID is: ", q.value)
                    if q.qualifierID == QTypes.ID_293:
                        pass
                        # print("player position ID is: ", q.value)

            if event.typeID == EventIDs.ID_17_Card and event.playerID == int(
                    player_key
            ):
                for q in event.qEvents:
                    if q.qualifierID == QTypes.ID_32:
                        self.second_yellow_card += 1
                        if event.min >= 90:
                            self.second_yellow_card_min += 89
                        else:
                            self.second_yellow_card_min += event.min
                            self.total_off_sec += event.sec
                            if self.total_off_sec > 0:
                                self.second_yellow_card_min = self.second_yellow_card_min + 1
                    if q.qualifierID == QTypes.ID_33:
                        # print("Inside red card")
                        self.red_card += 1
                        if event.min >= 90:
                            self.red_card_min += 89
                        else:
                            self.red_card_min += event.min
                            self.total_off_sec += event.sec
                            if self.total_off_sec > 0:
                                self.red_card_min = self.red_card_min + 1

        # print("Player off:" + str(self.player_off))
        # print("Player on:" + str(self.player_on))
        games_played = self.player_starting11 + self.player_on
        self.total90 = (self.player_starting11 - self.player_off - self.red_card - self.second_yellow_card) * 90
        total_minutes = (
                self.total90 + self.red_card_min + self.second_yellow_card_min + self.total_on + self.total_off
        )  # + int(total_off_sec / 60) - int(total_on_sec / 60)

        player_total_games = dict()
        player_total_games["name"] = player_name
        player_total_games["player_id"] = player_key
        player_total_games["starting11"] = self.player_starting11
        player_total_games["used_sub"] = self.player_on
        player_total_games["games_played"] = games_played
        player_total_games["total_minutes"] = total_minutes

        self.event_results = player_total_games
        if print_results:
            self.printResults()
        return self.event_results

    def printResults(self):
        print("Games & Minutes")
        print("substitute on: " + str(self.substitute_on))
        print("substitute off: " + str(self.substitute_off))
        print("Formations played: ")
        print(self.formations_played)
        print("Positions played: ")
        print(self.positions_played)
        print("Exact Position: ")
        print(self.exact_position)
        print("Total 90: ")
        print(self.total90)
        print("red_card_min: ")
        print(self.red_card_min)
        print("second_yellow_card_min: ")
        print(self.second_yellow_card_min)
        print("total_on: ")
        print(self.total_on)
        print("total_off: ")
        print(self.total_off)

    def saveResults(self):
        print("save results method is called")

        self.event_results["substitute on"] = self.substitute_on
        self.event_results["substitute off"] = self.substitute_off
