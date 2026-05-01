"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-10-02
"""
from danalyticAPI.algorithms import alg as alg
from danalyticAPI.algorithms.algorithm import Algorithm
from danalyticAPI.algorithms.dtree import DecisionTree
from danalyticAPI.algorithms.cluster import Cluster
from danalyticAPI.algorithms.linearreg import LinearRegressionAlgorithm
from danalyticAPI.algorithms.logisticreg import LogisticRegressionAlgorithm
from danalyticAPI.algorithms.feature import FeatureSelection
from src.utils.Utils import Logger, get_func_input


# Define logger.
logger = Logger(__name__).get_analytic_engine_logger()


# Define dictionary between handlers and algorithms.
functions = {
    alg.Algorithm: Algorithm(),
    alg.DecisionTree: DecisionTree(),
    alg.LogisticRegression: LogisticRegressionAlgorithm(),
    alg.LinearRegression: LinearRegressionAlgorithm(),
    alg.Cluster: Cluster(),
    alg.FeatureSelection: FeatureSelection(),
    alg.Svm: None
}

default_algorithm = alg.Algorithm
default_purpose = alg.data


class AnalyticEngine:
    def __init__(
            self,
            setup_data: dict = None
    ):
        self.data = setup_data
        self.algorithm = functions[default_algorithm]
        self.purpose = default_purpose
        self.algorithm_function = getattr(
            self.algorithm, self.purpose
        )
        self.input = {}
        logger.info("Analytic engine is started.")

    def _get_algorithm(self):
        try:
            algorithm = self.data[alg.algorithm][alg.name]
        except KeyError as error:
            logger.warning(
                "While reading setup data, the key for the name of "
                f"the algorithm could not be found: {error}"
            )
        else:
            if algorithm not in functions:
                logger.error(
                    f"Requested algorithm could not be found: {name}."
                )
            else:
                self.algorithm = functions[algorithm]
        return self

    def _get_purpose(self):
        try:
            purpose = self.data[alg.algorithm][alg.function]
        except KeyError as error:
            logger.warning(
                "While reading setup data, the key for the function "
                f"of the algorithm could not be found: {error}"
            )
        else:
            if not hasattr(self.algorithm, purpose):
                logger.error(
                    f"Provided algorithm {self.algorithm} does not "
                    f"have the requested method {purpose}."
                )
            else:
                self.purpose = purpose
        return self

    def _get_input(self):
        try:
            candidate_input = self.data[alg.algorithm][alg.function_input]
        except KeyError:
            logger.warning(
                f"Requested function will not have any input: {self.purpose}"
            )
        else:
            input_keys_candidate = set(candidate_input.keys())
            input_keys = set(get_func_input(self.algorithm_function))
            if not input_keys_candidate.issubset(input_keys):
                logger.error(
                    f"Provided inputs keys do not match with function: "
                    f"Function Inputs: {input_keys}, "
                    f"Provided Inputs: {input_keys_candidate}."
                )
            else:
                self.input = candidate_input
        return self

    def _setup_algorithm(self):
        self.algorithm.setup(self.data)
        return self

    def _run_algorithm(self):
        self._setup_algorithm()._get_input()
        try:
            algorithm_output =  self.algorithm_function(**self.input)
        except Exception as err:
            logger.error(
                f"Provided function could not run: {err}"
            )
        else:
            return algorithm_output

    def handle(self):
        self._get_algorithm()._get_purpose()
        self.algorithm_function = getattr(self.algorithm, self.purpose)
        return self._run_algorithm()