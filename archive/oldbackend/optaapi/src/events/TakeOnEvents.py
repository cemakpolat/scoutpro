# This class checks the following Opta F24 events:
#     "3":"Take Ons"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *
from src.events.QTypes import *
import pandas as pd


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

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}
        self.data = []

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
                if event.typeID == EventIDs.ID_3_Take_On:
                    self.total_take_ons += 1
                    self.x = event.x
                    self.y = event.y
                    if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                        self.take_ons_in_box += 1
                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_211:
                            self.take_on_overrun += 1
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.take_ons_successful += 1
                        if self.x > 66.6:
                            self.take_on_in_attacking_third += 1
                        if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                            self.successful_take_ons_in_box += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.take_ons_unsuccessful += 1
                        if self.x > 66.6:
                            self.take_on_in_attacking_third_uns += 1

        if (self.take_ons_successful + self.take_ons_unsuccessful) != 0:
            self.take_on_success_rate = 100 * round(
                float(
                    self.take_ons_successful
                    / (self.take_ons_successful + self.take_ons_unsuccessful)
                ),
                4,
            )
        if (self.take_on_in_attacking_third + self.take_on_in_attacking_third_uns) != 0:
            self.take_on_success_rate_attacking_third = 100 * round(
                float(
                    self.take_on_in_attacking_third
                    / (
                        self.take_on_in_attacking_third
                        + self.take_on_in_attacking_third_uns
                    )
                ),
                4,
            )
        self.tackled = self.take_ons_unsuccessful - self.take_on_overrun

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        print("---- Take On ----")
        print("total take ons: " + str(self.total_take_ons))
        print("successful take ons: " + str(self.take_ons_successful))
        print("unsuccessful take ons: " + str(self.take_ons_unsuccessful))
        print("take on success rate: " + str(self.take_on_success_rate))
        print("total overrun take ons: " + str(self.take_on_overrun))
        print(
            "successful take ons in attacking third: "
            + str(self.take_on_in_attacking_third)
        )
        print(
            "successful take on percentage in attacking third: "
            + str(self.take_on_success_rate_attacking_third)
        )
        print("take on attempts in box: " + str(self.take_ons_in_box))
        print("successful take ons in box: " + str(self.successful_take_ons_in_box))
        print("times tackled: " + str(self.tackled))

    def saveResults(self):
        print("save results method is called")

        self.event_results["total take ons"] = self.total_take_ons
        self.event_results["successful take ons"] = self.take_ons_successful
        self.event_results["unsuccessful take ons"] = self.take_ons_unsuccessful
        self.event_results["take on success rate"] = self.take_on_success_rate
        self.event_results["total overrun take ons"] = self.take_on_overrun
        self.event_results[
            "successful take ons in attacking third"
        ] = self.take_on_in_attacking_third
        self.event_results[
            "successful take on percentage in attacking third"
        ] = self.take_on_success_rate_attacking_third
        self.event_results["take on attempts in box"] = self.take_ons_in_box
        self.event_results[
            "successful take ons in box"
        ] = self.successful_take_ons_in_box
        self.event_results["tackled"] = self.tackled

    def getDataFrame(self):

        self.data = [
            ["total take ons", self.total_take_ons],
            ["successful take ons", self.take_ons_successful],
            ["total overrun take ons", self.take_ons_unsuccessful],
            ["total overrun take ons", self.take_on_success_rate],
            ["successful take ons in attacking third", self.take_on_in_attacking_third],
            [
                "successful take on percentage in attacking third",
                self.take_on_success_rate_attacking_third,
            ],
            ["take on attempts in box", self.take_ons_in_box],
            ["successful take ons in box", self.successful_take_ons_in_box],
            ["tackled", self.tackled],
        ]
