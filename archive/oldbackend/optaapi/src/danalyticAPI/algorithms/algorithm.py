"""
@author: Hüseyin Eren
@created by huseyin_eren at 2023-07-03

Purpose:
    algorithm.py script file contains the main Algorithm object for
    apply inheritance definition into all the subclasses of data
    analytic functions defined on the project.

Useful Links:
    1 - [data camp](https://www.datacamp.com/community/tutorials/decision-tree-classification-python?utm_source=adwords_ppc&utm_campaignid=898687156&utm_adgroupid=48947256715&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=332602034349&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=9060640&gclid=Cj0KCQjwp4j6BRCRARIsAGq4yMEcWrrn6exFOzQSI8R9vZ-2d1lywnJPihhJkmNMpzYOQsRxtBpukQYaAlFDEALw_wcB)
    2 - [heartbeat](https://heartbeat.fritz.ai/decision-tree-classification-in-python-with-scikit-learn-245502ada8aa) \
    3 - [stackable](https://stackabuse.com/applying-wrapper-methods-in-python-for-feature-selection/)
    4 - [hacker earth](https://www.hackerearth.com/de/practice/machine-learning/machine-learning-algorithms/ml-decision-tree/tutorial/)
    5 - [towards-datascience](https://towardsdatascience.com/machine-learning-basics-descision-tree-from-scratch-part-i-4251bfa1b45c)

"""
import json
import sys
import os
import pandas as pd
from random import choice
import requests
from src.danalyticAPI.algorithms import alg
from src.dataRetrieving.readData import (
    json_to_df_statistics_games as read_json,
    excel_to_df as read_excel,
    csv_to_df as read_csv
)
from src.feedAPI.GameAPI import GameAPI
from src.utils.Utils import (
    Logger,
    get_src_path,
    df_to_dict
)


# Define logger.
logger = Logger(__name__).get_algorithm_logger()


# Define main folder for the storage of data.
data_folder = get_src_path("\\repo\\")


# Define reader.
reader = {
    "json": read_json,
    "xlsx": read_excel,
    "csv": read_csv
}

# Limiting total number of games to get their data just for testing.
limit = 10

# Some default variables.
default_competition_id = 115
default_season_id = 2018
default_game_api = GameAPI(
    competitionID=default_competition_id,
    seasonID=default_season_id
)

# Define column parameters.
column_params = {
    alg.included: "included_columns",
    alg.excluded: "excluded_columns",
    alg.target: "target_columns"
}

