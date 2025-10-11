# This class checks the following Opta F24 events:
#     "1":"Pass"
#     "2":"Offside Pass"
#     "3":"Take On"
#     "4":"Foul" (outcome = 1)
#     "7":"Tackle"
#     "8":"Interception"
#     "9":"Turnover"
#     "10":"Save"
#     "11":"Claim"
#     "12":"Clearance"
#     "13":"Miss"
#     "14":"Post"
#     "15":"Attempt Saved"
#     "16":"Goal"
#     "41":"Punch"
#     "42":"Good skill"
#     "45":"Challenge"
#     "50":"Dispossessed"
#     "54":"Smother"
#     "61":"Ball touch"
#     "73":"Other Ball Contact"
#     "74":"Blocked Pass"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from src.events.Events import *
from src.events.QTypes import *
import pandas as pd


class TouchEvents:
    def __init__(self):
        # simple ball control event counters
        self.total_touches = 0
        self.total_touches_in_attacking_third = 0
        self.total_touches_in_middle_third = 0
        self.total_touches_in_defensive_third = 0
        self.total_touches_in_box = 0
        self.turnover = 0
        self.turnover_percentage = 0
        self.take_on_overrun = 0
        self.defensive_touches = 0

        # save
        self.save_by_outfield_player = 0

        # tackles
        self.total_tackles = 0
        self.total_successful_tackles = 0
        self.tackle_made_percentage = 0
        self.total_tackles_in_attacking_third = 0
        self.total_tackles_in_middle_third = 0
        self.total_tackles_in_defensive_third = 0
        self.total_challenges = 0
        self.tackle_attempts = 0
        self.tackle_success_percentage = 0
        self.last_man_tackles = 0

        # ball recoveries
        self.total_ball_recovery = 0
        self.total_recoveries_in_defensive_third = 0
        self.total_recoveries_in_middle_third = 0
        self.total_recoveries_in_attacking_third = 0

        # interceptions
        self.total_interceptions = 0
        self.total_interceptions_in_defensive_third = 0
        self.total_interceptions_in_middle_third = 0
        self.total_interceptions_in_attacking_third = 0

        # clearances
        self.total_clearances = 0
        self.total_clearances_in_defensive_third = 0
        self.total_clearances_in_middle_third = 0
        self.total_clearances_in_attacking_third = 0
        self.blocked_cross = 0
        self.headed_clearance = 0
        self.total_real_clearances = 0
        self.clearances_off_the_line = 0

        # offsides provoked
        self.total_offsides_provoked = 0

        # event coordinates
        self.x = 0
        self.x_end = 0
        self.y = 0
        self.y_end = 0
        self.event_results = {}
        # Add to excel
        self.data = []

    # todo: use this function in nearly all if blocks under callEventHandler method

    def touchesCounter(self, event):

        if event.x <= 33.29:
            self.total_touches_in_defensive_third += 1
        elif 33.29 < event.x <= 66.61:
            self.total_touches_in_middle_third += 1
        elif event.x > 66.61:
            self.total_touches_in_attacking_third += 1

        if event.x >= 83 and 21.1 <= event.y <= 78.9:
            self.total_touches_in_box += 1

    def tacklesCounter(self, event):
        if event.x <= 33.29:
            self.total_tackles_in_defensive_third += 1
        elif 33.29 < event.x <= 66.61:
            self.total_tackles_in_middle_third += 1
        elif event.x > 66.61:
            self.total_tackles_in_attacking_third += 1

    def clearanceCounter(self, event):
        if event.x <= 33.29:
            self.total_clearances_in_defensive_third += 1
            qualifier_list = []
            for q in event.qEvents:
                qualifier_list.append(q.qualifierID)
                if q.qualifierID == QTypes.ID_185:
                    self.total_clearances_in_defensive_third -= 1
        if 33.29 < event.x <= 66.6:
            self.total_clearances_in_middle_third += 1
            qualifier_list = []
            for q in event.qEvents:
                qualifier_list.append(q.qualifierID)
                if q.qualifierID == QTypes.ID_185:
                    self.total_clearances_in_middle_third -= 1
        if event.x > 66.6:
            self.total_clearances_in_attacking_third += 1
            qualifier_list = []
            for q in event.qEvents:
                qualifier_list.append(q.qualifierID)
                if q.qualifierID == QTypes.ID_185:
                    self.total_clearances_in_attacking_third -= 1

    def interceptionsCounter(self, event):
        if event.x <= 33.29:
            self.total_interceptions_in_defensive_third += 1
        elif 33.29 < event.x <= 66.61:
            self.total_interceptions_in_middle_third += 1
        elif event.x > 66.61:
            self.total_interceptions_in_attacking_third += 1

    def recoverCounter(self, event):
        if event.x <= 33.29:
            self.total_recoveries_in_defensive_third += 1
        if 33.29 < event.x <= 66.61:
            self.total_recoveries_in_middle_third += 1
        if event.x > 66.61:
            self.total_recoveries_in_attacking_third += 1

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
                if event.typeID == EventIDs.ID_1_Pass_Events:
                    self.total_touches += 1
                    self.touchesCounter(event)
                    if event.outcome == EventIDs.UNSUCCESSFUL:
                        self.turnover += 1

                elif event.typeID == EventIDs.ID_2_Offside_Pass:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_3_Take_On:
                    self.total_touches += 1
                    self.touchesCounter(event)

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if event.outcome == EventIDs.UNSUCCESSFUL:
                        self.turnover += 1
                        if QTypes.ID_211 in qualifier_list:
                            self.turnover += 1

                elif event.typeID == EventIDs.ID_4_Foul:
                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.total_touches += 1
                        self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_7_Tackle:
                    self.total_touches += 1
                    self.total_tackles += 1
                    self.tackle_attempts += 1
                    self.defensive_touches += 1

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                        if q.qualifierID == QTypes.ID_14:
                            self.last_man_tackles += 1

                    self.touchesCounter(event)
                    self.tacklesCounter(event)

                    if event.outcome == EventIDs.SUCCESSFUL:
                        self.total_successful_tackles += 1
                    elif event.outcome == EventIDs.UNSUCCESSFUL:
                        self.turnover += 1

                elif event.typeID == EventIDs.ID_8_Interception:
                    self.total_touches += 1
                    self.total_interceptions += 1
                    self.defensive_touches += 1
                    self.touchesCounter(event)
                    self.interceptionsCounter(event)

                elif event.typeID == EventIDs.ID_10_Save:
                    self.total_touches += 1
                    qualifier_list = []

                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_94 in qualifier_list:
                        self.save_by_outfield_player += 1
                        self.defensive_touches += 1

                    if QTypes.ID_14 in qualifier_list and QTypes.ID_94 in qualifier_list:
                        self.clearances_off_the_line += 1

                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_12_Clearance:

                    self.total_touches += 1
                    self.total_clearances += 1
                    self.defensive_touches += 1

                elif event.typeID == EventIDs.ID_13_Miss:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_14_Post:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_15_Attempt_Saved:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_16_Goal:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_42_Good_skill:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_50_Dispossessed:
                    self.total_touches += 1
                    self.touchesCounter(event)

                # elif event.typeID == EventIDs.ID_54_Smother:
                #     self.total_touches += 1
                #     self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_61_Ball_touch:
                    self.total_touches += 1
                    self.touchesCounter(event)

                    if event.outcome == EventIDs.UNSUCCESSFUL:
                        self.turnover += 1

                elif event.typeID == EventIDs.ID_73_Other_Ball_Contact:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_74_Blocked_Pass:
                    self.total_touches += 1
                    self.touchesCounter(event)

                elif event.typeID == EventIDs.ID_45_Challenge:
                    self.total_challenges += 1
                    self.tackle_attempts += 1

                elif event.typeID == EventIDs.ID_49_Ball_recovery:
                    self.total_ball_recovery += 1
                    self.touchesCounter(event)
                    self.recoverCounter(event)

                elif event.typeID == EventIDs.ID_55_Offside_provoked:
                    self.total_offsides_provoked += 1

        self.total_real_clearances = self.total_clearances - self.blocked_cross
        if self.total_touches != 0:
            self.turnover_percentage = 100 * round(
                float(self.turnover / self.total_touches), 4
            )
        if self.tackle_attempts != 0:
            self.tackle_made_percentage = 100 * round(
                float(self.total_tackles / self.tackle_attempts), 4
            )
            self.tackle_success_percentage = 100 * round(
                float(self.total_successful_tackles / self.tackle_attempts), 4
            )

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        # print touch parameters
        print("---- Touch ----")
        # print touch parameters
        print("total touches: " + str(self.total_touches))
        print(
            "touches in defensive third: " + str(self.total_touches_in_defensive_third)
        )
        print("touches in middle third: " + str(self.total_touches_in_middle_third))
        print(
            "touches in attacking third: " + str(self.total_touches_in_attacking_third)
        )
        print("touches in opponent box: " + str(self.total_touches_in_box))
        print("total turnovers: " + str(self.turnover))
        print("turnover percentage: " + str(self.turnover_percentage))
        # print tackle parameters
        print("total tackles: " + str(self.total_tackles))
        print("total successful tackles: " + str(self.total_successful_tackles))
        print("total tackle attempts: " + str(self.tackle_attempts))
        print("tackle made percentage: " + str(self.tackle_made_percentage))
        print("tackle success percentage: " + str(self.tackle_success_percentage))
        print(
            "tackles in defensive third: " + str(self.total_tackles_in_defensive_third)
        )
        print("tackles in middle third: " + str(self.total_tackles_in_middle_third))
        print(
            "tackles in attacking third: " + str(self.total_tackles_in_attacking_third)
        )
        print("last man tackles: " + str(self.last_man_tackles))
        print("total challenges lost: " + str(self.total_challenges))
        # print ball recoveries
        print("total ball recoveries: " + str(self.total_ball_recovery))
        print(
            "recoveries in defensive third: "
            + str(self.total_recoveries_in_defensive_third)
        )
        print(
            "recoveries in middle third: " + str(self.total_recoveries_in_middle_third)
        )
        print(
            "recoveries in attacking third: "
            + str(self.total_recoveries_in_attacking_third)
        )
        # print interceptions
        print("total interceptions: " + str(self.total_interceptions))
        print(
            "interceptions in defensive third: "
            + str(self.total_interceptions_in_defensive_third)
        )
        print(
            "interceptions in middle third: "
            + str(self.total_interceptions_in_middle_third)
        )
        print(
            "interceptions in attacking third: "
            + str(self.total_interceptions_in_attacking_third)
        )
        # print clearances
        print("total clearances: " + str(self.total_clearances))
        print(
            "clearances in defensive third: "
            + str(self.total_clearances_in_defensive_third)
        )
        print(
            "clearances in middle third: " + str(self.total_clearances_in_middle_third)
        )
        print(
            "clearances in attacking third: "
            + str(self.total_clearances_in_attacking_third)
        )
        print("total blocked crosses: " + str(self.blocked_cross))
        print("total headed clearances: " + str(self.headed_clearance))
        # print offsides provoked
        print("total offsides provoked: " + str(self.total_offsides_provoked))
        print("Shots Blocked By Outfielder: " + str(self.save_by_outfield_player))
        print("total defensive touches: " + str(self.defensive_touches))
        print("total clearances off the line: " + str(self.clearances_off_the_line))

    def saveResults(self):
        print("save results method is called")
        # print touch parameters

        self.event_results["total touches"] = int(self.total_touches)
        self.event_results["touches in defensive third"] = int(
            self.total_touches_in_defensive_third
        )
        self.event_results["touches in middle third"] = int(
            self.total_touches_in_middle_third
        )
        self.event_results["touches in attacking third"] = int(
            self.total_touches_in_attacking_third
        )
        self.event_results["touches in opponent box"] = int(self.total_touches_in_box)
        self.event_results["total turnovers"] = int(self.turnover)
        self.event_results["turnover percentage"] = int(self.turnover_percentage)
        # print tackle parameters
        self.event_results["total tackles"] = int(self.total_tackles)
        self.event_results["total successful tackles"] = int(
            self.total_successful_tackles
        )
        self.event_results["total tackle attempts"] = int(self.tackle_attempts)
        self.event_results["tackle made percentage"] = int(self.tackle_made_percentage)
        self.event_results["tackle success percentage"] = int(
            self.tackle_success_percentage
        )
        self.event_results["tackles in defensive third"] = int(
            self.total_tackles_in_defensive_third
        )
        self.event_results["tackles in middle third"] = int(
            self.total_tackles_in_middle_third
        )
        self.event_results["tackles in attacking third"] = int(
            self.total_tackles_in_attacking_third
        )
        self.event_results["last man tackles"] = int(self.last_man_tackles)
        self.event_results["total challenges lost"] = int(self.total_challenges)
        # print ball recoveries
        self.event_results["total ball recoveries"] = int(self.total_ball_recovery)
        self.event_results["recoveries in defensive third"] = int(
            self.total_recoveries_in_defensive_third
        )
        self.event_results["recoveries in middle third"] = int(
            self.total_recoveries_in_middle_third
        )
        self.event_results["recoveries in attacking third"] = int(
            self.total_recoveries_in_attacking_third
        )
        # print interceptions
        self.event_results["total interceptions"] = int(self.total_interceptions)
        self.event_results["interceptions in defensive third"] = int(
            self.total_interceptions_in_defensive_third
        )
        self.event_results["interceptions in middle third"] = int(
            self.total_interceptions_in_middle_third
        )
        self.event_results["interceptions in attacking third"] = int(
            self.total_interceptions_in_attacking_third
        )
        # print clearances
        self.event_results["total clearances"] = int(self.total_clearances)
        self.event_results["clearances in defensive third"] = int(
            self.total_clearances_in_defensive_third
        )
        self.event_results["clearances in middle third"] = int(
            self.total_clearances_in_middle_third
        )
        self.event_results["clearances in attacking third"] = int(
            self.total_clearances_in_attacking_third
        )
        self.event_results["total blocked crosses"] = int(self.blocked_cross)
        self.event_results["total headed clearances"] = int(self.headed_clearance)
        # print offsides provoked
        self.event_results["total offsides provoked"] = int(
            self.total_offsides_provoked
        )
        self.event_results["Shots Blocked By Outfielder"] = int(
            self.save_by_outfield_player
        )
        self.event_results["total defensive touches"] = int(self.defensive_touches)
        self.event_results["total clearances off the line"] = int(
            self.clearances_off_the_line
        )

    def getDataFrame(self):
        self.data = [
            ["total touches", self.total_touches],
            ["touches in defensive third", self.total_touches_in_defensive_third],
            ["touches in middle third", self.total_touches_in_middle_third],
            ["touches in attacking third", self.total_touches_in_attacking_third],
            ["touches in opponent box", self.total_touches_in_box],
            ["total tackles", self.total_tackles],
            ["total successful tackles", self.total_successful_tackles],
            ["total tackle attempts", self.tackle_attempts],
            ["tackle made percentage", self.tackle_made_percentage],
            ["tackle success percentage", self.tackle_success_percentage],
            ["tackles in defensive third", self.total_tackles_in_defensive_third],
            ["tackles in middle third", self.total_tackles_in_middle_third],
            ["tackles in attacking third", self.total_tackles_in_attacking_third],
            ["last man tackles", self.last_man_tackles],
            ["total challenges", self.total_challenges],
            ["total ball recoveries", self.total_ball_recovery],
            ["recoveries in defensive third", self.total_recoveries_in_defensive_third],
            ["recoveries in middle third", self.total_recoveries_in_middle_third],
            ["recoveries in attacking third", self.total_recoveries_in_attacking_third],
            ["total interceptions", self.total_interceptions],
            [
                "interceptions in defensive third",
                self.total_interceptions_in_defensive_third,
            ],
            ["interceptions in middle third", self.total_interceptions_in_middle_third],
            [
                "interceptions in attacking third",
                self.total_interceptions_in_attacking_third,
            ],
            ["total clearances", self.total_clearances],
            ["clearances in defensive third", self.total_clearances_in_defensive_third],
            ["clearances in middle third", self.total_clearances_in_middle_third],
            ["clearances in attacking third", self.total_clearances_in_attacking_third],
            ["total blocked crosses", self.blocked_cross],
            ["total headed clearances", self.headed_clearance],
            ["total offsides provoked", self.total_offsides_provoked],
            ["total defensive touches", self.defensive_touches],
            ["total clearances off the line", self.clearances_off_the_line],
        ]

        # Create the pandas DataFrame
        df = pd.DataFrame(self.data, columns=["criteria", "Total"])
        return df
