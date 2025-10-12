"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-09-06
"""
import random
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from src.danalyticAPI.algorithms.algorithm import Algorithm
from src.danalyticAPI.algorithms import alg
from src.utils.Utils import Logger, df_to_dict


config_params = {
    alg.test_size: "test_size",
    alg.random_state: "random_state",
    alg.criterion: "criterion"
}


# Define logger.
logger = Logger(__name__).get_logistic_regression_logger()


class LogisticRegressionAlgorithm(Algorithm):
    def __init__(self):
        """

        Parameters:
            :param pd.Dataframe self.X_train:
            :param pd.Dataframe self.X_test:
            :param pd.Dataframe self.y_train:
            :param pd.Dataframe self.y_test:
            :param pd.Dataframe self.y_predict:
            :param int self.random_state:
            :param float self.test_size:
            :param LogisticRegression self.regression:

        """
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

    def _adjust_y(self):
        total_targets = len(self.target_columns)
        if total_targets > 1:
            objective_target = random.choice(self.target_columns)
            logger.warning(
                f"The Logistic Regression algorithms require only"
                f"one target feature, however provided number of target "
                f"features are {total_targets}. Thus, only one of them "
                f"will be chosen: {objective_target}"
            )
            self.target_columns = [objective_target]

    def _convert_y(self):
        if len(self.target_columns) > 0:
            objective_target = self.target_columns[0]
            try:
                self.y = self.y[objective_target]
            except KeyError:
                logger.error(
                    f"Target data frame does not have the column: {objective_target}"
                )

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
        # Make sure there is only one target.
        self._adjust_y()
        # Define data y from pima.
        self._construct_y()
        # Make sure target y is in Series class.
        self._convert_y()
        # Define config.
        if alg.algorithm in setup_data:
            self._config(config_data=setup_data[alg.algorithm])
        else:
            logger.warning(
                f"Setup data has a missing crucial key: {alg.algorithm}"
            )
        # Split dataset into training set and test set.
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
        # Create Logistic Regression classifier object
        self.regression = LogisticRegression(
            solver="liblinear", C=10.0, random_state=0
        )
        try:
            self.regression.fit(self.X_train, self.y_train)
        except Exception as err:
            logger.error(
                f"Logistic Regression can not be trained: {err}"
            )
        else:
            logger.info("Logistic Regression has been trained")
        return self

    def predict(self):
        if self.regression is None:
            self.train()
        # Predict the response for test dataset
        try:
            self.y_predict = self.regression.predict(self.X_test)
        except Exception as err:
            logger.error(
                f"Logistic Regression can not being executed: {err}"
            )
        else:
            logger.info("Logistic Regression is being executed")
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
        result_data = prediction.join(
            other=self.y_test,
            lsuffix=" (true)",
            rsuffix=" (predict)"
        )
        return df_to_dict(result_data)

    def confusion(self):
        if self.y_predict is None:
            self.predict()
        cm = confusion_matrix(self.y_test, self.y_predict)
        cm_df = pd.DataFrame(
            data=cm,
            index=self.regression.classes_,
            columns=self.regression.classes_
        )
        return df_to_dict(cm_df)
