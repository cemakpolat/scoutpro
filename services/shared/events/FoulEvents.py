# This class checks the following Opta F24 events:
#     "4":"Foul"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from .Events import *
from .QTypes import *
import pandas as pd


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

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}
        self.eventType = "Foul"

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
                if event.typeID == EventIDs.ID_4_Foul:
                    self.fouls_total += 1
                    self.x = event.x
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.fouls_won += 1
                        if self.x <= 33.3:
                            self.fouls_won_in_defending_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.fouls_won_in_middle_third += 1
                        if self.x > 66.6:
                            self.fouls_won_in_attacking_third += 1
                        for q in event.qEvents:
                            if q.qualifierID == QTypes.ID_9:
                                self.penalty_won += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.fouls_conceded += 1
                        if self.x <= 33.3:
                            self.fouls_committed_in_defending_third += 1
                        if 33.3 < self.x <= 66.6:
                            self.fouls_committed_in_middle_third += 1
                        if self.x > 66.6:
                            self.fouls_committed_in_attacking_third += 1
                        for q in event.qEvents:
                            if q.qualifierID == QTypes.ID_9:
                                self.penalty_conceded += 1
                            elif q.qualifierID == QTypes.ID_10:
                                self.handball_conceded += 1

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        print("---- Foul ----")
        # print("total fouls: " + str(self.fouls_total))
        print("total fouls suffered: " + str(self.fouls_won))
        print("total fouls committed: " + str(self.fouls_conceded))
        print("total handballs conceded: " + str(self.handball_conceded))
        print("total penalties conceded: " + str(self.penalty_conceded))
        print("total penalties won: " + str(self.penalty_won))
        print(
            "total fouls suffered in defending third: "
            + str(self.fouls_won_in_defending_third)
        )
        print(
            "total fouls suffered in middle third: "
            + str(self.fouls_won_in_middle_third)
        )
        print(
            "total fouls suffered in attacking third: "
            + str(self.fouls_won_in_attacking_third)
        )
        print(
            "total fouls committed in defending third: "
            + str(self.fouls_committed_in_defending_third)
        )
        print(
            "total fouls committed in middle third: "
            + str(self.fouls_committed_in_middle_third)
        )
        print(
            "total fouls committed in attacking third: "
            + str(self.fouls_committed_in_attacking_third)
        )

    def saveResults(self):
        print("save results method is called")

        self.event_results["total fouls suffered"] = self.fouls_won
        self.event_results["total fouls committed"] = self.fouls_conceded
        self.event_results["total handballs conceded"] = self.handball_conceded
        self.event_results["total penalties conceded"] = self.penalty_conceded
        self.event_results["total penalties won"] = self.penalty_won
        self.event_results[
            "total fouls suffered in defending third"
        ] = self.fouls_won_in_defending_third
        self.event_results[
            "total fouls suffered in middle third"
        ] = self.fouls_won_in_middle_third
        self.event_results[
            "total fouls suffered in attacking third"
        ] = self.fouls_won_in_attacking_third
        self.event_results[
            "total fouls committed in defending third"
        ] = self.fouls_committed_in_defending_third
        self.event_results[
            "total fouls committed in middle third"
        ] = self.fouls_committed_in_middle_third
        self.event_results[
            "total fouls committed in attacking third"
        ] = self.fouls_committed_in_attacking_third

        # PlayerStatistics.appendResults(self.eventType, self.event_results)

    def getDataFrame(self):
        self.data = [
            ["total fouls suffered", self.fouls_won],
            ["total fouls committed", self.fouls_conceded],
            ["total handballs conceded", self.handball_conceded],
            ["total penalties conceded", self.penalty_conceded],
            ["total penalties won", self.penalty_won],
            [
                "total fouls suffered in defending third",
                self.fouls_won_in_defending_third,
            ],
            ["total fouls suffered in middle third", self.fouls_won_in_middle_third],
            [
                "total fouls suffered in attacking third",
                self.fouls_won_in_attacking_third,
            ],
            [
                "total fouls committed in defending third",
                self.fouls_committed_in_defending_third,
            ],
            [
                "total fouls committed in middle third",
                self.fouls_committed_in_middle_third,
            ],
            [
                "total fouls committed in attacking third",
                self.fouls_committed_in_attacking_third,
            ],
        ]

        # Create the pandas DataFrame
        # df = pd.DataFrame(self.data, columns=[player_name, "Total"])
        # return df
