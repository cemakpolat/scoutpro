# This class checks the following Opta F24 events:
#     "44":"Aerial Duels"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *

from src.events.QTypes import *
import pandas as pd


class AerialDuelEvents:
    def __init__(self):

        # simple aerial_duel counters
        self.total_aerial_duels = 0
        self.successful_aerial_duels = 0
        self.unsuccessful_aerial_duels = 0

        # aerial duel regions
        self.aerial_duels_in_attacking_third = 0
        self.aerial_duels_in_middle_third = 0
        self.aerial_duels_in_defending_third = 0
        self.aerial_duels_in_attacking_half = 0
        self.aerial_duels_in_defending_half = 0

        # successful aerial duel regions
        self.successful_aerial_duels_attacking_third = 0
        self.successful_aerial_duels_middle_third = 0
        self.successful_aerial_duels_defensive_third = 0
        self.successful_aerial_duels_attacking_half = 0
        self.successful_aerial_duels_defending_half = 0

        # aerial duel success rate
        self.aerial_duel_success_rate = 0
        self.aerial_duel_success_attacking_third = 0
        self.aerial_duel_success_middle_third = 0
        self.aerial_duel_success_defending_third = 0
        self.aerial_duel_success_in_attacking_half = 0
        self.aerial_duel_success_in_defending_half = 0

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}
        self.playerId = ""
        self.eventType = "Aerial"

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
                self.playerId = event.playerID
                if event.typeID == EventIDs.ID_44_Aerial:
                    self.total_aerial_duels += 1
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.successful_aerial_duels += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.unsuccessful_aerial_duels += 1

                    self.x = event.x

                    if self.x <= 50:
                        self.aerial_duels_in_defending_half += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_aerial_duels_defending_half += 1

                    if self.x > 50:
                        self.aerial_duels_in_attacking_half += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_aerial_duels_attacking_half += 1

                    if self.x <= 33.3:
                        self.aerial_duels_in_defending_third += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_aerial_duels_defensive_third += 1

                    if 33.3 < self.x <= 66.6:
                        self.aerial_duels_in_middle_third += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_aerial_duels_middle_third += 1

                    if self.x > 66.6:
                        self.aerial_duels_in_attacking_third += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_aerial_duels_attacking_third += 1

                elif event.typeID == EventIDs.ID_4_Foul:
                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_264:
                            self.total_aerial_duels += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_aerial_duels += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_aerial_duels += 1
                            self.x = float(event.x)
                            if self.x <= 50:
                                self.aerial_duels_in_defending_half += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_aerial_duels_defending_half += 1
                            elif self.x > 50:
                                self.aerial_duels_in_attacking_half += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_aerial_duels_attacking_half += 1

                            if self.x <= 33.3:
                                self.aerial_duels_in_defending_third += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_aerial_duels_defensive_third += 1
                            elif 33.3 < self.x <= 66.6:
                                self.aerial_duels_in_middle_third += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_aerial_duels_middle_third += 1
                            elif self.x > 66.6:
                                self.aerial_duels_in_attacking_third += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_aerial_duels_attacking_third += 1

        if self.total_aerial_duels != 0:
            self.aerial_duel_success_rate = round(
                (100 * float(self.successful_aerial_duels / self.total_aerial_duels)), 2
            )
            if self.aerial_duels_in_attacking_third != 0:
                self.aerial_duel_success_attacking_third = round(
                    (
                            100
                            * float(
                        self.successful_aerial_duels_attacking_third
                        / self.aerial_duels_in_attacking_third
                    )
                    ),
                    2,
                )
            if self.aerial_duels_in_middle_third != 0:
                self.aerial_duel_success_middle_third = round(
                    (100 * float(self.successful_aerial_duels_middle_third / self.aerial_duels_in_middle_third)),
                    2,
                )
            if self.aerial_duels_in_defending_third != 0:
                self.aerial_duel_success_defending_third = round(
                    (
                            100
                            * float(
                        self.successful_aerial_duels_defensive_third
                        / self.aerial_duels_in_defending_third
                    )
                    ),
                    2,
                )
            if self.aerial_duels_in_attacking_half != 0:
                self.aerial_duel_success_in_attacking_half = round(
                    (
                            100
                            * float(
                        self.successful_aerial_duels_attacking_half
                        / self.aerial_duels_in_attacking_half
                    )
                    ),
                    2,
                )
            if self.aerial_duels_in_defending_half != 0:
                self.aerial_duel_success_in_defending_half = round(
                    (
                            100
                            * float(
                        self.successful_aerial_duels_defending_half
                        / self.aerial_duels_in_defending_half
                    )
                    ),
                    2,
                )

        if print_results:
            self.printResults()

        self.saveResults()
        return self.event_results

    def printResults(self):
        print("---- Aerial Duel ----")
        print("total aerial duels: " + str(self.total_aerial_duels))
        print("aerial duels won: " + str(self.successful_aerial_duels))
        print("aerial duels lost: " + str(self.unsuccessful_aerial_duels))
        print("aerial duels won percentage: " + str(self.aerial_duel_success_rate))
        print(
            "aerial duels in attacking half: "
            + str(self.aerial_duels_in_attacking_half)
        )
        print(
            "aerial duels won percentage in attacking half: "
            + str(self.aerial_duel_success_in_attacking_half)
        )
        print(
            "aerial duels in defending half: "
            + str(self.aerial_duels_in_defending_half)
        )
        print(
            "aerial duels won percentage in defending half: "
            + str(self.aerial_duel_success_in_defending_half)
        )
        print(
            "aerial duels in attacking third: "
            + str(self.aerial_duels_in_attacking_third)
        )
        print(
            "aerial duels won percentage in attacking third: "
            + str(self.aerial_duel_success_attacking_third)
        )
        print("aerial duels in middle third: " + str(self.aerial_duels_in_middle_third))
        print(
            "aerial duels won percentage in middle third: "
            + str(self.aerial_duel_success_middle_third)
        )
        print(
            "aerial duels in defending third: "
            + str(self.aerial_duels_in_defending_third)
        )
        print(
            "aerial duels won percentage in defending third: "
            + str(self.aerial_duel_success_defending_third)
        )

    def saveResults(self):

        # self.event_results["playerId"] = str(self.playerId)
        self.event_results["total aerial duels"] = self.total_aerial_duels
        self.event_results["aerial duels won"] = self.successful_aerial_duels
        self.event_results["aerial duels lost"] = self.unsuccessful_aerial_duels
        self.event_results[
            "aerial duels won percentage"
        ] = self.aerial_duel_success_rate
        self.event_results[
            "aerial duels in attacking half"
        ] = self.aerial_duels_in_attacking_half
        self.event_results[
            "aerial duels won percentage in attacking half"
        ] = self.aerial_duel_success_in_attacking_half
        self.event_results[
            "aerial duels in defending half"
        ] = self.aerial_duels_in_defending_half
        self.event_results[
            "aerial duels won percentage in defending half"
        ] = self.successful_aerial_duels_defending_half
        self.event_results[
            "aerial duels in attacking third"
        ] = self.aerial_duels_in_attacking_third
        self.event_results[
            "aerial duels won percentage in attacking third"
        ] = self.aerial_duel_success_attacking_third
        self.event_results[
            "aerial duels in middle third"
        ] = self.aerial_duels_in_middle_third
        self.event_results[
            "aerial duels won percentage in middle third"
        ] = self.aerial_duel_success_middle_third
        self.event_results[
            "aerial duels in defending third"
        ] = self.aerial_duels_in_defending_third
        self.event_results[
            "aerial duels won percentage in defending third"
        ] = self.aerial_duel_success_defending_third

        # PlayerStatistics.writeInExcell(self.eventType, self.event_results)

    def getDataFrame(self):
        self.data = [
            ["total aerial duels", self.total_aerial_duels],
            ["aerial duels won", self.successful_aerial_duels],
            ["aerial duels lost", self.unsuccessful_aerial_duels],
            ["aerial duels won percentage", self.aerial_duel_success_rate],
            ["aerial duels in attacking half", self.aerial_duels_in_attacking_half],
            [
                "aerial duels won percentage in attacking half",
                self.aerial_duel_success_in_attacking_half,
            ],
            ["aerial duels in defending half", self.aerial_duels_in_defending_half],
            [
                "aerial duels won percentage in defending half",
                self.aerial_duel_success_in_defending_half,
            ],
            ["aerial duels in attacking third", self.aerial_duels_in_attacking_third],
            [
                "aerial duels won percentage in attacking third",
                self.aerial_duel_success_attacking_third,
            ],
            ["aerial duels in middle third", self.aerial_duels_in_middle_third],
            [
                "aerial duels won percentage in middle third",
                self.aerial_duel_success_middle_third,
            ],
            ["aerial duels in defending third", self.aerial_duels_in_defending_third],
            [
                "aerial duels won percentage in defending third",
                self.aerial_duel_success_defending_third,
            ],
        ]

        # Create the pandas DataFrame
        df = pd.DataFrame(self.data, columns=["", "Total"])
        return df
