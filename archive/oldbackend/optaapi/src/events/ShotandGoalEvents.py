# This class checks the following Opta F24 events:
#     "13":"Miss"
#     "14":"Post"
#     "15":"Attempt Saved"
#     "16":"Goal"
#     "60": "Chances Missed"
# author: Doruk Sahinel, Cem Akpolat


from src.events.Events import *
from src.events.QTypes import *
import pandas as pd


class ShotandGoalEvents:
    def __init__(self):

        # goal counters
        self.goals = 0
        self.goals_inside_the_box = 0
        self.goals_outside_the_box = 0
        self.left_footed_goals = 0
        self.right_footed_goals = 0
        self.non_penalty_goals = 0
        self.goals_from_penalties = 0
        self.goals_from_set_play = 0
        self.goals_from_set_piece_cross = 0
        self.goals_from_set_piece_throw_in = 0
        self.goals_from_open_play = 0
        self.goals_from_volleys = 0
        self.goals_from_corners = 0
        self.goals_from_fast_break = 0
        self.goals_from_regular_play = 0
        self.goals_deflected = 0
        self.goals_from_direct_free_kicks = 0
        self.headed_goals = 0
        self.goals_with_other_part_of_body = 0
        self.own_goal = 0
        self.minutes_per_goal = 0
        self.goals_unassisted = 0

        # goal after dribble
        self.dribble_event_id = 0
        self.dribble_check = 0
        self.event_id = 0
        self.shots_after_dribble = 0

        # total shots
        self.total_shots = 0
        self.total_shots_with_blocks = 0
        self.penalty_shots_taken = 0
        self.left_footed_shots = 0
        self.right_footed_shots = 0
        self.shots_inside_box = 0
        self.shots_outside_box = 0
        self.total_headed_shots = 0
        self.shots_with_first_touch = 0
        self.total_big_chances = 0
        self.total_direct_free_kicks = 0
        self.shot_cleared_off_line = 0
        self.shots_deflected = 0
        self.shots_from_set_play = 0
        self.shots_from_fast_break = 0
        self.shots_unassisted = 0
        self.shots_cleared_off_the_line_inside_box = 0
        self.shots_cleared_off_the_line_outside_box = 0

        # blocked shots
        self.blocked_shot = 0
        self.blocked_shot_left = 0
        self.blocked_shot_right = 0
        self.shots_blocked_inside_box = 0
        self.shots_blocked_outside_box = 0
        self.headed_shots_blocked = 0
        self.blocked_shots_with_other_part_of_body = 0
        self.shots_blocked_from_big_chances = 0
        self.blocked_direct_free_kicks = 0
        self.shots_blocked_from_set_play = 0

        # shots off target
        self.shots_off_target = 0
        self.shots_off_target_inside_box = 0
        self.shots_off_target_outside_box = 0
        self.shots_off_target_from_set_piece_cross = 0
        self.shots_off_target_from_set_play = 0
        self.shots_off_target_from_set_piece_throw_in = 0
        self.shots_off_target_from_corners = 0
        self.shots_off_target_from_regular_play = 0
        self.shots_off_target_from_fast_break = 0
        self.shots_off_target_from_open_play = 0
        self.shots_off_target_from_penalties = 0
        self.headed_shots_off_target = 0
        self.left_footed_shots_off_target = 0
        self.right_footed_shots_off_target = 0
        self.shots_hit_woodwork = 0
        self.shots_hit_the_post_from_big_chances = 0
        self.shots_off_target_from_big_chances = 0
        self.direct_free_kicks_off_target = 0

        # shots on target
        self.shots_on_target = 0
        self.headed_shots_on_target = 0
        self.shots_on_target_from_set_piece_cross = 0
        self.shots_on_target_from_set_play = 0
        self.shots_on_target_from_set_piece_throw_in = 0
        self.shots_on_target_from_corners = 0
        self.shots_on_target_from_regular_play = 0
        self.shots_on_target_from_fast_break = 0
        self.shots_on_target_from_open_play = 0
        self.shots_on_target_from_penalties = 0
        self.shots_on_target_inside_box = 0
        self.shots_on_target_outside_box = 0
        self.left_footed_shots_on_target = 0
        self.right_footed_shots_on_target = 0
        self.penalty_shots_saved = 0
        self.shots_on_target_from_direct_free_kicks = 0

        # big chances
        self.goals_from_big_chances = 0
        self.shots_on_target_from_big_chances = 0
        self.chance_missed = 0
        self.big_chances_missed = 0

        # goal percentages
        self.headed_goals_rate = 0
        self.open_play_goals_rate = 0
        self.headed_shots_rate = 0
        self.inside_the_box_shots_rate = 0
        self.outside_the_box_shots_rate = 0
        self.left_foot_shots_rate = 0
        self.right_foot_shots_rate = 0
        self.shots_on_target_rate = 0
        self.blocked_shots_rate = 0
        self.shooting_percentage = 0
        self.no_block_shooting_percentage = 0
        self.big_chance_conversion_rate = 0
        self.free_kick_on_target_rate = 0
        self.unassisted_goals_shots_rate = 0

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}

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
                self.x = event.x
                self.y = event.y
                self.event_id = event.eventID

                if (
                        event.typeID == EventIDs.ID_13_Miss
                        or event.typeID == EventIDs.ID_14_Post
                        or event.typeID == EventIDs.ID_15_Attempt_Saved
                        or event.typeID == EventIDs.ID_16_Goal
                ):
                    self.dribble_check = int(self.event_id) - 1
                    if self.dribble_event_id == self.dribble_check:
                        self.shots_after_dribble += 1
                        self.dribble_event_id = 0
                    elif self.dribble_event_id != self.dribble_check:
                        self.dribble_event_id = 0

                if event.typeID == EventIDs.ID_13_Miss:
                    self.total_shots += 1
                    self.shots_off_target += 1
                    # if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                    #     self.shots_off_target_inside_box += 1

                    if self.x < 83.3 or self.y < 21.1 or self.y > 78.9:
                        self.shots_off_target_outside_box += 1
                    else:
                        self.shots_off_target_inside_box += 1

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_15 in qualifier_list:
                        self.headed_shots_off_target += 1

                    if QTypes.ID_72 in qualifier_list:
                        self.left_footed_shots_off_target += 1

                    if QTypes.ID_20 in qualifier_list:
                        self.right_footed_shots_off_target += 1

                    if QTypes.ID_24 in qualifier_list:
                        self.shots_off_target_from_set_play += 1
                        self.shots_off_target_from_set_piece_cross += 1

                    if QTypes.ID_160 in qualifier_list:
                        self.shots_off_target_from_set_play += 1
                        self.shots_off_target_from_set_piece_throw_in += 1

                    if QTypes.ID_25 in qualifier_list:
                        self.shots_off_target_from_corners += 1
                        self.shots_off_target_from_set_play += 1

                    if QTypes.ID_22 in qualifier_list:
                        self.shots_off_target_from_regular_play += 1
                        self.shots_off_target_from_open_play += 1

                    if QTypes.ID_23 in qualifier_list:
                        self.shots_off_target_from_fast_break += 1
                        self.shots_off_target_from_open_play += 1

                    if QTypes.ID_9 in qualifier_list:
                        self.shots_off_target_from_penalties += 1

                    if QTypes.ID_214 in qualifier_list:
                        self.shots_off_target_from_big_chances += 1

                    if QTypes.ID_328 in qualifier_list:
                        self.shots_with_first_touch += 1

                    if QTypes.ID_26 in qualifier_list:
                        self.direct_free_kicks_off_target += 1

                    if QTypes.ID_133 in qualifier_list:
                        self.shots_deflected += 1

                elif event.typeID == EventIDs.ID_14_Post:
                    self.total_shots += 1
                    self.shots_off_target += 1
                    self.shots_hit_woodwork += 1

                    if self.x < 83.3 or self.y < 21.1 or self.y > 78.9:
                        self.shots_off_target_outside_box += 1
                    else:
                        self.shots_off_target_inside_box += 1

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_15 in qualifier_list:
                        self.headed_shots_off_target += 1

                    if QTypes.ID_72 in qualifier_list:
                        self.left_footed_shots_off_target += 1

                    if QTypes.ID_20 in qualifier_list:
                        self.right_footed_shots_off_target += 1

                    if QTypes.ID_24 in qualifier_list:
                        self.shots_off_target_from_set_play += 1
                        self.shots_off_target_from_set_piece_cross += 1

                    if QTypes.ID_160 in qualifier_list:
                        self.shots_off_target_from_set_play += 1
                        self.shots_off_target_from_set_piece_throw_in += 1

                    if QTypes.ID_25 in qualifier_list:
                        self.shots_off_target_from_corners += 1
                        self.shots_off_target_from_set_play += 1

                    if QTypes.ID_22 in qualifier_list:
                        self.shots_off_target_from_regular_play += 1
                        self.shots_off_target_from_open_play += 1

                    if QTypes.ID_23 in qualifier_list:
                        self.shots_off_target_from_fast_break += 1
                        self.shots_off_target_from_open_play += 1

                    if QTypes.ID_9 in qualifier_list:
                        self.shots_off_target_from_penalties += 1

                    if QTypes.ID_214 in qualifier_list:
                        self.shots_hit_the_post_from_big_chances += 1
                        self.shots_off_target_from_big_chances += 1

                    if QTypes.ID_328 in qualifier_list:
                        self.shots_with_first_touch += 1

                    if QTypes.ID_26 in qualifier_list:
                        self.direct_free_kicks_off_target += 1
                        # self.shots_off_target_from_set_play += 1

                    if QTypes.ID_133 in qualifier_list:
                        self.shots_deflected += 1

                    if QTypes.ID_215 in qualifier_list:
                        self.shots_unassisted += 1

                elif event.typeID == EventIDs.ID_15_Attempt_Saved:

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_101 in qualifier_list:
                        self.total_shots += 1
                        self.shot_cleared_off_line += 1
                        self.shots_on_target += 1
                        if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                            self.shots_cleared_off_the_line_inside_box += 1
                        if self.x < 83.3 or self.y < 21.1 or self.y > 78.9:
                            self.shots_cleared_off_the_line_outside_box += 1

                    if QTypes.ID_82 in qualifier_list and "101" not in qualifier_list:
                        self.blocked_shot += 1

                        if QTypes.ID_72 in qualifier_list:
                            self.blocked_shot_left += 1

                        if QTypes.ID_20 in qualifier_list:
                            self.blocked_shot_right += 1

                        if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                            self.shots_blocked_inside_box += 1

                        if self.x < 83.3 or self.y < 21.1 or self.y > 78.9:
                            self.shots_blocked_outside_box += 1

                        if QTypes.ID_21 in qualifier_list:
                            self.blocked_shots_with_other_part_of_body += 1

                        if QTypes.ID_15 in qualifier_list:
                            self.headed_shots_blocked += 1

                        if QTypes.ID_328 in qualifier_list:
                            self.shots_with_first_touch += 1

                        if QTypes.ID_214 in qualifier_list:
                            self.shots_blocked_from_big_chances += 1

                        if QTypes.ID_26 in qualifier_list:
                            self.blocked_direct_free_kicks += 1
                            self.shots_blocked_from_set_play += 1

                        if QTypes.ID_24 in qualifier_list:
                            self.shots_blocked_from_set_play += 1

                        if QTypes.ID_160 in qualifier_list:
                            self.shots_blocked_from_set_play += 1

                        if QTypes.ID_25 in qualifier_list:
                            self.shots_blocked_from_set_play += 1

                        if QTypes.ID_215 in qualifier_list:
                            self.shots_unassisted += 1

                    if QTypes.ID_82 not in qualifier_list:
                        self.total_shots += 1
                        self.shots_on_target += 1

                    if (
                            QTypes.ID_15 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.headed_shots_on_target += 1

                    if (
                            QTypes.ID_22 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_open_play += 1

                    if (
                            QTypes.ID_23 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_fast_break += 1
                        self.shots_on_target_from_open_play += 1

                    if QTypes.ID_9 in qualifier_list and QTypes.ID_82 not in qualifier_list:
                        self.penalty_shots_saved += 1
                        self.shots_on_target_from_penalties += 1

                    if (
                            QTypes.ID_72 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.left_footed_shots_on_target += 1

                    if (
                            QTypes.ID_20 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.right_footed_shots_on_target += 1

                    if (
                            QTypes.ID_24 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_set_piece_cross += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_160 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_set_piece_throw_in += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_25 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_corners += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_26 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_direct_free_kicks += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_214 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_from_big_chances += 1

                    if (
                            QTypes.ID_328 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_with_first_touch += 1

                    if (
                            QTypes.ID_133 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_deflected += 1

                    if (
                            QTypes.ID_215 in qualifier_list
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_unassisted += 1

                    if (
                            self.x >= 83.3
                            and 21.1 <= self.y <= 78.9
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_inside_box += 1

                    if self.x < 83.3 and QTypes.ID_82 not in qualifier_list:
                        self.shots_on_target_outside_box += 1

                    if (
                            self.x >= 83.3
                            and self.y < 21.1
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_outside_box += 1

                    if (
                            self.x >= 83.3
                            and self.y > 78.9
                            and QTypes.ID_82 not in qualifier_list
                    ):
                        self.shots_on_target_outside_box += 1

                elif event.typeID == EventIDs.ID_16_Goal:
                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_28 in qualifier_list:
                        self.own_goal += 1

                    if QTypes.ID_28 not in qualifier_list:
                        self.total_shots += 1
                        self.goals += 1
                        self.shots_on_target += 1

                    if (
                            QTypes.ID_15 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.headed_shots_on_target += 1
                        self.headed_goals += 1

                    if (
                            QTypes.ID_22 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_regular_play += 1
                        self.goals_from_open_play += 1
                        self.shots_on_target_from_open_play += 1

                    if (
                            QTypes.ID_23 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_fast_break += 1
                        self.goals_from_open_play += 1
                        self.shots_on_target_from_open_play += 1
                        self.shots_on_target_from_fast_break += 1

                    if (
                            QTypes.ID_24 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_set_play += 1
                        self.goals_from_set_piece_cross += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_160 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_set_play += 1
                        self.goals_from_set_piece_throw_in += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_25 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_corners += 1
                        self.goals_from_set_play += 1
                        self.shots_on_target_from_set_play += 1

                    if (
                            QTypes.ID_26 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_direct_free_kicks += 1
                        self.goals_from_set_play += 1
                        self.shots_on_target_from_set_play += 1
                        self.shots_on_target_from_direct_free_kicks += 1

                    if QTypes.ID_9 in qualifier_list and QTypes.ID_28 not in qualifier_list:
                        self.goals_from_penalties += 1
                        self.shots_on_target_from_penalties += 1

                    if (
                            QTypes.ID_108 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_volleys += 1

                    if (
                            QTypes.ID_133 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_deflected += 1
                        self.shots_deflected += 1

                    if (
                            self.x >= 83.3
                            and 21.1 <= self.y <= 78.9
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_inside_the_box += 1
                        self.shots_on_target_inside_box += 1

                    if (
                            self.x < 83.3
                            or self.y < 21.1
                            or self.y > 78.9
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_outside_the_box += 1
                        self.shots_on_target_outside_box += 1

                    if (
                            QTypes.ID_72 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.left_footed_goals += 1
                        self.left_footed_shots_on_target += 1

                    if (
                            QTypes.ID_20 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.right_footed_goals += 1
                        self.right_footed_shots_on_target += 1

                    if (
                            QTypes.ID_21 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_with_other_part_of_body += 1

                    if (
                            QTypes.ID_214 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_from_big_chances += 1
                        self.shots_on_target_from_big_chances += 1

                    if (
                            QTypes.ID_215 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.goals_unassisted += 1
                        self.shots_unassisted += 1

                    if (
                            QTypes.ID_328 in qualifier_list
                            and QTypes.ID_28 not in qualifier_list
                    ):
                        self.shots_with_first_touch += 1
                elif event.typeID == EventIDs.ID_60_Chance_missed:
                    self.chance_missed += 1
                elif event.typeID == EventIDs.ID_3_Take_On:
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.dribble_event_id = int(event.eventID)

        self.non_penalty_goals = self.goals - self.goals_from_penalties
        self.total_shots_with_blocks = self.total_shots + self.blocked_shot
        self.penalty_shots_taken = (
                self.shots_on_target_from_penalties + self.shots_off_target_from_penalties
        )
        self.left_footed_shots = (
                self.left_footed_shots_on_target + self.left_footed_shots_off_target
        )  # + self.blocked_shot_left
        self.right_footed_shots = (
                self.right_footed_shots_on_target + self.right_footed_shots_off_target
        )  # + self.blocked_shot_right
        self.shots_inside_box = (
                self.shots_off_target_inside_box + self.shots_on_target_inside_box
        )  # + self.shots_blocked_inside_box
        self.shots_outside_box = (
                self.shots_off_target_outside_box + self.shots_on_target_outside_box
        )  # + self.shots_blocked_outside_box
        self.total_headed_shots = (
                self.headed_shots_on_target
                + self.headed_shots_off_target
                + self.headed_shots_blocked
        )
        self.total_big_chances = (
                self.shots_on_target_from_big_chances
                + self.shots_off_target_from_big_chances
                + self.shots_blocked_from_big_chances
                + self.chance_missed
        )
        self.big_chances_missed = self.total_big_chances - self.goals_from_big_chances
        self.total_direct_free_kicks = (
                self.shots_on_target_from_direct_free_kicks
                + self.direct_free_kicks_off_target
        )  # + self.blocked_direct_free_kicks
        self.shots_from_set_play = (
                self.shots_on_target_from_set_play
                + self.shots_off_target_from_set_play
                + self.shots_blocked_from_set_play
        )
        self.shots_from_fast_break = (
                self.shots_on_target_from_fast_break + self.shots_off_target_from_fast_break
        )
        if self.goals != 0:
            if total_minutes is not None:
                if total_minutes != 0:
                    self.minutes_per_goal = round(float(self.goals / total_minutes), 2)
            self.headed_goals_rate = round(float(self.headed_goals / self.goals), 2)
            self.open_play_goals_rate = round(
                float(self.goals_from_open_play / self.goals), 2
            )
        if self.total_shots != 0:
            self.no_block_shooting_percentage = round(
                float(self.goals / self.total_shots), 2
            )
        if self.total_shots_with_blocks != 0:
            self.headed_shots_rate = round(
                float(self.total_headed_shots / self.total_shots_with_blocks), 2
            )
            self.inside_the_box_shots_rate = round(
                float(self.shots_inside_box / self.total_shots_with_blocks), 2
            )
            self.outside_the_box_shots_rate = round(
                float(self.shots_outside_box / self.total_shots_with_blocks), 2
            )
            self.left_foot_shots_rate = round(
                float(self.left_footed_shots / self.total_shots_with_blocks), 2
            )
            self.right_foot_shots_rate = round(
                float(self.right_footed_shots / self.total_shots_with_blocks), 2
            )
            self.shots_on_target_rate = round(
                float(self.shots_on_target / self.total_shots_with_blocks), 2
            )
            self.blocked_shots_rate = round(
                float(self.blocked_shot / self.total_shots_with_blocks), 2
            )
            self.shooting_percentage = round(
                float(self.goals / self.total_shots_with_blocks), 2
            )
        if self.total_big_chances != 0:
            self.big_chance_conversion_rate = round(
                float(self.goals_from_big_chances / self.total_big_chances), 2
            )
        if self.total_direct_free_kicks != 0:
            self.free_kick_on_target_rate = round(
                float(
                    self.shots_on_target_from_direct_free_kicks
                    / self.total_direct_free_kicks
                ),
                2,
            )
        if self.total_shots_with_blocks != 0:
            # self.unassisted_goals_shots_rate = round(float(self.goals_unassisted / self.shots_unassisted), 2)
            self.unassisted_goals_shots_rate = round(
                float(self.shots_unassisted / self.total_shots_with_blocks), 2
            )

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        # print goal stats
        print("---- Shot & Goals ----")
        print("Goals: " + str(self.goals))
        print("Left footed goals: " + str(self.left_footed_goals))
        print("Right footed goals: " + str(self.right_footed_goals))
        print("Non-penalty goals: " + str(self.non_penalty_goals))
        print("Goals from inside the box: " + str(self.goals_inside_the_box))
        print("Goals from outside the box: " + str(self.goals_outside_the_box))
        print("Goals from open play: " + str(self.goals_from_open_play))
        print("Goals from regular play: " + str(self.goals_from_regular_play))
        print("Goals from fast breaks: " + str(self.goals_from_fast_break))
        print("Goals from set plays: " + str(self.goals_from_set_play))
        print("Goals from set piece cross: " + str(self.goals_from_set_piece_cross))
        print("Goals from throw in: " + str(self.goals_from_set_piece_throw_in))
        print("Goals from corners: " + str(self.goals_from_corners))
        print("Goals from penalties: " + str(self.goals_from_penalties))
        print("Goals with volleys: " + str(self.goals_from_volleys))
        print("Headed goals: " + str(self.headed_goals))
        print(
            "Goals with other part of body: " + str(self.goals_with_other_part_of_body)
        )
        print("Deflected goals: " + str(self.goals_deflected))
        print("Own goals: " + str(self.own_goal))
        print("goals unassisted: " + str(self.goals_unassisted))

        # print total shot stats
        print("Total shots (excluding blocks): " + str(self.total_shots))
        print("Total shots (including blocks): " + str(self.total_shots_with_blocks))
        print("Total shots from set play: " + str(self.shots_from_set_play))
        print("Total shots from fast break: " + str(self.shots_from_fast_break))
        print("Shots from inside the box: " + str(self.shots_inside_box))
        print("Shots from outside the box: " + str(self.shots_outside_box))
        print("Left footed shots: " + str(self.left_footed_shots))
        print("Right footed shots: " + str(self.right_footed_shots))
        print("Headed shots: " + str(self.total_headed_shots))
        print("Penalty shots taken: " + str(self.penalty_shots_taken))
        print(
            "Shots attempted first time without another touch: "
            + str(self.shots_with_first_touch)
        )
        print("Shots cleared off line: " + str(self.shot_cleared_off_line))
        print(
            "Shots cleared off line inside the box: "
            + str(self.shots_cleared_off_the_line_inside_box)
        )
        print(
            "Shots cleared off line outside the box: "
            + str(self.shots_cleared_off_the_line_outside_box)
        )
        print("Deflected shots: " + str(self.shots_deflected))
        print("shots unassisted: " + str(self.shots_unassisted))
        print("Total shots after dribble: " + str(self.shots_after_dribble))

        # Blocked shots
        print("Blocked shots: " + str(self.blocked_shot))
        print("Blocked shots left: " + str(self.blocked_shot_left))
        print("Blocked shots right: " + str(self.blocked_shot_right))
        print("Blocked shots headed: " + str(self.headed_shots_blocked))
        print(
            "Blocked shots with other parts of body: "
            + str(self.blocked_shots_with_other_part_of_body)
        )
        print(
            "Blocked shots from inside the box: " + str(self.shots_blocked_inside_box)
        )
        print(
            "Blocked shots from outside the box: " + str(self.shots_blocked_outside_box)
        )

        # print shots on target
        print("Total shots on target: " + str(self.shots_on_target))
        print(
            "Shots on target from inside the box: "
            + str(self.shots_on_target_inside_box)
        )
        print(
            "Shots on target from outside the box: "
            + str(self.shots_on_target_outside_box)
        )
        print("Headed shots on target: " + str(self.headed_shots_on_target))
        print("Left footed shots on target: " + str(self.left_footed_shots_on_target))
        print("Right footed shots on target: " + str(self.right_footed_shots_on_target))
        print(
            "Shots on target from set plays: " + str(self.shots_on_target_from_set_play)
        )
        print(
            "Shots on target from open play: "
            + str(self.shots_on_target_from_open_play)
        )
        print(
            "Shots on target from penalties: "
            + str(self.shots_on_target_from_penalties)
        )
        print("Penalty shots saved (shooter): " + str(self.penalty_shots_saved))
        print("Shots on target from corners: " + str(self.shots_on_target_from_corners))
        print(
            "Shots on target from throw ins: "
            + str(self.shots_on_target_from_set_piece_throw_in)
        )

        # print shots off target
        print("Total shots off target: " + str(self.shots_off_target))
        print(
            "Shots off target from inside the box: "
            + str(self.shots_off_target_inside_box)
        )
        print(
            "Shots off target from outside the box: "
            + str(self.shots_off_target_outside_box)
        )
        print("Headed shots off target: " + str(self.headed_shots_off_target))
        print("Left footed shots off target: " + str(self.left_footed_shots_off_target))
        print(
            "Right footed shots off target: " + str(self.right_footed_shots_off_target)
        )
        print(
            "Shots off target from set plays: "
            + str(self.shots_off_target_from_set_play)
        )
        print(
            "Shots off target from open play: "
            + str(self.shots_off_target_from_open_play)
        )
        print("Shots hit woodwork: " + str(self.shots_hit_woodwork))
        print(
            "Shots off target from penalties: "
            + str(self.shots_off_target_from_penalties)
        )
        print(
            "Shots off target from corners: " + str(self.shots_off_target_from_corners)
        )
        print(
            "Shots off target from throw ins: "
            + str(self.shots_off_target_from_set_piece_throw_in)
        )

        # Free kicks
        # print("DIRECT FREE KICKS")
        print(
            "Shot attempts from direct free kicks: " + str(self.total_direct_free_kicks)
        )
        print("Goals from direct free kicks: " + str(self.goals_from_direct_free_kicks))
        print(
            "Shot attempts from free kicks on target: "
            + str(self.shots_on_target_from_direct_free_kicks)
        )
        print(
            "Shot attempts from free kicks off target: "
            + str(self.direct_free_kicks_off_target)
        )
        print("Blocked direct free kicks: " + str(self.blocked_direct_free_kicks))
        print(
            "Percentage of free kicks on target: " + str(self.free_kick_on_target_rate)
        )

        # Big Chances
        # print("BIG CHANCES")
        print("Total big chances: " + str(self.total_big_chances))
        print("Goals from big chances: " + str(self.goals_from_big_chances))
        print(
            "Shots on target from big chances: "
            + str(self.shots_on_target_from_big_chances)
        )
        print(
            "Shots off target from big chances: "
            + str(self.shots_off_target_from_big_chances)
        )
        print(
            "Blocked shots from big chances: "
            + str(self.shots_blocked_from_big_chances)
        )
        print("Big chances missed: " + str(self.big_chances_missed))
        print("Chances missed: " + str(self.chance_missed))
        print(
            "Big chance conversion percentage: " + str(self.big_chance_conversion_rate)
        )

        # goal percentages
        print("Minutes per goal: " + str(self.minutes_per_goal))
        print("Percentage of shots on target: " + str(self.shots_on_target_rate))
        print("Percentage of goals headed: " + str(self.headed_goals_rate))
        print("Percentage of shots headed: " + str(self.headed_shots_rate))
        print("Percentage of goals from open play: " + str(self.open_play_goals_rate))
        print(
            "Percentage of shots inside the box: " + str(self.inside_the_box_shots_rate)
        )
        print(
            "Percentage of shots outside the box: "
            + str(self.outside_the_box_shots_rate)
        )
        print("Percentage of shots via left foot: " + str(self.left_foot_shots_rate))
        print("Percentage of shots via right foot: " + str(self.right_foot_shots_rate))
        print("Percentage of shots blocked: " + str(self.blocked_shots_rate))  #
        print(
            "Shooting percentage (goals per shot excluding blocks): "
            + str(self.no_block_shooting_percentage)
        )
        print(
            "Shot conversion rate (goals per shot including blocks): "
            + str(self.shooting_percentage)
        )
        print(
            "goals unassisted / shots unassisted: "
            + str(self.unassisted_goals_shots_rate)
        )

        print("DEBUG")
        print("self.shots_outside_box: " + str(self.shots_outside_box))
        print(
            "self.shots_off_target_outside_box: "
            + str(self.shots_off_target_outside_box)
        )
        print(
            "self.shots_on_target_outside_box: " + str(self.shots_on_target_outside_box)
        )
        print("self.shots_blocked_outside_box: " + str(self.shots_blocked_outside_box))

    def saveResults(self):
        print("save results method is called")

        self.event_results["Goals"] = self.goals
        self.event_results["Left footed Goals"] = self.left_footed_goals
        self.event_results["Right footed goals"] = self.right_footed_goals
        self.event_results["Non-penalty goals"] = self.non_penalty_goals
        self.event_results["Goals from inside the box"] = self.goals_inside_the_box
        self.event_results["Goals from outside the box"] = self.goals_outside_the_box
        self.event_results["Goals from open play"] = self.goals_from_open_play
        self.event_results["Goals from regular play"] = self.goals_from_regular_play
        self.event_results["Goals from fast breaks"] = self.goals_from_fast_break
        self.event_results["Goals from set plays"] = self.goals_from_set_play
        self.event_results[
            "Goals from set piece cross"
        ] = self.goals_from_set_piece_cross
        self.event_results["Goals from throw in"] = self.goals_from_set_piece_throw_in
        self.event_results["Goals from corners"] = self.goals_from_corners
        self.event_results["Goals from penalties"] = self.goals_from_penalties
        self.event_results["Goals with volleys"] = self.goals_from_volleys
        self.event_results["Headed goals"] = self.headed_goals
        self.event_results[
            "Goals with other part of body"
        ] = self.goals_with_other_part_of_body
        self.event_results["Deflected goals"] = self.goals_deflected
        self.event_results["Own goals"] = self.own_goal
        self.event_results["goals unassisted"] = self.goals_unassisted

        self.event_results["otal shots (excluding blocks)"] = self.total_shots
        self.event_results[
            "Total shots (including blocks)"
        ] = self.total_shots_with_blocks
        self.event_results["Total shots from set play"] = self.shots_from_set_play
        self.event_results["Total shots from fast break"] = self.shots_from_fast_break
        self.event_results["Shots from inside the box"] = self.shots_inside_box
        self.event_results["Shots from outside the box"] = self.shots_outside_box
        self.event_results["Left footed shots"] = self.left_footed_shots
        self.event_results["Right footed shots"] = self.right_footed_shots
        self.event_results["Headed shots"] = self.total_headed_shots
        self.event_results["Penalty shots taken"] = self.penalty_shots_taken
        self.event_results[
            "Shots attempted first time without another touch"
        ] = self.shots_with_first_touch
        self.event_results["Shots cleared off line"] = self.shot_cleared_off_line
        self.event_results[
            "Shots cleared off line inside the box"
        ] = self.shots_cleared_off_the_line_inside_box
        self.event_results[
            "Shots cleared off line ourside the box"
        ] = self.shots_cleared_off_the_line_outside_box
        self.event_results["Deflected shots"] = self.shots_deflected
        self.event_results["shots unassisted"] = self.shots_unassisted
        self.event_results["Total shots after dribble"] = self.shots_after_dribble

        self.event_results["Blocked shots"] = self.blocked_shot
        self.event_results["Blocked shots left"] = self.blocked_shot_left
        self.event_results["Blocked shots right"] = self.blocked_shot_right
        self.event_results["Blocked shots headed"] = self.headed_shots_blocked
        self.event_results[
            "Blocked shots with other parts of body"
        ] = self.blocked_shots_with_other_part_of_body
        self.event_results[
            "Blocked shots from inside the box"
        ] = self.shots_blocked_inside_box
        self.event_results[
            "Blocked shots from outside the box"
        ] = self.shots_blocked_outside_box

        self.event_results["Total shots on target"] = self.shots_on_target
        self.event_results[
            "Shots on target from inside the box"
        ] = self.shots_on_target_inside_box
        self.event_results[
            "Shots on target from outside the box"
        ] = self.shots_on_target_outside_box
        self.event_results["Headed shots on target"] = self.headed_shots_on_target
        self.event_results[
            "Left footed shots on target"
        ] = self.left_footed_shots_on_target
        self.event_results[
            "Right footed shots on target"
        ] = self.right_footed_shots_on_target
        self.event_results[
            "Shots on target from set plays"
        ] = self.shots_on_target_from_set_play
        self.event_results[
            "Shots on target from open play"
        ] = self.shots_on_target_from_open_play
        self.event_results[
            "Shots on target from penalties"
        ] = self.shots_on_target_from_penalties
        self.event_results["Penalty shots saved (shooter)"] = self.penalty_shots_saved
        self.event_results[
            "Shots on target from corners"
        ] = self.shots_on_target_from_corners
        self.event_results[
            "Shots on target from throw ins"
        ] = self.shots_on_target_from_set_piece_throw_in

        # TODO: continue from here
        self.event_results["Total shots off target"] = self.shots_off_target
        self.event_results[
            "Shots off target from inside the box"
        ] = self.shots_off_target_inside_box
        self.event_results[
            "Shots off target from outside the box"
        ] = self.shots_off_target_outside_box
        self.event_results["Headed shots off target"] = self.headed_shots_off_target
        self.event_results[
            "Left footed shots off target"
        ] = self.left_footed_shots_off_target
        self.event_results[
            "Right footed shots off target"
        ] = self.right_footed_shots_off_target
        self.event_results[
            "Shots off target from set plays"
        ] = self.shots_off_target_from_set_play
        self.event_results[
            "Shots off target from open play"
        ] = self.shots_off_target_from_open_play
        self.event_results["Shots hit woodwork"] = self.shots_hit_woodwork
        self.event_results[
            "Shots off target from penalties"
        ] = self.shots_off_target_from_penalties
        self.event_results[
            "Shots off target from corners"
        ] = self.shots_off_target_from_corners
        self.event_results[
            "Shots off target from throw ins"
        ] = self.shots_off_target_from_set_piece_throw_in

        self.event_results[
            "Shot attempts from direct free kicks"
        ] = self.total_direct_free_kicks
        self.event_results[
            "Goals from direct free kicks"
        ] = self.goals_from_direct_free_kicks
        self.event_results[
            "Shot attempts from free kicks on target"
        ] = self.shots_on_target_from_direct_free_kicks
        self.event_results[
            "Shot attempts from free kicks off target"
        ] = self.direct_free_kicks_off_target
        self.event_results["Blocked direct free kicks"] = self.blocked_direct_free_kicks
        self.event_results[
            "Percentage of free kicks on target"
        ] = self.free_kick_on_target_rate

        self.event_results["Total big chances"] = self.total_big_chances
        self.event_results["Goals from big chances"] = self.goals_from_big_chances
        self.event_results[
            "Shots on target from big chances"
        ] = self.shots_on_target_from_big_chances
        self.event_results[
            "Shots off target from big chances"
        ] = self.shots_off_target_from_big_chances
        self.event_results[
            "Blocked shots from big chances"
        ] = self.shots_blocked_from_big_chances
        self.event_results["Chances missed"] = self.chance_missed
        self.event_results[
            "Big chance conversion percentage"
        ] = self.big_chance_conversion_rate

        self.event_results["Minutes per goal"] = self.minutes_per_goal
        self.event_results["Percentage of shots on target"] = self.shots_on_target_rate
        self.event_results["Percentage of goals headed"] = self.headed_goals_rate
        self.event_results["Percentage of shots headed"] = self.headed_shots_rate
        self.event_results[
            "Percentage of goals from open play"
        ] = self.open_play_goals_rate
        self.event_results[
            "Percentage of shots inside the box"
        ] = self.inside_the_box_shots_rate
        self.event_results[
            "Percentage of shots outside the box"
        ] = self.outside_the_box_shots_rate
        self.event_results[
            "Percentage of shots via left foot"
        ] = self.left_foot_shots_rate
        self.event_results[
            "Percentage of shots via right foot"
        ] = self.right_foot_shots_rate
        self.event_results["Percentage of shots blocked"] = self.right_foot_shots_rate
        self.event_results["Percentage of shots blocked"] = self.blocked_shots_rate
        self.event_results[
            "Shooting percentage (goals per shot excluding blocks)"
        ] = self.no_block_shooting_percentage
        self.event_results[
            "Shot conversion rate (goals per shot including blocks)"
        ] = self.shooting_percentage
        self.event_results[
            "goals unassisted / shots unassisted"
        ] = self.unassisted_goals_shots_rate

    def getDataFrame(self):
        self.data = [
            ["Goals", self.goals],
            ["Left footed goals", self.left_footed_goals],
            ["Right footed goals", self.right_footed_goals],
            ["Non-penalty goals", self.non_penalty_goals],
            ["Goals from inside the box", self.goals_inside_the_box],
            ["Goals from outside the box", self.goals_outside_the_box],
            ["Goals from open play", self.goals_from_open_play],
            ["Goals from regular play", self.goals_from_regular_play],
            ["Goals from fast breaks", self.goals_from_fast_break],
            ["Goals from set plays", self.goals_from_set_play],
            ["Goals from set piece cross", self.goals_from_set_piece_cross],
            ["Goals from throw in", self.goals_from_set_piece_throw_in],
            ["Goals from corners", self.goals_from_corners],
            ["Goals from penalties", self.goals_from_penalties],
            ["Goals with volleys", self.goals_from_volleys],
            ["Headed goals", self.headed_goals],
            ["Goals with other part of body", self.goals_with_other_part_of_body],
            ["Deflected goals", self.goals_deflected],
            ["Own goals", self.own_goal],
            ["goals unassisted", self.goals_unassisted],
            ["Total shots (excluding blocks)", self.total_shots],
            ["Total shots (including blocks)", self.total_shots_with_blocks],
            ["Total shots from set play", self.shots_from_set_play],
            ["Total shots from fast break", self.shots_from_fast_break],
            ["Shots from inside the box", self.shots_inside_box],
            ["Shots from outside the box", self.shots_outside_box],
            ["Left footed shots", self.left_footed_shots],
            ["Right footed shots", self.right_footed_shots],
            ["Headed shots", self.total_headed_shots],
            ["Penalty shots taken", self.penalty_shots_taken],
            [
                "Shots attempted first time without another touch",
                self.shots_with_first_touch,
            ],
            ["Shots cleared off line", self.shot_cleared_off_line],
            [
                "Shots cleared off line inside the box",
                self.shots_cleared_off_the_line_inside_box,
            ],
            [
                "Shots cleared off line outside the box",
                self.shots_cleared_off_the_line_outside_box,
            ],
            ["Deflected shots", self.shots_deflected],
            ["shots unassisted", self.shots_unassisted],
            ["Total shots after dribble", self.shots_after_dribble],
            ["Blocked shots", self.blocked_shot],
            ["Blocked shots left", self.blocked_shot_left],
            ["Blocked shots right", self.blocked_shot_right],
            ["Blocked shots headed", self.headed_shots_blocked],
            [
                "Blocked shots with other parts of body",
                self.blocked_shots_with_other_part_of_body,
            ],
            ["Blocked shots from inside the box", self.shots_blocked_inside_box],
            ["Blocked shots from outside the box", self.shots_blocked_outside_box],
            ["Total shots on target", self.shots_on_target],
            ["Shots on target from inside the box", self.shots_on_target_inside_box],
            ["Shots on target from outside the box", self.shots_on_target_outside_box],
            ["Headed shots on target", self.headed_shots_on_target],
            ["Left footed shots on target", self.left_footed_shots_on_target],
            ["Right footed shots on target", self.right_footed_shots_on_target],
            ["Shots on target from set plays", self.shots_on_target_from_set_play],
            ["Shots on target from open play", self.shots_on_target_from_open_play],
            ["Shots on target from penalties", self.shots_on_target_from_penalties],
            ["Penalty shots saved (shooter)", self.penalty_shots_saved],
            ["Shots on target from corners", self.shots_on_target_from_corners],
            [
                "Shots on target from throw ins",
                self.shots_on_target_from_set_piece_throw_in,
            ],
            ["Total shots off target", self.shots_off_target],
            ["Shots off target from inside the box", self.shots_off_target_inside_box],
            [
                "Shots off target from outside the box",
                self.shots_off_target_outside_box,
            ],
            ["Headed shots off target", self.headed_shots_off_target],
            ["Left footed shots off target", self.left_footed_shots_off_target],
            ["Right footed shots off target", self.right_footed_shots_off_target],
            ["Shots off target from set plays", self.shots_off_target_from_set_play],
            ["Shots off target from open play", self.shots_off_target_from_open_play],
            ["Shots hit woodwork", self.shots_hit_woodwork],
            ["Shots off target from penalties", self.shots_off_target_from_penalties],
            ["Shots off target from corners", self.shots_off_target_from_corners],
            [
                "Shots off target from throw ins",
                self.shots_off_target_from_set_piece_throw_in,
            ],
            ["Shot attempts from direct free kicks", self.total_direct_free_kicks],
            ["Goals from direct free kicks", self.goals_from_direct_free_kicks],
            [
                "Shot attempts from free kicks on target",
                self.shots_on_target_from_direct_free_kicks,
            ],
            [
                "Shot attempts from free kicks off target",
                self.direct_free_kicks_off_target,
            ],
            ["Blocked direct free kicks", self.blocked_direct_free_kicks],
            ["Percentage of free kicks on target", self.free_kick_on_target_rate],
            ["Total big chances", self.total_big_chances],
            ["Goals from big chances", self.goals_from_big_chances],
            ["Shots on target from big chances", self.shots_on_target_from_big_chances],
            [
                "Shots off target from big chances",
                self.shots_off_target_from_big_chances,
            ],
            ["Blocked shots from big chances", self.shots_blocked_from_big_chances],
            ["Big chances missed", self.big_chances_missed],
            ["Chances missed", self.chance_missed],
            ["Big chance conversion percentage", self.big_chance_conversion_rate],
            ["Minutes per goal", self.minutes_per_goal],
            ["Percentage of shots on target", self.shots_on_target_rate],
            ["Percentage of goals headed", self.headed_goals_rate],
            ["Percentage of shots headed", self.headed_shots_rate],
            ["Percentage of goals from open play", self.open_play_goals_rate],
            ["Percentage of shots inside the box", self.inside_the_box_shots_rate],
            ["Percentage of shots outside the box", self.outside_the_box_shots_rate],
            ["Percentage of shots via left foot", self.left_foot_shots_rate],
            ["Percentage of shots via right foot", self.right_foot_shots_rate],
            ["Percentage of shots blocked", self.blocked_shots_rate],  #
            [
                "Shooting percentage (goals per shot excluding blocks)",
                self.no_block_shooting_percentage,
            ],
            [
                "Shot conversion rate (goals per shot including blocks)",
                self.shooting_percentage,
            ],
        ]
        # Create the pandas DataFrame
        df = pd.DataFrame(self.data, columns=["", "Total"])
