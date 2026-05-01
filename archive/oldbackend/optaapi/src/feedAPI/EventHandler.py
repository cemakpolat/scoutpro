"""
This class handles the F24 events data and distributes to the related event handler
Author: Cem Akpolat, Doruk Sahinel

"""
import sys

sys.path.append("..")  # Adds higher directory to python modules path.
from src.events.Events import EventIDs
from src.events.Events import EventTypesHelper
from src.events.PassEvent import PassEvent as PassEvents
from src.events.AerialDuelEvents import AerialDuelEvents
from src.events.FoulEvents import FoulEvents
from src.events.AssistEvents import AssistEvents
from src.events.BallControlEvents import BallControlEvents
from src.events.ShotandGoalEvents import ShotandGoalEvents
from src.events.DuelEvents import DuelEvents
from src.events.TakeOnEvents import TakeOnEvents
from src.events.GoalkeeperEvents import GoalkeeperEvents
from src.events.CardEvents import CardEvents
from src.events.GamesandMinutesEvents import GamesandMinutesEvents
from src.events.TouchEvents import TouchEvents
from src.events.EventMinutes import EventMinutes


class EventHandler:
    def __init__(self):
        print("Event handler is started")
        self.event_helper = EventTypesHelper()

    def handle_events(self, eventType, data, print_results=True):
        if isinstance(eventType, list):
            self.handleMultipleEvent(eventType, data, print_results)
        elif isinstance(eventType, list):
            if eventType == EventIDs.ALL:
                self.handle_all_events(data, print_results)
            else:
                self.handle_single_event(eventType, data)
        else:
            print("evenType is unknown!")

    # All events are handled a result list is returned to the requester
    def handle_all_events(self, data, print_results=False):
        import time
        start_time = time.time()
        results = []
        print("--------------All Events are Handling----------------")
        # return here a list of events
        results.append({"aerial": AerialDuelEvents().callEventHandler(data, print_results)})
        print("aerial event is done!")
        results.append({"pass": PassEvents().callEventHandler(data, print_results)})
        print("pass event is done!")
        results.append({"foul": FoulEvents().callEventHandler(data, print_results)})
        print("foul event is done!")
        results.append({"assist": AssistEvents().callEventHandler(data, print_results)})
        print("assists event is done!")
        results.append({"ballControl": BallControlEvents().callEventHandler(data, print_results)})
        print("ball_control event is done!")
        results.append({"takeOn": TakeOnEvents().callEventHandler(data, print_results)})
        print("take_on event is done!")
        results.append({"card": CardEvents().callEventHandler(data, print_results)})
        print("card event is done!")
        results.append({"touch": TouchEvents().callEventHandler(data, print_results)})
        print("touch event is done!")
        results.append({"duel": DuelEvents().callEventHandler(data, print_results)})
        print("duel event is done!")
        results.append({"shot": ShotandGoalEvents().callEventHandler(data, print_results)})
        print("shot event is done!")
        results.append({"goalKeeper": GoalkeeperEvents().callEventHandler(data, print_results)})
        print("goalkeeper event is done!")
        end_time = time.time()

        print("total duration:", end_time-start_time)
        # all data should be stored in a single file and database after the processing steps
        # should we store the updated result in the database, it is actually not neccessary if we won't learn from it

        return results

    # A single event type is handled and its result is returned
    def handle_single_event(self, eventType, data, print_results=True):

        if eventType is EventIDs.AerialDuelEvents:
            print("---------Aerial Events are Handling--------------")
            result = {"aerial": AerialDuelEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.AssistEvents:
            print("---------Assist Events are Handling--------------")
            result = {"assist": AssistEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.BallControlEvents:
            print("---------Ball Control Events are Handling--------------")
            result = {"ballControl": BallControlEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.CardEvents:
            print("---------Card Events are Handling--------------")
            result = {"card": CardEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.DuelEvents:
            print("---------Duel Events are Handling--------------")
            result = {"duel": DuelEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.FoulEvents:
            print("---------Foul Events are Handling--------------")
            result = {"foul": FoulEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.GoalkeeperEvents:
            print("---------Goalkeeper Events are Handling--------------")
            result = {"goalKeeper": GoalkeeperEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.PassEvents:
            print("---------Pass Events are Handling--------------")
            result = {"pass": PassEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.ShotandGoalEvents:
            print("---------Shot and Goal Events are Handling--------------")
            result = {"shot": ShotandGoalEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.TakeOnEvents:
            print("---------Take on Events are Handling--------------")
            result = {"takeOn": TakeOnEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.TouchEvents:
            print("---------Touch Events are Handling--------------")
            result = {"touch": TouchEvents().callEventHandler(data, print_results)}

        elif eventType is EventIDs.EventMinutes:
            print("---------Event Minutes are Handling--------------")
            result = {"minutes": EventMinutes().callEventHandler(data)}

        elif eventType is EventIDs.GamesandMinutesEvents:
            print("---------Event Minutes are Handling--------------")
            result = {"player_min": GamesandMinutesEvents().callEventHandler(data)}

        else:
            print("Event type is not known!")
            result = {str(eventType): None}

        return result

    def handle_all_events_v2(self, data, print_results=True):# event handler for front_end
        results = {}
        # return here a dict of events
        results["aerial"] = AerialDuelEvents().callEventHandler(data, print_results)
        results["pass"] = PassEvents().callEventHandler(data, print_results)
        results["foul"] = FoulEvents().callEventHandler(data, print_results)
        results["assist"] = AssistEvents().callEventHandler(data, print_results)
        results["ballControl"] = BallControlEvents().callEventHandler(data, print_results)
        results["takeOn"] = TakeOnEvents().callEventHandler(data, print_results)
        results["card"] = CardEvents().callEventHandler(data, print_results)
        results["touch"] = TouchEvents().callEventHandler(data, print_results)
        results["duel"] = DuelEvents().callEventHandler(data, print_results)
        results["shot"] = ShotandGoalEvents().callEventHandler(data, print_results)
        results["goalKeeper"] = GoalkeeperEvents().callEventHandler(data, print_results)

        # all data should be stored in a single file and database after the processing steps
        # should we store the updated result in the database, it is actually not neccessary if we won't learn from it

        return results

    def handle_single_event_v2(self, event_type, data, print_results=True):  # event handler for front_end
        result = None

        if event_type == "aerial":
            result = {"aerial": AerialDuelEvents().callEventHandler(data, print_results)}

        elif event_type == "assist":
            result = {"assist": AssistEvents().callEventHandler(data, print_results)}

        elif event_type == "ballControl":
            result = {"ballControl": BallControlEvents().callEventHandler(data, print_results)}

        elif event_type == "card":
            result = {"card": CardEvents().callEventHandler(data, print_results)}

        elif event_type == "duel":
            result = {"duel": DuelEvents().callEventHandler(data, print_results)}

        elif event_type == "foul":
            result = {"foul": FoulEvents().callEventHandler(data, print_results)}

        elif event_type == "goalKeeper":
            result = {"goalKeeper": GoalkeeperEvents().callEventHandler(data, print_results)}

        elif event_type == "pass":
            result = {"pass": PassEvents().callEventHandler(data, print_results)}

        elif event_type == "shot":
            result = {"shot": ShotandGoalEvents().callEventHandler(data, print_results)}

        elif event_type == "takeOn":
            result = {"takeOn": TakeOnEvents().callEventHandler(data, print_results)}

        elif event_type == "touch":
            result = {"touch": TouchEvents().callEventHandler(data, print_results)}

        elif event_type == "minutes":
            result = {"minutes": EventMinutes().callEventHandler(data)}

        return result

    # More than one event is taken and the requested events' statistics are returned
    def handleMultipleEvent(self, eventTypes, data, print_results=True):
        results = []
        for eventType in eventTypes:
            results.append(self.handle_single_event(eventType, data, print_results))
        return results
