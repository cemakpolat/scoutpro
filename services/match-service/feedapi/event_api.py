"""
@author: Cem Akpolat
@created by cemakpolat at 2020-10-08
Migrated to microservices - imports updated to use shared libraries
"""
import json
import random
import sys

# Add shared libraries to path
sys.path.append('/app')

# Shared library imports
from shared.connectors import Connector, main_conn
from shared.models.mongoengine.feed_models import *
from shared.utils import opta_utils as Utils


class EventAPI:
    def __init__(self, competition_id=None, season_id=None):
        self.competitionID = competition_id
        self.seasonID = season_id
        self.connector = main_conn
        self.doc_name = Utils.get_doc_name
        self.online = False
        self.db_port = 27017
        self.host = "localhost"
        self.event_names = [
            "aerial", "pass", "foul", "card", "ballControl",
            "takeOn", "touch", "duel", "shot", "assist", "goalkeeper"
        ]
        self.connector.connect()

    def setCompetitionSeason(self, competition_id, season_id):
        self.competitionID = competition_id
        self.seasonID = season_id

    def processEvent(self, event):
        obj = []
        print(event.to_json)
        for qid in event.qEvents:
            obj.append(
                {"id": qid.ID, "qualifierID": qid.qualifierID, "value": qid.value}
            )

        jsonObj = json.loads(event.to_json())
        jsonObj["qEvents"] = obj
        return jsonObj

    def getEventById(self, id):
        event = F24_Event.objects(
            Q(ID=id)
        )  # TODO: replace objects with another function that calls only unique element!
        return json.dumps(self.processEvent(event[0]))

    def getEventsBy(self):
        """
        Test methods
        :return:
        """
        events = F24_Event.objects(Q(outcome=1))[0:100].to_json()
        return events

    def getEventByOId(self, oid):
        event = F24_Event.objects(Q(id=oid))
        return json.dumps(self.processEvent(event[0]))

    def getQEventByOId(self, oid):
        qualifier_event = F24_QEvent.objects(Q(id=oid))
        obj = {'id': qualifier_event.ID, 'qualifierID': qualifier_event.qualifierID, 'value': qualifier_event.value}
        return json.dumps(obj)

    def getMatchEvent(self, gameId):
        """
        Event data for a unique matchId
        """
        game_api = GameAPI.GameAPI(self.competitionID, self.seasonID)
        events = game_api.getGameEvents(gameId)
        return events

    def getTeamEvents(self, team_name):
        """
        This is avaialable in TeamAPI
        """
        team_api = TeamAPI.TeamAPI(self.competitionID, self.seasonID)
        events = team_api.getTeamEvents(team_name)
        return events

    # ---------------------Get All Events with Parameters----------------

    def getAllEventParams(self):
        events = random.sample(
            population=self.event_names, k=len(self.event_names)
        )
        result = dict()
        for event in events:
            result[event] = self.getEventParams(event_name=event)
        return result

    # ---------------------Match Events with Parameters----------------

    def matchEventParams(self, params: list):
        events = random.sample(
            population=self.event_names, k=len(self.event_names)
        )
        result = dict()

        try:
            params_set = set(params)
        except TypeError:
            print("The params input must be an array, "
                  "that is consisting of some parameters.")
            return result

        for event in events:
            all_params = set(self.getEventParams(event_name=event))
            common_params = all_params.intersection(params_set)
            if len(common_params) != 0:
                result[event] = list(common_params)
                params_set.difference_update(common_params)

        return result

    # ---------------------Check Event Parameters----------------

    def checkEventParams(self, event: str, params: list):
        all_params = self.getEventParams(event)

        all_params_set = set(all_params)

        try:
            params_set = set(params)
        except TypeError:
            print("The params input must be an array, "
                  "that is consisting of some parameters.")
            return None

        if params_set.issubset(all_params_set):
            return True
        else:
            return False

    # ------------Get Event Collection Names Dictionary----------------

    def getEventCollectionDict(self):
        events = {
            "aerial": self.doc_name(doc=AerialEvent),
            "pass": self.doc_name(doc=PassEvent),
            "foul": self.doc_name(doc=FoulEvent),
            "card": self.doc_name(doc=CardEvent),
            "ballControl": self.doc_name(doc=BallControlEvent),
            "takeOn": self.doc_name(doc=TakeOnEvent),
            "touch": self.doc_name(doc=TouchEvent),
            "duel": self.doc_name(doc=DuelEvent),
            "shot": self.doc_name(doc=ShotandGoalEvent),
            "assist": self.doc_name(doc=AssistEvent),
            "goalkeeper": self.doc_name(doc=GoalkeeperEvent)
        }

        return events

    # ------------Get Event Collection Names Inverse Dictionary----------------

    def getEventCollectionInverseDict(self):
        inverse_events = {
            self.doc_name(doc=AerialEvent): "aerial",
            self.doc_name(doc=PassEvent): "pass",
            self.doc_name(doc=FoulEvent): "foul",
            self.doc_name(doc=CardEvent): "card",
            self.doc_name(doc=BallControlEvent): "ballControl",
            self.doc_name(doc=TakeOnEvent): "takeOn",
            self.doc_name(doc=TouchEvent): "touch",
            self.doc_name(doc=DuelEvent): "duel",
            self.doc_name(doc=ShotandGoalEvent): "shot",
            self.doc_name(doc=AssistEvent): "assist",
            self.doc_name(doc=GoalkeeperEvent): "goalkeeper"
        }

        return inverse_events

    # ------------Get Event Names in PlayerStatistics Dictionary----------------

    def getEventFieldsDict(self):
        events = {
            "aerial": "aerialEvent",
            "pass": "passEvent",
            "foul": "foulEvent",
            "card": "cardEvent",
            "ballControl": "ballControlEvent",
            "takeOn": "takeOnEvent",
            "touch": "touchEvent",
            "duel": "duelEvent",
            "shot": "shotEvent",
            "assist": "assistEvent",
            "goalkeeper": "goalkeeperEvent"
        }
        return events

    # ---------------------Get Event Dictionary----------------

    def getEventDict(self):
        events = {
            "aerial": AerialEvent,
            "pass": PassEvent,
            "foul": FoulEvent,
            "card": CardEvent,
            "ballControl": BallControlEvent,
            "takeOn": TakeOnEvent,
            "touch": TouchEvent,
            "duel": DuelEvent,
            "shot": ShotandGoalEvent,
            "assist": AssistEvent,
            "goalkeeper": GoalkeeperEvent
        }
        return events

    def multi_event_dict(self):
        events = {
            "aerial": "AerialDuelEvents",
            "pass": "PassEvents",
            "foul": "FoulEvents",
            "card": "CardEvents",
            "ballControl": "BallControlEvents",
            "takeOn": "TakeOnEvents",
            "touch": "TouchEvents",
            "duel": "DuelEvents",
            "shot": "ShotandGoalEvents",
            "assist": "AssistEvents",
            "goalkeeper": "GoalkeeperEvents",
            "minutes": "GamesandMinutesEvents"
        }
        return events

    # --------------------Get Event Parameters-----------------

    def getEventParams(self, event_name: str):
        events = self.getEventDict()
        params_list = list()
        for field in events[event_name]._fields:
            params_list.append(field)
        return params_list

    # --------------Get Document Objects Fields-----------------

    def getDocumentFields(self, document_obj):

        fields = dict()
        fields_list = list()
        for field in document_obj._fields:
            fields_list.append(field)

        fields["fields"] = fields_list

        return fields

    # -------------------------------------------------------