class Algorithm:
    """
    Algorithm class will be the parent class of all Machine Learning
    algorithms. The main reason for why we are creating such a structure
    is to provide same loading data methods for each of these algorithms.
    Otherwise, we could need to provide same loading operations over again,
    for each of these ML operations.

    Parameters:
        :param pd.DataFrame self.pima:
        :param pd.DataFrame self.X:
        :param pd.DataFrame self.y:
        :param list self.included_columns:
        :param list self.excluded_columns:
        :param list self.target_columns:

    """
    def __init__(self):
        self.pima = None
        self.X = None
        self.y = None
        self.included_columns = None
        self.excluded_columns = None
        self.target_columns = None
        self.label = None

    def _construct_columns(self):
        if not isinstance(self.included_columns, list):
            self.included_columns = self.pima.columns.tolist()
        excluded_columns = list()
        if isinstance(self.excluded_columns, list):
            excluded_columns += self.excluded_columns
        if isinstance(self.target_columns, list):
            excluded_columns += self.target_columns
        self.included_columns = list(
            set(self.included_columns).difference(
                set(excluded_columns)
            )
        )
        return self

    def _construct_X(self):
        # Train Data.
        try:
            self.X = self.pima[self.included_columns]
        except Exception as err:
            logger.error(
                f"Data X (train features) could not be created: {err}"
            )
        return self

    def _construct_y(self):
        # Target Data.
        if not isinstance(self.target_columns, list):
            target = choice(self.included_columns)
            logger.warning(
                    f"Target feature could not be found, hence "
                    f"following feature has been chosen as "
                    f"target feature randomly: {target}"
            )
            self.target_columns = [target]
            self._construct_columns()
            self._construct_X()
        try:
            self.y = self.pima[self.target_columns]
        except KeyError as err:
            logger.error(
                f"Data y (train target) could not be defined: {err}"
            )
        return self

    def _load_features(self, setup_data: dict):
        if alg.features in setup_data:
            for key, value in column_params.items():
                if key in setup_data[alg.features]:
                    setattr(
                        self,
                        value,
                        setup_data[alg.features][key]
                    )
        else:
            logger.warning(
                "Provided setup_data does not have features key. "
                "Therefore, all columns in the provided data will, "
                "be taken on for the objective algorithm."
            )

    def _load_data(self, setup_data: dict):
        self._load_features(setup_data)
        if alg.data in setup_data:
            data = setup_data[alg.data]
            if alg.file in data:
                file = data[alg.file]
                return self.load_data_from_file(**file)
            elif alg.query in data:
                query = data[alg.query]
                return self.load_data_from_db(**query)
            elif alg.url in data:
                url = data[alg.url]
                return self.load_data_from_url(url)
            else:
                logger.error(
                    "Provided setup_data does not have a "
                    "suitable loading data option."
                )
        else:
            logger.warning(
                "Provided setup_data does not have data key. "
                "Therefore, all games in the season will be taken, "
                "this make take some time to execute ..."
            )
            query = {
                "competitionID": default_competition_id,
                "seasonID": default_season_id,
                "game_ids": default_game_api.get_random_game_ids(
                    k=limit
                ),
                "limit": limit
            }
            return self.load_data_from_db(**query)

    def load_data_from_file(self, **file):
        if alg.file_name not in file:
            logger.error(
                "Setup data must have file_name key in file load option."
            )
        else:
            extension = file[alg.file_name].split(".")[-1]
            if extension not in reader:
                logger.error(
                    "Provided extension type "
                    f"does not supported: {extension}"
                )
            else:
                if alg.path not in file:
                    file[alg.path] = data_folder
                function = reader[extension]
                data = function(
                    **file
                )
                self.pima = data
        return self._construct_columns()

    def load_data_from_db(self, **kwargs):
        season = {
            alg.competition_id: default_competition_id,
            alg.season_id: default_season_id
        }
        for key in season:
            if key in kwargs:
                season[key] = kwargs[key]
                del kwargs[key]
            else:
                logger.error(
                    "While assigning competition and season, "
                    f"following key is missing: {key}."
                )
        game_api = GameAPI(**season)
        games = game_api.get_match_data(
            **kwargs
        )
        json_data = {
            "games": games
        }
        data = read_json(
            json_file_itself=json_data,
        )
        self.pima = data
        return self._construct_columns()

    def load_data_from_url(self, url: str, **kwargs):
        result = requests.get(
            url=url,
            **kwargs
        )
        json_data = result.json()
        data = read_json(
            json_file_itself=json_data,
        )
        self.pima = data
        return self._construct_columns()

    def data(
            self,
            train_data: bool = False,
            target_data: bool = False
    ):
        if train_data:
            if self.X is None:
                self._construct_X()
            data_frame = self.X
        elif target_data:
            if self.y is None:
                self._construct_y()
            data_frame = self.y
        else:
            data_frame = self.pima
        data_frame_json = df_to_dict(
            data_frame=data_frame
        )
        data = {
            "data": data_frame_json,
            "included_columns": self.included_columns,
            "excluded_columns": self.excluded_columns,
            "target_columns": self.target_columns
        }
        return data

    def setup(self, setup_data: dict):
        """
        Setup function will provide the necessary information about the
        algorithm, in other word a configuration variable. For the main
        structure of setup data, one may check alg.py script. It also
        provides different options for loading data.

        :param dict setup_data:
        :return:
        """
        # Left as empty for abstract/inheritance definition.
        self._load_data(setup_data=setup_data)
        return self

    def train(self):
        # Left as empty for abstract/inheritance definition.
        return self

    def predict(self):
        # Left as empty for abstract/inheritance definition.
        return self


if __name__ == "__main__":
    pass
