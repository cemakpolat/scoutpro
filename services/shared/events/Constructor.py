"""

"""

import copy
from src.restapi import APIHelpers
from src.events.Events import *
from src.events.QTypes import *


class Constructor:
    def __init__(self):

        self.away_team = None
        self.home_team = None

        self.away_goalkeeper = None
        self.home_goalkeeper = None

        self.clean_sheet_home = True
        self.clean_sheet_away = True

        self.substitute_id = None

        self.x = None
        self.y = None

        self.pass_dict = dict()
        self.ball_touch_dict = dict()
        self.take_on_dict = dict()

        self.events = None
        self.index = 0
        self.counter = 0
        self.last_event = 0

    # ---------NEW EVENTS---------

    # GOALKEEPERS
    def _clean_sheet(self, event, player_id, team_id):
        self.create_new_event(
            event=event, new_type_id=101, new_player_id=player_id,
            new_team_id=team_id, new_qualifiers=[]
        )

    def _shot_against(self, event, player_id, team_id):
        self.create_new_event(
            event=event, new_type_id=90, new_player_id=player_id,
            new_team_id=team_id, new_qualifiers=[]
        )

    def _goal_against(self, event, player_id, team_id, own_goal=False):
        new_q_event = []
        if own_goal:
            new_q_event = [{
                "ID": 0,
                "qualifierID": 921,
                "value": "team_own_goal"
            }]
        else:
            self._shot_on_target_against(event=event, player_id=player_id, team_id=team_id)

        self.create_new_event(
            event=event, new_type_id=92, new_player_id=player_id,
            new_team_id=team_id, new_qualifiers=new_q_event
        )

        return self

    def _shot_on_target_against(self, event, player_id, team_id, save_type=None):
        if save_type is None:
            save_type = []

        new_q_event = []
        if "1on1" in save_type:
            new_q_event.append({
                "ID": 0,
                "qualifierID": 934,
                "value": "save_1on1"
            })
        if "inside" in save_type:
            new_q_event.append({
                    "ID": 0,
                    "qualifierID": 914,
                    "value": "save_inside_box"
                })
        elif "outside" in save_type:
            new_q_event.append({
                    "ID": 0,
                    "qualifierID": 924,
                    "value": "save_outside_box"
                })

        self._shot_against(event=event, player_id=player_id, team_id=team_id)
        self.create_new_event(
            event=event, new_type_id=94, new_player_id=player_id,
            new_team_id=team_id, new_qualifiers=new_q_event
        )
        return self

    def _crosses_against(self, event, player_id, team_id):
        self.create_new_event(
            event=event, new_type_id=96, new_player_id=player_id,
            new_team_id=team_id, new_qualifiers=[]
        )
        return self

    # ASSISTS
    def _assist(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=80, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _first_touch_assist(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=81, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _key_pass(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=84, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _key_pass_dribble(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=83, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _chances_set_play(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=85, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _chances_open_play(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=86, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    def _first_touch_key_pass(self, event, player_id, team_id):
        self.create_new_event_append_qualifiers(
            event=event, new_type_id=87, new_player_id=player_id, new_team_id=team_id, new_qualifiers=[]
        )
        return self

    # ---------CONVERTER---------
    @staticmethod
    def convert_str_to_int(*params):
        new_list = list()
        for param in params:
            try:
                new_list.append(int(param))
            except TypeError:
                new_list.append(param)
        return tuple(new_list)

    # --------CREATE NEW EVENTS---------
    @staticmethod
    def create_new_qualifiers(new_q_event):
        temp_q_event = new_q_event
        if isinstance(new_q_event, dict):
            try:
                temp_q_event = APIHelpers.QEvent(
                    id=new_q_event["ID"], qualifierID=new_q_event["qualifierID"], value=new_q_event["value"]
                )
            except KeyError:
                print(
                    f"The dictionary {new_q_event} does not contain one of the following key: ",
                    "'ID', 'value' or 'qualifierID'"
                    )
        return temp_q_event

    def create_new_event(self, event, new_type_id, new_player_id, new_team_id, new_qualifiers):
        new_q_events = []
        for q_event in new_qualifiers:
            new_q_events.append(self.create_new_qualifiers(q_event))

        set_value_dict = {
            "QEvent": new_q_events,
            "type_id": new_type_id,
            "player_id": new_player_id,
            "team_id": new_team_id,
            "event_id": self.last_event + self.counter,
            "id": int("9" + str(event.ID))
        }

        new_event = copy.deepcopy(event)
        for key, value in set_value_dict.items():
            new_event.setFeature(
                feature=key, value=value
            )

        self.update_events(new_event=new_event)
        self.counter += 1
        return self

    def create_new_event_append_qualifiers(self, event, new_type_id, new_player_id, new_team_id, new_qualifiers):
        new_q_events = event.qEvents
        for q_event in new_qualifiers:
            new_q_events.append(self.create_new_qualifiers(q_event))

        set_value_dict = {
            "QEvent": new_q_events,
            "type_id": new_type_id,
            "player_id": new_player_id,
            "team_id": new_team_id,
            "event_id": self.last_event + self.counter,
            "id": int("9" + str(event.ID))
        }

        new_event = copy.deepcopy(event)
        for key, value in set_value_dict.items():
            new_event.setFeature(
                feature=key, value=value
            )
        self.update_events(new_event=new_event)
        self.counter += 1
        return self

    # --------UPDATE EVENTS--------
    def update_events(self, new_event):
        if not isinstance(new_event, list):
            new_event = [new_event]
        self.events[self.index:self.index] = new_event
        self.index += len(new_event)
        return self

    # -------MAIN FUNCTION HELPER-----
    def team_on(self, team_id):
        if self.away_team is None:
            self.away_team = team_id
        elif self.home_team is None:
            self.home_team = team_id
        return self

    def player_on(self, player_id):
        if self.away_goalkeeper is None:
            self.away_goalkeeper = player_id
            self.clean_sheet_away = True
        elif self.home_goalkeeper is None:
            self.home_goalkeeper = player_id
            self.clean_sheet_home = True
        return self

    def player_off(self, event, player_id):
        if player_id == self.away_goalkeeper:
            if self.clean_sheet_away:
                self._clean_sheet(
                    event=event, player_id=self.away_goalkeeper, team_id=self.away_team
                )
            self.away_goalkeeper = None
        elif player_id == self.home_goalkeeper:
            if self.clean_sheet_home:
                self._clean_sheet(
                    event=event, player_id=self.home_goalkeeper, team_id=self.home_team
                )
            self.home_goalkeeper = None
        else:
            pass
        return self

    def match_team_player(self, team_id, inverse=True):
        if team_id == self.away_team:
            other_team = self.home_team
            if inverse:
                goalkeeper = self.home_goalkeeper
            else:
                goalkeeper = self.away_goalkeeper
        else:
            other_team = self.away_team
            if inverse:
                goalkeeper = self.away_goalkeeper
            else:
                goalkeeper = self.home_goalkeeper
        return tuple([other_team, goalkeeper])

    def change_clean_sheet(self, player_id):
        if self.away_goalkeeper == player_id:
            self.clean_sheet_away = False
        else:
            self.clean_sheet_home = False
        return self

    def key_pass_dribble_check(self, event_id):
        updated_event_id = int(event_id) - 1
        if updated_event_id in self.take_on_dict:
            return self.take_on_dict[updated_event_id]
        return None

    def get_assist_event(self, qualifier_dict, qualifier_id):
        assist_event = None
        try:
            assist_event = self.pass_dict[int(qualifier_dict[qualifier_id].value)]
        except KeyError:
            try:
                assist_event = self.ball_touch_dict[int(qualifier_dict[qualifier_id].value)]
            except KeyError:
                print("Assist Event could not be defined.")
        return assist_event

    def create_assist_event(self, qualifier_dict, define_assist=False):
        assist_event = self.get_assist_event(qualifier_dict=qualifier_dict, qualifier_id=QTypes.ID_55)
        if assist_event is None:
            return None

        player_id, team_id = self.convert_str_to_int(assist_event.playerID, assist_event.teamID)

        dribble_check = self.key_pass_dribble_check(event_id=assist_event.eventID)
        if dribble_check is not None:
            self._key_pass_dribble(event=dribble_check, player_id=player_id, team_id=team_id)

        if define_assist:
            self._assist(event=assist_event, player_id=player_id, team_id=team_id)
            if QTypes.ID_328 in qualifier_dict:
                self._first_touch_assist(event=assist_event, player_id=player_id, team_id=team_id)

        else:
            self._key_pass(event=assist_event, player_id=player_id, team_id=team_id)

            if (
                    QTypes.ID_24 in qualifier_dict
                    or QTypes.ID_25 in qualifier_dict
                    or QTypes.ID_26 in qualifier_dict
                    or QTypes.ID_160 in qualifier_dict
            ):
                self._chances_set_play(event=assist_event, player_id=player_id, team_id=team_id)

            if (
                    QTypes.ID_22 in qualifier_dict
                    or QTypes.ID_23 in qualifier_dict
            ):
                self._chances_open_play(event=assist_event, player_id=player_id, team_id=team_id)

            if QTypes.ID_328 in qualifier_dict:
                self._first_touch_key_pass(event=assist_event, player_id=player_id, team_id=team_id)

    # --------MAIN FUNCTION----------
    def event_handler(self, data):
        """
        This function will construct new events for goalkeepers' and assists statistics.
        The usual event handlers use PlayerID and TypeID to assign statistics for a player from an event.
        However, in some cases for assists' and goalkeepers' statistics, these two identifier will not be enough.
        Hence, the algorithm will require all the events that occurred in the game for determining all the statistics,
        which causes the algorithm run slower. To prevent this, while saving F24 Event types into MongoDB, we will
        construct new events that are already assigned to the objective goalkeepers or any player in game.

        :param list data: The list of ALL F24 type events occurred in a game.
        :return: Function returns a deep copy of data itself, which appended with new events.
        :rtype: list
        """
        self.events = copy.deepcopy(data)
        self.last_event = int(data[-1].eventID) + 1

        for event in data:
            self.index += 1
            type_id = int(event.typeID)

            if type_id == EventIDs.ID_34_Team_set_up:
                team_id, player_id = self.convert_str_to_int(event.teamID, event.playerID)
                self.team_on(team_id=team_id)

                line_up = list()
                goal_keeper_index = 0
                for q in event.qEvents:
                    if int(q.qualifierID) == QTypes.ID_30:
                        line_up = q.value.split(",")
                    elif int(q.qualifierID) == QTypes.ID_44:
                        for index in range(len(q.value.split(","))):
                            if int(str(q.value.split(",")[index]).strip()) == 1:
                                goal_keeper_index = index
                try:
                    self.player_on(player_id=int(str(line_up[goal_keeper_index]).strip()))
                except KeyError:
                    print("Please provide ALL F24 events of the game.")
                    return self.events

            elif type_id == EventIDs.ID_18_Player_Off:
                player_id = self.convert_str_to_int(event.playerID)
                self.player_off(event=event, player_id=player_id)

                for q in event.qEvents:
                    if int(q.qualifierID) == QTypes.ID_55:
                        self.substitute_id = int(q.value)

            elif type_id == EventIDs.ID_19_Player_on:
                player_id = self.convert_str_to_int(event.playerID)
                substitute_for_goalkeeper = False
                temp_substitute_id = 0
                for q in event.qEvents:
                    if int(q.qualifierID) == QTypes.ID_44:
                        if q.value == "Goalkeeper":
                            substitute_for_goalkeeper = True
                    elif int(q.qualifierID) == QTypes.ID_55:
                        temp_substitute_id = int(q.value)

                if substitute_for_goalkeeper:
                    if self.substitute_id - 1 == temp_substitute_id:
                        self.player_on(player_id=player_id)
                        self.substitute_id = None

            elif type_id == EventIDs.ID_17_Card:
                player_id = self.convert_str_to_int(event.playerID)
                for q in event.qEvents:
                    if int(q.qualifierID) == QTypes.ID_32 or int(q.qualifierID) == QTypes.ID_33:
                        self.player_off(event=event, player_id=player_id)

            elif type_id == EventIDs.ID_16_Goal:
                team_id, player_id = self.convert_str_to_int(event.teamID, event.playerID)
                own_goal = False
                qualifier_dict = dict()
                for q in event.qEvents:
                    qualifier_dict[int(q.qualifierID)] = q

                if QTypes.ID_28 in qualifier_dict:
                    own_goal = True
                else:
                    if QTypes.ID_55 in qualifier_dict:
                        self.create_assist_event(qualifier_dict=qualifier_dict, define_assist=True)

                other_team, goalkeeper = self.match_team_player(team_id=team_id, inverse=not own_goal)
                self.change_clean_sheet(player_id=goalkeeper)
                if own_goal:
                    other_team = team_id
                self._goal_against(
                    event=event, player_id=goalkeeper, team_id=other_team, own_goal=own_goal
                )

            elif type_id == EventIDs.ID_13_Miss or type_id == EventIDs.ID_14_Post:
                team_id, player_id = self.convert_str_to_int(event.teamID, event.playerID)
                other_team, goalkeeper = self.match_team_player(team_id=team_id)
                self._shot_against(event=event, player_id=goalkeeper, team_id=other_team)

                qualifier_dict = dict()
                for q in event.qEvents:
                    qualifier_dict[int(q.qualifierID)] = q
                if (QTypes.ID_29 in qualifier_dict) and (QTypes.ID_55 in qualifier_dict):
                    self.create_assist_event(qualifier_dict=qualifier_dict)

            elif type_id == EventIDs.ID_15_Attempt_Saved:
                team_id = self.convert_str_to_int(event.teamID)
                self.x = float(event.x)
                self.y = float(event.y)
                other_team, goalkeeper = self.match_team_player(team_id=team_id)

                qualifier_dict = dict()
                for q in event.qEvents:
                    qualifier_dict[int(q.qualifierID)] = q
                if (QTypes.ID_29 in qualifier_dict) and (QTypes.ID_55 in qualifier_dict):
                    self.create_assist_event(qualifier_dict=qualifier_dict)

                save_type = []
                if QTypes.ID_82 not in qualifier_dict:
                    if self.x >= 83.3 and 21.1 <= self.y <= 78.9:
                        save_type.append("inside")
                    else:
                        save_type.append("outside")

                    if(
                            QTypes.ID_89 in qualifier_dict
                            and QTypes.ID_94 not in qualifier_dict
                            and QTypes.ID_190 not in qualifier_dict
                    ):
                        save_type.append("1on1")

                    self._shot_on_target_against(
                        event=event, player_id=goalkeeper, team_id=other_team, save_type=save_type
                    )

                elif QTypes.ID_101 in qualifier_dict:
                    self._shot_on_target_against(
                        event=event, player_id=goalkeeper, team_id=other_team
                    )

                else:
                    self._shot_against(
                        event=event, player_id=goalkeeper, team_id=other_team
                    )

            elif type_id == EventIDs.ID_60_Chance_missed:
                qualifier_dict = dict()
                for q in event.qEvents:
                    qualifier_dict[int(q.qualifierID)] = q
                if (QTypes.ID_29 in qualifier_dict) and (QTypes.ID_55 in qualifier_dict):
                    self.create_assist_event(qualifier_dict=qualifier_dict)

            elif type_id == EventIDs.ID_1_Pass_Events:
                event_id, team_id = self.convert_str_to_int(event.eventID, event.teamID)
                self.pass_dict[event_id] = event
                other_team, goalkeeper = self.match_team_player(team_id=team_id)

                for q in event.qEvents:
                    if int(q.qualifierID) == QTypes.ID_2:
                        self._crosses_against(
                            event=event, player_id=goalkeeper, team_id=other_team
                        )

            elif type_id == EventIDs.ID_61_Ball_touch:
                event_id = self.convert_str_to_int(event.eventID)
                self.ball_touch_dict[event_id] = event

            elif type_id == EventIDs.ID_3_Take_On:
                event_id = self.convert_str_to_int(event.eventID)
                self.take_on_dict[event_id] = event

            elif type_id == EventIDs.ID_30_End:
                if int(event.periodID) == 2:
                    self.player_off(event=event, player_id=self.away_goalkeeper)
                    self.player_off(event=event, player_id=self.home_goalkeeper)
                    break

        print(f"New events are constructed! Total number of new events : {self.counter}")
        return self.events


if __name__ == "__main__":
    pass
