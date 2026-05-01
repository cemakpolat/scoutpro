from .Events import EventIDs
from .QTypes import QTypes


class TeamAPI:
    """Stub - team data is now served by team-service via HTTP"""
    pass


class EventMinutes:
    def __init__(self):
        self.goals = list()
        self.yellow_cards = list()
        self.red_cards = list()
        self.player_off = list()
        self.player_on = list()
        self.end_of_first_half = list()
        self.end_of_the_game = list()

        self.team_id_dict = dict()
        self.player_id_dict = dict()
        self.converter = False
        self.competitionID = None
        self.seasonID = None
        self.tapi = None

        self.results = dict()

    def callEventHandler(self, data):
        if "events" in data:
            events = data["events"]

        else:
            events = None

        if "teamID" in data:
            if not isinstance(data["teamID"], list) and data["teamID"]:
                team_id = [int(str(data["teamID"]).replace("t", ""))]
            else:
                team_id = data["teamID"]
        else:
            team_id = None

        if "playerID" in data:
            if not isinstance(data["playerID"], list) and data["playerID"]:
                player_id = [int(str(data["playerID"]).replace("p", ""))]
            else:
                player_id = data["playerID"]
        else:
            player_id = None

        if "teamID_dict" in data:
            self.team_id_dict = data["teamID_dict"]

        if "playerID_dict" in data:
            self.player_id_dict = data["playerID_dict"]

        if "converter" in data:
            self.converter = data["converter"]

            if "competitionID" in data and "seasonID" in data:
                self.competitionID = data["competitionID"]
                self.seasonID = data["seasonID"]
                self.tapi = TeamAPI.TeamAPI(int(self.competitionID), int(self.seasonID))
            else:
                print("If the convert option has been chosen, then both the competitionID and ",
                      "the seasonID must be given in data dictionary.")
                self.converter = False

        if events:
            for event in events:
                if team_id:
                    if hasattr(event, "teamID"):
                        if event.teamID not in team_id:
                            continue

                if player_id:
                    if hasattr(event, "playerID"):
                        if event.playerID not in player_id:
                            continue

                if event.typeID == EventIDs.ID_16_Goal:
                    event_time, team, player = self.get_event_min_player_team(event)

                    qualifier_list = []
                    for q in event.qEvents:
                        qualifier_list.append(q.qualifierID)

                    if QTypes.ID_28 in qualifier_list:
                        """Own goal case."""
                        self.goals.append({team: {player: {"own_goal": event_time}}})

                    else:
                        if QTypes.ID_9 in qualifier_list:
                            """Successful goal case in penalty."""
                            self.goals.append({team: {player: {"penalty": event_time}}})

                        else:
                            """Successful goal case in penalty."""
                            self.goals.append({team: {player: {"goal": event_time}}})

                elif event.typeID == EventIDs.ID_17_Card:
                    event_time, team, player = self.get_event_min_player_team(event)

                    for q in event.qEvents:
                        if q.qualifierID == QTypes.ID_31:
                            """Yellow card case."""
                            self.yellow_cards.append({team: {player: {"yellow_card": event_time}}})

                        elif q.qualifierID == QTypes.ID_32:
                            """Second yellow card case."""
                            self.yellow_cards.append({team: {player: {"second_yellow_card": event_time}}})

                        elif q.qualifierID == QTypes.ID_33:
                            """Red card case."""
                            self.red_cards.append({team: {player: {"red_card": event_time}}})

                elif event.typeID == EventIDs.ID_18_Player_Off:
                    event_time, team, player = self.get_event_min_player_team(event)
                    """Player off from the game case."""
                    self.player_off.append({team: {player: {"player_off": event_time}}})

                elif event.typeID == EventIDs.ID_19_Player_on:
                    event_time, team, player = self.get_event_min_player_team(event)
                    """Player on to the game case."""
                    self.player_on.append({team: {player: {"player_on": event_time}}})

                elif event.typeID == EventIDs.ID_30_End:
                    event_time, team, player = self.get_event_min_player_team(event)
                    period_id = int(event_time["period"])

                    if period_id == 1:
                        """End of the first half of the game case."""
                        self.end_of_first_half.append({team: {"end_of_the_first_half": event_time}})
                        pass
                    elif period_id == 2:
                        """End of the game case."""
                        self.end_of_the_game.append({team: {"end_of_the_game": event_time}})

        self.saveResults()

        return self.results

    def get_event_min_player_team(self, event_object):
        event = event_object

        event_time = {
            "min": event.min,
            "sec": event.sec
        }

        if hasattr(event, "periodID"):
            event_time["period"] = event.periodID

        if self.converter:
            if hasattr(event, "teamID"):
                if event.teamID in self.team_id_dict:
                    team = self.team_id_dict[event.teamID]
                else:
                    team = self.tapi.get_team_name(event.teamID)
                    self.team_id_dict[event.teamID] = team
            else:
                team = None

            if hasattr(event, "playerID"):
                if event.playerID in self.player_id_dict:
                    player = self.player_id_dict[event.playerID]
                else:
                    player = self.tapi.get_player_name(event.playerID)
                    self.player_id_dict[event.playerID] = player
            else:
                player = None

        else:
            if hasattr(event, "teamID"):
                team = event.teamID
            else:
                team = None

            if hasattr(event, "playerID"):
                player = event.playerID
            else:
                player = None

        return event_time, team, player

    def saveResults(self):
        self.results = {
            "Goals": self.goals,
            "Yellow Cards": self.yellow_cards,
            "Red Cards": self.red_cards,
            "Player On": self.player_on,
            "Player Off": self.player_off,
            "First Half End": self.end_of_first_half,
            "End of the Game": self.end_of_the_game
        }
