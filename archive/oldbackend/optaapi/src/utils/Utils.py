"""
Author: Cem Akpolat

"""

import logging
import os
import sys
import pandas as pd
import numpy as np
from fake_useragent import UserAgent
import xlrd
import json
import jsonpickle
from pymongo import monitoring
import requests
import random


class CommandLogger(monitoring.CommandListener):
    def __init__(self, log: logging.Logger):
        self.logger = log

    def started(self, event):
        self.logger.debug(
            "Command {0.command_name} with request id "
            "{0.request_id} started on server "
            "{0.connection_id}".format(event)
        )

    def succeeded(self, event):
        self.logger.debug(
            "Command {0.command_name} with request id "
            "{0.request_id} on server {0.connection_id} "
            "succeeded in {0.duration_micros} "
            "microseconds".format(event)
        )

    def failed(self, event):
        self.logger.debug(
            "Command {0.command_name} with request id "
            "{0.request_id} on server {0.connection_id} "
            "failed in {0.duration_micros} "
            "microseconds".format(event)
        )


class Logger:
    """
    Logger class provides us to modify logging object
    with more simple syntax and more simple definitions,
    especially for the definitions of paths and log files.

    """
    def __init__(
            self,
            name: str = None,
            file_name: str = None,
            path: str = None,
            extra: dict = None
    ):
        self.name = name or __name__
        self.file_name = file_name or "main.log"
        self.path = path or get_src_path("\\src\\log\\")

        # Main Attributes
        self.logger = None
        self.formatter = None
        self.file_handler = None

        # Formats.
        self.extra = extra or dict()
        self.formats = list()

        # Level Attribute
        self._level = logging.WARNING

        # Define handlers and main attributes
        self._define_handlers()

    def _define_format(self) -> str:
        self.formats = [
            "levelname", "asctime", "name"
        ] + list(self.extra.keys()) + [
            "message"
        ]
        fmt = ""
        for format_str in self.formats:
            fmt += f"%({format_str})s: "
        fmt = fmt.rstrip().rstrip(":")
        return fmt

    def _define_handlers(self):
        # Define main logging object.
        self.logger = logging.getLogger(name=self.name)

        # Define formatter.
        fmt = self._define_format()
        self.formatter = logging.Formatter(fmt)

        # Define file handler.
        self.file_handler = logging.FileHandler(self.path + self.file_name)
        self.file_handler.setFormatter(self.formatter)

        # Configure main logging object with above definitions.
        self.logger.addHandler(self.file_handler)
        self.logger.setLevel(level=self._level)
        self.logger = logging.LoggerAdapter(self.logger, self.extra)
        return self

    def update_logger_attr(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self._define_handlers()

    def get_logger(self) -> logging.Logger:
        return self.logger

    def get_parser_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="parser.log")
        return self.get_logger()

    def get_parsing_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="parsing.log")
        return self.get_logger()

    def get_saver_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="saver.log")
        return self.get_logger()

    def get_feed_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="feed.log")
        return self.get_logger()

    def get_connector_logger(
            self,
            debug: bool = False
    ):
        if debug:
            self._level = logging.DEBUG
        else:
            self._level = logging.INFO
        self.update_logger_attr(file_name="connector.log")
        monitoring.register(CommandLogger(log=self.logger))
        return self.get_logger()

    def get_query_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="query.log")
        return self.get_logger()

    def get_player_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="player.log")
        return self.get_logger()

    def get_team_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="team.log")
        return self.get_logger()

    def get_game_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="game.log")
        return self.get_logger()

    def get_reader_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="reader.log")
        return self.get_logger()

    def get_rest_api_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="rest.log")
        return self.get_logger()

    def get_algorithm_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="algorithm.log")
        return self.get_logger()

    def get_analytic_engine_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="analyticEngine.log")
        return self.get_logger()

    def get_feature_selection_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="feature.log")
        return self.get_logger()

    def get_linear_regression_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="linearRegression.log")
        return self.get_logger()

    def get_logistic_regression_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="linearRegression.log")
        return self.get_logger()

    def get_cluster_logger(self):
        self._level = logging.INFO
        self.update_logger_attr(file_name="cluster.log")
        return self.get_logger()


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def convert_input_into_list(*params):
    converted_params = list()
    for param in params:

        if param is not None:
            if not isinstance(param, list):
                if isinstance(param, dict):
                    param = list(param.keys())
                elif isinstance(param, str) or isinstance(param, int):
                    param = [param]
                else:
                    try:
                        param = list(param)
                    except Exception as err:
                        print(f"CAUTION! Some items could not converted into 'list' type: {param}")
                        print(err)
                        param = list()
        converted_params.append(param)

    return tuple(converted_params)


