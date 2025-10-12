"""
@author: Cem Akpolat
@created by cemakpolat at 2020-07-24
"""
import json

from flask import Blueprint, Response
from src.feedAPI.EventAPI import EventAPI

events = Blueprint("events", __name__)

@events.route("/events", methods=["GET"], endpoint="get all events")
def get_events():
    event = EventAPI()
    result = event.getEventBy()
    return Response(result, mimetype="application/json", status=200)


@events.route("/events/<id>", methods=["GET"], endpoint="event")
def get_event_id(id):
    event = EventAPI()
    result = event.getEventById(id)
    return Response(result, mimetype="application/json", status=200)


@events.route("/events/o/<oid>", methods=["GET"], endpoint="event via oid")
def get_event_oid(oid):
    event = EventAPI()
    result = event.getEventByOId(oid)
    return Response(result, mimetype="application/json", status=200)


@events.route("/qevents/o/<oid>", methods=["GET"], endpoint="qevent via oid")
def get_qevent_oid(oid):
    event = EventAPI()
    result = event.getQEventByOId(oid)
    return Response(result, mimetype="application/json", status=200)


@events.route("/qevents/<id>", methods=["GET"], endpoint="qevent")
def get_qevent_id(id):
    event = EventAPI()
    result = event.getQEventById(id)
    return Response(result, mimetype="application/json", status=200)

#---------------------Get Event Parameters-----------------

@events.route("/events/<event_name>/params", methods=["GET"], endpoint="get event parameters")
def get_event_params(event_name):
    event = EventAPI()
    result = event.getEventParams(event_name=event_name)
    result = json.dumps(result, indent=4)
    return Response(result, mimetype="application/json", status=200)