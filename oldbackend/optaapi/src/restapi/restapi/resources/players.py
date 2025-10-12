"""
@author: Cem Akpolat
@created by cemakpolat at 2020-07-24
"""

# !/usr/bin/env python
# encoding: utf-8
# https://github.com/closeio/flask-mongorest
# https://github.com/paurakhsharma/flask-rest-api-blog-series/blob/master/Part%20-%201/movie-bag/app.py
# from flask_mongoengine import MongoEngine
from src.feedAPI.PlayerAPI import PlayerAPI
from src.feedAPI.EventAPI import EventAPI
from flask import Blueprint, Response, request
from src.dbase.DBHelper import *
import json

from src.feedAPI.TeamAPI import TeamAPI
from src.restapi.restapi.resources import errors as err
from src.restapi.restapi.resources import helper as hlp
from src.dataRetrieving import readData as ml_read_filter
from bson import json_util

players = Blueprint("players", __name__)

path = "./input/"


@players.route("/players/<id>", endpoint="player")
def get_player(id):
    player = F9_Player.objects(uID=id).to_json()
    print(player)
    return Response(player, mimetype="application/json", status=200)


@players.route(
    "/statistics/aerial/player/<id>", endpoint="player aerial statistic with id"
)
def get_player_statistics_aerial(id):
    statistics = AerialEvent.objects(id=id).to_json()
    return Response(statistics, mimetype="application/json", status=200)


@players.route(
    "/statistics/players/compare", endpoint="compare player statistics", methods=["POST"]
)
def get_players_statistics_compare():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    team_players = json.loads(request.data)
    papi = PlayerAPI(competition_id, season_id)
    statistics = papi.comparePlayersEventStatistics(team_players)
    return Response(statistics, mimetype="application/json", status=200)


# -------------Get Player Personal Information------------------

