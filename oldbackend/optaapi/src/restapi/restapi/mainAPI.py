"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-07-24


ENCODING:
    utf-8

SWAGGER:
    https://www.imaginarycloud.com/blog/flask-python/

Useful Links:
    https://github.com/closeio/flask-mongorest
    https://github.com/paurakhsharma/flask-rest-api-blog-series/blob/master/Part%20-%201/movie-bag/app.py
"""
from flask import Flask
from src.utils.Utils import Logger
from src.restapi.restapi.resources import (
    players,
    teams,
    analytics,
    games,
    events,
    errors
)


app = Flask(__name__)

err = errors.ErrorHandler(app)

logger = Logger(__name__).get_logger()

api_version = "/api/v1"

app.register_blueprint(players.players, url_prefix=api_version)
app.register_blueprint(teams.teams, url_prefix=api_version)
app.register_blueprint(analytics.analytic, url_prefix=api_version)
app.register_blueprint(games.games, url_prefix=api_version)
app.register_blueprint(events.events, url_prefix=api_version)


def run():
    logger.info("Rest server is started...")
    app.run(
        port=8080,
        debug=False
    )