def convert_input_into_int_list(*params_list):
    converted_params_lists = list()
    for param in params_list:
        if param is not None:
            if isinstance(param, list):
                temp_params_list = list()
                for item in param:
                    try:
                        item = int(item)
                    except Exception as err:
                        print(f"CAUTION! Some items could not converted into 'int' type: {item}")
                        print(err)
                    temp_params_list.append(item)
            else:
                temp_params_list = param
            converted_params_lists.append(temp_params_list)
        else:
            converted_params_lists.append(None)
    return tuple(converted_params_lists)


def convert_input_into_str_list(*params, remove_char=""):
    converted_params = list()
    for param in params:
        temp_param = None
        if param is not None:
            if hasattr(param, "__getitem__"):
                temp_param = list()
                for item in param:
                    try:
                        temp_param.append(str(item).replace(remove_char, ""))
                    except Exception as err:
                        print(f"CAUTION! Some items could not converted into str type: {item}")
                        print(err)
                        temp_param.append(item)
        converted_params.append(temp_param)
    return tuple(converted_params)

# http://www.edwardhk.com/language/c/comparison-of-popular-excel-libraries/
# https://www.dataquest.io/blog/excel-and-pandas/
# https://www.marsja.se/pandas-excel-tutorial-how-to-read-and-write-excel-files/
# https://xlsxwriter.readthedocs.io/working_with_pandas.html
# https://xlsxwriter.readthedocs.io/example_pandas_multiple.html


def writeInExcell():

    print("test")
    # use for writing xlsxWriter

    # Create some Pandas dataframes from some data.
    df1 = pd.DataFrame(
        {
            "New Data coming from OPTA": [10, 20, 30, 20, 15, 30, 45],
            "Cem": [10, 20, 30, 20, 15, 30, 45],
        }
    )
    df2 = pd.DataFrame({"Data": [21, 22, 23, 24]})
    df3 = pd.DataFrame({"Data": [31, 32, 33, 34]})
    df4 = pd.DataFrame({"Data": [41, 42, 43, 44]})

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter("../results/pandas_multiple.xlsx", engine="xlsxwriter")

    # Write each dataframe to a different worksheet.
    df1.to_excel(writer, sheet_name="Aerial")
    df2.to_excel(writer, sheet_name="Sheet2")
    df3.to_excel(writer, sheet_name="Sheet3")

    # Write the dataframe without the header and index.
    df4.to_excel(
        writer, sheet_name="Sheet4", startrow=7, startcol=4, header=False, index=False
    )

    workbook = writer.book
    worksheet = writer.sheets["Aerial"]

    # Add a header format.
    header_format = workbook.add_format(
        {
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#D7E4BC",
            "border": 1,
        }
    )

    # Write the column headers with the defined format.
    for col_num, value in enumerate(df1.columns.values):
        worksheet.write(0, col_num + 1, value, header_format)

    # Apply a conditional format to the cell range.
    worksheet.conditional_format("B2:B8", {"type": "3_color_scale"})

    # Create a chart object.
    chart = workbook.add_chart({"type": "column"})

    # Configure the series of the chart from the dataframe data.
    chart.add_series({"values": "=Aerial!$B$2:$B$8"})

    # Insert the chart into the worksheet.
    worksheet.insert_chart("D2", chart)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


def readExcel():

    book = xlrd.open_workbook("../results/pandas_multiple.xlsx")
    print(book.nsheets)
    print(book.sheet_names())
    sheet = book.sheet_by_index(1)
    cell = sheet.cell(0, 1)  # where row=row number and col=column number
    print(cell.value)  # to print the cell contents


def jsonSerializer(obj):
    """
    Converts the given feed into the serialized json object.

    :param feed:
    :return:
    """
    # print("Encode Object into JSON formatted Data using jsonpickle")
    empJSON = jsonpickle.encode(obj, unpicklable=False)

    print("Writing JSON Encode data into Python String")
    # jsondata = json.dumps(empJSON, indent=4)
    # feedjson = jsonpickle.decode(jsondata)
    return empJSON


def loading_bar(norm, current_index, print_result=False, percentage=100, percentage_notation="%"):
    loading_string = "Loading: "
    result = None
    if isinstance(percentage_notation, str):
        loading_string += str(percentage_notation) + "{}"
    else:
        loading_string += "{}"

    if norm != 0 and current_index >= 0:
        result = int(float(1/norm) * int(current_index) * percentage)

    if print_result:
        print(loading_string.format(str(result)))
    return result



