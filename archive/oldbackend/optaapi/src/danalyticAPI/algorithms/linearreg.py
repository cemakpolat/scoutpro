"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-09-06
"""
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.linear_model import LinearRegression
from src.danalyticAPI.algorithms.algorithm import Algorithm
from src.danalyticAPI.algorithms import alg
from src.utils.Utils import Logger, df_to_dict


config_params = {
    alg.test_size: "test_size",
    alg.random_state: "random_state",
    alg.criterion: "criterion"
}


# Define logger.
logger = Logger(__name__).get_linear_regression_logger()


class LinearRegressionAlgorithm(Algorithm):
    """

    Parameters:
        :param KMeans self.kmeans:
        :param pd.Dataframe self.X_train:
        :param pd.Dataframe self.X_test:
        :param pd.Dataframe self.y_train:
        :param pd.Dataframe self.y_test:
        :param pd.Dataframe self.y_predict:
        :param int self.random_state:
        :param float self.test_size:
        :param LinearRegression self.regression:

    """
    def __init__(self):
        super().__init__()
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.random_state = None
        self.test_size = 0.2
        self.criterion = None
        self.y_predict = None
        self.regression = None

    def _config(self, config_data: dict):
        if alg.config in config_data:
            config = config_data[alg.config]
            for key, value in config_params.items():
                if key in config:
                    setattr(self, value, config[key])
        return self

    def setup(self, setup_data: dict):
        # General data loading.
        try:
            self._load_data(setup_data=setup_data)
        except Exception as err:
            logger.error(
                "While pre-loading data, "
                f"following error occurred: {err}"
            )
        # Construct self.X and self.y
        self._construct_X()
        self._construct_y()
        # Define config.
        if alg.algorithm in setup_data:
            self._config(config_data=setup_data[alg.algorithm])
        else:
            logger.warning(
                f"Setup data has a missing crucial key: {alg.algorithm}"
            )
        # Split dataset into training set and test set
        try:
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                self.X, self.y, test_size=self.test_size, random_state=self.random_state
            )
        except Exception as err:
            logger.error(
                "While using train test split function, "
                f"following error occurred: {err}"
            )
        return self

    def train(self):
        # Building Regression Model
        # Create Linear Regression classifier object
        self.regression = LinearRegression()
        try:
            self.regression.fit(self.X_train, self.y_train)
        except Exception as err:
            logger.error(
                f"Linear Regression can not be trained: {err}"
            )
        else:
            logger.info("Linear Regression has been trained")
        return self

    def predict(self):
        if self.regression is None:
            self.train()
        # Predict the response for test dataset
        try:
            self.y_predict = self.regression.predict(self.X_test)
        except Exception as err:
            logger.error(
                f"Linear Regression can not being executed: {err}"
            )
        else:
            logger.info("Linear Regression is being executed")
        y_predict = pd.DataFrame(
            data=self.y_predict,
            index=self.X_test.index,
            columns=self.target_columns
        )
        # Evaluating the applied model using the test data
        result = {
            "y_predict": df_to_dict(y_predict),
            "score": self.regression.score(self.X_test, self.y_test)
        }
        return result

    def result(self):
        self.predict()
        prediction = pd.DataFrame(
            data=self.y_predict,
            index=self.X_test.index,
            columns=self.target_columns
        )
        result_data = self.y_test.join(
            other=prediction,
            lsuffix=" (true)",
            rsuffix=" (predict)"
        )
        return df_to_dict(result_data)
