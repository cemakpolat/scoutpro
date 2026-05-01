# This class checks the following Opta F24 events:
#     "17":"Cards"
# author: Doruk Sahinel, Cem Akpolat

from __future__ import division
from .Events import *
from .QTypes import *


class CardEvents:
    def __init__(self):

        # simple card event counters
        self.total_cards = 0
        self.yellow_card = 0
        self.second_yellow_card = 0
        self.red_card = 0
        self.card_rescinded = 0
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
                if event.typeID == EventIDs.ID_17_Card:
                    self.total_cards += 1
                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_31:
                            self.yellow_card += 1
                        elif q.qualifierID == QTypes.ID_32:
                            self.second_yellow_card += 1
                        elif q.qualifierID == QTypes.ID_33:
                            self.red_card += 1
                        elif q.qualifierID == QTypes.ID_171:
                            self.card_rescinded += 1

        if print_results:
            self.printResults()
        self.saveResults()
        return self.event_results

    def printResults(self):
        print("---- Card ----")
        print("total cards: " + str(self.total_cards))
        print("total yellow cards: " + str(self.yellow_card))
        print("total second yellow cards: " + str(self.second_yellow_card))
        print("total red cards: " + str(self.red_card))
        print("total rescinded cards: " + str(self.card_rescinded))

    def saveResults(self):
        print("save results method is called")
        self.event_results["total cards"] = self.total_cards
        self.event_results["total yellow cards"] = self.yellow_card
        self.event_results["total second yellow cards"] = self.second_yellow_card
        self.event_results["total red cards"] = self.red_card
        self.event_results["total rescinded cards"] = self.card_rescinded

    def getDataFram(self):
        self.data = [
            ["total cards", self.total_cards],
            ["total yellow cards", self.yellow_card],
            ["total second yellow cards", self.second_yellow_card],
            ["total red cards", self.red_card],
            ["total rescinded cards", self.card_rescinded],
        ]

        # Create the pandas DataFrame
        # df = pd.DataFrame(self.data, columns=[player_name, "Total"])
        # print(df)
        # return df
