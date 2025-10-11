"""
@author: Huseyin Eren
@created by huseyin_eren at 2022-08-20
"""
import math
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from src.danalyticAPI.algorithms.algorithm import Algorithm
from sklearn.metrics.cluster import silhouette_score
from src.danalyticAPI.algorithms import alg
from src.utils.Utils import Logger, df_to_dict, df_to_list


# Define logger.
logger = Logger(__name__).get_cluster_logger()


config_params = {
    alg.random_state: "random_state",
    alg.n_cluster: "n_cluster"
}


class Cluster(Algorithm):
    """

        Parameters:
        :param KMeans self.kmeans:
        :param int self.random_state:
        :param int self.n_cluster:

    """
    def __init__(self):
        super().__init__()
        self.random_state = None
        self.n_cluster = None
        self.kmeans = None
        self.train_flag = False
        self.repetition = 5

    def _config(self, config_data: dict):
        if alg.config in config_data:
            config = config_data[alg.config]
            for key, value in config_params.items():
                if key in config:
                    setattr(self, value, config[key])
        return self

    def _new_cluster(self):
        # Define new Cluster object.
        cluster = Cluster()
        cluster.n_cluster = self.n_cluster
        cluster.random_state = self.random_state
        return cluster

    def setup(self, setup_data: dict):
        # General data loading.
        self._load_data(setup_data=setup_data)
        # Fill the None values in data.
        self.pima.fillna(
            value=0,
            inplace=True
        )
        # Define data X from pima.
        self._construct_X()
        # Normalize data X to apply clustering.
        self.X = pd.DataFrame(
            data=MinMaxScaler().fit_transform(
                X=self.X
            ),
            index=self.X.index,
            columns=self.X.columns
        )
        # Define config.
        if alg.algorithm in setup_data:
            self._config(config_data=setup_data[alg.algorithm])
        else:
            logger.warning(
                f"Setup data has a missing crucial key: {alg.algorithm}"
            )

    def train(self):
        self.kmeans = KMeans(
            n_clusters=self.n_cluster,
            random_state=self.random_state
        )
        try:
            self.kmeans.fit_predict(
                X=self.X
            )
        except Exception as err:
            logger.error(
                f"While using KMeans algorithm, "
                f"following error occurred: {err}"
            )
        else:
            self.train_flag = True
        return self

    def predict(self):
        if self.kmeans is None:
            self.train()

        if self.train_flag:
            labels = pd.DataFrame(
                data=self.kmeans.labels_,
                index=self.X.index,
                columns=["label"]
            )
            centers = pd.DataFrame(
                data=self.kmeans.cluster_centers_.tolist(),
                index=range(self.n_cluster),
                columns=self.X.columns
            )
            results = {
                "labels": df_to_dict(labels),
                "centers": df_to_dict(centers),
                "inertia": self.kmeans.inertia_
            }
            return results

    def result(self):
        if self.kmeans is None:
            self.train()

        if self.train_flag:
            labels = pd.DataFrame(
                data=self.kmeans.labels_,
                index=self.X.index,
                columns=["label"]
            )
            result_df = pd.concat(
                objs=[self.pima, labels],
                axis="columns"
            )
            result_json = df_to_dict(result_df)
            return result_json

    def visualise(self):
        if len(self.X) >= 2:
            # Apply PCA.
            pca_data = PCA(
                n_components=2,
                random_state=self.random_state
            ).fit_transform(
                X=self.X
            )
            visualisation_data = pd.DataFrame(
                data=pca_data,
                columns=["x", "y"]
            )
            # Define new Cluster object.
            cluster = self._new_cluster()
            cluster.X = visualisation_data
            # Obtain prediction.
            prediction = cluster.predict()
            labels = prediction.pop("labels")
            labels_df = pd.DataFrame(
                data=labels
            ).transpose()
            visualisation_data = pd.concat(
                objs=[visualisation_data, labels_df],
                axis="columns"
            )
            prediction["visualisation"] = df_to_dict(
                visualisation_data
            )
            return prediction
        else:
            logger.error(
                f"Visualisation of the Cluster will be possible "
                f"in the case of more than 2 features, but given "
                f"number of features is {len(self.X)}."
            )

    def elbow(self):
        # Define new Cluster object.
        cluster = self._new_cluster()
        cluster.X = self.X
        # Define range of n_clusters.
        max_n = int(self.n_cluster * math.sqrt(5))
        transform = 2
        interval = range(transform, max_n + transform)
        elbow = [None]*max_n
        for index in range(max_n):
            n_cluster = interval[index]
            cluster.n_cluster = n_cluster
            cluster.train()
            sse = cluster.kmeans.inertia_
            elbow[index] = sse
        sse_data = pd.DataFrame(
            data=[interval, elbow],
            index=["n_cluster", "error"]
        ).transpose()
        sse_data_json = df_to_list(sse_data)
        return sse_data_json

    def silhouette(self):
        repetitions = ["R{}".format(i) for i in range(1, self.repetition + 1)]
        # Define range of n_clusters.
        max_n = int(self.n_cluster * math.sqrt(5))
        transform = 2
        interval = range(transform, max_n + transform)
        ssl = pd.DataFrame(
            index=interval,
            columns=repetitions
        )
        for n_cluster in ssl.index:
            for repeat in ssl.columns:
                algorithm = self._new_cluster()
                algorithm.X = self.X
                algorithm.train()
                ssl.at[n_cluster, repeat] = silhouette_score(
                    algorithm.X,
                    algorithm.kmeans.labels_
                )
        ssl["n_cluster"] = interval
        ssl["silhouette"] = ssl[repetitions].mean(axis=1)
        ssl = ssl[["n_cluster", "silhouette"]]
        ssl_json = df_to_list(ssl)
        return ssl_json
