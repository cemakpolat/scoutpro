from src.saveData.SaveData import SaveData

# Define data base save variables.
db_name = "statsfabrik"
db_port = 27017
db_host = "localhost"
db_alias = "default"

# Define season id's.
season_2016 = 2016
season_2017 = 2017
season_2018 = 2018
season_2019 = 2019

# Define competition id's.
super_lig = 115
la_liga = 23

# Define first game id's and
# total number of games played in the league.
game_dict = {
    season_2016: {
        super_lig: {
            "first_game_id": 871375,
            "total_number_of_games": 306
        },
        la_liga: {
            "first_game_id": 869457,
            "total_number_of_games": 380,
        }
    },
    season_2017: {
        super_lig: {
            "first_game_id": 935586,
            "total_number_of_games": 306
        },
        la_liga: {
            "first_game_id": 942799,
            "total_number_of_games": 380,
        }
    },
    season_2018: {
        super_lig: {
            "first_game_id": 1002148,
            "total_number_of_games": 306
        },
        la_liga: {
            "first_game_id": 1009316,
            "total_number_of_games": 380,
        }
    },
    season_2019: {
        super_lig: {
            "first_game_id": 1080974,
            "total_number_of_games": 252
        },
        la_liga: {
            "first_game_id": 1074815,
            "total_number_of_games": 300,
        }
    }
}


# Save functions
def save_single_session(
        season_id: int,
        competition_id: int,
        derived_stats: bool = True
)-> None:
    """
    Description:
        Main function to save data of a single competitions' season data.
        Since it takes too much time to save all data at once, it will be
        more useful to use this function to save the data one season and
        competition at one run.

    Parameters:
        :param int season_id: Code of season, which can be chosen above
            variables in the script file.
        :param int competition_id: Code of competition, which can be chosen
            above variables in the script file.
        :param bool derived_stats: Save all derived statistics flag, such as
            per90 or percentile statistics. It is recommended to save all of
            these data, so default value is True.
    Return:
        :return: None

    """
    try:
        game_info = game_dict[season_id][competition_id]
    except KeyError as err:
        print(
            f"Provided seas or competition could not be found: {err}"
        )
        print(
            f"SESSION COULD NOT BE SAVED: "
            f"competition: {competition_id}, "
            f"season: {season_id}."
        )
    else:
        saver = SaveData(
            competition_id=competition_id,
            season_id=season_id,
            game_id_start_int=game_info["first_game_id"],
            index_norm=game_info["total_number_of_games"],
            name=db_name,
            port=db_port,
            host=db_host,
            alias=db_alias
        )
        saver.save_all_main()
        if derived_stats:
            saver.save_all_general()
        print(
            f"SESSION SUCCESSFULLY SAVED: "
            f"competition: {competition_id}, "
            f"season: {season_id}."
        )

def save_all(
    derived_stats: bool = True
) -> None:
    """
    Description:
        Main loop function for saving all data from local files into
        MongoDB. It may take quite a long time to save all data from
        scratch. Therefore, it is recommended to begin with much
        smaller version of above dictionary, for instance saving
        the data for just one season at a time, instead saving all of
        them in same run. To do this, try to use "save_single_session"
        function.

    Parameters:
        :param bool derived_stats: Save all derived statistics flag, such as
            per90 or percentile statistics. It is recommended to save all of
            these data, so default value is True.

    Return:
        :return: None
    """
    for season_id, temp_dicts in game_dict.items():
        for competition_id in temp_dicts:
            save_single_session(
                season_id=season_id,
                competition_id=competition_id,
                derived_stats=derived_stats
            )


if __name__ == "__main__":
    test_season = season_2018
    test_competition = super_lig
    save_single_session(
        season_id=test_season,
        competition_id=test_competition
    )
