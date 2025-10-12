"""
@author: Cem Akpolat, Hüseyin Eren
@created by cemakpolat at 2020-10-02

Purpose:
    alg.py script file contains key variables for the
    ML algorithms provided in the project.

"""

###########################
# Training and Prediction #
###########################
training = "training"
prediction = "prediction"


##############
# Algorithms #
##############
Algorithm = "algorithm"
Cluster = "cluster"
Svm = "svm"
DecisionTree = "decision-tree"
LinearRegression = "linear-regression"
LogisticRegression = "logistic-regression"
FeatureSelection = "feature-selection"


#######################
# Algorithm Functions #
#######################
competition_id = "competitionID"
season_id = "seasonID"
load_file_excel = "load_data_from_file"
load_file_csv = ""
load_file_json = ""
load_db = ""
load_url = ""
setup = "setup"
train = "train"
predict = "predict"


########################
# Setup Data Variables #
########################

# ---ALGORITHM---
# placement -> setup_data[algorithm]
algorithm = "algorithm"

# placement -> setup_data[algorithm][name]
name = "name"

# placement -> setup_data[algorithm][function]
function = "function"

# placement -> setup_data[algorithm][function_input]
function_input = "input"

# placement -> setup_data[config]
config = "config"

# placement -> setup_data[config][test_size]
test_size = "test_size"

# placement -> setup_data[config][random_state]
random_state = "random_state"

# placement -> setup_data[config][n_cluster]
n_cluster = "n_cluster"

# placement -> setup_data[config][criterion]
criterion = "criterion"

# placement -> setup_data[config][threshold]
threshold = "threshold"

# placement -> setup_data[config][normalise]
normalise = "normalise"

# ---DATA---
# placement -> setup_data[data]
data = "data"

# placement -> setup_data[data][query]
query = "query"

# placement -> setup_data[data][query][game_ids]
games = "game_ids"

# placement -> setup_data[data][query][team_ids]
teams = "team_ids"

# placement -> setup_data[data][query][player_ids]
players = "player_ids"

# placement -> setup_data[data][query][time_interval]
time_interval = "time_interval"

# placement -> setup_data[data][query][events]
events = "event_names"

# placement -> setup_data[data][file]
file = "file"

# placement -> setup_data[data][file][file_name]
file_name = "file_name"

# placement -> setup_data[data][file][path]
path = "path"

# placement -> setup_data[data][file][sheet_name]
sheet_name = "sheet_name"

# placement -> setup_data[data][url]
url = "url"

# ---FEATURES---
# placement -> setup_data[features]
features = "features"

# placement -> setup_data[features][columns]
columns = "columns"

# placement -> setup_data[features][included]
included = "included"

# placement -> setup_data[features][excluded]
excluded = "excluded"

# placement -> setup_data[features][target]
target = "target"
