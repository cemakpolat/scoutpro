"""
@author: Doruk Sahinel, Hüseyin Eren
@created by doruksahinel at 2022-03-25

This python file is used to read files inside the input folder. An example is provided with an Excel file.
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from src.restapi.restapi.resources import helper as hlp
from src.utils.Utils import get_src_path, Logger
from src.events.Events import EventTypes, event_names_statistics
from src.feedAPI import PlayerAPI
from src.feedAPI import TeamAPI
from src.feedAPI import GameAPI


data_folder = get_src_path("\\src\\input\\")


logger = Logger(__name__).get_reader_logger()


def player_api(competition_id, season_id):
    return PlayerAPI.PlayerAPI(competitionID=competition_id, seasonID=season_id)


def team_api(competition_id, season_id):
    return TeamAPI.TeamAPI(competitionID=competition_id, seasonID=season_id)


def game_api(competition_id, season_id):
    return GameAPI.GameAPI(competitionID=competition_id, seasonID=season_id)


def csv_to_df(file_name: str, path=None, param_names: list = None):
    if path is None:
        path = get_src_path("/src/input/")
    csv_file = pd.read_csv(filepath_or_buffer=path + file_name, names=param_names)
    return csv_file


def excel_to_df(file_name: str, sheet_name=None, path=None, param_names: list = None):
    if path is None:
        path = get_src_path("/src/input/")
    df = pd.read_excel(io=path + file_name, sheet_name=sheet_name, names=param_names)
    return df


def json_to_df_statistics(
        file_name: str = None,
        sheet_name: str = None,
        path: str = None,
        path_output: str = None,
        json_file_itself: dict = None,
        event_names: list = None,
        param_names: list = None,
        reset_df_index: bool or dict = False
) -> pd.DataFrame:
    if path is None:
        path = get_src_path("/src/input/")
        path_output = get_src_path("/src/output/")

    if file_name is None and json_file_itself is not None:
        data = json_file_itself

    elif file_name is not None and json_file_itself is None:
        with open(path + file_name, "r", encoding="utf8") as file:
            data = json.load(file)

    else:
        print("Both file_name and json_file_itself can not be None or not None at the same time!")
        return pd.DataFrame()

    existing_keys = list()

    for key in data.keys():
        temp_key = str(key).strip().lower()
        if temp_key in ["players", "teams", "games"]:
            existing_keys.append(key)
        else:
            continue

    event_names = event_names or []

    if len(event_names) == 0:
        event_names = event_names_statistics

    all_possible_object_names = [
        "name",
        "playerName",
        "teamName"
    ]

    all_data_frames = list()

    for key in existing_keys:
        temp_data = data[key]
        if not isinstance(temp_data, list):
            continue
        temp_json_file = dict()

        for document in temp_data:

            if "events" in document:
                document = document["events"]

            if not isinstance(document, list):
                try:
                    document = [document]
                except TypeError:
                    continue

            for statistics_object in document:

                if isinstance(statistics_object, list):
                    try:
                        if len(statistics_object) > 1:
                            print("CAUTION: Reading operation may not read all the files, try to reduce dimension.")
                        statistics_object = statistics_object[0]

                    except IndexError:
                        continue

                if not isinstance(statistics_object, dict):
                    continue

                name_of_object = None
                stats_values_of_object = dict()

                for name in all_possible_object_names:
                    if name in statistics_object:
                        if name_of_object is None and name_of_object not in temp_json_file:
                            name_of_object = statistics_object[name]
                        elif name_of_object is None and name_of_object in temp_json_file:
                            name_of_object += " (" + str(statistics_object[name]) + ")"
                        else:
                            continue

                for document_key in statistics_object.keys():
                    if str(document_key).strip() in event_names:
                        if isinstance(statistics_object[document_key], list):
                            try:
                                statistics_object[document_key] = statistics_object[document_key][0]
                            except IndexError:
                                continue
                        if isinstance(statistics_object[document_key], dict):
                            if hasattr(param_names, '__getitem__'):
                                for item in param_names.copy():
                                    if item in statistics_object[document_key]:
                                        stats_values_of_object[item] = statistics_object[document_key][item]
                                        try:
                                            param_names.remove(item)
                                        except AttributeError:
                                            continue
                            else:
                                stats_values_of_object = {**stats_values_of_object, **statistics_object[document_key]}

                if name_of_object is None or stats_values_of_object == dict():
                    continue

                else:
                    if name_of_object in temp_json_file:
                        for attr in stats_values_of_object.keys():
                            if attr in temp_json_file[name_of_object]:
                                if "rate" not in str(attr) and "ercentage" not in str(attr):
                                    temp_json_file[name_of_object][attr] += stats_values_of_object[attr]
                                else:
                                    temp_json_file[name_of_object][attr] = (temp_json_file[name_of_object][attr] +
                                                                            stats_values_of_object[attr]) / 2

                            else:
                                temp_json_file[name_of_object][attr] = stats_values_of_object[attr]
                    else:
                        temp_json_file[name_of_object] = stats_values_of_object

        temp_data_frame = pd.DataFrame(temp_json_file).transpose()
        columns = temp_data_frame.columns
        temp_data_frame[columns] = temp_data_frame[columns].apply(pd.to_numeric)
        all_data_frames.append(temp_data_frame)

        if reset_df_index:
            try:
                mapper = reset_df_index["mapper"]
            except TypeError or KeyError:
                mapper = {"index": "player"}
            temp_data_frame.reset_index(inplace=True)
            temp_data_frame.rename(mapper=mapper, axis=1, inplace=True)

    if len(all_data_frames) == 0:
        return pd.DataFrame()

    elif len(all_data_frames) == 1:
        all_data_frames = all_data_frames[0]

    if sheet_name:
        if isinstance(all_data_frames, list):
            for i in range(len(all_data_frames)):
                temp_sheet_name = str(existing_keys[i]) + " " + sheet_name
                all_data_frames[i].to_excel(path_output + temp_sheet_name)
        else:
            all_data_frames.to_excel(path_output + sheet_name)

    return all_data_frames


def json_to_df_statistics_games(
        file_name: str = None,
        path: str = None,
        json_file_itself: dict = None,
):
    path = path or data_folder

    if isinstance(json_file_itself, dict):
        data = json_file_itself
    else:
        with open(path + file_name, "r", encoding="utf8") as file:
            data = json.load(file)

    if "games" in data:
        data = data["games"]

    for index, game in enumerate(data):
        try:
            game_info = game["game"][0]
            events = game["events"]
            game_id = game_info["ID"]
            home_team = game_info["homeTeamName"]
            away_team = game_info["awayTeamName"]
            home_score = game_info["homeScore"]
            away_score = game_info["awayScore"]
            away_outcome = 0
            home_outcome = 0
            if away_score > home_score:
                away_outcome += 1
            elif home_score > away_score:
                home_outcome += 1
            game_stats = {
                "gameId": game_id
            }

            single_team_or_player_flag = False
            if len(events) == 1:
                single_team_or_player_flag = True

            for team in events:
                away_home = ""
                if single_team_or_player_flag:
                    if "teamName" in team:
                        game_stats["Team Name"] = team["teamName"]
                        if away_team == team["teamName"]:
                            game_stats["Game Outcome"] = away_outcome
                        elif home_team == team["teamName"]:
                            game_stats["Game Outcome"] = home_outcome
                        else:
                            continue

                    if "playerName" in team:
                        game_stats["Player Name"] = team["playerName"]
                        if "totalMin" in team:
                            game_stats["Total Play Time"] = team["totalMin"]

                else:
                    game_teams_info = {
                        "Home Score": home_score,
                        "Away Score": away_score,
                        "Home Outcome": home_outcome,
                        "Away Outcome": away_outcome
                    }
                    game_stats = {**game_stats, **game_teams_info}
                    if team["teamName"] == away_team:
                        away_home = "Away "
                    elif team["teamName"] == home_team:
                        away_home = "Home "
                    else:
                        logger.error(
                            f"Team name {team['teamName']} does not "
                            f"belong any of away or home teams: {[away_team, home_team]}"
                        )

                for event_name in event_names_statistics:
                    if event_name in team:
                        for key, value in team[event_name].items():
                            game_stats[away_home + key] = value
            data[index] = game_stats

        except Exception as err:
            logger.error(
                f"While reading game statistics, following error occurred: {err}"
            )
            data[index] = {}
            continue

    data = pd.DataFrame(
        data=data
    )
    return data


def json_to_df_personal(
        file_name=None, sheet_name=None, path_input=None,path_output=None, json_file_itself=None
):
    if path_input is None:
        path_input = get_src_path("/src/input/")
        path_output = get_src_path("/src/output/")

    if file_name is None and json_file_itself is not None:
        data = json_file_itself

    elif file_name is not None and json_file_itself is None:
        with open(path_input + file_name, "r", encoding="utf8") as file:
            data = json.load(file)

    else:
        print("Both file_name and json_file_itself can not be None or not None at the same time!")
        return pd.DataFrame()

    if "players" not in data:
        print("Given json file does not have 'players' field.")
        return pd.DataFrame()

    if not hasattr(data["players"], '__getitem__'):
        print("The object data['players'] must have the '__getitem__' attribute.")
        return pd.DataFrame()

    json_file = dict()
    index = -1

    def _check_value_type_exist(dict_object):
        if not hasattr(dict_object, '__getitem__'):
            return False
        if "type" not in dict_object or "value" not in dict_object:
            return False
        return True

    for player in data["players"]:
        player_info_list = None
        if not _check_value_type_exist(player):
            try:
                player_info_list = list(player.values())[0]
            except IndexError:
                print("CAUTION: Reading operation may not read all the files, try to reduce dimension.")
                continue
        if player_info_list:
            player = player_info_list

        temp_player_info_dict = dict()
        for player_info in player:
            if not _check_value_type_exist(player_info):
                continue
            temp_player_info_dict[player_info["type"]] = player_info["value"]

        if 0 < len(temp_player_info_dict):
            index += 1
            json_file[index] = temp_player_info_dict

    data_frame = pd.DataFrame(json_file).transpose()

    if sheet_name:
        data_frame.to_excel(path_output + sheet_name)

    return data_frame


def json_to_df_events(
        file_name=None, sheet_name=None, path_input=None, path_output=None,
        json_file_itself=None, drop_features=None, convert_ids=False
):
    if path_input is None:
        path_input = get_src_path("/src/input/")
        path_output = get_src_path("/src/output/")

    if file_name is None and json_file_itself is not None:
        data = json_file_itself

    elif file_name is not None and json_file_itself is None:
        with open(path_input + file_name, "r", encoding="utf8") as file:
            data = json.load(file)

    else:
        print("Both file_name and json_file_itself can not be None or not None at the same time!")
        return pd.DataFrame()

    data_frame = pd.DataFrame()

    drop_features_flag = True
    if drop_features is None or drop_features is True:
        drop_features = ["ID", "qEvents", "lastModified", "version"]
    elif isinstance(drop_features_flag, str):
        drop_features = [drop_features]
    else:
        drop_features_flag = False

    if "game" in data:
        if 0 < len(data["game"]):
            if "competitionID" in data["game"][0]:
                competition_id = int(data["game"][0]["competitionID"])
            else:
                print("Given json file does not have proper 'game' field.")
                return data_frame

            if "seasonID" in data["game"][0]:
                season_id = int(data["game"][0]["seasonID"])
            else:
                print("Given json file does not have proper 'game' field.")
                return data_frame
        else:
            print("Given json file does not have proper 'game' field.")
            return data_frame
    else:
        print("Given json file does not have 'game' field.")
        return data_frame

    if "events" not in data:
        print("Given json file does not have 'events' field.")
        return data_frame

    if not hasattr(data["events"], '__getitem__'):
        print("The object data['players'] must have the '__getitem__' attribute.")
        return pd.DataFrame()
    papi = player_api(competition_id=competition_id, season_id=season_id)
    tapi = team_api(competition_id=competition_id, season_id=season_id)
    for event in data["events"]:
        temp_event = event

        if drop_features_flag:
            for column in drop_features:
                del temp_event[column]

        if "typeID" in temp_event:
            temp_event["typeID"] = str(EventTypes[str(temp_event["typeID"])]).strip().lower()
        else:
            continue

        if "teamID" in temp_event:
            if convert_ids:
                temp_event["teamName"] = tapi.get_team_name(team_id=str(temp_event["teamID"]))
        else:
            continue

        if "playerID" in temp_event:
            if convert_ids:
                temp_event["playerName"] = papi.getPlayerName(player_id=str(temp_event["playerID"]))
        else:
            continue

        temp_df = pd.DataFrame(data=temp_event, index=[0])
        data_frame = pd.concat(objs=[data_frame, temp_df], ignore_index=True)

    if sheet_name:
        data_frame.to_excel(path_output + sheet_name)

    return data_frame


if __name__ == "__main__":
    print(
        json_to_df_statistics_games(
            file_name="temp.json"
        )
    )






