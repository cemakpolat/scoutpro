# This class checks the following Opta F24 Assist events:
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *
from src.events.QTypes import QTypes


class AssistEvents:
    def __init__(self):
        # simple ball control event counters
        self.total_assists = 0
        self.assists_from_open_play = 0
        self.assists_from_free_kick = 0
        self.assists_from_goal_kick = 0
        self.assists_from_corners = 0
        self.assists_from_set_play = 0
        self.assists_from_throw_in = 0
        self.intentional_assists = 0
        self.open_play_assist_rate = 0
        self.assist_and_key_passes = 0
        self.key_pass_corner = 0
        self.key_pass_free_kick = 0
        self.key_pass_goal_kick = 0
        self.key_pass_throw_in = 0
        self.key_passes = 0
        self.key_passes_after_dribble = 0
        self.total_take_ons = 0
        self.assist_for_first_touch_goal = 0
        self.chances_created_from_set_play = 0
        self.chances_created_from_open_play = 0
        self.keypass_for_first_touch_shot = 0
        self.minutes_per_chance = 0

        self.event_results = {}
        self.x = 0
        self.y = 0
        # Add to excel
        self.data = []

    def callEventHandler(self, data, print_results=False):

        teamID = data["teamID"]
        if not isinstance(teamID, list):
            teamID = [int(teamID)]

        playerID = data["playerID"]
        if isinstance(playerID, str) or isinstance(playerID, int):
            playerID = [int(playerID)]

        events = data["events"]
        total_minutes = data["total_minutes"]

        for event in events:
            try:
                temp_player_id = int(event.playerID)
                temp_team_id = int(event.teamID)
            except (AttributeError, ValueError, TypeError):
                continue

            if temp_player_id in playerID and temp_team_id in teamID:
                typeID = int(event.typeID)
                if typeID == EventIDs.ID_80_Assist:
                    self.total_assists += 1
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(int(q.qualifierID))
                    if (
                            QTypes.ID_22 in qualifier_list
                            or QTypes.ID_23 in qualifier_list
                    ):
                        self.assists_from_open_play += 1
                        self.chances_created_from_open_play += 1
                    if (
                            QTypes.ID_24 in qualifier_list
                            or QTypes.ID_25 in qualifier_list
                            or QTypes.ID_26 in qualifier_list
                            or QTypes.ID_160 in qualifier_list
                    ):
                        self.assists_from_set_play += 1
                        self.chances_created_from_set_play += 1
                    if QTypes.ID_24 in qualifier_list:
                        self.assists_from_free_kick += 1
                    if QTypes.ID_25 in qualifier_list:
                        self.assists_from_corners += 1
                    if QTypes.ID_107 in qualifier_list:
                        self.assists_from_throw_in += 1
                    if QTypes.ID_124 in qualifier_list:
                        self.assists_from_goal_kick += 1
                    if QTypes.ID_154 in qualifier_list:
                        self.intentional_assists += 1

                elif typeID == EventIDs.ID_81_First_Touch_Assist:
                    self.assist_for_first_touch_goal += 1

                elif typeID == EventIDs.ID_83_Key_Pass_Dribble:
                    self.key_passes_after_dribble += 1

                elif typeID == EventIDs.ID_84_Key_Pass:
                    self.key_passes += 1
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(int(q.qualifierID))
                    if QTypes.ID_5 in qualifier_list:
                        self.key_pass_free_kick += 1
                    if QTypes.ID_6 in qualifier_list:
                        self.key_pass_corner += 1
                    if QTypes.ID_107 in qualifier_list:
                        self.key_pass_throw_in += 1
                    if QTypes.ID_124 in qualifier_list:
                        self.key_pass_goal_kick += 1

                elif typeID == EventIDs.ID_85_Chances_Set_Play:
                    self.chances_created_from_set_play += 1

                elif typeID == EventIDs.ID_86_Chances_Open_Play:
                    self.chances_created_from_open_play += 1

                elif typeID == EventIDs.ID_87_First_Touch_Key_Pass:
                    self.keypass_for_first_touch_shot += 1

        self.assist_and_key_passes = self.total_assists + self.key_passes
        self.keypass_for_first_touch_shot = (
            self.keypass_for_first_touch_shot + self.assist_for_first_touch_goal
        )
        if self.total_assists != 0:
            self.open_play_assist_rate = round(
                (100 * float(self.assists_from_open_play / self.total_assists)), 2
            )
        if total_minutes:
            if self.assist_and_key_passes != 0:
                self.minutes_per_chance = round(
                    (float(total_minutes / self.assist_and_key_passes)), 2
                )

        if print_results:
            self.printResults()
        self.saveResults()

        return self.event_results

    def printResults(self):
        print("----- Assist ----")
        print("total assists: " + str(self.total_assists))
        print("total intentional assists: " + str(self.intentional_assists))
        print("total assists from open play: " + str(self.assists_from_open_play))
        print("open play assist percentage: " + str(self.open_play_assist_rate))
        print("total assists from set play: " + str(self.assists_from_set_play))
        print("total assists from free kicks: " + str(self.assists_from_free_kick))
        print("total assists from corners: " + str(self.assists_from_corners))
        print("total assists from throw in: " + str(self.assists_from_throw_in))
        print("total assists from goal kick: " + str(self.assists_from_goal_kick))
        print(
            "total assists for first touch goals: "
            + str(self.assist_for_first_touch_goal)
        )
        print("total assists and key passes: " + str(self.assist_and_key_passes))
        print("total key passes: " + str(self.key_passes))
        print("total key passes from free kicks: " + str(self.key_pass_free_kick))
        print("total key passes from corners: " + str(self.key_pass_corner))
        print("total key passes from throw in: " + str(self.key_pass_throw_in))
        print("total key passes from goal kick: " + str(self.key_pass_goal_kick))
        # print("total key passes following a dribble: " + str(self.key_passes_after_dribble))
        print(
            "total key passes from set play: " + str(self.chances_created_from_set_play)
        )
        print(
            "total key passes from open play: "
            + str(self.chances_created_from_open_play)
        )
        print(
            "total key passes for first touch shot: "
            + str(self.keypass_for_first_touch_shot)
        )
        print("minutes per chance: " + str(self.minutes_per_chance))

    def saveResults(self):

        print("save results method is called")
        self.event_results["total assists"] = self.total_assists
        self.event_results["total intentional assists"] = self.intentional_assists
        self.event_results["total assists from open play"] = self.assists_from_open_play
        self.event_results["open play assist percentage"] = self.open_play_assist_rate
        self.event_results["total assists from set play"] = self.assists_from_set_play
        self.event_results[
            "total assists from free kicks"
        ] = self.assists_from_free_kick
        self.event_results["total assists from corners"] = self.assists_from_corners
        self.event_results["total assists from throw in"] = self.assists_from_throw_in
        self.event_results["total assists from goal kicks"] = self.assists_from_goal_kick
        self.event_results["total assists for first touch goals"] = self.assist_for_first_touch_goal
        self.event_results["total assists and key passes"] = self.assist_and_key_passes
        self.event_results["total key passes"] = self.key_passes
        self.event_results["total key passes from free kicks"] = self.key_pass_free_kick
        self.event_results["total key passes from corners"] = self.key_pass_corner
        self.event_results["total key passes from throw ins"] = self.key_pass_throw_in
        self.event_results["total key passes from goal kicks"] = self.key_pass_goal_kick
        self.event_results["total key passes from set plays"] = self.chances_created_from_set_play
        self.event_results["total key passes from open plays"] = self.chances_created_from_open_play
        self.event_results["total key passes following a dribble"] = self.key_passes_after_dribble
        self.event_results["total key passes for first touch shot"] = self.keypass_for_first_touch_shot
        self.event_results["minutes per chance"] = self.minutes_per_chance

        # PlayerStatistics.writeInExcell(self.eventType, self.event_results)

    def getDataFram(self):
        self.data = [
            ["total assists", self.total_assists],
            ["total intentional assists", self.intentional_assists],
            ["total assists from open play", self.assists_from_open_play],
            ["open play assist percentage", self.open_play_assist_rate],
            ["total assists from set play", self.assists_from_set_play],
            ["total assists from free kicks", self.assists_from_free_kick],
            ["total assists from corners", self.assists_from_corners],
            ["total assists from throw in", self.assists_from_throw_in],
            ["total assists from goal kicks", self.assists_from_goal_kick],
            ["total assists for first touch goals", self.assist_for_first_touch_goal],
            ["total assists and key passes", self.assist_and_key_passes],
            ["total key passes", self.key_passes],
            ["total key passes from free kicks", self.key_pass_free_kick],
            ["total key passes from corners", self.key_pass_corner],
            ["total key passes from throw ins", self.key_pass_throw_in],
            ["total key passes from goal kicks", self.key_pass_goal_kick],
            ["total key passes from set plays", self.chances_created_from_set_play],
            ["total key passes from open plays", self.chances_created_from_open_play],
            ["total key passes for first touch shot", self.keypass_for_first_touch_shot],
            ["minutes per chance", self.minutes_per_chance],
        ]

        # Create the pandas DataFrame
        # df = pd.DataFrame(self.data, columns=["", 'Total'])
