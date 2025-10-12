import os
import pandas as pd
from src.utils.Utils import get_src_path
from src.feedAPI import TeamAPI
from src.feedAPI import GameAPI
from src.feedAPI import EventAPI
from src.danalyticAPI.DataRetrieving.ReadData import json_to_df_statistics


class MatchData:
    def __init__(
            self, competition_id: int,
            season_id: int,
            game_id: int = None,
            events: list = None,
            event_params: list = None,
            main_path: str = None
    ):
        # Main input variables.
        self.competition_id = int(competition_id)
        self.season_id = int(season_id)
        self.events = events
        self.event_params = event_params
        self.max_iter_count = 5

        # API variables.
        self.tapi = TeamAPI.TeamAPI(
            competitionID=self.competition_id, seasonID=self.season_id
        )
        self.gapi = GameAPI.GameAPI(
            competitionID=self.competition_id, seasonID=self.season_id
        )
        self.evapi = EventAPI.EventAPI(
            competition_id=self.competition_id, season_id=self.season_id
        )

        # Season all game ids.
        self.all_games_ids = self.gapi.get_season_all_games_ids()

        # Define path and events.
        self.game_id = int()
        self.game_id_index = int()
        self.main_path = str()
        self.save_path = str()
        self._define_game_id(candidate_game_id=game_id)
        self._define_path(candidate_path=main_path)

        # Game variables.
        self.game_summary = None
        self.event_times = None
        self.away_team_id = None
        self.away_team_name = None
        self.home_team_id = None
        self.home_team_name = None
        self.first_half_break = None
        self.second_half_break = None

        # Get match data function variables.
        self.gmd_game_ids = None
        self.gmd_team_ids = None
        self.gmd_player_ids = None
        self.gmd_event_names = None
        self.gmd_time_interval = None

        # Define game variables.
        self._define_game_variables()

        # Define get match data variables.
        self._define_gmd_variables()

    def _define_game_variables(self):
        self._get_match_data_summary().\
            _get_match_events_time().\
            _get_home_away_teams().\
            _get_break_times()
        return self

    def _define_gmd_variables(self):
        self.gmd_game_ids = [self.game_id]
        self.gmd_team_ids = [self.away_team_id, self.home_team_id]
        self.gmd_player_ids = None
        self.gmd_event_names = self.events
        self.gmd_time_interval = None
        return self

    def _define_game_id(self, candidate_game_id: int = None):
        if candidate_game_id is not None:
            if candidate_game_id in self.all_games_ids:
                self.game_id_index = self.all_games_ids.index(
                    candidate_game_id
                )
                self.game_id = candidate_game_id
                return self

        self.game_id = self.all_games_ids[0]
        return self

    def _define_path(self, candidate_path: str = None):
        if candidate_path is None:
            candidate_path = ""
        if os.path.isdir(candidate_path):
            self.main_path = candidate_path
        else:
            self.main_path = get_src_path("/src/output/")
        self.save_path = self.main_path + f"/{self.competition_id}/{self.season_id}/"
        return self

    def _get_match_events_time(self):
        self.event_times = list(
            self.gapi.get_match_data(
                game_ids=[self.game_id],
                show_event_time=True,
                event_times_converter=False
            )
        )
        return self

    def _get_match_data_summary(self):
        self.game_summary = list(
            self.gapi.get_match_data(
                game_ids=[self.game_id],
                parse=False,
                get_only_games=True
            )
        )
        return self

    def _get_home_away_teams(self):
        if len(self.game_summary) != 0:
            self.away_team_id = int(
                    self.game_summary[0]["game"][0]["awayTeamID"]
                )
            self.away_team_name = str(
                self.game_summary[0]["game"][0]["awayTeamName"]
            )
            self.home_team_id = int(
                self.game_summary[0]["game"][0]["homeTeamID"]
            )
            self.home_team_name = str(
                self.game_summary[0]["game"][0]["homeTeamName"]
            )
        return self

    def _get_break_times(self):
        if len(self.event_times) == 0:
            return None
        result = {
            "first_half_break": None,
            "second_half_break": None
        }
        try:
            for key in result:
                for end_time in self.event_times[0]["events"]["minutes"][key]:
                    count = 0
                    while count < self.max_iter_count:
                        end_time = end_time[next(iter(end_time))]
                        if "min" in end_time:
                            break
                        else:
                            count += 1

                    if "min" in end_time:
                        setattr(self, key, end_time)
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

        return self

    def update_game_id(self, new_game_id: int):
        self._define_game_id(candidate_game_id=new_game_id)
        self._define_game_variables()._define_gmd_variables()
        return self

    def next_game(self):
        try:
            self.update_game_id(
                new_game_id=self.all_games_ids[
                    self.game_id_index + 1
                ]
            )
        except IndexError:
            print("Current game is the last game in the season!")
        return self

    def update_gmd_all_inputs(
            self, team_ids: list = None, player_ids: list = None,
            event_names: list = None, time_interval: dict = None
    ):
        self.gmd_team_ids = team_ids
        self.gmd_player_ids = player_ids
        self.gmd_event_names = event_names
        self.gmd_time_interval = time_interval
        return self

    def update_gmd_single_input(
            self, input_name: str, new_input_value
    ):
        if "gmd_" not in input_name:
            input_name = "gmd_" + input_name
        try:
            setattr(self, input_name, new_input_value)
        except AttributeError as err:
            print(err)
        return self

    def gmd_run(self):
        return self.gapi.get_match_data(
                game_ids=self.gmd_game_ids,
                team_ids=self.gmd_team_ids,
                player_ids=self.gmd_player_ids,
                event_names=self.gmd_event_names,
                time_interval=self.gmd_time_interval
            )

    def get_data_frame(self):
        result = {"games": list(self.gmd_run())}
        df = json_to_df_statistics(
            json_file_itself=result,
            event_names=self.events,
            param_names=self.event_params
        )
        return df

    def save_data_frame(
            self, data_frame: pd.DataFrame = None,
            file_name: str = None, concat: bool = False,
            sheet_name: str = None, index: bool = False
    ):
        if data_frame is None:
            data_frame = self.get_data_frame()

        if file_name is None:
            file_name = str(self.game_id) + ".xlsx"

        if sheet_name is None:
            sheet_name = "Sheet1"

        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        first_create_mode = True
        data_frame_path = self.save_path + file_name
        start_row = 0
        if os.path.isfile(data_frame_path):
            if concat:
                start_row = len(
                    pd.read_excel(
                        io=data_frame_path, sheet_name=sheet_name
                    ).index
                ) + 1
                first_create_mode = False

        if first_create_mode:
            excel_writer = pd.ExcelWriter(
                path=data_frame_path, engine="xlsxwriter"
            )
        else:
            excel_writer = pd.ExcelWriter(
                path=data_frame_path, engine="openpyxl", mode="a",
                if_sheet_exists="overlay"
            )
        data_frame.to_excel(
            excel_writer=excel_writer,
            sheet_name=sheet_name,
            index=index,
            startrow=start_row,
            header=first_create_mode
        )
        excel_writer.save()
        return self


