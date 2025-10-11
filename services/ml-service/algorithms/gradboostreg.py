"""
@author: Cem Akpolat
@created by cemakpolat at 2020-09-06
"""
import os
import pandas as pd
from sklearn.model_selection import train_test_split  # Import train_test_split function
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.datasets import load_boston
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
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

file_name = os.path.normcase(os.path.join(script_dir, "../gradboostReg/dtfirst.csv"))
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

# with new parameters
gbr = GradientBoostingRegressor(
    n_estimators=600, max_depth=5, learning_rate=0.01, min_samples_split=3
)
# with default parameters
gbr = GradientBoostingRegressor()

print(gbr)
GradientBoostingRegressor(
    alpha=0.9,
    criterion="friedman_mse",
    init=None,
    learning_rate=0.1,
    loss="ls",
    max_depth=3,
    max_features=None,
    max_leaf_nodes=None,
    min_impurity_decrease=0.0,
    min_impurity_split=None,
    min_samples_leaf=1,
    min_samples_split=2,
    min_weight_fraction_leaf=0.0,
    n_estimators=100,
    presort="auto",
    random_state=None,
    subsample=1.0,
    verbose=0,
    warm_start=False,
)

gbr.fit(X_train, y_train)

ypred = gbr.predict(X_test)
mse = mean_squared_error(y_test, ypred)


print("MSE: %.2f" % mse)

x_ax = range(len(y_test))
plt.scatter(x_ax, y_test, s=5, color="blue", label="original")
plt.plot(x_ax, ypred, lw=0.8, color="red", label="predicted")
plt.legend()
plt.show()
