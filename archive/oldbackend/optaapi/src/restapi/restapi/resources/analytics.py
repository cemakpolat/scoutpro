"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-09-28

Important documents to follow up through the script file:

    https://www.datacamp.com/community/tutorials/machine-learning-models-api-python

    https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask

    https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/

"""
import json
import threading
import time
import pandas as pd
from flask import (
    Blueprint,
    request,
    jsonify,
    Response
)
from werkzeug.utils import secure_filename
from src.danalyticAPI.engine import (
    AnalyticEngine,
    default_algorithm,
    default_purpose
)
from danalyticAPI.algorithms import alg as alg
from src.utils.Utils import get_src_path


# Define blueprint object for the api.
analytic = Blueprint("analytic", __name__)


# Define main folder for the storage of data.
data_folder = get_src_path("\\repo\\")


## alf_config: {'name': 'decision-tree', 'config': {'param1': '3'}, 'file':'file-name'}
## feature_set[{'Aerial': ['total aerial duels', 'aerial duels won', 'aerial duels lost', 'aerial duels won percentage', 'aerial duels in attacking half', 'aerial duels won percentage in attacking half', 'aerial duels in defending half', 'aerial duels won percentage in defending half', 'aerial duels in attacking third', 'aerial duels won percentage in attacking third', 'aerial duels in middle third', 'aerial duels won percentage in middle third', 'aerial duels in defending third', 'aerial duels won percentage in defending third']}]
@analytic.route(
    rule="/analytic/",
    methods=["GET", "POST"],
    endpoint="run_algorithm",
    defaults={
        "algorithm": None,
        "purpose": None,
    }
)
@analytic.route(
    rule="/analytic/<string:algorithm>/<string:purpose>",
    methods=["GET", "POST"],
    endpoint="run_algorithm"
)
def run_algorithm(
        algorithm: str = None,
        purpose: str = None
) -> Response:
    """
    The given request is the main rule to connect the analytic API of the application.
    By providing the algorithm name and the function name of the algorithm URL can be
    constructed. All possible algorithm names and their function has been provided
    in the documentation below.

    To use the request, setup data is crucial. The request takes the setup data in
    JSON format with POST method. The construction of setup data is also provided
    in the documentation in below.

    Possible Algorithms and Their Functions:
        1) algorithm:
            -data:
                input{
                    train_data: bool = False,
                    target_data: bool = False
                }

        2) feature-selection:
            -pca:
                input{
                    n_components: int
                }

            -pca_info:
                input{}

            -correlate:
                input{}

            -correlated:
                input{}

            -correlation:
                input{}

            -anova_regression:
                input{}

            -anova_classifier:
                input{}

            -mutual_info_regression:
                input{}

            -mutual_info_classifier:
                input{}

            -lasso:
                input{}

            -chi_square:
                input{}

        3) cluster:
            -predict:
                input{}

            -result:
                input{}

            -visualise:
                input{}

            -elbow:
                input{}

            -silhouette:
                input{}
        
        4) linear-regression:
            -predict:
                input{}

            -result:
                input{}

        4) logistic-regression:
            -predict:
                input{}

            -result:
                input{}

            -confusion:
                input{}

    Setup Data:
        {
            "algorithm": {
                "name": <string>,
                "function": <string>,
                "input": <dict>,
                "config": {
                    "test_size": <float>,
                    "random_state": <float>,
                    "criterion": <string>,
                    "n_cluster": <integer>,
                    "threshold": <float>,
                    "normalise": <bool>
                }
            },
            "data": {
                "query": {
                    competitionID: <int>,
                    seasonID: <int>,
                    game_ids: <list>,
                    team_ids: <list>,
                    player_ids: <list>,
                    time_interval: <list>,
                    event_names: <list>
                },
                "file": {
                    file_name: <string>,
                    path: <string>,
                    sheet_name: <string>,
                },
                "url": <string>
            },
            "features": {
                "included": <list>,
                "excluded": <list>,
                "target": <list>,
            }
        }

    Example Usage:
        Linear Regression Obtain Data
        -URL: .../api/v1/analytic/cluster/data
        -METHOD: POST
        -JSON:
            {
                "algorithm": {
                    "input": {
                        "train_data": True
                    },
                    "config": {
                        "n_cluster": 4
                    }
                },
                "data": {
                    "query": {
                        "competitionID": 115,
                        "seasonID": 2018,
                        "team_ids": [378],
                        "event_names": ["ballControl"]
                    }
                },
                "features": {
                    "excluded": ["gameId", "Team Name"],
                    "target": ["bad ball touches"]
                }
            }


    Parameters:
        :param str algorithm: Name of the algorithm to run.
        :param str purpose: Name of the function of the algorithm to execute.
        :return: Resulting data in JSON format.

    """
    if request.method == "POST":
        content = request.get_json(
            silent=True
        )
        content = update_content(
            content=content,
            algorithm=algorithm,
            purpose=purpose
        )
        engine = AnalyticEngine(
            setup_data=content
        )
        result = engine.handle()
        response = json.dumps(
            obj=result,
            indent=4
        )
        return Response(
            response=response,
            mimetype="application/json",
            status=200
        )


class DataCampThread(threading.Thread):
    def __init__(self, name, delay):
        threading.Thread.__init__(self)
        self.name = name
        self.delay = delay

    def run(self):
        print("Starting Thread:", self.name)
        thread_delay(self.name, self.delay)
        print("Execution of Thread:", self.name, "is complete!")


def thread_delay(thread_name, delay):
    count = 0
    while count < 3:
        time.sleep(delay)
        count += 1
        print(thread_name, "-------->", time.time())


def update_content(
        content: dict = None,
        purpose: str = None,
        algorithm: str = None
):
    content = content or dict()
    algorithm = algorithm or default_algorithm
    purpose = purpose or default_purpose
    if not alg.algorithm in content:
        content[alg.algorithm] = dict()
    content[alg.algorithm][alg.name] = algorithm
    content[alg.algorithm][alg.function] = purpose
    return content

# t1 = DataCampThread('t1', 1)
# t1.start()
# t1.join()


if __name__ == "__main__":
    test_url = 'http://127.0.0.1:8080/api/v1/analytic/cluster/elbow'
    gs_url = "http://127.0.0.1:8080/api/v1/games/get?competition=115&season=2018&team=Galatasaray&event_names=ballControl"
    local_data = "Turkish_Super_League_19-20_28_Week_Stats.xlsx"
    setup_data = {
        "algorithm": {
            "name": "linear-regression",
            "function": "result",
        },
        "excluded_features": ["gameID"],
        "target_features": ["Home total cards"],
        "data": {
            "file": {
                "file_name": local_data,
                "sheet_name": "Game Results"
            }
        }
    }

    engine_result = AnalyticEngine(
        setup_data
    ).handle()

    print(engine_result)

    """
    import requests
    request_result = requests.post(
        url=test_url,
        json=setup_data
    )
    print(request_result.json())
    """


