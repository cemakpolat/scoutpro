# This class checks the following Opta F24 events:
#     "1":"Pass"
# author:Cem Akpolat, Doruk Sahinel
from src.events.Events import EventIDs
from src.events.QTypes import QTypes
import math


class PassEvent:
    def __init__(self):

        # simple pass counters
        self.passes_total = 0
        self.passes_successful = 0
        self.passes_unsuccessful = 0
        self.forward_passes = 0
        self.offensive_passes = 0
        self.successful_offensive_passes = 0
        self.unsuccessful_offensive_passes = 0
        self.backward_passes = 0
        self.sideway_passes = 0
        self.total_passes_in_defensive_third = 0
        self.total_passes_in_middle_third = 0
        self.total_passes_in_attacking_third = 0
        self.total_passes_successful_in_defensive_third = 0
        self.total_passes_successful_in_middle_third = 0
        self.total_passes_successful_in_attacking_third = 0
        self.total_passes_successful_in_box = 0
        self.pass_completion_percentage_in_the_final_third = 0
        self.pass_completion_percentage_in_the_defensive_third = 0
        self.pass_completion_percentage_in_the_middle_third = 0
        self.total_passes_into_defensive_third = 0
        self.total_passes_into_middle_third = 0
        self.total_passes_into_attacking_third = 0
        self.total_passes_into_box = 0
        self.passes_into_box_with_cross = 0
        self.total_passes_into_opponent_half = 0
        self.passes_into_box_with_cross = 0
        self.total_passes_successful_into_defensive_third = 0
        self.total_passes_successful_into_middle_third = 0
        self.total_passes_successful_into_attacking_third = 0
        self.total_passes_successful_into_box = 0
        self.pass_completion_percentage_into_defensive_third = 0
        self.pass_completion_percentage_into_middle_third = 0
        self.pass_completion_percentage_into_attacking_third = 0
        self.total_passes_into_own_half = 0
        self.total_passes_successful_into_opponent_half = 0
        self.total_passes_successful_into_own_half = 0
        self.total_passes_forward = 0
        self.forward_pass_attempt_rate = 0

        self.total_pass_length = 0
        self.average_pass_length = 0
        self.average_pass_length = 0
        self.successful_passes_into_box_with_cross = 0
        self.pass_originate_and_end_in_opponent_half = 0
        self.pass_originate_and_end_in_opponent_half_successful = 0
        self.pass_completion_percentage_in_opponent_half = 0
        self.pass_originate_and_end_in_own_half = 0
        self.pass_originate_and_end_in_own_half_successful = 0
        self.total_passes_into_defensive_third_from_own_box = 0
        self.total_crosses_into_box = 0
        self.total_passes_into_box_with_cross = 0
        self.unsuccessful_passes_in_opponent_half = 0
        self.unsuccessful_passes_in_own_half = 0

        # cross counters
        self.total_crosses = 0
        self.successful_crosses = 0
        self.unsuccessful_crosses = 0
        self.crosses_from_free_kicks = 0
        self.successful_crosses_from_free_kicks = 0
        self.crosses_from_right_third = 0
        self.crosses_from_left_third = 0
        self.crosses_from_open_play = 0
        self.successful_crosses_from_open_play = 0
        self.overhit_cross = 0
        self.unsuccessful_crosses_from_open_play = 0
        self.cross_success_rate = 0
        self.cross_success_rate_open_play = 0
        self.cross_pass_ratio_in_attacking_third = 0
        self.successful_crosses_into_box = 0

        self.successful_passes_into_box_with_cross = 0
        self.pass_originate_and_end_in_opponent_half = 0
        self.pass_originate_and_end_in_opponent_half_successful = 0
        self.pass_completion_percentage_in_opponent_half = 0
        self.pass_originate_and_end_in_own_half = 0
        self.pass_originate_and_end_in_own_half_successful = 0
        self.total_passes_into_defensive_third_from_own_box = 0
        self.total_crosses_into_box = 0
        self.total_passes_into_box_with_cross = 0
        self.unsuccessful_passes_in_opponent_half = 0
        self.unsuccessful_passes_in_own_half = 0

        self.total_pass_length = 0

        # free kick counters
        self.total_free_kicks_taken = 0
        self.successful_free_kick = 0
        self.unsuccessful_free_kick = 0
        self.direct_free_kick = 0
        self.indirect_free_kick = 0

        # corner counters
        self.total_corners = 0
        self.successful_corner = 0
        self.unsuccessful_corner = 0
        self.corners_into_box_successful = 0
        self.corner_left = 0
        self.corner_right = 0
        self.successful_corner_left = 0
        self.successful_corner_right = 0
        self.unsuccessful_corner_left = 0
        self.unsuccessful_corner_right = 0
        self.corner_cross_accuracy_percentage = 0
        self.corner_success_percentage_left = 0
        self.corner_success_percentage_right = 0
        self.crosses_from_corners = 0
        self.successful_crosses_from_corners = 0
        self.short_corners = 0

        # keeper throws
        self.keeper_throw = 0
        self.successful_keeper_throw = 0
        self.unsuccessful_keeper_throw = 0
        self.goal_kick = 0

        # throw_ins
        self.throw_in = 0
        self.successful_throw_in = 0
        self.unsuccessful_throw_in = 0
        self.pass_success_rate = 0
        # long passes
        self.long_passes = 0
        self.successful_long_passes = 0
        self.unsuccessful_long_passes = 0
        self.long_pass_ratio = 0
        self.long_pass_success_rate = 0

        # pass types
        self.headed_pass = 0
        self.headed_pass_successful = 0
        self.through_ball = 0
        self.through_ball_successful = 0
        self.chipped_passes = 0
        self.chipped_passes_successful = 0
        self.lay_off_passes = 0
        self.lay_off_passes_successful = 0
        self.lay_off_passes_unsuccessful = 0
        self.launch_passes = 0
        self.successful_launch_passes = 0
        self.flick_on_passes = 0
        self.flick_on_passes_successful = 0
        self.flick_on_passes_unsuccessful = 0
        self.flick_on_passes_success_ratio = 0
        self.pull_back_passes = 0
        self.switch_play_passes = 0
        self.switch_play_passes_successful = 0
        self.blocked_passes = 0

        # assists and key passes
        self.assist_and_key_passes = 0
        self.second_assist = 0

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.angle = 0
        self.event_results = {}
        self.eventType = "Pass"
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
                self.x = event.x
                self.y = event.y
                if event.typeID == EventIDs.ID_74_Blocked_Pass:
                    self.blocked_passes += 1
                if event.typeID == EventIDs.ID_1_Pass_Events:
                    qualifier_list = []
                    for q in event.qEvents:
                        # qlist
                        qualifier_list.append(q.qualifierID)
                        if q.qualifierID == QTypes.ID_140:
                            self.x_end = float(q.value)
                        elif q.qualifierID == QTypes.ID_141:
                            self.y_end = float(q.value)
                        elif q.qualifierID == QTypes.ID_213:
                            self.angle = math.degrees(is_float(q.value))
                        # exclude some qtypes from the qlist and proceed
                    if QTypes.ID_6 in qualifier_list:
                        self.total_corners += 1
                        if (
                            QTypes.ID_1 not in qualifier_list
                            and QTypes.ID_2 not in qualifier_list
                        ):
                            self.short_corners += 1
                        if QTypes.ID_2 in qualifier_list:
                            self.crosses_from_corners += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_crosses_from_corners += 1
                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.successful_corner += 1
                            if self.y > 50:
                                self.successful_corner_left += 1
                            if self.y < 50:
                                self.successful_corner_right += 1
                            if self.x_end >= 83.3 and 21.1 <= self.y_end <= 78.9:
                                self.corners_into_box_successful += 1
                        elif event.outcome == EventIDs.UNSUCCESSFUL:
                            self.unsuccessful_corner += 1
                            if self.y > 50:
                                self.unsuccessful_corner_left += 1
                            if self.y < 50:
                                self.unsuccessful_corner_right += 1

                    if (
                        QTypes.ID_2 not in qualifier_list
                        and QTypes.ID_107 not in qualifier_list
                        and QTypes.ID_123 not in qualifier_list
                    ):
                        self.passes_total += 1
                        if QTypes.ID_1 in qualifier_list:
                            self.long_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_long_passes += 1
                            if event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_long_passes += 1
                        if QTypes.ID_155 in qualifier_list:
                            self.chipped_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.chipped_passes_successful += 1
                        if self.x <= 33.3:
                            self.total_passes_in_defensive_third += 1
                        elif self.x > 33.3 and self.x <= 66.6:
                            self.total_passes_in_middle_third += 1
                        elif self.x > 66.6:
                            self.total_passes_in_attacking_third += 1

                        if self.x_end <= 33.3:
                            self.total_passes_into_defensive_third += 1
                            if self.x <= 17 and 21.1 <= self.y <= 78.9:
                                self.total_passes_into_defensive_third_from_own_box += 1
                        elif self.x_end > 33.3 and self.x_end <= 66.6:
                            self.total_passes_into_middle_third += 1

                        if self.x < 66.6 and self.x_end >= 66.6:
                            self.total_passes_into_attacking_third += 1

                        if self.x < 50 and self.x_end >= 50:
                            self.total_passes_into_opponent_half += 1
                        if self.x > 50 and self.x_end >= 50:
                            self.pass_originate_and_end_in_opponent_half += 1
                        elif self.x_end < 50:
                            self.total_passes_into_own_half += 1
                            if self.x < 50:
                                self.pass_originate_and_end_in_own_half += 1

                        if self.x_end >= 83 and self.y_end >= 21.1 and self.y_end <= 78.9:
                            self.total_passes_into_box += 1

                        if self.angle >= 315 or self.angle < 45:
                            self.total_passes_forward += 1

                        if event.outcome == EventIDs.SUCCESSFUL:
                            self.passes_successful += 1

                            if self.x <= 33.3:
                                self.total_passes_successful_in_defensive_third += 1
                            elif self.x > 33.3 and self.x <= 66.6:
                                self.total_passes_successful_in_middle_third += 1
                            elif self.x > 66.6:
                                self.total_passes_successful_in_attacking_third += 1

                            if self.x >= 83 and self.y >= 21.1 and self.y <= 78.9:
                                self.total_passes_successful_in_box += 1
                            elif self.x_end <= 33.3:
                                self.total_passes_successful_into_defensive_third += 1

                            elif self.x_end > 33.3 and self.x_end <= 66.6:
                                self.total_passes_successful_into_middle_third += 1

                            elif self.x < 66.6 and self.x_end >= 66.6:
                                self.total_passes_successful_into_attacking_third += 1

                            if self.x < 50 and self.x_end >= 50:
                                self.total_passes_successful_into_opponent_half += 1

                            elif self.x > 50 and self.x_end >= 50:
                                self.pass_originate_and_end_in_opponent_half_successful += 1

                            if self.x_end <= 50 and self.x > 50:
                                self.total_passes_successful_into_own_half += 1

                            elif self.x_end <= 50 and self.x < 50:
                                self.pass_originate_and_end_in_own_half_successful += 1

                            if self.x_end >= 83 and 21.1 <= self.y_end <= 78.9:
                                self.total_passes_successful_into_box += 1

                        elif event.outcome == EventIDs.UNSUCCESSFUL:
                            self.passes_unsuccessful += 1
                            if self.x_end >= 50:
                                self.unsuccessful_passes_in_opponent_half += 1
                            elif self.x_end < 50:
                                self.unsuccessful_passes_in_own_half += 1

                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_2:
                            self.total_crosses += 1
                            if self.y <= 33.3:
                                self.crosses_from_right_third += 1

                            if self.y > 66.6:
                                self.crosses_from_left_third += 1

                            if self.x_end >= 83.3 and 21.1 <= self.y_end <= 78.9:
                                self.total_crosses_into_box += 1

                            qlist = []
                            for q in event.qEvents:
                                qlist.append(q.qualifierID)

                            if QTypes.ID_5 in qlist and QTypes.ID_2 in qlist:
                                self.crosses_from_free_kicks += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_crosses_from_free_kicks += 1

                            if (
                                QTypes.ID_2 in qlist
                                and QTypes.ID_5 not in qlist
                                and QTypes.ID_6 not in qlist
                            ):
                                self.crosses_from_open_play += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_crosses_from_open_play += 1
                                elif event.outcome == EventIDs.UNSUCCESSFUL:
                                    self.unsuccessful_crosses_from_open_play += 1

                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_crosses += 1
                                if self.x_end >= 83.3 and 21.1 <= self.y_end <= 78.9:
                                    self.successful_crosses_into_box += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_crosses += 1

                        elif q.qualifierID == QTypes.ID_107:
                            self.throw_in += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_throw_in += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_throw_in += 1
                        elif q.qualifierID == QTypes.ID_123:
                            self.keeper_throw += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_keeper_throw += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_keeper_throw += 1

                        elif q.qualifierID == QTypes.ID_3:
                            self.headed_pass += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.headed_pass_successful += 1
                        elif q.qualifierID == QTypes.ID_4:
                            self.through_ball += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.through_ball_successful += 1
                        elif q.qualifierID == QTypes.ID_5:
                            self.total_free_kicks_taken += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_free_kick += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.unsuccessful_free_kick += 1

                        elif (
                            q.qualifierID == QTypes.ID_140
                        ):  # TODO: X_end and X double check!
                            self.x_end = float(q.value)
                            self.x = float(event.x)
                            if self.x < self.x_end:
                                self.offensive_passes += 1
                                if event.outcome == EventIDs.SUCCESSFUL:
                                    self.successful_offensive_passes += 1
                                elif event.outcome == EventIDs.UNSUCCESSFUL:
                                    self.unsuccessful_offensive_passes += 1
                            elif self.x > self.x_end:
                                self.backward_passes += 1
                            elif self.x == self.x_end:
                                self.sideway_passes += 1

                        elif q.qualifierID == QTypes.ID_152:
                            self.direct_free_kick += 1

                        elif q.qualifierID == QTypes.ID_156:
                            self.lay_off_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.lay_off_passes_successful += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.lay_off_passes_unsuccessful += 1

                        elif q.qualifierID == QTypes.ID_157:
                            self.launch_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.successful_launch_passes += 1

                        elif q.qualifierID == QTypes.ID_168:
                            self.flick_on_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.flick_on_passes_successful += 1
                            elif event.outcome == EventIDs.UNSUCCESSFUL:
                                self.flick_on_passes_unsuccessful += 1

                        elif q.qualifierID == QTypes.ID_195:
                            self.pull_back_passes += 1

                        elif q.qualifierID == QTypes.ID_196:
                            self.switch_play_passes += 1
                            if event.outcome == EventIDs.SUCCESSFUL:
                                self.switch_play_passes_successful += 1

                        elif q.qualifierID == QTypes.ID_210:
                            self.assist_and_key_passes += 1

                        elif q.qualifierID == QTypes.ID_218:
                            self.second_assist += 1

                        elif q.qualifierID == QTypes.ID_124:
                            self.goal_kick += 1

                        elif q.qualifierID == QTypes.ID_241:
                            self.indirect_free_kick += 1

                        elif q.qualifierID == QTypes.ID_345:
                            self.overhit_cross += 1

                        elif q.qualifierID == QTypes.ID_212:
                            self.total_pass_length += float(q.value)

        self.total_passes_into_box_with_cross = (
            self.total_passes_into_box + self.total_crosses_into_box
        )
        self.successful_passes_into_box_with_cross = (
            self.successful_crosses_into_box + self.total_passes_successful_into_box
        )
        if self.passes_total != 0:
            self.average_pass_length = round(
                float(self.total_pass_length / self.passes_total), 2
            )

            self.pass_success_rate = round(
                (100 * float(self.passes_successful / self.passes_total)), 2
            )

            self.forward_pass_attempt_rate = round(
                (100 * float(self.total_passes_forward / self.passes_total)), 2
            )
        
        if self.total_crosses != 0:
            self.cross_success_rate = round(
                (100 * float(self.successful_crosses / self.total_crosses)), 2
            )
        if self.crosses_from_open_play != 0:
            self.cross_success_rate_open_play = round(
                (
                    100
                    * float(
                        self.successful_crosses_from_open_play
                        / self.crosses_from_open_play
                    )
                ),
                2,
            )
        if self.total_passes_in_attacking_third != 0 and (self.crosses_from_open_play + self.total_passes_in_attacking_third) != 0:
            self.cross_pass_ratio_in_attacking_third = round(
                (
                    100
                    * float(
                        self.crosses_from_open_play
                        / (
                            self.crosses_from_open_play
                            + self.total_passes_in_attacking_third
                        )
                    )
                ),
                2,
            )
        if self.passes_total != 0:
            self.long_pass_ratio = round(
                (100 * float(self.long_passes / self.passes_total)), 2
            )
        if self.flick_on_passes != 0:
            self.flick_on_passes_success_ratio = round(
                (100 * float(self.flick_on_passes_successful / self.flick_on_passes)), 2
            )
        if self.total_passes_in_attacking_third != 0:
            self.pass_completion_percentage_in_the_final_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_in_attacking_third
                        / self.total_passes_in_attacking_third
                    )
                ),
                2,
            )
        if self.total_passes_in_middle_third != 0:
            self.pass_completion_percentage_in_the_middle_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_in_middle_third
                        / self.total_passes_in_middle_third
                    )
                ),
                2,
            )
        if self.total_passes_in_defensive_third != 0:
            self.pass_completion_percentage_in_the_defensive_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_in_defensive_third
                        / self.total_passes_in_defensive_third
                    )
                ),
                2,
            )
        if self.long_passes != 0:
            self.long_pass_success_rate = round(
                (100 * float(self.successful_long_passes / self.long_passes)), 2
            )
        if self.total_passes_into_defensive_third != 0:
            self.pass_completion_percentage_into_defensive_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_into_defensive_third
                        / self.total_passes_into_defensive_third
                    )
                ),
                2,
            )
        if self.total_passes_into_middle_third != 0:
            self.pass_completion_percentage_into_middle_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_into_middle_third
                        / self.total_passes_into_middle_third
                    )
                ),
                2,
            )
        if self.total_passes_into_attacking_third != 0:
            self.pass_completion_percentage_into_attacking_third = round(
                (
                    100
                    * float(
                        self.total_passes_successful_into_attacking_third
                        / self.total_passes_into_attacking_third
                    )
                ),
                2,
            )
        if self.pass_originate_and_end_in_opponent_half != 0:
            self.pass_completion_percentage_in_opponent_half = round(
                (
                    100
                    * float(
                        self.pass_originate_and_end_in_opponent_half_successful
                        / self.pass_originate_and_end_in_opponent_half
                    )
                ),
                2,
            )

        ##Corner Percentages - TO BE DONE
        self.corner_left = self.successful_corner_left + self.unsuccessful_corner_left
        self.corner_right = (
            self.successful_corner_right + self.unsuccessful_corner_right
        )
        if self.crosses_from_corners != 0:
            self.corner_cross_accuracy_percentage = round(
                (
                    100
                    * float(
                        self.successful_crosses_from_corners / self.crosses_from_corners
                    )
                ),
                2,
            )
        if self.corner_left != 0:
            self.corner_success_percentage_left = round(
                (100 * float(self.successful_corner_left / self.corner_left)), 2
            )
        if self.corner_right != 0:
            self.corner_success_percentage_right = round(
                (100 * float(self.successful_corner_right / self.corner_right)), 2
            )

        if print_results:
            self.printResults()
        self.saveResults()

        return self.event_results

    def printResults(self):
        # PASS EVENTS
        print("---- Pass ----")
        print("Total passes attempted: " + str(self.passes_total))
        print("Average pass distance: " + str(self.average_pass_length))

        print(
            "Total passes attempted in defensive third: "
            + str(self.total_passes_in_defensive_third)
        )
        print(
            "Total passes attempted in middle third: "
            + str(self.total_passes_in_middle_third)
        )
        print(
            "Total passes attempted in attacking third: "
            + str(self.total_passes_in_attacking_third)
        )
        print(
            "Total passes attempted into defensive third: "
            + str(self.total_passes_into_defensive_third)
        )
        print(
            "Total passes attempted into defensive third from own box: "
            + str(self.total_passes_into_defensive_third_from_own_box)
        )
        print(
            "Total passes attempted into middle third: "
            + str(self.total_passes_into_middle_third)
        )
        print(
            "Total passes attempted into attacking third: "
            + str(self.total_passes_into_attacking_third)
        )
        print("Total passes attempted into the box: " + str(self.total_passes_into_box))
        print(
            "Total passes attempted into the box (with crosses): "
            + str(self.total_passes_into_box_with_cross)
        )
        print("Total passes attempted forward: " + str(self.total_passes_forward))
        print(
            "Total passes attempted in opponent half (both originate and end): "
            + str(self.pass_originate_and_end_in_opponent_half)
        )
        print(
            "Total passes attempted in own half (both originate and end): "
            + str(self.pass_originate_and_end_in_own_half)
        )
        print("Forward pass attempt percentage: " + str(self.forward_pass_attempt_rate))
        print("Total passes completed: " + str(self.passes_successful))
        print(
            "Total passes completed from defensive third: "
            + str(self.total_passes_successful_in_defensive_third)
        )
        print(
            "Total passes completed from middle third: "
            + str(self.total_passes_successful_in_middle_third)
        )
        print(
            "Total passes completed from attacking third: "
            + str(self.total_passes_successful_in_attacking_third)
        )
        print(
            "Total passes completed inside the box: "
            + str(self.total_passes_successful_in_box)
        )
        print(
            "Total passes completed into defensive third: "
            + str(self.total_passes_successful_into_defensive_third)
        )
        print(
            "Total passes completed into middle third: "
            + str(self.total_passes_successful_into_middle_third)
        )
        print(
            "Total passes completed into attacking third: "
            + str(self.total_passes_successful_into_attacking_third)
        )
        print(
            "Total passes completed into the box: "
            + str(self.total_passes_successful_into_box)
        )
        print(
            "Total passes completed into the box (including crosses): "
            + str(self.successful_passes_into_box_with_cross)
        )
        print(
            "Total passes attempted into opponent half: "
            + str(self.total_passes_into_opponent_half)
        )
        print(
            "Total passes attempted into own half: "
            + str(self.total_passes_into_own_half)
        )
        print(
            "Total passes completed into opponent half: "
            + str(self.total_passes_successful_into_opponent_half)
        )
        print(
            "Total passes completed into own half: "
            + str(self.total_passes_successful_into_own_half)
        )
        print(
            "Total passes completed in opponent half (both originate and end): "
            + str(self.pass_originate_and_end_in_opponent_half_successful)
        )
        print(
            "Total passes completed in own half (both originate and end): "
            + str(self.pass_originate_and_end_in_own_half_successful)
        )
        print("Passes completion percentage: " + str(self.pass_success_rate))
        print(
            "Passes completion percentage in defensive third: "
            + str(self.pass_completion_percentage_in_the_defensive_third)
        )
        print(
            "Passes completion percentage in middle third: "
            + str(self.pass_completion_percentage_in_the_middle_third)
        )
        print(
            "Passes completion percentage in attacking third: "
            + str(self.pass_completion_percentage_in_the_final_third)
        )
        print(
            "Passes completion percentage into defensive third: "
            + str(self.pass_completion_percentage_into_defensive_third)
        )
        print(
            "Passes completion percentage into middle third: "
            + str(self.pass_completion_percentage_into_middle_third)
        )
        print(
            "Passes completion percentage into attacking third: "
            + str(self.pass_completion_percentage_into_attacking_third)
        )
        print(
            "Passes completion percentage in opponent half (both originate and end): "
            + str(self.pass_completion_percentage_in_opponent_half)
        )
        print("Unsuccessful passes: " + str(self.passes_unsuccessful))
        print(
            "Unsuccessful passes in opponent half: "
            + str(self.unsuccessful_passes_in_opponent_half)
        )
        print(
            "Unsuccessful passes in own half: "
            + str(self.unsuccessful_passes_in_own_half)
        )
        print("Total attempted long passes: " + str(self.long_passes))
        print("Total completed long passes: " + str(self.successful_long_passes))
        print(
            "Pass completion ratio on long passes: " + str(self.long_pass_success_rate)
        )
        print("Long ball percentage: " + str(self.long_pass_ratio))
        print("Total offensive passes: " + str(self.offensive_passes))
        print(
            "Total successful offensive passes: "
            + str(self.successful_offensive_passes)
        )
        print(
            "Total unsuccessful offensive passes: "
            + str(self.unsuccessful_offensive_passes)
        )
        print("Total headed passes attempted: " + str(self.headed_pass))
        print("Total headed passes completed: " + str(self.headed_pass_successful))
        print("Total through balls attempted: " + str(self.through_ball))
        print("Total through balls completed: " + str(self.through_ball_successful))
        print("Chipped passes attempted: " + str(self.chipped_passes))
        print("Chipped passes completed: " + str(self.chipped_passes_successful))
        print("Lay-off passes: " + str(self.lay_off_passes))
        print("Successful lay-off passes: " + str(self.lay_off_passes_successful))
        print("Unsuccessful lay-off passes: " + str(self.lay_off_passes_unsuccessful))
        print("Total launches: " + str(self.launch_passes))
        print("Accurate launches: " + str(self.successful_launch_passes))
        print("Flick-on passes: " + str(self.flick_on_passes))
        print("Flick-on passes successful: " + str(self.flick_on_passes_successful))
        print("Flick-on passes unsuccessful: " + str(self.flick_on_passes_unsuccessful))
        print(
            "Flick-on passes success percentage: "
            + str(self.flick_on_passes_success_ratio)
        )
        print("Pull back passes: " + str(self.pull_back_passes))
        print("Switch play passes attempted: " + str(self.switch_play_passes))
        print(
            "Switch play passes completed: " + str(self.switch_play_passes_successful)
        )
        print("Assists and key passes: " + str(self.assist_and_key_passes))
        print("Second assists: " + str(self.second_assist))
        print("Blocked passes: " + str(self.blocked_passes))
        print("Indirect free kicks taken: " + str(self.indirect_free_kick))
        print("Total goal kicks: " + str(self.goal_kick))

        # Crosses
        print("Total crosses attempted: " + str(self.total_crosses))
        print(
            "Total crosses attempted from left third: "
            + str(self.crosses_from_left_third)
        )
        print(
            "Total crosses attempted from right third: "
            + str(self.crosses_from_right_third)
        )
        print("Crosses completed: " + str(self.successful_crosses))
        print("Unsuccessful crosses: " + str(self.unsuccessful_crosses))
        print("Cross accuracy percentage: " + str(self.cross_success_rate))
        print("Overhit cross: " + str(self.overhit_cross))
        print(
            "Total crosses attempted from free kicks: "
            + str(self.crosses_from_free_kicks)
        )
        print(
            "Total crosses completed from free kicks: "
            + str(self.successful_crosses_from_free_kicks)
        )
        print(
            "Total crosses attempted from open play: "
            + str(self.crosses_from_open_play)
        )
        print(
            "Total crosses completed from open play: "
            + str(self.successful_crosses_from_open_play)
        )
        print(
            "Total crosses unsuccessful from open play: "
            + str(self.unsuccessful_crosses_from_open_play)
        )
        print(
            "Cross accuracy percentage from open play: "
            + str(self.cross_success_rate_open_play)
        )
        print(
            "Cross pass ratio in attacking third: "
            + str(self.cross_pass_ratio_in_attacking_third)
        )

        # Throw ins
        print("Total throw ins: " + str(self.throw_in))
        print("Total throw ins to own player: " + str(self.successful_throw_in))
        print("Total throw ins to opponent player: " + str(self.unsuccessful_throw_in))

        # Corners
        print("Total corners: " + str(self.total_corners))
        print("Short corners: " + str(self.short_corners))

        print("Crosses from corners: " + str(self.crosses_from_corners))
        print("Successful corners: " + str(self.successful_corner))
        print(
            "Successful crosses from corners: "
            + str(self.successful_crosses_from_corners)
        )
        print("Unsuccessful corners: " + str(self.unsuccessful_corner))
        print("Successful corners into box: " + str(self.corners_into_box_successful))
        print("Successful corners from left: " + str(self.successful_corner_left))
        print("Successful corners from right: " + str(self.successful_corner_right))
        print("Unsuccessful corners from left: " + str(self.unsuccessful_corner_left))
        print("Unsuccessful corners from right: " + str(self.unsuccessful_corner_right))
        print(
            "Cross accuracy percentage on corners: "
            + str(self.corner_cross_accuracy_percentage)
        )
        print(
            "Percentage of successful corners from left: "
            + str(self.corner_success_percentage_left)
        )
        print(
            "Percentage of successful corners from right: "
            + str(self.corner_success_percentage_right)
        )

    def saveResults(self):
        print("save results method is called")

        self.event_results["Total passes attempted"] = int(self.passes_total)
        self.event_results["Average pass distance"] = int(self.average_pass_length)

        self.event_results["Total passes attempted in defensive third"] = int(
            self.total_passes_in_defensive_third
        )
        self.event_results["Total passes attempted in middle third"] = int(
            self.total_passes_in_middle_third
        )
        self.event_results["Total passes attempted in attacking third"] = int(
            self.total_passes_in_attacking_third
        )
        self.event_results["Total passes attempted into defensive third"] = int(
            self.total_passes_into_defensive_third
        )
        self.event_results[
            "Total passes attempted into defensive third from own box"
        ] = int(self.total_passes_into_defensive_third_from_own_box)
        self.event_results["Total passes attempted into middle third"] = int(
            self.total_passes_into_middle_third
        )
        self.event_results["Total passes attempted into attacking third"] = int(
            self.total_passes_into_attacking_third
        )
        self.event_results["Total passes attempted into the box"] = int(
            self.total_passes_into_box
        )
        self.event_results["Total passes attempted into the box (with crosses)"] = int(
            self.total_passes_into_box_with_cross
        )
        self.event_results["Total passes attempted forward"] = int(
            self.total_passes_forward
        )
        self.event_results[
            "Total passes attempted in opponent half (both originate and end)"
        ] = int(self.pass_originate_and_end_in_opponent_half)
        self.event_results[
            "Total passes attempted in own half (both originate and end)"
        ] = int(self.pass_originate_and_end_in_own_half)
        self.event_results["Forward pass attempt percentage"] = int(
            self.forward_pass_attempt_rate
        )
        self.event_results["Total passes completed"] = int(self.passes_successful)
        self.event_results["Total passes completed from defensive third"] = int(
            self.total_passes_successful_in_defensive_third
        )
        self.event_results["Total passes completed from middle third"] = int(
            self.total_passes_successful_in_middle_third
        )
        self.event_results["Total passes completed from attacking third"] = int(
            self.total_passes_successful_in_attacking_third
        )
        self.event_results["Total passes completed inside the box"] = int(
            self.total_passes_successful_in_box
        )
        self.event_results["Total passes completed into defensive third"] = int(
            self.total_passes_successful_into_defensive_third
        )
        self.event_results["Total passes completed into middle third"] = int(
            self.total_passes_successful_into_middle_third
        )
        self.event_results["Total passes completed into attacking third"] = int(
            self.total_passes_successful_into_attacking_third
        )
        self.event_results["Total passes completed into the box"] = int(
            self.total_passes_successful_into_box
        )
        self.event_results[
            "Total passes completed into the box (including crosses)"
        ] = int(self.successful_passes_into_box_with_cross)
        self.event_results["Total passes attempted into opponent half"] = int(
            self.total_passes_into_opponent_half
        )
        self.event_results["Total passes attempted into own half"] = int(
            self.total_passes_into_own_half
        )
        self.event_results["Total passes completed into opponent half"] = int(
            self.total_passes_successful_into_opponent_half
        )
        self.event_results["Total passes completed into own half"] = int(
            self.total_passes_successful_into_own_half
        )
        self.event_results[
            "Total passes completed in opponent half (both originate and end)"
        ] = int(self.pass_originate_and_end_in_opponent_half_successful)
        self.event_results[
            "Total passes completed in own half (both originate and end)"
        ] = int(self.pass_originate_and_end_in_own_half_successful)
        self.event_results["Passes completion percentage"] = int(self.pass_success_rate)
        self.event_results["Passes completion percentage in defensive third"] = int(
            self.pass_completion_percentage_in_the_defensive_third
        )
        self.event_results["Passes completion percentage in middle third"] = int(
            self.pass_completion_percentage_in_the_middle_third
        )
        self.event_results["Passes completion percentage in attacking third"] = int(
            self.pass_completion_percentage_in_the_final_third
        )
        self.event_results["Passes completion percentage into defensive third"] = int(
            self.pass_completion_percentage_into_defensive_third
        )
        self.event_results["Passes completion percentage into middle third"] = int(
            self.pass_completion_percentage_into_middle_third
        )
        self.event_results["Passes completion percentage into attacking third"] = int(
            self.pass_completion_percentage_into_attacking_third
        )
        self.event_results[
            "Passes completion percentage in opponent half (both originate and end)"
        ] = int(self.pass_completion_percentage_in_opponent_half)
        self.event_results["Unsuccessful passes"] = int(self.passes_unsuccessful)
        self.event_results["Unsuccessful passes in opponent half"] = int(
            self.unsuccessful_passes_in_opponent_half
        )
        self.event_results["Unsuccessful passes in own half"] = int(
            self.unsuccessful_passes_in_own_half
        )
        self.event_results["Total attempted long passes"] = int(self.long_passes)
        self.event_results["Total completed long passes"] = int(
            self.successful_long_passes
        )
        self.event_results["Pass completion ratio on long passes"] = int(
            self.long_pass_success_rate
        )
        self.event_results["Long ball percentage"] = int(self.long_pass_ratio)
        self.event_results["Total offensive passes"] = int(self.offensive_passes)
        self.event_results["Total successful offensive passes"] = int(
            self.successful_offensive_passes
        )
        self.event_results["Total unsuccessful offensive passes"] = int(
            self.unsuccessful_offensive_passes
        )
        self.event_results["Total headed passes attempted"] = int(self.headed_pass)
        self.event_results["Total headed passes completed"] = int(
            self.headed_pass_successful
        )
        self.event_results["Total through balls attempted"] = int(self.through_ball)
        self.event_results["Total through balls completed"] = int(
            self.through_ball_successful
        )
        self.event_results["Chipped passes attempted"] = int(self.chipped_passes)
        self.event_results["Chipped passes completed"] = int(
            self.chipped_passes_successful
        )
        self.event_results["Lay-off passes"] = int(self.lay_off_passes)
        self.event_results["Successful lay-off passes"] = int(
            self.lay_off_passes_successful
        )
        self.event_results["Unsuccessful lay-off passes"] = int(
            self.lay_off_passes_unsuccessful
        )
        self.event_results["Total launches"] = int(self.launch_passes)
        self.event_results["Accurate launches"] = int(self.successful_launch_passes)
        self.event_results["Flick-on passes"] = int(self.flick_on_passes)
        self.event_results["Flick-on passes successful"] = int(
            self.flick_on_passes_successful
        )
        self.event_results["Flick-on passes unsuccessful"] = int(
            self.flick_on_passes_unsuccessful
        )
        self.event_results["Flick-on passes success percentage"] = int(
            self.flick_on_passes_success_ratio
        )
        self.event_results["Pull back passes"] = int(self.pull_back_passes)
        self.event_results["Switch play passes attempted"] = int(
            self.switch_play_passes
        )
        self.event_results["Switch play passes completed"] = int(
            self.switch_play_passes_successful
        )
        self.event_results["Assists and key passes"] = int(self.assist_and_key_passes)
        self.event_results["Second assists"] = int(self.second_assist)
        self.event_results["Blocked passes"] = int(self.blocked_passes)
        self.event_results["Indirect free kicks taken"] = int(self.indirect_free_kick)
        self.event_results["Total goal kicks"] = int(self.goal_kick)

        # Crosses
        self.event_results["Total crosses attempted"] = int(self.total_crosses)
        self.event_results["Total crosses attempted from left third"] = int(
            self.crosses_from_left_third
        )
        self.event_results["Total crosses attempted from right third"] = int(
            self.crosses_from_right_third
        )
        self.event_results["Crosses completed"] = int(self.successful_crosses)
        self.event_results["Unsuccessful crosses"] = int(self.unsuccessful_crosses)
        self.event_results["Cross accuracy percentage"] = int(self.cross_success_rate)
        self.event_results["Overhit cross"] = int(self.overhit_cross)
        self.event_results["Total crosses attempted from free kicks"] = int(
            self.crosses_from_free_kicks
        )
        self.event_results["Total crosses completed from free kicks"] = int(
            self.successful_crosses_from_free_kicks
        )
        self.event_results["Total crosses attempted from open play"] = int(
            self.crosses_from_open_play
        )
        self.event_results["Total crosses completed from open play"] = int(
            self.successful_crosses_from_open_play
        )
        self.event_results["Total crosses unsuccessful from open play"] = int(
            self.unsuccessful_crosses_from_open_play
        )
        self.event_results["Cross accuracy percentage from open play"] = int(
            self.cross_success_rate_open_play
        )
        self.event_results["Cross pass ratio in attacking third"] = int(
            self.cross_pass_ratio_in_attacking_third
        )

        # Throw ins
        self.event_results["Total throw ins"] = int(self.throw_in)
        self.event_results["Total throw ins to own player"] = int(
            self.successful_throw_in
        )
        self.event_results["Total throw ins to opponent player"] = int(
            self.unsuccessful_throw_in
        )

        # Corners
        self.event_results["Total corners"] = int(self.total_corners)
        self.event_results["Short corners"] = int(self.short_corners)

        self.event_results["Crosses from corners"] = int(self.crosses_from_corners)
        self.event_results["Successful corners"] = int(self.successful_corner)
        self.event_results["Successful crosses from corners"] = int(
            self.successful_crosses_from_corners
        )
        self.event_results["Unsuccessful corners"] = int(self.unsuccessful_corner)
        self.event_results["Successful corners into box"] = int(
            self.corners_into_box_successful
        )
        self.event_results["Successful corners from left"] = int(
            self.successful_corner_left
        )
        self.event_results["Successful corners from right"] = int(
            self.successful_corner_right
        )
        self.event_results["Unsuccessful corners from left"] = int(
            self.unsuccessful_corner_left
        )
        self.event_results["Unsuccessful corners from right"] = int(
            self.unsuccessful_corner_right
        )
        self.event_results["Cross accuracy percentage on corners"] = int(
            self.corner_cross_accuracy_percentage
        )
        self.event_results["Percentage of successful corners from left"] = int(
            self.corner_success_percentage_left
        )
        self.event_results["Percentage of successful corners from right"] = int(
            self.corner_success_percentage_right
        )

        # PlayerStatistics.appendResults(self.eventType, self.event_results)

    def getDataFrame(self):
        self.data = [
            ["Total passes attempted", self.passes_total],
            [
                "Total passes attempted in defensive third",
                self.total_passes_in_defensive_third,
            ],
            [
                "Total passes attempted in middle third",
                self.total_passes_in_middle_third,
            ],
            [
                "Total passes attempted in attacking third",
                self.total_passes_in_attacking_third,
            ],
            [
                "Total passes attempted into defensive third",
                self.total_passes_into_defensive_third,
            ],
            [
                "Total passes attempted into defensive third from own box",
                self.total_passes_into_defensive_third_from_own_box,
            ],
            [
                "Total passes attempted into middle third",
                self.total_passes_into_middle_third,
            ],
            [
                "Total passes attempted into attacking third",
                self.total_passes_into_attacking_third,
            ],
            ["Total passes attempted into the box", self.total_passes_into_box],
            [
                "Total passes attempted into the box (with crosses)",
                self.total_passes_into_box_with_cross,
            ],
            ["Total passes attempted forward", self.total_passes_forward],
            [
                "Total passes attempted in opponent half (both originate and end)",
                self.pass_originate_and_end_in_opponent_half,
            ],
            [
                "Total passes attempted in own half (both originate and end)",
                self.pass_originate_and_end_in_own_half,
            ],
            ["Forward pass attempt percentage", self.forward_pass_attempt_rate],
            ["Total passes completed", self.passes_successful],
            [
                "Total passes completed from defensive third",
                self.total_passes_successful_in_defensive_third,
            ],
            [
                "Total passes completed from middle third",
                self.total_passes_successful_in_middle_third,
            ],
            [
                "Total passes completed from attacking third",
                self.total_passes_successful_in_attacking_third,
            ],
            [
                "Total passes completed inside the box",
                self.total_passes_successful_in_box,
            ],
            [
                "Total passes completed into defensive third",
                self.total_passes_successful_into_defensive_third,
            ],
            [
                "Total passes completed into middle third",
                self.total_passes_successful_into_middle_third,
            ],
            [
                "Total passes completed into attacking third",
                self.total_passes_successful_into_attacking_third,
            ],
            [
                "Total passes completed into the box",
                self.total_passes_successful_into_box,
            ],
            [
                "Total passes completed into the box (including crosses)",
                self.successful_passes_into_box_with_cross,
            ],
            [
                "Total passes attempted into opponent half",
                self.total_passes_into_opponent_half,
            ],
            ["Total passes attempted into own half", self.total_passes_into_own_half],
            [
                "Total passes completed into opponent half",
                self.total_passes_successful_into_opponent_half,
            ],
            [
                "Total passes completed into own half",
                self.total_passes_successful_into_own_half,
            ],
            [
                "Total passes completed in opponent half (both originate and end)",
                self.pass_originate_and_end_in_opponent_half_successful,
            ],
            [
                "Total passes completed in own half (both originate and end)",
                self.pass_originate_and_end_in_own_half_successful,
            ],
            ["Passes completion percentage", self.pass_success_rate],
            [
                "Passes completion percentage in defensive third",
                self.pass_completion_percentage_in_the_defensive_third,
            ],
            [
                "Passes completion percentage in middle third",
                self.pass_completion_percentage_in_the_middle_third,
            ],
            [
                "Passes completion percentage in attacking third",
                self.pass_completion_percentage_in_the_final_third,
            ],
            [
                "Passes completion percentage into defensive third",
                self.total_passes_successful_into_defensive_third,
            ],
            [
                "Passes completion percentage into middle third",
                self.pass_completion_percentage_into_middle_third,
            ],
            [
                "Passes completion percentage into attacking third",
                self.pass_completion_percentage_into_attacking_third,
            ],
            [
                "Passes completion percentage in opponent half (both originate and end)",
                self.pass_completion_percentage_in_opponent_half,
            ],
            ["Unsuccessful passes", self.passes_unsuccessful],
            [
                "Unsuccessful passes in opponent half",
                self.unsuccessful_passes_in_opponent_half,
            ],
            ["Unsuccessful passes in own half", self.unsuccessful_passes_in_own_half],
            ["Total attempted long passes", self.long_passes],
            ["Total completed long passes", self.successful_long_passes],
            ["Pass completion ratio on long passes", self.long_pass_success_rate],
            ["Long ball percentage", self.long_pass_ratio],
            ["Total offensive passes", self.offensive_passes],
            ["Total successful offensive passes", self.successful_offensive_passes],
            ["Total unsuccessful offensive passes", self.unsuccessful_offensive_passes],
            ["Total headed passes attempted", self.headed_pass],
            ["Total headed passes completed", self.headed_pass_successful],
            ["Total through balls attempted", self.through_ball],
            ["Total through balls completed", self.through_ball_successful],
            ["Chipped passes attempted", self.chipped_passes],
            ["Chipped passes completed", self.chipped_passes_successful],
            ["Lay-off passes", self.lay_off_passes],
            ["Successful lay-off passes", self.lay_off_passes_successful],
            ["Unsuccessful lay-off passes", self.lay_off_passes_unsuccessful],
            ["Flick-on passes", self.flick_on_passes],
            ["Flick-on passes successful", self.flick_on_passes_successful],
            ["Flick-on passes unsuccessful", self.flick_on_passes_unsuccessful],
            ["Flick-on passes success percentage", self.flick_on_passes_success_ratio],
            ["Pull back passes", self.pull_back_passes],
            ["Switch play passes attempted", self.switch_play_passes],
            ["Switch play passes completed", self.switch_play_passes_successful],
            ["Blocked passes", self.blocked_passes],
            ["Indirect free kicks taken", self.indirect_free_kick],
            ["Total goal kicks", self.goal_kick],
            ["Total crosses attempted", self.total_crosses],
            ["Total crosses attempted from left third", self.crosses_from_left_third],
            ["Total crosses attempted from right third", self.crosses_from_right_third],
            ["Crosses completed", self.successful_crosses],
            ["Unsuccessful crosses", self.unsuccessful_crosses],
            ["Cross accuracy percentage", self.cross_success_rate],
            ["Overhit cross", self.overhit_cross],
            ["Total crosses attempted from free kicks", self.crosses_from_free_kicks],
            [
                "Total crosses completed from free kicks",
                self.successful_crosses_from_free_kicks,
            ],
            ["Total crosses attempted from open play", self.crosses_from_open_play],
            [
                "Total crosses completed from open play",
                self.successful_crosses_from_open_play,
            ],
            [
                "Total crosses unsuccessful from open play",
                self.unsuccessful_crosses_from_open_play,
            ],
            [
                "Cross accuracy percentage from open play",
                self.cross_success_rate_open_play,
            ],
            [
                "Cross pass ratio in attacking third",
                self.cross_pass_ratio_in_attacking_third,
            ],
            ["Total throw ins", self.throw_in],
            ["Total throw ins to own player", self.successful_throw_in],
            ["Total throw ins to opponent player", self.unsuccessful_throw_in],
            ["Total corners", self.total_corners],
            ["Short corners", self.short_corners],
            ["Crosses from corners", self.crosses_from_corners],
            ["Successful corners", self.successful_corner],
            ["Successful crosses from corners", self.successful_crosses_from_corners],
            ["Unsuccessful corners", self.unsuccessful_corner],
            ["Successful corners into box", self.corners_into_box_successful],
            ["Successful corners from left", self.successful_corner_left],
            ["Successful corners from right", self.successful_corner_right],
            ["Unsuccessful corners from left", self.unsuccessful_corner_left],
            ["Unsuccessful corners from right", self.unsuccessful_corner_right],
            [
                "Cross accuracy percentage on corners",
                self.corner_cross_accuracy_percentage,
            ],
            [
                "Percentage of successful corners from left",
                self.corner_success_percentage_left,
            ],
            [
                "Percentage of successful corners from right",
                self.corner_success_percentage_right,
            ],
        ]

        # Create the pandas DataFrame
        # df = pd.DataFrame(self.data, columns=["", "Total"])
        # print(df)


def is_float(input):
    try:
        num = float(input)
    except ValueError:
        return False
    return True


def is_int(input):
    try:
        num = int(input)
    except ValueError:
        return False
    return True
