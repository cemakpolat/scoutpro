# This class checks the following Opta F24 events:
#     "44":"Aerial Duels"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *

from src.events.QTypes import *
import pandas as pd


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

        # event coordinates
        self.total_aerial_duels = 0
        self.unsuccessful_aerial_duels = 0
        self.successful_aerial_duels = 0
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}
        self.playerId = ""
        self.eventType = "Duel"

    def callEventHandler(self, data, print_results=False):
        teamID = data["teamID"]
        if not isinstance(teamID, list):
            teamID = [int(teamID)]

        playerID = data["playerID"]
        if isinstance(playerID, str) or isinstance(playerID, int):
            playerID = [int(playerID)]

        events = data["events"]
        for event in events:
            try:
                temp_player_id = int(event.playerID)
                temp_team_id = int(event.teamID)
            except (AttributeError, ValueError, TypeError):
                continue

            if temp_player_id in playerID and temp_team_id in teamID:
                self.x = float(event.x)
                if event.typeID == EventIDs.ID_44_Aerial:
                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_285:
                            self.defensive_duels += 1
                        elif q.qualifierID == QTypes.ID_286:
                            self.offensive_duels += 1
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.successful_duels += 1
                        if self.x <= 33.3:
                            self.successful_duels_defensive_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.successful_duels_middle_third += 1
                        if self.x > 66.6:
                            self.successful_duels_attacking_third += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.unsuccessful_duels += 1
                        if self.x <= 33.3:
                            self.unsuccessful_duels_defensive_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.unsuccessful_duels_middle_third += 1
                        if self.x > 66.6:
                            self.unsuccessful_duels_attacking_third += 1
                    self.total_aerial_duels += 1
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.successful_aerial_duels += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.unsuccessful_aerial_duels += 1
                elif event.typeID == EventIDs.ID_3_Take_On:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if (
                        event.outcome == EventIDs.SUCCESSFUL
                        and QTypes.ID_211 not in qualifier_list
                    ):
                        self.successful_duels += 1
                        self.successful_ground_duels += 1
                        if QTypes.ID_285 in qualifier_list:
                            self.defensive_duels += 1
                        if QTypes.ID_286 in qualifier_list:
                            self.offensive_duels += 1
                        if self.x <= 33.3:
                            self.successful_duels_defensive_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.successful_duels_middle_third += 1
                        if self.x > 66.6:
                            self.successful_duels_attacking_third += 1
                    elif (
                        event.outcome == EventIDs.UNSUCCESSFUL
                        and QTypes.ID_211 not in qualifier_list
                    ):
                        self.unsuccessful_duels += 1
                        self.unsuccessful_ground_duels += 1
                        if QTypes.ID_285 in qualifier_list:
                            self.defensive_duels += 1
                        if QTypes.ID_286 in qualifier_list:
                            self.offensive_duels += 1
                        if self.x <= 33.3:
                            self.unsuccessful_duels_defensive_third += 1
                        elif 33.3 < self.x <= 66.6:
                            self.unsuccessful_duels_middle_third += 1
                        elif self.x > 66.6:
                            self.unsuccessful_duels_attacking_third += 1
                elif event.typeID == EventIDs.ID_4_Foul:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    for q in event.qEvents:
                        if (
                            q.qualifierID == QTypes.ID_12
                            and event.outcome == EventIDs.SUCCESSFUL
                        ):
                            self.successful_duels += 1
                            if self.x <= 33.3:
                                self.successful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.successful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.successful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.successful_ground_duels += 1
                            elif QTypes.ID_285 in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 in qualifier_list:
                                self.offensive_duels += 1
                        elif (
                            q.qualifierID == QTypes.ID_13
                            and event.outcome == EventIDs.SUCCESSFUL
                        ):
                            self.successful_duels += 1
                            if self.x <= 33.3:
                                self.successful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.successful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.successful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.successful_ground_duels += 1
                            elif QTypes.ID_285 in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 in qualifier_list:
                                self.offensive_duels += 1
                        elif (
                            q.qualifierID == QTypes.ID_242
                            and event.outcome == EventIDs.SUCCESSFUL
                        ):
                            self.successful_duels += 1
                            if self.x <= 33.3:
                                self.successful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.successful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.successful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.successful_ground_duels += 1
                            elif QTypes.ID_285 in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 in qualifier_list:
                                self.offensive_duels += 1
                        if (
                            q.qualifierID == QTypes.ID_12
                            and event.outcome == EventIDs.UNSUCCESSFUL
                        ):
                            self.unsuccessful_duels += 1
                            if self.x <= 33.3:
                                self.unsuccessful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.unsuccessful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.unsuccessful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.unsuccessful_ground_duels += 1
                            elif QTypes.ID_285 not in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 not in qualifier_list:
                                self.offensive_duels += 1
                        elif (
                            q.qualifierID == QTypes.ID_13
                            and event.outcome == EventIDs.UNSUCCESSFUL
                        ):
                            self.unsuccessful_duels += 1
                            if self.x <= 33.3:
                                self.unsuccessful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.unsuccessful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.unsuccessful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.unsuccessful_ground_duels += 1
                            elif QTypes.ID_285 not in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 not in qualifier_list:
                                self.offensive_duels += 1
                        elif (
                            q.qualifierID == QTypes.ID_242
                            and event.outcome == EventIDs.UNSUCCESSFUL
                        ):
                            self.unsuccessful_duels += 1
                            if self.x <= 33.3:
                                self.unsuccessful_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.unsuccessful_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.unsuccessful_duels_attacking_third += 1
                            if QTypes.ID_264 not in qualifier_list:
                                self.unsuccessful_ground_duels += 1
                            elif QTypes.ID_285 not in qualifier_list:
                                self.defensive_duels += 1
                            elif QTypes.ID_286 not in qualifier_list:
                                self.offensive_duels += 1
                elif event.typeID == EventIDs.ID_7_Tackle:
                    self.successful_duels += 1
                    self.successful_ground_duels += 1
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if QTypes.ID_285 not in qualifier_list:
                        self.defensive_duels += 1
                    if self.x <= 33.3:
                        self.successful_duels_defensive_third += 1
                    elif 33.3 < self.x <= 66.6:
                        self.successful_duels_middle_third += 1
                    elif self.x > 66.6:
                        self.successful_duels_attacking_third += 1
                elif event.typeID == EventIDs.ID_54_Smother:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if QTypes.ID_285 not in qualifier_list:
                        self.defensive_duels += 1
                    elif QTypes.ID_286 not in qualifier_list:
                        self.offensive_duels += 1
                    elif QTypes.ID_232 not in qualifier_list:
                        self.successful_duels += 1
                        self.successful_ground_duels += 1
                        if self.x <= 33.3:
                            self.successful_duels_defensive_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.successful_duels_middle_third += 1
                        if self.x > 66.6:
                            self.successful_duels_attacking_third += 1
                elif event.typeID == EventIDs.ID_45_Challenge:
                    self.unsuccessful_duels += 1
                    self.unsuccessful_ground_duels += 1
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if QTypes.ID_285 not in qualifier_list:
                        self.defensive_duels += 1
                    # if QTypes.ID_286 not in qualifier_list:
                    #    self.offensive_duels += 1
                    if self.x <= 33.3:
                        self.unsuccessful_duels_defensive_third += 1
                    if 33.3 < self.x <= 66.6:
                        self.unsuccessful_duels_middle_third += 1
                    if self.x > 66.6:
                        self.unsuccessful_duels_attacking_third += 1
                elif event.typeID == EventIDs.ID_50_Dispossessed:
                    self.unsuccessful_duels += 1
                    self.unsuccessful_ground_duels += 1
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if (
                        QTypes.ID_285 in qualifier_list
                        and QTypes.ID_286 not in qualifier_list
                    ):
                        self.defensive_duels += 1
                    if (
                        QTypes.ID_286 in qualifier_list
                        and QTypes.ID_285 not in qualifier_list
                    ):
                        self.offensive_duels += 1
                    if self.x <= 33.3:
                        self.unsuccessful_duels_defensive_third += 1
                    if 33.3 < self.x <= 66.6:
                        self.unsuccessful_duels_middle_third += 1
                    if self.x > 66.6:
                        self.unsuccessful_duels_attacking_third += 1

        self.total_duels = self.successful_duels + self.unsuccessful_duels
        self.duels_in_attacking_third = (
            self.successful_duels_attacking_third
            + self.unsuccessful_duels_attacking_third
        )
        self.duels_in_middle_third = (
            self.successful_duels_middle_third + self.unsuccessful_duels_middle_third
        )
        self.duels_in_defending_third = (
            self.successful_duels_defensive_third
            + self.unsuccessful_duels_defensive_third
        )

        if self.total_duels != 0:
            self.duel_success_rate = round(
                (100 * float(self.successful_duels / self.total_duels)), 2
            )
        if self.duels_in_attacking_third != 0:
            self.duel_success_attacking_third = round(
                (
                    100
                    * float(
                        self.successful_duels_attacking_third
                        / self.duels_in_attacking_third
                    )
                ),
                2,
            )
        if self.duels_in_middle_third != 0:
            self.duel_success_middle_third = round(
                (
                    100
                    * float(
                        self.successful_duels_middle_third / self.duels_in_middle_third
                    )
                ),
                2,
            )
        if self.duels_in_defending_third != 0:
            self.duel_success_defending_third = round(
                (
                    100
                    * float(
                        self.successful_duels_defensive_third
                        / self.duels_in_defending_third
                    )
                ),
                2,
            )

        if print_results:
            self.printResults()
        self.saveResults()

        return self.event_results

    def printResults(self):
        print("----  Duel ----")
        print("total duels: " + str(self.total_duels))
        print("defensive duels: " + str(self.defensive_duels))
        print("offensive duels: " + str(self.offensive_duels))
        print("total successful duels: " + str(self.successful_duels))
        print("total unsuccessful duels: " + str(self.unsuccessful_duels))
        print("duel success percentage: " + str(self.duel_success_rate))
        print("duels in attacking third: " + str(self.duels_in_attacking_third))
        print("duels in middle third: " + str(self.duels_in_middle_third))
        print("duels in defending third: " + str(self.duels_in_defending_third))
        print(
            "duel success percentage in attacking third: "
            + str(self.duel_success_attacking_third)
        )
        print(
            "duel success percentage in middle third: "
            + str(self.duel_success_middle_third)
        )
        print(
            "duel success percentage in defending third: "
            + str(self.duel_success_defending_third)
        )
        print("total ground duels won: " + str(self.successful_ground_duels))
        print("total ground duels lost: " + str(self.unsuccessful_ground_duels))

    def saveResults(self):

        self.event_results["total duels"] = int(self.total_duels)
        self.event_results["defensive duels"] = int(self.defensive_duels)
        self.event_results["offensive duels"] = int(self.offensive_duels)
        self.event_results["total successful duels"] = int(self.successful_duels)
        self.event_results["total unsuccessful duels"] = int(self.unsuccessful_duels)
        self.event_results["duel success percentage"] = int(self.duel_success_rate)
        self.event_results["duels in attacking third"] = int(
            self.duels_in_attacking_third
        )
        self.event_results["duels in middle third"] = int(self.duels_in_middle_third)
        self.event_results["duels in defending third"] = int(
            self.duels_in_defending_third
        )
        self.event_results["duel success percentage in attacking third"] = int(
            self.duel_success_attacking_third
        )
        self.event_results["duel success percentage in middle third"] = int(
            self.duel_success_middle_third
        )
        self.event_results["duel success percentage in defending third"] = int(
            self.duel_success_defending_third
        )
        self.event_results["total ground duels won"] = int(self.successful_ground_duels)
        self.event_results["total ground duels lost"] = int(
            self.unsuccessful_ground_duels
        )

        # PlayerStatistics.writeInExcell(self.eventType, self.event_results)

    def getDataFrame(self):
        self.data = [
            ["total duels", self.total_duels],
            ["total successful duels", self.successful_duels],
            ["total unsuccessful duels", self.unsuccessful_duels],
            ["duel success percentage", self.duel_success_rate],
            ["duels in attacking third", self.duels_in_attacking_third],
            ["duels in middle third", self.duels_in_middle_third],
            ["duels in defending third", self.duels_in_defending_third],
            ["total ground duels won", self.successful_ground_duels],
            ["total ground duels lost", self.unsuccessful_ground_duels],
        ]

        # Create the pandas DataFrame
        #df = pd.DataFrame(self.data, columns=[player_name, "Total"])
        #return df
