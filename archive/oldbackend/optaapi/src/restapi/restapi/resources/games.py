"""
@author: Cem Akpolat
@created by cemakpolat at 2020-07-24
"""
import json

from bson import json_util
from flask import Blueprint, Response, request
from src.feedAPI.GameAPI import GameAPI
from src.feedAPI import EventAPI
from src.feedAPI import TeamAPI
from src.feedAPI import PlayerAPI
from src.restapi.restapi.resources import errors as err
from src.restapi.restapi.resources import helper as hlp


games = Blueprint("games", __name__)
path = "./input/"


@games.route("/games/<id>", methods=["GET"], endpoint="game")
def get_game_id(id):
    game = GameAPI()
    result = game.getGameDataById(id)
    return Response(result, mimetype="application/json", status=200)


@games.route("/games/o/<oid>", methods=["GET"], endpoint="game via oid")
def get_game_oid(oid):
    game = GameAPI()
    result = game.getGameDataById(oid)
    return Response(result, mimetype="application/json", status=200)


# ----------------------Get All Matches of a Team----------------------------
@games.route("/games/all_matches/<team_name>", endpoint="get all matches of a team")
def get_all_matches(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
    raw_team_ids = hlp.separate_raw_string(team_name, ",")
    team_ids = list()
    for team in raw_team_ids:
        try:
            team_ids.append(int(str(team).strip().replace("t", "")))
        except ValueError:
            team_ids.append(int(tapi.get_team_id(team.strip()).replace("t", "")))

    gapi = GameAPI(int(competition_id.strip()), int(season_id.strip()))

    # Calculate the total time it takes to execute the given operation.
    from time import time
    operation_starting_time = time()

    all_documents = gapi.get_match_data(
        team_ids=team_ids,
        parse=False,
        all_games_bool=True,
        get_only_games=True
    )

    all_games = dict()
    all_games_list = list()

    for document in all_documents:
        all_games_list.append(document)

    # Collect all the result.
    all_games["Total number of games in the operation"] = len(all_games_list)
    all_games["Total time it takes to execute the operation"] = time() - operation_starting_time
    all_games["games"] = all_games_list

    result = json_util.dumps(all_games, indent=4)

    return Response(result, mimetype="application/json", status=200)


# ---------------Get Match Events With Respect to Players or Teams----------------------------

@games.route("/games/get", endpoint="get match data")
def get_match_data():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    player_ids = request.args.get("player")
    team_ids = request.args.get("team")
    game_ids = request.args.get("games")
    all_games_bool = request.args.get("all_games")
    event_names = request.args.get("event_names")
    time_interval = request.args.get("time_interval")
    parse = request.args.get("parse")
    show_events = request.args.get("show_events")
    show_event_time = request.args.get("show_event_time")
    input_file_name = request.args.get("file_name")
    get_general = request.args.get("get_general")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    if game_ids:
        game_ids = hlp.separate_raw_string(game_ids, ",")

    if team_ids:
        tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
        raw_team_ids = hlp.separate_raw_string(team_ids, ",")
        team_ids = list()
        for team in raw_team_ids:
            try:
                team_ids.append(int(str(team).strip()))
            except ValueError:
                team_ids.append(int(tapi.get_team_id(team.strip())))

    if player_ids:
        tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
        raw_player_ids = hlp.separate_raw_string(player_ids, ",")
        player_ids = list()
        for player in raw_player_ids:
            try:
                player_ids.append(int(str(player).strip()))
            except ValueError:
                player_ids.append(int(tapi.get_player_id(player.strip())))

    if event_names:
        multi_event_dict = EventAPI.EventAPI().multi_event_dict()
        raw_event_names = hlp.separate_raw_string(event_names, ",")
        event_names = list()
        for event in raw_event_names:
            if event.strip() in multi_event_dict.values():
                event_names.append(event)
            else:
                try:
                    event_names.append(multi_event_dict[event.strip()])
                except KeyError:
                    raise err.IncorrectParams(message="Example input for event_names: aerial, pass, card")

    if time_interval:
        time_interval = hlp.mongodb_time_query_converter(raw_string=time_interval, return_time_interval=False,
                                                         return_time_query=True)

    if parse:
        parse = hlp.convert_raw_string_into_bool(parse)
    else:
        parse = True

    if all_games_bool:
        all_games_bool = hlp.convert_raw_string_into_bool(all_games_bool)

    if show_events:
        show_events = hlp.convert_raw_string_into_bool(show_events)

    if show_event_time:
        show_event_time = hlp.convert_raw_string_into_bool(show_event_time)

    gapi = GameAPI(int(competition_id.strip()), int(season_id.strip()))

    # Calculate the total time it takes to execute the given operation.
    from time import time
    operation_starting_time = time()

    all_documents = gapi.get_match_data(
        game_ids=game_ids,
        team_ids=team_ids,
        player_ids=player_ids,
        parse=parse,
        event_names=event_names,
        time_interval=time_interval,
        all_games_bool=all_games_bool,
        show_events=show_events,
        show_event_time=show_event_time
    )

    all_games = dict()
    all_games_list = list()

    for document in all_documents:
        all_games_list.append(document)

    # Collect all the result.
    all_games["Total number of games in the operation"] = len(all_games_list)
    all_games["Total time it takes to execute the operation"] = time() - operation_starting_time
    all_games["games"] = all_games_list

    if (not player_ids) and (not team_ids) and get_general:
        temp = dict()
        temp["homeTeamName"] = all_games["games"][0]["game"][0]["homeTeamName"]
        temp["homeScore"] = all_games["games"][0]["game"][0]["homeScore"]

        temp["awayTeamName"] = all_games["games"][0]["game"][0]["awayTeamName"]
        temp["awayScore"] = all_games["games"][0]["game"][0]["awayScore"]

        general_stat_list = []
        temp["general_stats"] = []

        def f(st, d_s_array, new_name_array):
            array = []
            for i in range(len(d_s_array)):
                d_s = d_s_array[i]
                stat = dict()
                stat["HomeTeam"] = all_games["games"][0]["events"][1][st][d_s]
                stat["TeamStats"] = new_name_array[i]
                stat["AwayTeam"] = all_games["games"][0]["events"][0][st][d_s]
                array.append(stat)
            return array

        general_stat_list += f("shot",
                               ["Goals", "otal shots (excluding blocks)", "Total shots on target"],
                               ["Goals", "Shots", "Shots On Target"])

        general_stat_list += f("pass",
                                ["Total passes attempted", "Passes completion percentage", "Total corners"],
                                ["Passes", "Pass Accuracy", "Corners"])

        general_stat_list += f("foul", ["total fouls committed"], ["Fouls"])

        general_stat_list += f("card",
                               ["total yellow cards", "total red cards"],
                               ["Yellow Cards", "Red Cards"])

        general_stat_list[7]["HomeTeam"] += all_games["games"][0]["events"][1]["card"]["total second yellow cards"]
        general_stat_list[7]["AwayTeam"] += all_games["games"][0]["events"][0]["card"]["total second yellow cards"]

        general_stat_list += f("ballControl",
                               ["total offsides"],
                               ["Offsides"])

        temp["general_stats"] = general_stat_list
        all_games = temp

        # stat = dict()
        # stat["HomeTeam"] = all_games["games"][0]["events"][1]["shot"]["Goals"]
        # stat["TeamStats"] = "Goals"
        # stat["AwayTeam"] = all_games["games"][0]["events"][0]["shot"]["Goals"]
        # general_stat_list.append(stat)



    # if player_ids and (not team_ids):
    #     papi = PlayerAPI.PlayerAPI(int(competition_id.strip()), int(season_id.strip()))
    #     team_name = papi.getTeam


    result = json_util.dumps(all_games, indent=4)

    # Save the query result as a JSON file.
    if input_file_name:
        file_name = input_file_name
    else:
        file_name = "temp.json"

    with open(path+file_name, "w", encoding="utf8") as f:
        f.write(result)

    response = Response(result, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# ---------------Get Player Minute Stats in a Match----------------------------
@games.route("/games/get/player_min", endpoint="get player min stat in a match")
def get_player_min_stats():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    team_id = request.args.get("team")
    game_id = request.args.get("game")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    if game_id:
        try:
            game_id = int(str(game_id.strip()))
        except ValueError:
            raise err.IncorrectParams(
                message="game parameter must be an integer: ex. 100286"
            )

    if team_id:
        try:
            team_id = int(str(team_id).strip())
        except ValueError:
            tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
            team_id = tapi.get_team_id(team_id.strip())

    gapi = GameAPI(int(competition_id.strip()), int(season_id.strip()))

    # Calculate the total time it takes to execute the given operation.
    from time import time
    operation_starting_time = time()

    all_documents = list(gapi.get_game_minutes_stats(
        game_id=game_id,
        team_id=team_id
    ))

    all_games = dict()

    # Collect all the result.
    all_games["Total time it takes to execute the operation"] = time() - operation_starting_time
    all_games["games"] = all_documents

    result = json_util.dumps(all_games, indent=4)

    response = Response(result, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

"""
# -----------Compare Single Match Events With Respect to Players or Teams----------------------

@games.route("/games/compare_stats", endpoint="compare match events stats")
def compare_match_events():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    player_ids = request.args.get("player")
    team_ids = request.args.get("team")
    game_id = request.args.get("game")
    event_names = request.args.get("event_names")
    time_interval = request.args.get("time_interval")
    per_90 = request.args.get("per_90")
    simplify_data = request.args.get("simplify_data")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    if game_id:
        game_id = hlp.separate_raw_string(game_id, ",")
    else:
        err.IncorrectParams(message="Game parameter can not be empty!")

    if team_ids:
        tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
        raw_team_ids = hlp.separate_raw_string(team_ids, ",")
        team_ids = list()
        for team in raw_team_ids:
            try:
                team_ids.append(int(str(team).strip().replace("t", "")))
            except ValueError:
                team_ids.append(int(tapi.getTeamUID(team.strip()).replace("t", "")))

    if player_ids:
        tapi = TeamAPI.TeamAPI(int(competition_id.strip()), int(season_id.strip()))
        raw_player_ids = hlp.separate_raw_string(player_ids, ",")
        player_ids = list()
        for player in raw_player_ids:
            try:
                player_ids.append(int(str(player).strip().replace("p", "")))
            except ValueError:
                player_ids.append(int(tapi.getPlayerUID(player.strip()).replace("p", "")))

    if event_names:
        multi_event_dict = EventAPI.EventAPI().multi_event_dict()
        raw_event_names = hlp.separate_raw_string(event_names, ",")
        event_names = list()
        for event in raw_event_names:
            if event.strip() in multi_event_dict.values():
                event_names.append(event)
            else:
                try:
                    event_names.append(multi_event_dict[event.strip()])
                except KeyError:
                    raise err.IncorrectParams(message="Example input for event_names: aerial, pass, card")

    if time_interval:
        all_time_intervals = dict()
        index = 0
        for interval in hlp.separate_raw_string(time_interval, ","):
            all_time_intervals[index] = hlp.mongodb_time_query_converter(interval, return_time_interval=False,
                                                                         return_time_query=True)
            index += 1

    if per_90:
        if hlp.convert_raw_string_into_bool(per_90):
            per_90 = {
                "before": hlp.length_of_time_interval_obtained_from_converter(all_time_intervals[0]),
                "after": hlp.length_of_time_interval_obtained_from_converter(all_time_intervals[-1])
            }

    if simplify_data:
        simplify_data = hlp.convert_raw_string_into_bool(simplify_data)

    gapi = GameAPI(int(competition_id.strip()), int(season_id.strip()))

    from src.danalyticAPI.DataRetrieving import ReadData as ml_read_filter
    import numpy as np

    for key in all_time_intervals:

        all_documents = gapi.get_match_data(
            game_ids=game_id,
            team_ids=team_ids,
            player_ids=player_ids,
            event_names=event_names,
            time_interval=all_time_intervals[key],
        )

        all_games = dict()
        all_games_list = list()

        for document in all_documents:
            all_games_list.append(document)

        # Collect all the result.
        all_games["games"] = all_games_list

        temp_dict = dict()
        for event in raw_event_names:
            temp_dict[event] = ml_read_filter.read_df_from_json_file_statistics(json_file_itself=all_games,
                                                                                event_names=event)
        all_time_intervals[key] = temp_dict

    result_html_string = "<br/> <h1> Event Statistics Compare Before and After the Certain Event </h1> <br/>"
    before_stats = all_time_intervals[0]
    after_stats = all_time_intervals[1]

    for event in raw_event_names:

        before_stats_event = before_stats[event]
        after_stats_event = after_stats[event]

        if per_90:
            if per_90["before"] and per_90["after"]:
                before_stats_event = before_stats_event.multiply(90 / per_90["before"])
                after_stats_event = after_stats_event.multiply(90 / per_90["after"])

        result_html_string += " <h2> {} Statistics Compare </h2> ".format(str(event).title())

        temp_merged_data_frame = ml_read_filter.concat_data_frames([before_stats_event, after_stats_event])

        if simplify_data:
            temp_merged_data_frame = ml_read_filter.get_rid_of_correlated_groups(temp_merged_data_frame)

        for team in set(temp_merged_data_frame.index):
            result_html_string += "<br/> <h2> {} </h2> <br/>".format(str(team).title())
            result_html_string += temp_merged_data_frame.loc[team].to_html()

            team_before_stats_event = temp_merged_data_frame.loc[team].reset_index(drop=True).iloc[0]
            team_after_stats_event = temp_merged_data_frame.loc[team].reset_index(drop=True).iloc[1]

            team_before_matrix_norm = np.linalg.norm(team_before_stats_event)
            team_after_matrix_norm = np.linalg.norm(team_after_stats_event)
            distance_between_matrices = np.linalg.norm(team_after_stats_event - team_before_stats_event)

            cosine_theta_similarity_conditions = team_after_matrix_norm != float(0) and \
                                                 team_before_matrix_norm != float(0) and \
                                                 1 < len(temp_merged_data_frame.columns)

            if cosine_theta_similarity_conditions:
                cosine_theta_similarity = np.dot(team_after_stats_event, team_before_stats_event) / \
                                          (team_after_matrix_norm * team_before_matrix_norm)
                cosine_similarity = round(float(cosine_theta_similarity*100), 6)

            result_html_string += " <br> Norm of the before matrix: " + str(team_before_matrix_norm) + " <br> "
            result_html_string += " <br> Norm of the after matrix: " + str(team_after_matrix_norm) + " <br> "
            result_html_string += " <br> Distance between matrices: " + str(distance_between_matrices) + " <br> "

            if cosine_theta_similarity_conditions:
                result_html_string += " <br> Cosine similarity percentage: %" + str(cosine_similarity) + " <br> "

    return Response(result_html_string, mimetype="application/json", status=200)

# ---------------------------------------------------
"""


# ----------------------------------------------------
@games.route(
    "/game/statistics/team/<team_name>/stat_type/<stat_type>/game_id/<game_id>",
    endpoint="game team statistics"
)
def get_team_game_stat(team_name, stat_type, game_id):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI.TeamAPI(competition_id, season_id)
    team_statistics = tapi.getTeamGamesStatisticsWithGameIDs(
        team_name, [game_id], stat_type)
    team_statistics = json.dumps(team_statistics, indent=4)
    response = Response(team_statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@games.route(
    "/game/statistics/player/<player_name>/stat_type/<stat_type>/game_id/<game_id>",
    endpoint="game player statistics"
)
def get_player_game_stat(player_name, stat_type, game_id):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI.PlayerAPI(competition_id, season_id)
    team_statistics = papi.getPlayerGamesStatisticsWithGameIDs(
        player_name, [game_id], stat_type)
    team_statistics = json.dumps(team_statistics, indent=4)
    response = Response(team_statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
