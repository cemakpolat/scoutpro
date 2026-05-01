"""
@author: Cem Akpolat
@created by cemakpolat at 2020-09-06
"""
import os
import pandas as pd
from sklearn.model_selection import train_test_split  # Import train_test_split function
import matplotlib.pyplot as plt
from sklearn import (
    metrics,
)  # Import scikit-learn metrics module for accuracy calculation


from sklearn.linear_model import LinearRegression

# Load Data
col_names = [
    "Besiktas",
    "Total passes attempted",
    "Total shots (including blocks)",
    "outcome",
]
col_names = [
    "Besiktas",
    "Total passes attempted",
    "Total shots (including blocks)",
    "outcome",
]

# load dataset
script_dir = os.getcwd()
read_file = pd.read_excel("dtfirst.xlsx")
# Write the dataframe object
# into csv file
read_file.to_csv("dtfirst.csv", index=None, header=True)

file_name = os.path.normcase(os.path.join(script_dir, "../svm/dtfirst.csv"))
print(file_name)
pima = pd.read_csv(file_name, header=None, names=col_names)
pima = pima.drop(columns=["Besiktas"])
pima = pima.iloc[
    1:
]  # delete the first raw of the dataframe,this should be indeed handled normally by the train_test_split itself >/
pima.head()


# split dataset in features and target variable
feature_cols = ["Total passes attempted", "Total shots (including blocks)"]
X = pima[feature_cols]  # Features
y = pima["outcome"]  # Target variable, our case this will be the goal

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

from sklearn.svm import SVC

svclassifier = SVC(kernel="sigmoid", C=1.0)
svclassifier.fit(X_train, y_train)
y_pred = svclassifier.predict(X_test)
print("Accuracy:", metrics.accuracy_score(y_test, y_pred))

print(y_pred)
from sklearn.metrics import classification_report, confusion_matrix

print(confusion_matrix(y_test, y_pred))
print(classification_report(y_test, y_pred))

x_ax = range(len(y_test))
plt.scatter(x_ax, y_test, s=5, color="blue", label="original")
plt.plot(x_ax, y_pred, lw=0.8, color="red", label="predicted")
plt.legend()
plt.show()
