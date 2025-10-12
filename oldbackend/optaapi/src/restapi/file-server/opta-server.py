"""
@author: Cem Akpolat
@created by cemakpolat at 2020-09-24
"""

from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import json, os

# credentials
url = "http://omo.akamai.opta.net/competition.php?"
url24 = "http://omo.akamai.opta.net/?"
competition_id = "115"
season_id = "2018-old"
username = "besiktas"
password = "c59mrbsa"

# host
host = "localhost"
port = 27017

app = Flask(__name__)
api = Api(app)


class Feeds:
    f1 = "f1"
    f9 = "f9"
    f24 = "f24"
    f40 = "f40"
    feed1 = "feed1"
    feed9 = "feed9"
    feed24 = "feed24"
    feed40 = "feed40"
    feed1DB = "feed1"
    feed9DB = "feed9"
    feed24DB = "feed24"
    feed40DB = "feed40"
    feedConfigs = "feedConfigs"


# Check the codes in https://www.programiz.com/python-programming/json
def getFeed(feedName, competition_id, season_id, gameId=None):
    filename = feedName + "_" + str(competition_id) + "_" + str(season_id)
    data = "{}"

    if gameId is not None:
        if feedName is "feed24":
            gameId = gameId.replace("g", "")
        filename = filename + "_" + str(gameId)
    path = "feeds" + "/" + str(competition_id) + "/" + str(season_id)
    print(filename)
    try:

        if not os.path.exists(path):
            print("file path does not exist ->" + path)
        with open(os.path.join(path, filename)) as f:
            data = json.load(f)
        return data
    except IOError:
        print("Either folder could not be created or file could not be saved!")


class opta_rest(Resource):
    # http://127.0.0.1:5000/?feed_type=f40&competition=115&season_id=2017&user=cem&psw=a&json
    # http://127.0.0.1:5000/?feed_type=f1&competition=115&season_id=2017&user=cem&psw=a&json
    # http: // 127.0.0.1: 5000 /?game_id = 935627 & feed_type = f24 & competition = 115 & season_id = 2017 & user = cem & psw = a & json
    # http: // 127.0.0.1: 5000 /?game_id = 935627 & feed_type = f9 & competition = 115 & season_id = 2017 & user = cem & psw = a & json
    def get(self):
        feed_type = request.args.get("feed_type")
        competition_id = request.args.get("competition")
        season_id = request.args.get("season_id")
        game_id = request.args.get("game_id")

        username = request.args.get("user")
        password = request.args.get("psw")
        output_fornat = request.args.get("json")

        data = getFeed(feed_type, competition_id, season_id, game_id)

        return jsonify(data)


api.add_resource(opta_rest, "/")


if __name__ == "__main__":
    app.run(debug=True)
