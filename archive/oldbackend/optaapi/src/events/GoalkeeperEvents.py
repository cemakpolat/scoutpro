# This class checks the following Opta F24 events:
#
#     "54":"Smother"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *
from src.events.QTypes import *
import pandas as pd


class GoalkeeperEvents:
    def __init__(self):

        # duel counters
        self.clean_sheet = 0
        self.gk_sweeper = 0
        self.crosses_faced = 0
        self.cross_percentage_gk = 0
        self.crosses_claimed = 0
        self.crosses_punched = 0
        self.goals_against = 0
        self.gk_pick_ups = 0
        self.gk_touches = 0
        self.successful_goal_kicks = 0
        self.goal_kicks = 0
        self.gk_catch_on_cross = 0
        self.gk_drop_on_cross = 0
        self.successful_gk_throws = 0
        self.gk_throws = 0
        self.crosses_not_claimed = 0
        self.save_percentage = 0
        self.save_1on1 = 0
        self.save_caught_or_collected = 0
        self.saves = 0
        self.gk_smother = 0
        self.save_body = 0
        self.save_caught = 0
        self.save_collected = 0
        self.save_diving = 0
        self.save_feet = 0
        self.save_fingertip = 0
        self.save_hands = 0
        self.save_inside_box = 0
        self.save_outside_box = 0
        self.save_penalty = 0
        self.save_parried_danger = 0
        self.save_parried_safe = 0
        self.save_reaching = 0
        self.save_standing = 0
        self.save_stooping = 0
        self.accurate_keeper_sweeper = 0
        self.shots_against = 0
        self.shots_on_target_against = 0
        self.average_shot_distance_against = 0
        self.shots_on_target_conceded = 0
        self.headed_shots_on_target_conceded = 0
        self.shots_on_target_conceded_inside_box = 0
        self.shots_on_target_conceded_outside_box = 0
        self.big_chances_faced = 0
        self.shots_conceded_including_blocks = 0
        self.headed_shots_conceded = 0

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0

        # opponent_events
        self.team_own_goals = 0
        self.saves_from_own_player = 0
        self.penalty_faced = 0
        self.penalties_missed = 0
        self.penalties_scored = 0
        self.penalties_saved = 0
        self.save_percentage_denominator = 0
        # check division by 0
        self.cross_percentage_check = False

        self.event_results = {}
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

        for event in events:
            try:
                temp_player_id = int(event.playerID)
                temp_team_id = int(event.teamID)
            except (AttributeError, ValueError, TypeError):
                continue

            if temp_player_id in playerID and temp_team_id in teamID:
                typeID = int(event.typeID)

                if event.typeID == EventIDs.ID_10_Save:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(int(q.qualifierID))
                    if (
                            QTypes.ID_94 not in qualifier_list
                            and QTypes.ID_190 not in qualifier_list
                    ):
                        self.saves += 1
                        if QTypes.ID_21 in qualifier_list:
                            self.save_body += 1
                        if QTypes.ID_176 in qualifier_list:
                            self.save_caught += 1
                        if QTypes.ID_177 in qualifier_list:
                            self.save_collected += 1
                        if QTypes.ID_179 in qualifier_list:
                            self.save_diving += 1
                        if QTypes.ID_183 in qualifier_list:
                            self.save_feet += 1
                        if QTypes.ID_175 in qualifier_list:
                            self.save_fingertip += 1
                        if QTypes.ID_182 in qualifier_list:
                            self.save_hands += 1
                        if QTypes.ID_9 in qualifier_list:
                            self.save_penalty += 1
                        if QTypes.ID_174 in qualifier_list:
                            self.save_parried_danger += 1
                        if QTypes.ID_173 in qualifier_list:
                            self.save_parried_safe += 1
                        if QTypes.ID_181 in qualifier_list:
                            self.save_reaching += 1
                        if QTypes.ID_178 in qualifier_list:
                            self.save_standing += 1
                        if QTypes.ID_180 in qualifier_list:
                            self.save_stooping += 1
                        if QTypes.ID_101 in qualifier_list:
                            self.shots_against += 1

                        if QTypes.ID_139 in qualifier_list:
                            self.saves_from_own_player += 1
                            self.shots_against += 1
                            self.shots_on_target_against += 1

                            self.x = float(event.x)
                            self.y = float(event.y)

                            if self.x <= 17 and 21.1 <= self.y <= 78.9:
                                self.save_inside_box += 1
                            if self.x > 17 or self.y < 21.1 or self.y > 78.9:
                                self.save_outside_box += 1

                elif typeID == EventIDs.ID_11_Claim:
                    self.crosses_claimed += 1
                    self.cross_percentage_check = True
                    if int(event.outcome) == EventIDs.SUCCESSFUL:
                        self.gk_catch_on_cross += 1
                    elif int(event.outcome) == EventIDs.UNSUCCESSFUL:
                        self.gk_drop_on_cross += 1
                        self.crosses_not_claimed += 1

                elif typeID == EventIDs.ID_41_Punch:
                    self.crosses_punched += 1
                    self.cross_percentage_check = True

                elif typeID == EventIDs.ID_52_Keeper_pick_up:
                    self.gk_pick_ups += 1

                elif typeID == EventIDs.ID_54_Smother:
                    self.gk_smother += 1

                elif typeID == EventIDs.ID_1_Pass_Events:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(int(q.qualifierID))
                    if QTypes.ID_123 in qualifier_list:
                        self.gk_throws += 1
                        if int(event.outcome) == EventIDs.SUCCESSFUL:
                            self.successful_gk_throws += 1
                    if QTypes.ID_124 in qualifier_list:
                        self.goal_kicks += 1
                        if int(event.outcome) == EventIDs.SUCCESSFUL:
                            self.successful_goal_kicks += 1

                elif typeID == EventIDs.ID_59_Keeper_sweeper:
                    self.gk_sweeper += 1
                    if int(event.outcome) == EventIDs.SUCCESSFUL:
                        self.accurate_keeper_sweeper += 1

                elif typeID == EventIDs.ID_53_Cross_not_claimed:
                    self.crosses_not_claimed += 1
                    self.cross_percentage_check = True

                elif typeID == EventIDs.ID_58_Penalty_faced:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(int(q.qualifierID))
                    self.penalty_faced += 1
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)
                    if QTypes.ID_188 in qualifier_list:
                        self.penalties_missed += 1
                    if QTypes.ID_187 in qualifier_list:
                        self.penalties_saved += 1
                    if QTypes.ID_186 in qualifier_list:
                        self.penalties_scored += 1

                elif typeID == EventIDs.ID_90_Shot_Against:
                    self.shots_against += 1

                elif typeID == EventIDs.ID_92_Goal_Against:
                    self.goals_against += 1
                    for q in event.qEvents:
                        if QTypes.ID_921 == int(q.qualifierID):
                            self.team_own_goals += 1

                elif typeID == EventIDs.ID_94_Shot_On_Target_Against:
                    self.shots_on_target_against += 1
                    for q in event.qEvents:
                        if QTypes.ID_914 == int(q.qualifierID):
                            self.save_inside_box += 1
                        elif QTypes.ID_924 == int(q.qualifierID):
                            self.save_outside_box += 1
                        if QTypes.ID_934 == int(q.qualifierID):
                            self.save_1on1 += 1

                elif typeID == EventIDs.ID_96_Crosses_Against:
                    self.crosses_faced += 1

                elif typeID == EventIDs.ID_101_Clean_Sheet:
                    self.clean_sheet += 1

        self.save_caught_or_collected = self.save_caught + self.save_collected
        self.gk_touches = (
                self.saves
                + self.crosses_claimed
                + self.crosses_punched
                + self.gk_pick_ups
                + self.gk_smother
        )
        self.save_percentage_denominator = (
                self.shots_on_target_against
                + self.saves_from_own_player
                + self.team_own_goals
        )
        if self.save_percentage_denominator != 0:
            self.save_percentage = round(
                100
                * float(
                    1
                    - (
                            (self.goals_against + self.team_own_goals)
                            / self.save_percentage_denominator
                    )
                ),
                2,
            )
        if self.cross_percentage_check and (
                self.crosses_claimed + self.crosses_punched + self.crosses_not_claimed
        ) != 0:
            self.cross_percentage_gk = round(
                100
                * float(
                    (self.crosses_claimed + self.crosses_punched)
                    / (
                            self.crosses_claimed
                            + self.crosses_punched
                            + self.crosses_not_claimed
                    )
                ),
                2,
            )

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):

        print("---- Goal Keeper ----")
        print("clean sheets: " + str(self.clean_sheet))
        print("Goalkeeper sweepers: " + str(self.gk_sweeper))
        print("crosses faced: " + str(self.crosses_faced))
        print("cross percentage (GK): " + str(self.cross_percentage_gk))
        print("crosses claimed: " + str(self.crosses_claimed))
        print("crosses punched: " + str(self.crosses_punched))
        print("goals against: " + str(self.goals_against))
        print("goalkeeper pick ups: " + str(self.gk_pick_ups))
        # print("goalkeeper touches: " + str(self.gk_touches))
        print("Successful goal kicks: " + str(self.successful_goal_kicks))
        print("Goal kicks: " + str(self.goal_kicks))
        print("goalkeeper catches on crosses: " + str(self.gk_catch_on_cross))
        print("goalkeeper drops on crosses: " + str(self.gk_drop_on_cross))
        print("Successful goalkeeper throws: " + str(self.successful_gk_throws))
        print("Goalkeeper Throws: " + str(self.gk_throws))
        print("crosses not claimed: " + str(self.crosses_not_claimed))
        print("save percentage: " + str(self.save_percentage))
        print("Save When Attacker Was 1 On 1 With GK: " + str(self.save_1on1))
        print("Saves Caught Or Collected By GK: " + str(self.save_caught_or_collected))
        print("Saves: " + str(self.saves))
        print("Goalkeeper smother: " + str(self.gk_smother))
        print("Saves body: " + str(self.save_body))
        print("Saves caught: " + str(self.save_caught))
        print("Saves collected: " + str(self.save_collected))
        print("Saves diving: " + str(self.save_diving))
        print("Saves feet: " + str(self.save_feet))
        print("Saves fingertip: " + str(self.save_fingertip))
        print("Saves hands: " + str(self.save_hands))
        print("Saves inside box: " + str(self.save_inside_box))
        print("Saves outside box: " + str(self.save_outside_box))
        print("Saves penalty: " + str(self.save_penalty))
        print("Saves parried danger: " + str(self.save_parried_danger))
        print("Saves parried safe: " + str(self.save_parried_safe))
        print("Saves reaching: " + str(self.save_reaching))
        print("Saves standing: " + str(self.save_standing))
        print("Saves stooping: " + str(self.save_stooping))
        print("Accurate keeper sweepers:  " + str(self.accurate_keeper_sweeper))
        print("Shots against: " + str(self.shots_against))
        print("Shots on target against: " + str(self.shots_on_target_against))
        # print("Average shot distance against: " + str(self.average_shot_distance_against))
        # print("Shots on target conceded: " + str(self.shots_on_target_conceded))
        # print("Headed shots on target conceded: " + str(self.headed_shots_on_target_conceded))
        # print("Shots on target conceded inside box: " + str(self.shots_on_target_conceded_inside_box))
        # print("Shots on target conceded outside box: " + str(self.shots_on_target_conceded_outside_box))
        # print("Big chances faced: " + str(self.big_chances_faced))
        # print("Shots conceded including blocks: " + str(self.shots_conceded_including_blocks))
        # print("Headed shots conceded: " + str(self.headed_shots_conceded))
        print("team own goals: " + str(self.team_own_goals))
        print("penalties faced: " + str(self.penalty_faced))
        print("penalties scored: " + str(self.penalties_scored))
        print("penalties saved: " + str(self.penalties_saved))
        print("penalties missed: " + str(self.penalties_missed))

    def saveResults(self):
        print("save results method is called")

        self.event_results["clean sheets"] = self.clean_sheet
        self.event_results["goalkeeper sweepers"] = self.gk_sweeper
        self.event_results["crosses faced"] = self.crosses_faced
        self.event_results["cross percentage (GK)"] = self.cross_percentage_gk
        self.event_results["crosses claimed"] = self.crosses_claimed
        self.event_results["crosses punched"] = self.crosses_punched
        self.event_results["goals against"] = self.goals_against
        self.event_results["goalkeeper pick ups"] = self.gk_pick_ups
        self.event_results["successful goal kicks"] = self.successful_goal_kicks
        self.event_results["goal kicks"] = self.goal_kicks
        self.event_results["goalkeeper catches on crosses"] = self.gk_catch_on_cross
        self.event_results["goalkeeper drops on crosses"] = self.gk_drop_on_cross
        self.event_results["successful goalkeeper throws"] = self.successful_gk_throws
        self.event_results["goalkeeper throws"] = self.gk_throws
        self.event_results["crosses not claimed"] = self.crosses_not_claimed
        self.event_results["save percentage"] = self.save_percentage
        self.event_results["Save When Attacker Was 1 On 1 With GK"] = self.save_1on1
        self.event_results[
            "Saves Caught Or Collected By GK"
        ] = self.save_caught_or_collected
        self.event_results["Saves"] = self.saves
        self.event_results["Goalkeeper smother"] = self.gk_smother
        self.event_results["Saves body"] = self.save_body
        self.event_results["Saves caught"] = self.save_caught
        self.event_results["Saves collected"] = self.save_collected
        self.event_results["Saves diving"] = self.save_diving
        self.event_results["Saves feet"] = self.save_feet
        self.event_results["Saves fingertip"] = self.save_fingertip
        self.event_results["Saves hands"] = self.save_hands
        self.event_results["Saves inside box"] = self.save_inside_box
        self.event_results["Saves outside box"] = self.save_outside_box
        self.event_results["Saves penalty"] = self.save_penalty
        self.event_results["Saves parried danger"] = self.save_parried_danger
        self.event_results["Saves parried safe"] = self.save_parried_safe
        self.event_results["Saves reaching"] = self.save_reaching
        self.event_results["Saves standing"] = self.save_standing
        self.event_results["Saves stooping"] = self.save_stooping
        self.event_results["Accurate keeper sweepers"] = self.accurate_keeper_sweeper
        self.event_results["Shots against"] = self.shots_against
        self.event_results["Shots on target against"] = self.shots_on_target_against
        self.event_results["Team own goals"] = self.team_own_goals
        self.event_results["penalties faced"] = self.penalty_faced
        self.event_results["penalties opponent scored"] = self.penalties_scored
        self.event_results["penalties saved by keeper"] = self.penalties_saved
        self.event_results["penalties missed by opponent"] = self.penalties_missed

    def getDataFrame(self):
        data = [
            ["clean sheets", self.clean_sheet],
            ["goalkeeper sweepers", self.gk_sweeper],
            ["crosses faced", self.crosses_faced],
            ["cross percentage (GK)", self.cross_percentage_gk],
            ["crosses claimed", self.crosses_claimed],
            ["crosses punched", self.crosses_punched],
            ["goals against", self.goals_against],
            ["goalkeeper pick ups", self.gk_pick_ups],
            ["successful goal kicks", self.successful_goal_kicks],
            ["goal kicks", self.goal_kicks],
            ["goalkeeper catches on crosses", self.gk_catch_on_cross],
            ["goalkeeper drops on crosses", self.gk_drop_on_cross],
            ["successful goalkeeper throws", self.successful_gk_throws],
            ["goalkeeper throws", self.gk_throws],
            ["crosses not claimed", self.crosses_not_claimed],
            ["save percentage", self.save_percentage],
            ["Save When Attacker Was 1 On 1 With GK", self.save_1on1],
            ["Saves Caught Or Collected By GK", self.save_caught_or_collected],
            ["Saves", self.saves],
            ["Goalkeeper smother", self.gk_smother],
            ["Saves body", self.save_body],
            ["Saves caught", self.save_caught],
            ["Saves collected", self.save_collected],
            ["Saves diving", self.save_diving],
            ["Saves feet", self.save_feet],
            ["Saves fingertip", self.save_fingertip],
            ["Saves hands", self.save_hands],
            ["Saves inside box", self.save_inside_box],
            ["Saves outside box", self.save_outside_box],
            ["Saves penalty", self.save_penalty],
            ["Saves parried danger", self.save_parried_danger],
            ["Saves parried safe", self.save_parried_safe],
            ["Saves reaching", self.save_reaching],
            ["Saves standing", self.save_standing],
            ["Saves stooping", self.save_stooping],
            ["Accurate keeper sweepers", self.accurate_keeper_sweeper],
            ["Shots against", self.shots_against],
            ["Shots on target against", self.shots_on_target_against],
            ["Team own goals", self.team_own_goals],
            ["penalties faced", self.penalty_faced],
            ["penalties opponent scored", self.penalties_scored],
            ["penalties saved by keeper", self.penalties_saved],
            ["penalties missed by opponent", self.penalties_missed],
        ]

        return data
