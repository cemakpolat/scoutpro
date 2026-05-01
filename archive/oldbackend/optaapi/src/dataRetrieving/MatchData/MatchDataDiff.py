import os
from pathlib import Path
import pandas as pd
import numpy as np
from src.restapi.restapi.resources import helper as hlp
from src.utils.Utils import get_src_path, concat_data_frames
from src.feedAPI import TeamAPI
from src.feedAPI import GameAPI
from src.events.Events import EventTypes
from src.danalyticAPI.DataRetrieving.ReadData import json_to_df_statistics, \
    json_to_df_events


class MatchDataDiff:
    def __init__(
            self, game_id, competition_id, season_id, parameter_names, main_path=None, time_interval_measure=5
    ):
        self.game_id = game_id
        if not isinstance(self.game_id, list):
            self.game_id = [self.game_id]
        self.competition_id = int(competition_id)
        self.season_id = int(season_id)
        self.parameter_names = parameter_names
        self.main_path = main_path
        if self.main_path is None:
            self.main_path = get_src_path("/src/output/")
        self.time_interval_measure = int(time_interval_measure)

        self.max_iter_count = 5

    def tapi(self):
        return TeamAPI.TeamAPI(competitionID=self.competition_id, seasonID=self.season_id)

    def gapi(self):
        return GameAPI.GameAPI(competitionID=self.competition_id, seasonID=self.season_id)

    def update_game_id(self, new_game_id):
        self.game_id = new_game_id
        if not isinstance(self.game_id, list):
            self.game_id = [self.game_id]
        return self

    def convert_game_ids(self, game_ids=None):
        if game_ids is None:
            game_ids = self.game_id
        if not isinstance(game_ids, list):
            game_ids = [game_ids]
        return [str("g" + str(entry).replace("g", "").strip()) for entry in game_ids]

    def get_team_game_dict(self, game_ids=None, team_names=None):
        if team_names is None:
            team_names = self.tapi().get_all_team_names()

        if game_ids is not None:
            game_ids = self.convert_game_ids(game_ids=game_ids)

        if not isinstance(team_names, list):
            team_names = [team_names]
        teams_dict = {}

        for team_name in team_names:
            temp_dict = dict()
            temp_team_id = int(self.tapi().get_team_id(team_name=str(team_name)))
            all_game_ids = self.tapi().get_all_team_played_games(temp_team_id)
            if game_ids is not None:
                try:
                    all_game_ids = set(all_game_ids).intersection(set(game_ids))
                except Exception as err:
                    print(err)
                    continue
            temp_dict[temp_team_id] = all_game_ids
            teams_dict[team_name] = temp_dict

        return teams_dict

    def get_match_events_time(self):
        return list(self.gapi().get_match_data(
            game_ids=self.game_id, show_event_time=True, event_times_converter=False)
        )

    def get_match_data_summary(self):
        return list(self.gapi().get_match_data(
            game_ids=self.game_id, parse=False, get_only_games=True)
        )

    def get_home_away_teams(self):
        match_data_summary = self.get_match_data_summary()
        if len(match_data_summary) != 0:
            return {
                "away_team_id": int(
                    match_data_summary[0]["game"][0]["awayTeamID"]
                ),
                "home_team_id": int(
                    match_data_summary[0]["game"][0]["homeTeamID"]
                )
            }
        else:
            return None

    def get_break_times(self):
        event_time = self.get_match_events_time()
        if len(event_time) == 0:
            return None
        result = {
            "First Half End": None,
            "End of the Game": None
        }
        try:
            for key in result:
                for end_time in event_time[0]["events"]["minutes"][key]:
                    count = 0
                    while count < self.max_iter_count:
                        end_time = end_time[next(iter(end_time))]
                        if "min" in end_time:
                            break
                        else:
                            count += 1

                    if "min" in end_time:
                        result[key] = end_time
                        break

                    else:
                        print(
                            f"The dimension of the {key} json object is too large, ",
                            "please try to reduce the dimension."
                        )
                        return None

        except KeyError or AttributeError:
            print("The structure of the goal json file has been changed, please update the reading function.")
            return None

        return result

    def _check_boundary_conditions(self, event_time, half_end, game_end, case="both"):

        if int(event_time["period"]) == 1:
            boundary_start = {"min": 0, "sec": 0, "period": 1}
            boundary_end = half_end
        else:
            boundary_start = {"min": 45, "sec": 0, "period": 2}
            boundary_end = game_end

        intersection_flag_start = False
        intersection_flag_end = False

        if case == "before":
            if int(event_time["min"]) - self.time_interval_measure < int(boundary_start["min"]):
                intersection_flag_start = True
            elif int(event_time["min"]) - self.time_interval_measure == int(boundary_start["min"]):
                if int(event_time["sec"]) < int(boundary_start["sec"]):
                    intersection_flag_start = True

            return intersection_flag_start, boundary_start

        elif case == "after":
            if int(event_time["min"]) + self.time_interval_measure > int(boundary_end["min"]):
                intersection_flag_end = True
            elif int(event_time["min"]) + self.time_interval_measure == int(boundary_end["min"]):
                if int(event_time["sec"]) > int(boundary_end["sec"]):
                    intersection_flag_end = True

            return intersection_flag_end, boundary_end

        else:
            if int(event_time["min"]) - self.time_interval_measure < int(boundary_start["min"]):
                intersection_flag_start = True
            elif int(event_time["min"]) - self.time_interval_measure == int(boundary_start["min"]):
                if int(event_time["sec"]) < int(boundary_start["sec"]):
                    intersection_flag_start = True

            if int(event_time["min"]) + self.time_interval_measure > int(boundary_end["min"]):
                intersection_flag_end = True
            elif int(event_time["min"]) + self.time_interval_measure == int(boundary_end["min"]):
                if int(event_time["sec"]) > int(boundary_end["sec"]):
                    intersection_flag_end = True

            return intersection_flag_start, boundary_start, intersection_flag_end, boundary_end

    def _check_intersection_between_event_times(self, first_event_time, second_event_time):

        intersection_flag = False
        if int(first_event_time["period"]) == int(second_event_time["period"]):
            if int(first_event_time["min"]) + self.time_interval_measure > int(second_event_time["min"]):
                intersection_flag = True
            elif int(first_event_time["min"]) + self.time_interval_measure == int(second_event_time["min"]):
                if int(first_event_time["sec"]) > int(second_event_time["sec"]):
                    intersection_flag = True

        return intersection_flag

    @staticmethod
    def _update_time(time_dict, dt):
        """

        :param dict time_dict:
        :param int dt:
        :return:
        :rtype: dict
        """
        total_sec = int(time_dict["min"]) * 60 + int(time_dict["sec"]) + int(dt)
        return {
            "min": int(total_sec // 60),
            "sec": int(total_sec % 60),
            "period": time_dict["period"]
        }


class GoalDiff(MatchDataDiff):
    def __init__(
            self, game_id, competition_id, season_id, parameter_names, main_path=None, time_interval_measure=5
    ):
        MatchDataDiff.__init__(
            self, game_id, competition_id, season_id, parameter_names, main_path, time_interval_measure
        )

    def get_time_of_goal_events(self):
        match_data_summary = self.get_match_data_summary()
        if len(match_data_summary) == 0:
            return None

        away_score = int(match_data_summary[0]["game"][0]["awayScore"])
        home_score = int(match_data_summary[0]["game"][0]["homeScore"])
        if 0 == home_score + away_score:
            return None

        events_time = self.get_match_events_time()
        goal_events_time = list()

        try:
            for goal_event_time in events_time[0]["events"]["minutes"]["Goals"]:
                count = 0
                while count < self.max_iter_count:
                    goal_event_time = goal_event_time[next(iter(goal_event_time))]
                    if "min" in goal_event_time:
                        break
                    else:
                        count += 1

                if "min" in goal_event_time:
                    goal_events_time.append(goal_event_time)

                else:
                    print(
                        "The dimension of the 'Goal' json object is too large, please try to reduce the dimension."
                    )
                    return list()

        except KeyError or AttributeError:
            print("The structure of the goal json file has been changed, please update the reading function.")
            return list()

        return goal_events_time

    def construct_time_intervals(self):

        goal_events_time = self.get_time_of_goal_events()

        if goal_events_time is None:
            return None

        total_goals = len(goal_events_time)

        half_end, game_end = self.get_break_times().values()

        all_time_interval = list()
        intersection_flag = False

        for index in range(total_goals):
            temp_time_interval = {
                "before": {
                    "from": {"min": 0, "sec": 0, "period": 0},
                    "to": {"min": 0, "sec": 0, "period": 0}
                },
                "after": {
                    "from": {"min": 0, "sec": 0, "period": 0},
                    "to": {"min": 0, "sec": 0, "period": 0}
                }
            }

            if intersection_flag:
                temp_time_interval["before"]["from"] = all_time_interval[index - 1]["after"]["from"]
            else:
                condition, boundary = self._check_boundary_conditions(
                        event_time=goal_events_time[index], half_end=half_end, game_end=game_end, case="before"
                )
                if condition:
                    temp_time_interval["before"]["from"] = boundary
                else:
                    for key, value in goal_events_time[index].items():
                        if key == "min":
                            value = int(value) - self.time_interval_measure
                        temp_time_interval["before"]["from"][str(key)] = int(value)

            temp_time_interval["before"]["to"] = goal_events_time[index]

            temp_time_interval["after"]["from"] = self._update_time(time_dict=goal_events_time[index], dt=1)

            if index + 1 == total_goals:
                intersection_flag = False
            else:
                intersection_flag = self._check_intersection_between_event_times(
                    first_event_time=temp_time_interval["after"]["from"],
                    second_event_time=goal_events_time[index + 1]
                )

            if intersection_flag:
                temp_time_interval["after"]["to"] = self._update_time(time_dict=goal_events_time[index + 1], dt=-1)

            else:
                condition, boundary = self._check_boundary_conditions(
                    event_time=temp_time_interval["after"]["from"], half_end=half_end, game_end=game_end, case="after"
                )
                if condition:
                    temp_time_interval["after"]["to"] = boundary
                else:
                    for key, value in temp_time_interval["after"]["from"].items():
                        if key == "min":
                            value = int(value) + self.time_interval_measure
                        temp_time_interval["after"]["to"][str(key)] = int(value)

            all_time_interval.append(temp_time_interval)

        return all_time_interval

    def construct_goal_counter(self, team_id):
        events_time = self.get_match_events_time()
        goal_counter = list()
        counter = 0
        increment = 1
        if self.get_home_away_teams()["home_team_id"] != team_id:
            increment = -1

        try:
            for goal_event_time in events_time[0]["events"]["minutes"]["Goals"]:
                for temp_team_id in goal_event_time.keys():
                    if temp_team_id == team_id:
                        counter += increment
                        goal_counter.append(counter)
                    else:
                        counter -= increment
                        goal_counter.append(counter)

        except KeyError or AttributeError:
            print("The structure of the goal json file has been changed, please update the reading function.")
            return list()
        return goal_counter

    def get_goal_diff_stats(self, team_id, player_id=None):
        all_data_frames = list()
        all_time_intervals = self.construct_time_intervals()

        if all_time_intervals is None:
            return None

        total_goals = len(all_time_intervals)
        goal_counter = self.construct_goal_counter(team_id=team_id)

        if not isinstance(team_id, list):
            team_id = [team_id]
        if player_id is not None:
            if not isinstance(player_id, list):
                player_id = [player_id]

        for index in range(total_goals):
            temp_data_frame_list = list()
            for before_after in ["before", "after"]:
                temp_time_query = hlp.mongodb_time_query_converter(
                    raw_time_interval=all_time_intervals[index][before_after], return_time_interval=False,
                    return_time_query=True
                )

                result = self.gapi().get_match_data(
                    game_ids=self.game_id, team_ids=team_id, player_ids=player_id, time_interval=temp_time_query
                )

                if 0 < len(result):
                    temp_data_frame = json_to_df_statistics(
                        json_file_itself={"games": list(result)}, param_names=self.parameter_names.copy()
                    )

                    temp_data_frame["norm of time interval (min)"] = round(
                        hlp.length_of_time_interval_obtained_from_converter(
                            time_interval=all_time_intervals[index][before_after]
                        ),
                        2
                    )

                    temp_data_frame["time interval"] = hlp.inverse_of_mongo_db_time_query_converter(
                        all_time_intervals[index][before_after]
                    )
                    temp_data_frame.reset_index(inplace=True)
                    temp_data_frame_list.append(temp_data_frame)

            merged_df = pd.merge(
                left=temp_data_frame_list[0], right=temp_data_frame_list[1], on="index",
                suffixes=(" (before)", " (after)")
            )

            merged_df = merged_df.assign(
                goal_counter_home=goal_counter[index], team_id=team_id,
                game_id=self.game_id, **self.get_home_away_teams()
            )
            all_data_frames.append(merged_df)

        complete_df = pd.concat(all_data_frames).reset_index(drop=True)
        return complete_df

    def save_goal_diff_stats(self, game_ids=None, team_names=None, player_ids=None):

        teams_dict = self.get_team_game_dict(game_ids=game_ids, team_names=team_names)

        vast_df = list()
        for team_name, value in teams_dict.items():
            for team_id, game_ids in value.items():
                temp_path = self.main_path + f"/{team_name}/"
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)

                team_all_games_df = list()
                for game_id in game_ids:
                    self.update_game_id(new_game_id=str(game_id).replace("g", ""))
                    temp_file_path = temp_path + f"{game_id}.xlsx"
                    if Path(temp_file_path).is_file():
                        print("Given file already exists in the path; ", temp_file_path)
                        continue

                    game_diff_df = self.get_goal_diff_stats(team_id=team_id, player_id=player_ids)

                    if game_diff_df is None:
                        continue

                    if 0 < len(game_diff_df):
                        concat_data_frames(game_diff_df).to_excel(temp_file_path)
                        team_all_games_df.append(game_diff_df)
                    else:
                        pd.DataFrame().to_excel(temp_file_path)

                if len(team_all_games_df) != 0:
                    team_merged_data = concat_data_frames(team_all_games_df)

                    if not Path(temp_path + "team_merged_data.xlsx").is_file():
                        team_merged_data.to_excel(temp_path + "team_merged_data.xlsx")

                    vast_df.append(team_merged_data)

        if not Path(self.main_path + "vast_merged_data.xlsx").is_file():
            vast_df = pd.concat(vast_df).reset_index(drop=True)
            vast_df.to_excel(self.main_path + "vast_merged_data.xlsx")

        return vast_df

    def get_goal_diff_actions(self, team_id, player_id=None):

        all_time_intervals = self.construct_time_intervals()

        if all_time_intervals is None:
            return None

        total_goals = len(all_time_intervals)
        goal_counter = self.construct_goal_counter(team_id=team_id)

        if not isinstance(team_id, list):
            team_id = [team_id]
        if player_id is not None:
            if not isinstance(player_id, list):
                player_id = [player_id]

        data_frames = {
            "before": pd.DataFrame(),
            "after": pd.DataFrame(),
            "game": pd.DataFrame()
        }

        for index in range(total_goals):
            temp_game_dict = {
                "before": {
                    "total_minutes": 0,
                    "time_interval": 0
                },
                "after": {
                    "total_minutes": 0,
                    "time_interval": 0
                }
            }

            for before_after in ["before", "after"]:
                temp_time_query = hlp.mongodb_time_query_converter(
                    raw_time_interval=all_time_intervals[index][before_after], return_time_interval=False,
                    return_time_query=True
                )

                result = self.gapi().get_match_data(
                    game_ids=self.game_id, team_ids=team_id, player_ids=player_id,
                    time_interval=temp_time_query, parse=False, show_events=True
                )

                if 0 < len(result):
                    temp_data_frame = json_to_df_events(
                        json_file_itself=list(result)[0]
                    )

                    temp_game_dict[before_after]["total_minutes"] = round(
                        hlp.length_of_time_interval_obtained_from_converter(
                            time_interval=all_time_intervals[index][before_after]
                        ),
                        2
                    )

                    temp_game_dict[before_after]["time_interval"] = hlp.inverse_of_mongo_db_time_query_converter(
                        all_time_intervals[index][before_after]
                    )
                    temp_data_frame.reset_index(inplace=True)

                    old_df = data_frames[before_after]
                    new_df = pd.concat(objs=[old_df, temp_data_frame], ignore_index=True)
                    data_frames[before_after] = new_df

            old_game_df = data_frames["game"]
            temp_game_df = pd.DataFrame(
                data={
                    "total minutes (before)": temp_game_dict["before"]["total_minutes"],
                    "time interval (before)": temp_game_dict["before"]["time_interval"],
                    "total minutes (after)": temp_game_dict["after"]["total_minutes"],
                    "time interval (after)": temp_game_dict["after"]["time_interval"],
                    "goal counter home team": goal_counter[index]
                },
                index=[0]
            )
            new_game_df = pd.concat(
                objs=[old_game_df, pd.DataFrame(data=temp_game_df, index=[0])],
                ignore_index=True
            )
            away_team, home_team = self.get_home_away_teams().values()
            new_game_df["home team id"] = home_team
            new_game_df["away team id"] = away_team
            data_frames["game"] = new_game_df

        for data_frame in data_frames.values():
            data_frame["gameID"] = int(self.game_id[0])

        return data_frames

    def save_goal_diff_actions(self, game_ids=None, team_names=None, player_ids=None):

        teams_dict = self.get_team_game_dict(game_ids=game_ids, team_names=team_names)
        print(teams_dict)
        vast_df = {
            "before": pd.DataFrame(),
            "after": pd.DataFrame(),
            "game": pd.DataFrame()
        }
        for team_name, value in teams_dict.items():
            temp_path = self.main_path + f"/{team_name}/"
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            team_all_games_df = {
                "before": pd.DataFrame(),
                "after": pd.DataFrame(),
                "game": pd.DataFrame()
            }
            for team_id, game_ids in value.items():
                for game_id in game_ids:
                    self.update_game_id(new_game_id=str(game_id).replace("g", ""))
                    temp_file_path = temp_path + f"{game_id}.xlsx"
                    if Path(temp_file_path).is_file():
                        print("Given file already exists in the path; ", temp_file_path)
                        continue

                    game_diff_df = self.get_goal_diff_actions(team_id=team_id, player_id=player_ids)

                    if game_diff_df is None:
                        continue

                    temp_excel_writer = pd.ExcelWriter(path=temp_file_path, engine='xlsxwriter')
                    if 0 < len(game_diff_df):
                        for key, data_frame in game_diff_df.items():
                            data_frame.to_excel(excel_writer=temp_excel_writer, sheet_name=key, index=False)
                            team_all_games_df[key] = pd.concat(
                                objs=[team_all_games_df[key], data_frame], ignore_index=True
                            )
                        temp_excel_writer.save()

            team_merged_file_path = temp_path + "team_merged_data.xlsx"
            team_excel_writer = pd.ExcelWriter(path=team_merged_file_path, engine='xlsxwriter')
            for key, data_frame in team_all_games_df.items():
                data_frame.to_excel(excel_writer=team_excel_writer, sheet_name=key, index=False)
                vast_df[key] = pd.concat(
                    objs=[vast_df[key], data_frame], ignore_index=True
                )
            team_excel_writer.save()

        complete_excel_writer = pd.ExcelWriter(path=self.main_path + "vast_merged_data.xlsx", engine='xlsxwriter')
        for key, data_frame in vast_df.items():
            data_frame.to_excel(excel_writer=complete_excel_writer, sheet_name=key, index=False)
            vast_df[key] = pd.concat(
                objs=[vast_df[key], data_frame], ignore_index=True
            ).reset_index(drop=True)
        complete_excel_writer.save()
        return vast_df


if __name__ == "__main__":
    params = [
        'aerial duels won', 'aerial duels lost', 'Total passes completed', 'Unsuccessful passes',
        'Crosses completed', 'Unsuccessful crosses', 'Successful corners', 'Unsuccessful corners',
        'total assists', 'total interceptions', 'touches in opponent box', 'Goals', 'Total shots on target',
        'Total shots off target', 'total ball recoveries', 'total take ons'
    ]
    competition_id_super_lig = 115
    season_id_2018 = 2018
    season_id_2019 = 2019

    def run1():
        GoalDiff(
            game_id=None, competition_id=competition_id_super_lig,
            season_id=season_id_2018, parameter_names=params, main_path=get_src_path(
                "/src/output/LFA Season 19-20, 10 Minutes/"
            ), time_interval_measure=10
        ).save_goal_diff_stats()

    def run2():
        GoalDiff(
            game_id=1002152, competition_id=competition_id_super_lig,
            season_id=season_id_2018, parameter_names=params, main_path=get_src_path(
                "/src/output/test/test/"
            ), time_interval_measure=15
        ).save_goal_diff_actions()

    run2()