def get_src_path(
        append_src: str = None,
        include_src: bool = False,
        include_sys_path: bool = True,
) -> str:
    """
    The function returns the path of src file in the directory
    without depending on current working directory. It will be
    not applicable if the current working directory is out of the
    project file, as the main algorithm of the function is appending
    parent directory up to obtaining src directory it-self.

    Example usage can be, get_src_path(append_src='/src/input/')

    :param str append_src: Append new directory from src file.
    :param include_src: Include '/src/' in the obtained path string.
    :param bool include_sys_path: Append sys path list with obtained src path.
    :return: Resulting path string.
    """
    current_path = os.getcwd()
    max_iter = len(str(current_path).split("\\"))

    path = None
    iteration = 0
    while path is None and iteration < max_iter:
        candidate_path, candidate_directory = os.path.split(current_path)
        current_path = os.path.abspath(candidate_path)
        if candidate_directory == "src":
            path = current_path
            if include_sys_path:
                sys.path.append(path)
            break
        iteration += 1

    if isinstance(path, str):
        if include_src:
            path = os.path.join(path, "src")
        if append_src:
            path += append_src
        if not os.path.isdir(path):
            os.makedirs(name=path)

    return path


def concat_data_frames(data_frame_list, fill_nan_values=None, drop_non_values=True, reset_df_index=None):
    if not isinstance(data_frame_list, list):
        data_frame_list = [data_frame_list]

    concated_data_frame = pd.concat(data_frame_list)

    if concated_data_frame.isna().sum().sum() > 0:
        if fill_nan_values:
            concated_data_frame.fillna(value=fill_nan_values, inplace=True)
            print("There were nan values in the data frame and they have been replaced with, " + fill_nan_values)
        elif drop_non_values:
            concated_data_frame.dropna(inplace=True)
            print("There were nan values in the data frame and they have been dropped.")
        else:
            print("CAUTION: There are nan values in the merged data frame.")

    if reset_df_index:
        mapper = {"index": "player"}
        if "mapper" in reset_df_index:
            if reset_df_index["mapper"]:
                mapper = reset_df_index["mapper"]
        concated_data_frame.reset_index(inplace=True)
        concated_data_frame.rename(mapper=mapper, axis=1, inplace=True)

    return concated_data_frame


def merge_data_frames_by_assigning_ones_and_zeros(data_frame_list_for_assigning_ones,
                                                  data_frame_list_for_assigning_zeros,
                                                  ones_zeros_column_name="One or Zero"):
    if not isinstance(data_frame_list_for_assigning_ones, list):
        data_frame_list_for_assigning_ones = [data_frame_list_for_assigning_ones]

    if not isinstance(data_frame_list_for_assigning_zeros, list):
        data_frame_list_for_assigning_zeros = [data_frame_list_for_assigning_zeros]

    all_frames = list()

    for data_frame in data_frame_list_for_assigning_ones:
        data_frame[ones_zeros_column_name] = 1
        all_frames.append(data_frame)

    for data_frame in data_frame_list_for_assigning_zeros:
        data_frame[ones_zeros_column_name] = 0
        all_frames.append(data_frame)

    return pd.concat(all_frames)


def get_optimal_user_agent(browser_name=None, max_count=10, test_url='https://www.google.com/'):
    count = 0
    user_agent = None

    def _choose_fake_user_agent(candidate_browser_name):
        candidate_user_agent = UserAgent()
        if isinstance(candidate_browser_name, str):
            candidate_browser_name = candidate_browser_name.strip()
        elif hasattr(candidate_browser_name, "__getitem__"):
            candidate_browser_name = random.choice(candidate_browser_name)
        else:
            return candidate_user_agent.random
        return candidate_user_agent[candidate_browser_name]

    while user_agent is None and count <= max_count:
        temp_user_agent = _choose_fake_user_agent(candidate_browser_name=browser_name)
        temp_status_code = requests.get(test_url, headers={"User-Agent": temp_user_agent}).status_code
        if temp_status_code == 200:
            user_agent = temp_user_agent
            print(f"Fake user agent has been created at the attempt {count}, named as {user_agent}")
        else:
            count += 1

    if user_agent is None:
        print("The user agent could not be chosen, please check the test_url or try to specify name of the browser.")

    return user_agent


def get_correlated_features(df, threshold):
    col_corr = set()  # Set of all the names of correlated columns
    corr_matrix = df.corr()
    for i in range(len(corr_matrix.columns)):
        for j in range(i):
            if abs(corr_matrix.iloc[i, j]) > threshold:  # we are interested in absolute coeff value
                colname = corr_matrix.columns[i]  # getting the name of column
                col_corr.add(colname)
    return col_corr


