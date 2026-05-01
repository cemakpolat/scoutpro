# This class checks the following Opta F24 events:
#     "50":"Dispossessed"
#     "51":"Error"
#     "61":"Ball Touch"
#     "72":"Caught Offside"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from .Events import *
from .QTypes import *
import pandas as pd


class BallControlEvents:
    def __init__(self):

        # simple ball control event counters
        self.total_dispossessed = 0
        self.ball_touch = 0
        self.ball_hit_the_player = 0
        self.unsuccessful_control = 0
        self.caught_offside = 0
        self.errors = 0
        self.error_led_to_goal = 0
        self.error_led_to_shot = 0
        self.x = 0
        self.y = 0
        self.event_results = {}

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
                if event.typeID == EventIDs.ID_50_Dispossessed:
                    self.total_dispossessed += 1
                elif event.typeID == EventIDs.ID_51_Error:
                    self.errors += 1
                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_169:
                            self.error_led_to_shot += 1
                        if q.qualifierID == QTypes.ID_170:
                            self.error_led_to_goal += 1
                elif event.typeID == EventIDs.ID_61_Ball_touch:
                    # print("ball touch")
                    self.ball_touch += 1
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.ball_hit_the_player += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.unsuccessful_control += 1

        for event in events:
            self.x = event.x
            self.y = event.y
            if event.typeID == EventIDs.ID_2_Offside_Pass:
                for q in event.qEvents:
                    if q.qualifierID == QTypes.ID_7:
                        self.caught_offside += 1
        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        print("---- Ball Control ----")
        print("total dispossessed: " + str(self.total_dispossessed))
        print("total errors: " + str(self.errors))
        print("total errors led to goal: " + str(self.error_led_to_goal))
        print("total errors led to shot: " + str(self.error_led_to_shot))
        print("total offsides: " + str(self.caught_offside))
        print("bad ball touches: " + str(self.ball_touch))
        print("ball hit the player: " + str(self.ball_hit_the_player))
        print("unsuccessful ball controls: " + str(self.unsuccessful_control))

    def saveResults(self):
        print("save results method is called")

        self.event_results["total dispossessed"] = self.total_dispossessed
        self.event_results["total errors"] = self.errors
        self.event_results["total errors led to goal"] = self.error_led_to_goal
        self.event_results["total errors led to shot"] = self.error_led_to_shot
        self.event_results["total offsides"] = self.caught_offside
        self.event_results["bad ball touches"] = self.ball_touch
        self.event_results["ball hit the player"] = self.ball_hit_the_player
        self.event_results["unsuccessful ball controls"] = self.unsuccessful_control

    def getDataFrame(self):
        self.data = [
            ["total dispossessed", self.total_dispossessed],
            ["total errors", self.errors],
            ["total errors led to goal", self.error_led_to_goal],
            ["total errors led to shot", self.error_led_to_shot],
            ["total offsides", self.caught_offside],
            ["bad ball touches", self.ball_touch],
            ["ball hit the player", self.ball_hit_the_player],
            ["unsuccessful ball controls", self.unsuccessful_control],
        ]

        # Create the pandas DataFrame
        df = pd.DataFrame(self.data, columns=["", "Total"])
        return df
