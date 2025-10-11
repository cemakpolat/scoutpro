import pandas as pd
from dataRetrieving.MatchData import MatchData

# Define season id's.
season_2016 = 2016
season_2017 = 2017
season_2018 = 2018
season_2019 = 2019

# Define competition id's.
super_lig = 115
la_liga = 23


def get_season_all_match_data(
        competition_id: int,
        season_id: int,
        events: list = None,
        event_params: list = None,
        main_path: str = None
):
    MD = MatchData(
        competition_id=competition_id,
        season_id=season_id,
        events=events,
        event_params=event_params,
        main_path=main_path
    )
    norm = len(MD.all_games_ids)
    temp_file_name = "all_games.xlsx"
    new_columns = {
        "gameID": "game_id",
        "AwayTeamName": "away_team_name",
        "AwayTeamID": "away_team_id",
        "HomeTeamName": "home_team_name",
        "homeTeamID": "home_team_id",
    }
    for _ in range(norm):
        temp_df = MD.get_data_frame()
        ordered_columns = temp_df.columns.tolist()
        ordered_columns = list(new_columns.keys()) + ordered_columns
        for feature, attribute in new_columns.items():
            temp_series = pd.Series(
                data=getattr(MD, attribute),
                index=temp_df.index,
                name=feature
            )
            temp_df = pd.concat(
                [temp_df, temp_series], axis=1
            )
        temp_df = temp_df[ordered_columns]
        left_df = pd.DataFrame(
            data=temp_df.loc[MD.away_team_name]
        ).transpose()
        right_df = pd.DataFrame(
            data=temp_df.loc[MD.home_team_name]
        ).transpose()
        merged_df = pd.merge(
            left=left_df,
            right=right_df,
            left_on=list(new_columns.keys()),
            right_on=list(new_columns.keys()),
            how="outer",
            suffixes=(" (away)", " (home)")
        )
        MD.save_data_frame(
            data_frame=merged_df,
            file_name=temp_file_name,
            concat=True
        )
        MD.next_game()


if __name__ == "__main__":
    get_season_all_match_data(
        super_lig,
        season_2019
    )