def get_correlated_groups(df, threshold, print_groups=False):
    corrmat = df.corr()
    corrmat = corrmat.abs().unstack()  # absolute value of corr coef
    corrmat = corrmat.sort_values(ascending=False)
    corrmat = corrmat[corrmat >= threshold]  # threshold is used here
    corrmat = corrmat[corrmat < 1]
    corrmat = pd.DataFrame(corrmat).reset_index()
    corrmat.columns = ['feature1', 'feature2', 'corr']

    grouped_feature_ls = []
    correlated_groups = []

    for feature in corrmat.feature1.unique():

        if feature not in grouped_feature_ls:
            correlated_block = corrmat[corrmat.feature1 == feature]
            grouped_feature_ls = grouped_feature_ls + list(
                correlated_block.feature2.unique()) + [feature]

            # append the block of features to the list
            correlated_groups.append(correlated_block)

    if print_groups:
        print('found {} correlated groups'.format(len(correlated_groups)))
        print('out of {} total features'.format(df.shape[1]))

        for group in correlated_groups:
            print(group, "\n")

    return correlated_groups


def get_rid_of_correlated_groups(data_frame, threshold=0.9, undroppable_columns=list()):

    simplified_data_frame = data_frame

    # Drop the columns with having all same values.
    for column in simplified_data_frame.columns:
        if simplified_data_frame[column].max() == simplified_data_frame[column].min():
            simplified_data_frame.drop(columns=column, inplace=True)

    # Create correlation matrix.
    corr_matrix = simplified_data_frame.corr().abs()

    # Select upper triangle of correlation matrix.
    upper_tri_matrix = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

    # Find index of feature columns with correlation greater than the given threshold.
    to_drop = [column for column in upper_tri_matrix.columns if
               any(upper_tri_matrix[column] > threshold) and column not in undroppable_columns]

    simplified_data_frame.drop(simplified_data_frame[to_drop], axis=1, inplace=True)

    return simplified_data_frame


def convert_id(uid: str):
    if not isinstance(uid, str):
        try:
            uid = str(uid)
        except TypeError:
            print("Object could not converted into string.")
            return uid

    chars = ["p", "t", "g", "o", "man"]
    for char in chars:
        if char in uid:
            uid = uid.replace(char, "")
            break
    uid = int(uid.strip())

    return uid


def feed_dict(feed_name: str):
    feeds = {
        "feed1": 1,
        "feed9": 9,
        "feed24": 24,
        "feed40": 40,
        "feed124": 124,
        "feed130": 130,
        "feed140": 140,
        "feed340": 340
    }

    if feed_name in feeds:
        return feeds[feed_name]
    else:
        return None


def get_doc_name(doc: object) -> str:
    """
    The function takes 'Document' class as input, and returns the document name of the object
    that is stored in the MongoDB. The function could be useful for querying pipelines especially
    for the join operation, because for join operations it is required to use directly the
    document name of object in MongoDB.

    :param doc: Any class that is a subclass of mongoengine.document.Document class will be valid.
    :return: Document name stored in MongoDB
    :rtype: str
    """
    if hasattr(doc, "_meta"):
        if "collection" in doc._meta:
            return doc._meta["collection"]
        else:
            print("Document name could not be found !")
    else:
        print("The class of the input 'doc' object must be MongoEngine Document class or any superclass of it.")
    return str()


def get_func_input(fn):
    args_names = fn.__code__.co_varnames[:fn.__code__.co_argcount]
    return args_names


def numpy_to_json(array: np.array):
    temp_series = pd.Series(
        data=array
    )
    json_data = temp_series.to_json()
    return json_data


def df_to_json(
        data_frame: pd.DataFrame,
        orient: str = "index",
        index: bool = True,
        indent: int = 4,
        **kwargs
):
    df_json = data_frame.to_json(
        orient=orient,
        index=index,
        indent=indent,
        **kwargs
    )
    return df_json


def df_to_dict(
        data_frame: pd.DataFrame
):
    df_dict = data_frame.to_dict(
        orient="index"
    )
    return df_dict


def df_to_list(
        data_frame: pd.DataFrame
):
    df_list = data_frame.to_dict(
        orient="records"
    )
    return df_list


if __name__ == "__main__":
    test_data = [
        {
            "a": 1,
            "b": 2,
            "c": 3,
            "d": 4
        },
        {
            "a": 5,
            "b": 6,
            "c": 7,
            "d": 8
        },
        {
            "a": 9,
            "b": 10,
            "c": 11,
            "d": 12
        },
        {
            "a": 13,
            "b": 14,
            "c": 15,
            "d": 16
        },
        {
            "a": 17,
            "b": 18,
            "c": 19,
            "d": 20
        }
    ]
    test_data_frame = pd.DataFrame(test_data)
    all_orients = [
        "split",
        "records",
        "index",
        "columns",
        "values",
        "table"
    ]
    print(test_data_frame)
    print(df_to_json())
    pass