"""
@author: Cem Akpolat
@created by cemakpolat at 2020-08-28
"""
import os

# Load libraries
import pandas as pd
from sklearn.tree import DecisionTreeClassifier  # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split  # Import train_test_split function
from sklearn import (
    metrics,
)  # Import scikit-learn metrics module for accuracy calculation
from sklearn.metrics import confusion_matrix
import seaborn as sn
from matplotlib import pyplot as plt
from sklearn.tree import export_graphviz
from six import StringIO
from IPython.display import Image
import pydotplus
from pathlib import Path

## TODO:
"""
Assumption:
- User provides the data to the system via a url path
- User provides all col names, feature_cols, and target col
- User provides the test size
- User provides the algorithm parameters
- User trains the algorithm
- Users loads the data to be predicted 
- User receives the data from the system

"""
data_folder = Path("../repo/")


class DecisionTree:
    def __init__(self):
        self.pima = None
        self.col_names = None
        self.feature_cols = None
        self.label = None
        self.file_uri = None
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.test_size = 0.2
        self.y_pred = None
        self.dtree = None
        self.random_state = 1
        self.criterion = "entropy"

    def load_data_from_file(self, filename):
        """
        retrieve data from the given file
        :param filename:
        :return:
        """
        import sys
        print(sys.path)
        # read from the repo file
        self.pima = pd.read_excel(data_folder / filename)
        self.pima = self.pima.drop(
            columns=["gameID"]
        )  # TODO: remove the game Id or find a pattern for this
        df = pd.DataFrame(self.pima)
        self.all_features = df.columns.values

        # get all headers

    def load_data_from_db(self, tables):
        """
        retrieve data from the given table/collection names
        :param tables:
        :return:
        """
        print(tables)

    def load_data_from_url(self, file_uri):
        """
        retrieve data from a given url, the format of the data is not specified.

        :param file_uri:
        :return:
        """

        # Load Data

        script_dir = os.getcwd()
        file_name = os.path.normcase(os.path.join(script_dir, file_uri))
        pima = pd.read_excel(file_name, header=None, names=self.col_names)

        pima = pima.iloc[
            1:
        ]  # delete the first row of the dataframe,this should be indeed handled normally by the train_test_split itself >/
        pima.head()

    def setup(self, setupData):
        # load the file
        config = setupData["alg_configs"]
        self.feature_cols = setupData["included_features"]
        not_selected_features = setupData["excluded_features"]
        self.load_data_from_file(config["file_name"])

        # split dataset in features and target variable
        self.X = self.pima[self.feature_cols]  # Features
        # Target variable, our case this will be the goal
        self.y = self.pima[setupData["target_feature"]]

        if config["config"]["test_size"] is not None:
            self.test_size = config["config"]["test_size"]
        if config["config"]["random_state"] is not None:
            self.random_state = config["config"]["random_state"]
        if config["config"]["criterion"] is not None:
            self.criterion = config["config"]["criterion"]

        # Split dataset into training set and test set
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=self.test_size, random_state=self.random_state
        )

    def train(self):
        # # Building Decision Tree Model
        # Create Decision Tree classifer object

        self.dtree = DecisionTreeClassifier(criterion="entropy", max_depth=4)

        # Train Decision Tree Classifer
        self.dtree = self.dtree.fit(self.X_train, self.y_train)

        # Predict the response for test dataset
        self.y_pred = self.dtree.predict(self.X_test)

        # Evaluating the applied model using the test data
        ## Model Accuracy, how often is the classifier correct?
        print("Accuracy:", metrics.accuracy_score(self.y_test, self.y_pred))

    def predict(self):
        print("Decision Tree is being executed")
        self.dtree = DecisionTreeClassifier(criterion="entropy", max_depth=4)

        # Train Decision Tree Classifer
        self.dtree = self.dtree.fit(self.X_train, self.y_train)

        # Predict the response for test dataset
        self.y_pred = self.dtree.predict(self.X_test)

        # Evaluating the applied model using the test data
        ## Model Accuracy, how often is the classifier correct?
        print("Accuracy:", metrics.accuracy_score(self.y_test, self.y_pred))

    def displayConfisionMatrix(self):
        ## confusion matrix
        if self.y_pred is not None and self.y_test is not None:
            cfmat = confusion_matrix(self.y_test, self.y_pred)
            print(cfmat)
            plt.figure(figsize=(10, 8))
            sn.heatmap(cfmat, annot=True, fmt="d")
            plt.show()

    def plotDecisionTreeGraph(self):

        dot_data = StringIO()
        export_graphviz(
            self.dtree,
            out_file=dot_data,
            filled=True,
            rounded=True,
            special_characters=True,
            feature_names=self.feature_cols,
            class_names=["0", "1"],
        )
        graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
        graph.write_png("dtree.png")
        Image(graph.create_png())

    def getResultImageName(self):
        return "dtree.png"