if __name__ == "__main__":
    df_2016 = pd.read_excel(
        "all_games_2016.xlsx"
    )
    temp_series = pd.Series(
        data=2016,
        index=df_2016.index,
        name="season_id"
    )
    df_2016 = pd.concat(
        [df_2016, temp_series], axis=1
    )
    ordered_columns = df_2016.columns.tolist()
    ordered_columns.remove("season_id")
    ordered_columns.insert(
        4, "season_id"
    )
    df_2016 = df_2016[ordered_columns]

    df_2017 = pd.read_excel(
        "all_games_2017.xlsx"
    )
    temp_series = pd.Series(
        data=2017,
        index=df_2017.index,
        name="season_id"
    )
    df_2017 = pd.concat(
        [df_2017, temp_series], axis=1
    )
    ordered_columns = df_2017.columns.tolist()
    ordered_columns.remove("season_id")
    ordered_columns.insert(
        4, "season_id"
    )
    df_2017 = df_2017[ordered_columns]

    df_2018 = pd.read_excel(
        "all_games_2018.xlsx"
    )
    temp_series = pd.Series(
        data=2018,
        index=df_2018.index,
        name="season_id"
    )
    df_2018 = pd.concat(
        [df_2018, temp_series], axis=1
    )
    ordered_columns = df_2018.columns.tolist()
    ordered_columns.remove("season_id")
    ordered_columns.insert(
        4, "season_id"
    )
    df_2018 = df_2018[ordered_columns]

    df_2019 = pd.read_excel(
        "all_games_2019.xlsx"
    )
    temp_series = pd.Series(
        data=2019,
        index=df_2019.index,
        name="season_id"
    )
    df_2019 = pd.concat(
        [df_2019, temp_series], axis=1
    )
    ordered_columns = df_2019.columns.tolist()
    ordered_columns.remove("season_id")
    ordered_columns.insert(
        4, "season_id"
    )
    df_2019 = df_2019[ordered_columns]

    pd.concat([df_2016, df_2017, df_2018, df_2019]).to_excel(
        "all_games.xlsx", index=False
    )