# Example URL for "player personal info" request:
# http://127.0.0.1:5000/api/v1/players/personal/Josué?competition=115&season=2018
@players.route(
    "/players/personal/<player_name>",
    endpoint="player personal info"
)
def get_player_personal_info(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    papi = PlayerAPI(competition_id, season_id)
    player = list(papi.get_filtered_personal_players(query_conditions=[{"name": player_name.strip()}]))

    if player == list():
        raise err.IncorrectParams(message="Example input for player_name: Milan Lukac")
    else:
        result = dict()
        result[player_name] = player[0]
        result = json.dumps(result, indent=4)
        return Response(result, mimetype="application/json", status=200)


# -------------Get Any Event's All Statistics------------------

# Example URL for "player all statistics" request:
# http://127.0.0.1:5000/api/v1/statistics/players/Guven Yalcin
# /team/Besiktas?competition=115&season=2018&events=card, aerial
@players.route(
    "/players/statistics/<player_name>/team/<team_name>",
    endpoint="player all statistics"
)
def get_player_statistics(player_name, team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    raw_events = request.args.get("events")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    event_names = hlp.separate_raw_string(raw_events, ",")

    # The following codes will check that given parameters are all exist for the corresponding event database.
    if not hlp.check_events_existence(event_names):
        raise err.IncorrectParams(message="Example input for params: card, pass, aerial")

    papi = PlayerAPI(competition_id, season_id)
    statistics = papi.getPlayerStatistics(player_name=player_name, event_type=event_names)
    return Response(statistics, mimetype="application/json", status=200)


# -------------Get Any Event Statistics With Parameters------------------

# Example URL for "player event statistics" request:
# http://127.0.0.1:5000/api/v1/statistics/pass/Necip Uysal/Besiktas
# ?competition=115&season=2018&params=passes_total, passes_successful, passes_unsuccessful
@players.route(
    "/players/statistics/<event_name>/<player_name>/<team_name>",
    endpoint="player event statistics"
)
# The following function determines given event statistics for the given player with only desired parameters.
# Then it returns obtained information in JSON format with printing on the URL.
def get_player_event_statistics(event_name, player_name, team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    raw_params = request.args.get("params")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    # The desired parameters will be given to PlayerAPI functions in the list form.
    params = hlp.separate_raw_string(raw_params, ",")

    # The following codes will check that given parameters are all exist for the corresponding event database.
    if not EventAPI().checkEventParams(event=event_name, params=params):
        raise err.IncorrectParams(message="Example input for params: passes_total, passes_successful")

    papi = PlayerAPI(competition_id, season_id)
    statistics = papi.getEventParams(teamName=team_name, playerName=player_name, eventName=event_name, params=params)
    statistics = json.dumps(statistics, indent=4)

    return Response(statistics, mimetype="application/json", status=200)


# --------------------Compare Players--------------------------

# Example URL for "compare players" request
# http://127.0.0.1:5000/api/v1/players/compare?competition=115&season=2018&
# collections=aerial_event, card_event&params=&names=Burak Yilmaz, Bora Körk, Serginho
@players.route(
    "/players/compare",
    endpoint="compare players"
)
def compare_players():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    event_collections = request.args.get("collections")
    event_params = request.args.get("params")
    player_names = request.args.get("names")
    per90 = request.args.get("per90")
    percentile = request.args.get("percentile")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    # Preparing the all player names that we will compare.
    if player_names:
        player_names = hlp.separate_raw_string(player_names, ",")
        query_conditions_list = list()
        if player_names:
            for player_name in player_names:
                query_conditions_list.append({"name": {"$eq": player_name}})
        query_conditions = {"$or": query_conditions_list}
    else:
        raise err.IncorrectParams(message="Example input for names: Yavuz Özbakan, Serginho")

    # The desired parameters and collections will be given to PlayerAPI functions in the list form.
    if event_params:
        event_params = hlp.separate_raw_string(event_params, ",")

    if event_collections:
        event_collections = hlp.separate_raw_string(event_collections, ",")
        # The following codes will check that given parameters are all exist for the corresponding event.
        if not set(event_collections).issubset(set(list(EventAPI().getEventFieldsDict().keys()))):
            raise err.IncorrectParams(message="Example input for collection: aerial_event, pass_event, card_event")

    if per90:
        per90 = hlp.convert_raw_string_into_bool(per90)
    if percentile:
        percentile = hlp.convert_raw_string_into_bool(percentile)

    papi = PlayerAPI(competition_id, season_id)
    all_documents = papi.get_filtered_stats_players(
        event_collections=event_collections,
        query_conditions=query_conditions,
        event_params=event_params,
        per90=per90,
        percentile=percentile
    )
    result = json_util.dumps(list(all_documents), indent=4)

    return Response(result, mimetype="application/json", status=200)


# -------------Get Duplicate Player Names------------------

@players.route(
    "/players/duplicate_players",
    endpoint="get duplicate player names"
)
def get_all_duplicate_player_names():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    papi = PlayerAPI(competition_id, season_id)
    names = papi.getDuplicatePlayersName()
    result = dict()
    result["All Duplicated Players"] = names
    result = json.dumps(result, indent=4)
    return Response(result, mimetype="application/json", status=200)


# -----------------Search the Players wrt Event Parameters----------------------------

# Example URL for "player event statistics" request:
# http://127.0.0.1:5000/api/v1/players/get?competition=115&season=2018
# &collections=card_event, aerial_event&query=aerial_event.won > 15, card_event.yellow_card >= 7
# &params=card_event.yellow_card, playerName, aerial_event.won&sort=card_event.yellow_card:-1

@players.route(
    "/players/get/<personal_or_statistics>",
    endpoint="query on players"
)
def get_filtered_players(personal_or_statistics):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    team_names = request.args.get("team")
    event_collections = request.args.get("collections")
    event_params = request.args.get("params")
    query_conditions = request.args.get("query")
    sort_conditions = request.args.get("sort")
    limit = request.args.get("limit")
    input_file_name = request.args.get("file_name")
    per90 = request.args.get("per90")
    percentile = request.args.get("percentile")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    # Prepare the team_name variable.
    if team_names:
        team_names = hlp.separate_raw_string(team_names, ",")

    # The desired parameters and collections will be given to PlayerAPI functions in the list form.
    if event_params:
        event_params = hlp.separate_raw_string(event_params, ",")

    if event_collections:
        event_collections = hlp.separate_raw_string(event_collections, ",")
        # The following codes will check that given parameters are all exist for the corresponding event.
        if not set(event_collections).issubset(set(list(EventAPI().getEventFieldsDict().keys()))):
            raise err.IncorrectParams(message="Example input for collection: aerial_event, pass_event, card_event")

    # Prepare the query conditions.
    if query_conditions:
        query_conditions = hlp.mongodb_query_converter(query_conditions)

    # Prepare the sort condition of query result.
    if sort_conditions:
        sort_conditions = hlp.mongodb_sort_query_converter(sort_conditions)
        if sort_conditions is None:
            raise err.IncorrectParams(message="Example input for sort: aerial_event.won : 1")

    # Prepare the limit condition of query result.
    if limit:
        limit = hlp.mongodb_limit_query_converter(limit)
        if not limit:
            raise err.IncorrectParams(message="Example input for limit: 100")

    if per90:
        per90 = hlp.convert_raw_string_into_bool(per90)

    if percentile:
        percentile = hlp.convert_raw_string_into_bool(percentile)

    papi = PlayerAPI(competition_id, season_id)

    from time import time
    query_starting_time = time()

    resulting_data_type = personal_or_statistics.strip().lower()

    if resulting_data_type == "personal":
        all_documents = papi.get_filtered_personal_players(
            query_conditions=query_conditions,
            team_names=team_names,
            event_params=event_params,
            sort_conditions=sort_conditions,
            limit=limit
        )
    else:
        all_documents = papi.get_filtered_stats_players(
            event_collections=event_collections,
            query_conditions=query_conditions,
            team_names=team_names,
            event_params=event_params,
            sort_conditions=sort_conditions,
            limit=limit,
            per90=per90,
            percentile=percentile
        )

    filtered_players = dict()
    filtered_players_list = list()

    for temp_document in all_documents:
        filtered_players_list.append(temp_document)

    filtered_players["Total number of players satisfying the query"] = len(filtered_players_list)
    filtered_players["Total time it takes to execute the query"] = time()-query_starting_time
    filtered_players["players"] = filtered_players_list

    result = json_util.dumps(filtered_players, indent=4)

    if input_file_name:
        file_name = input_file_name
    else:
        file_name = "temp.json"

    with open(path+file_name, "w", encoding="utf8") as f:
        f.write(result)

    return Response(result, mimetype="application/json", status=200)


@players.route(
    "/players/get/general_stats",
    endpoint="query on general player stats"
)
def get_general_player_statistics():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    event_collections = request.args.get("collections")
    event_params = request.args.get("params")
    document_name = request.args.get("doc_name")
    output_file_name = request.args.get("file_name")

    # Checking that competition_id and season_id are both correctly given.
    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    # The desired parameters and collections will be given to PlayerAPI functions in the list form.
    if event_params:
        event_params = hlp.separate_raw_string(event_params, ",")

    if event_collections:
        event_collections = hlp.separate_raw_string(event_collections, ",")
        # The following codes will check that given parameters are all exist for the corresponding event.
        if not set(event_collections).issubset(set(list(EventAPI().getEventFieldsDict().keys()))):
            raise err.IncorrectParams(message="Example input for collection: aerial, pass, card")

    papi = PlayerAPI(competition_id, season_id)

    all_documents = papi.get_general_player_stats(
        event_collections=event_collections,
        params_names=event_params,
        doc_name=document_name
    )

    all_documents = hlp.get_rid_of_inner_lists(list(all_documents))

    result_dict = {"result": all_documents}
    result = json_util.dumps(result_dict, indent=4)

    if output_file_name:
        file_name = output_file_name
    else:
        file_name = "temp.json"

    with open(path+file_name, "w", encoding="utf8") as f:
        f.write(result)

    return Response(result, mimetype="application/json", status=200)

# ----------------------------------------------------


@players.route(
    "/statistics/important/players/<player_name>",
    endpoint="player important statistics"
)
def get_important_player_statistics(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     papi = PlayerAPI(competition_id, season_id)
    #     return papi.getPlayerStatistics(team_name=team_name, player_name=player_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"
    #

    papi = PlayerAPI(competition_id, season_id)
    stat_list = [["aerialEvent", ["totalDuels", "won", "lost", "wonPercentage"]],
                 ["assistEvent", ["total_assists", "intentional_assists", "assist_for_first_touch_goal",
                                  "key_passes", "keypass_for_first_touch_shot"]],
                 ["ballControlEvent"],
                 ["cardEvent", ["total_cards", "yellow_card", "second_yellow_card", "red_card"]],
                 ["duelEvent", ["total_duels", "successful_duels", "unsuccessful_duels", "duel_success_rate",
                                "duel_success_attacking_third", "duel_success_middle_third",
                                "duel_success_defending_third"]],
                 ["foulEvent", ["fouls_won", "fouls_conceded", "penalty_won", "penalty_conceded"]],
                 ["goalkeeperEvent",
                  ["clean_sheet", "goals_against", "save_percentage", "save_1on1", "saves", "penalty_faced",
                   "penalties_saved"]],
                 ["passEvent", ["passes_total", "passes_successful", "passes_unsuccessful", "pass_success_rate",
                                "total_crosses", "long_passes", "blocked_passes"]],
                 ["shotEvent", ["goals", "goals_outside_the_box", "non_penalty_goals",
                                "minutes_per_goal", "total_shots", "shots_on_target",
                                "goals_from_big_chances", "chance_missed"]],
                 ["takeOnEvent"],
                 ["touchEvent", ["total_touches", "total_tackles", "total_successful_tackles",
                                 "total_interceptions", "total_clearances", "blocked_cross"]]]


    statistics = papi.callPlayer_Fast_V4(player_name=player_name, stat_list=stat_list, get_translated=True)

    statistics2 = papi.callPlayer_percentile(player_name=player_name,
                                            stat_list=stat_list, get_translated=True)
    # print(statistics)
    # print(statistics2)
    combined_stat = dict()
    for stat in statistics:
        temp_dict = dict()
        for detailed_stat in statistics[stat]:
            temp_dict[detailed_stat] = [statistics[stat][detailed_stat], statistics2[stat][detailed_stat]]
        combined_stat[stat] = temp_dict

    combined_stat = json.dumps(combined_stat, indent=4)
    response = Response(combined_stat, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@players.route(
    "/per90/statistics/important/players/<player_name>",
    endpoint="player important per90 statistics"
)
def get_important_player_per90_statistics(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     papi = PlayerAPI(competition_id, season_id)
    #     return papi.getPlayerStatistics(team_name=team_name, player_name=player_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"
    #

    papi = PlayerAPI(competition_id, season_id)
    stat_list = [["aerialEvent", ["totalDuels", "won", "lost", "wonPercentage"]],
                        ["assistEvent", ["total_assists", "intentional_assists", "assist_for_first_touch_goal",
                                         "key_passes", "keypass_for_first_touch_shot"]],
                        ["ballControlEvent"],
                        ["cardEvent", ["total_cards", "yellow_card","second_yellow_card", "red_card"]],
                        ["duelEvent", ["total_duels", "successful_duels", "unsuccessful_duels", "duel_success_rate",
                                       "duel_success_attacking_third", "duel_success_middle_third",
                                       "duel_success_defending_third"]],
                        ["foulEvent", ["fouls_won", "fouls_conceded", "penalty_won", "penalty_conceded"]],
                        ["goalkeeperEvent", ["clean_sheet", "goals_against", "save_percentage", "save_1on1", "saves", "penalty_faced", "penalties_saved"]],
                        ["passEvent", ["passes_total", "passes_successful", "passes_unsuccessful", "pass_success_rate",
                                       "total_crosses", "long_passes", "blocked_passes"]],
                        ["shotEvent", ["goals", "goals_outside_the_box", "non_penalty_goals",
                                       "minutes_per_goal", "total_shots","shots_on_target",
                                       "goals_from_big_chances", "chance_missed"]],
                        ["takeOnEvent"],
                        ["touchEvent", ["total_touches", "total_tackles", "total_successful_tackles",
                                        "total_interceptions", "total_clearances", "blocked_cross"]]]


    statistics = papi.callPlayerPer90(player_name=player_name, stat_list=stat_list, get_translated=True)
    statistics = json.dumps(statistics, indent=4)
    response = Response(statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/important/stat_name/<stat_name>/stat_type/<stat_type>",
    endpoint="player average important statistics"
)
def get_average_player_statistics(stat_name, stat_type):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     papi = PlayerAPI(competition_id, season_id)
    #     return papi.getPlayerStatistics(team_name=team_name, player_name=player_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"
    #

    papi = PlayerAPI(competition_id, season_id)
    stat_list = [["aerialEvent", ["totalDuels", "won", "lost", "wonPercentage"]],
                        ["assistEvent", ["total_assists", "intentional_assists", "assist_for_first_touch_goal",
                                         "key_passes", "keypass_for_first_touch_shot"]],
                        ["ballControlEvent"],
                        ["cardEvent", ["total_cards", "yellow_card","second_yellow_card", "red_card"]],
                        ["duelEvent", ["total_duels", "successful_duels", "unsuccessful_duels", "duel_success_rate",
                                       "duel_success_attacking_third", "duel_success_middle_third",
                                       "duel_success_defending_third"]],
                        ["foulEvent", ["fouls_won", "fouls_conceded", "penalty_won", "penalty_conceded"]],
                        ["goalkeeperEvent", ["clean_sheet", "goals_against", "save_percentage", "save_1on1", "saves", "penalty_faced", "penalties_saved"]],
                        ["passEvent", ["passes_total", "passes_successful", "passes_unsuccessful", "pass_success_rate",
                                       "total_crosses", "long_passes", "blocked_passes"]],
                        ["shotEvent", ["goals", "goals_outside_the_box", "non_penalty_goals",
                                       "minutes_per_goal", "total_shots","shots_on_target",
                                       "goals_from_big_chances", "chance_missed"]],
                        ["takeOnEvent"],
                        ["touchEvent", ["total_touches", "total_tackles", "total_successful_tackles",
                                        "total_interceptions", "total_clearances", "blocked_cross"]]]


    statistics = papi.callSeasonAverage_Fast(stat_name=stat_name,stat_type=stat_type, stat_list=stat_list, get_translated=True)
    statistics = json.dumps(statistics, indent=4)
    response = Response(statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/position/players/<player_name>",
    endpoint="player position"
)
def get_position_player(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    position = papi.getPositionPlayer(player_name)
    position = json.dumps(position, indent=4)
    response = Response(position, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/important/players/average/<player_name>",
    endpoint="player statistics with comparison"
)
def get_important_combined_player_statistics(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     papi = PlayerAPI(competition_id, season_id)
    #     return papi.getPlayerStatistics(team_name=team_name, player_name=player_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"
    #

    papi = PlayerAPI(competition_id, season_id)
    stat_list = [["aerialEvent", ["totalDuels", "won", "lost", "wonPercentage"]],
                        ["assistEvent", ["total_assists", "intentional_assists", "assist_for_first_touch_goal",
                                         "key_passes", "keypass_for_first_touch_shot"]],
                        ["ballControlEvent"],
                        ["cardEvent", ["total_cards", "yellow_card","second_yellow_card", "red_card"]],
                        ["duelEvent", ["total_duels", "successful_duels", "unsuccessful_duels", "duel_success_rate",
                                       "duel_success_attacking_third", "duel_success_middle_third",
                                       "duel_success_defending_third"]],
                        ["foulEvent", ["fouls_won", "fouls_conceded", "penalty_won", "penalty_conceded"]],
                        ["goalkeeperEvent", ["clean_sheet", "goals_against", "save_percentage", "save_1on1", "saves", "penalty_faced", "penalties_saved"]],
                        ["passEvent", ["passes_total", "passes_successful", "passes_unsuccessful", "pass_success_rate",
                                       "total_crosses", "long_passes", "blocked_passes"]],
                        ["shotEvent", ["goals", "goals_outside_the_box", "non_penalty_goals",
                                       "minutes_per_goal", "total_shots","shots_on_target",
                                       "goals_from_big_chances", "chance_missed"]],
                        ["takeOnEvent"],
                        ["touchEvent", ["total_touches", "total_tackles", "total_successful_tackles",
                                        "total_interceptions", "total_clearances", "blocked_cross"]]]

    translate = {
        "Forward": "forward_all_players", "Midfielder": "midfielder_all_players",
        "Defender": "defender_all_players", "Goalkeeper": "goalkeeper_dominant"
    }

    statistics = papi.callPlayer_Fast_V4(player_name=player_name, stat_list=stat_list, get_translated=True)

    statistics2 = papi.callSeasonAverage_Fast(stat_name=translate[papi.getPositionPlayer(player_name)], stat_type="mean",
                                              stat_list=stat_list, get_translated=True)
    combined_stat = dict()
    for stat in statistics:
        temp_dict = dict()
        for detailed_stat in statistics[stat]:
            temp_dict[detailed_stat] = [statistics[stat][detailed_stat], statistics2[stat][detailed_stat]]
            # temp_dict[detailed_stat] = [statistics[stat][detailed_stat], 0]
        combined_stat[stat] = temp_dict

    combined_stat = json.dumps(combined_stat, indent=4)
    response = Response(combined_stat, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/stat_type/<stat_type>",
    endpoint="get sub_stats"
)
def get_sub_stat_names(stat_type):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    sub_stats = papi.get_all_sub_stat_names(stat_type)
    sub_stats = json.dumps(sub_stats, indent=4)
    response = Response(sub_stats, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/rank/player/stat_type/<stat_type>/detailed/<detailed_stat>/<limit_number>",
    endpoint="rank player"
)
def rank_players(stat_type, detailed_stat, limit_number):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    papi = PlayerAPI(competition_id, season_id)
    rank_list = papi.rankLeaguePlayers_V2(
        stat_group=stat_type,
        detailed_stat=detailed_stat,
        limit_number=int(limit_number)
    )
    result = json.dumps(rank_list, indent=4)
    response = Response(result, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/data/player/name/<player_name>",
    endpoint="personal player data"
)
def get_player_data_fast(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    tapi = TeamAPI(competition_id, season_id)

    papi = PlayerAPI(competition_id, season_id)
    team_data = tapi.get_team_data(papi.get_team_fast(player_name, True)[0])

    player_datas = papi.get_player_data_fast(player_name)
    if team_data[-1]["stat_type"] == "color_2":
        player_datas["color_1"] = team_data[-2]["stat_value"]
        player_datas["color_2"] = team_data[-1]["stat_value"]
    else:
        player_datas["color_1"] = team_data[-1]["stat_value"]
        player_datas["color_2"] = "#000000"
    player_datas = json.dumps(player_datas, indent=4)
    response = Response(player_datas, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/all/matches/player/<player_name>",
    endpoint="player matches"
)
def get_all_player_matches(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    position = papi.get_player_all_matches(player_name)
    position = json.dumps(position, indent=4)
    response = Response(position, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/statistics/essential/players/<player_name>",
    endpoint="player essential statistics"
)
def get_essential_player_statistics(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    result = []
    stat_list = [["assistEvent", ["total_assists"]],
                 ["ballControlEvent", ["caught_offside"]],
                 ["cardEvent", ["yellow_card", "second_yellow_card", "red_card"]],
                 ["foulEvent", ["fouls_conceded"]],
                 ["passEvent", ["passes_total", "pass_success_rate", "total_corners"]],
                 ["shotEvent", ["goals", "total_shots", "shots_on_target"]]]

    statistics = papi.callPlayer_Fast_V4(player_name=player_name, stat_list=stat_list, get_translated=True)
    shots = statistics["shot"]
    for s in shots:
        tmp = dict()
        tmp["stat_type"] = s
        tmp["stat_value"] = shots[s]
        result.append(tmp)

    result.append({"stat_type": "assist", "stat_value": statistics["assist"]["total_assists"]})

    passes = statistics["pass"]
    for s in passes:
        tmp = dict()
        tmp["stat_type"] = s
        tmp["stat_value"] = passes[s]
        result.append(tmp)

    result.append({"stat_type": "fouls", "stat_value": statistics["foul"]["fouls_conceded"]})

    card = statistics["card"]
    for s in card:
        tmp = dict()
        tmp["stat_type"] = s
        tmp["stat_value"] = card[s]
        result.append(tmp)

    result.append({"stat_type": "offside", "stat_value": statistics["ballControl"]["caught_offside"]})

    result = json.dumps(result, indent=4)
    response = Response(result, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/get/filtered/player/names",
    endpoint="filtered player names"
)
def get_player_filtered_names():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    time = request.args.get("time")
    team_name = request.args.get("team_name")
    position = request.args.get("position")

    papi = PlayerAPI(competition_id, season_id)
    player_list = papi.get_player_name_filtered(least_total_time=int(time),
                                              team_name=team_name,
                                              position=position)

    player_list = json.dumps(player_list, indent=4)
    response = Response(player_list, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/get/player/and/team/names",
    endpoint="player and team names"
)
def get_player_and_team_names():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    player_list = papi.get_season_all_player_and_team_name()

    player_list = json.dumps(player_list, indent=4)
    response = Response(player_list, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@players.route(
    "/get/player/all/player_names",
    endpoint="all player names"
)
def get_all_player_names():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    papi = PlayerAPI(competition_id, season_id)
    player_list = papi.get_season_all_player_name()

    player_list = json.dumps(player_list, indent=4)
    response = Response(player_list, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
