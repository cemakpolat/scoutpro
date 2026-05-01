"""
@author: Cem Akpolat
@created by cemakpolat at 2020-07-24
"""

import json
from bson import json_util
from src.feedAPI.PlayerAPI import PlayerAPI
from src.feedAPI.EventAPI import EventAPI
from flask import Blueprint, Response, request
from src.feedAPI.TeamAPI import TeamAPI
from src.restapi.restapi.resources import errors as err
from src.restapi.restapi.resources import helper as hlp

teams = Blueprint("teams", __name__)
path = "./input/"

# http://127.0.0.1:5000/api/v1/teams/Besiktas/players/Guven%20Yalcin?competition=115&season=2018


@teams.route("/teams/id/<id>", endpoint="team_with_id")
def get_team_with_id(id):
    return id


@teams.route("/teams/",  methods=["GET","POST"], endpoint="all teams")
def get_teams():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    if season_id is not None and competition_id is not None:
        papi = TeamAPI(competition_id, season_id)
        result = papi.getAllTeamNames()
        import json
        return Response(json.dumps(result), mimetype="application/json", status=200)
    else:
        return "Competition or Season Ids or both is not available!"


@teams.route("/teams/<name>",  methods=["GET","POST"], endpoint="team_with_name")
def get_team_with_name(name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    if season_id is not None and competition_id is not None:
        papi = TeamAPI(competition_id, season_id)
        result = papi.getTeamData(teamName=name)
        return Response(result, mimetype="application/json", status=200)
    else:
        return "Competition or Season Ids or both is not available!"


@teams.route("teams/<team_name>/players/<player_name>", endpoint="player")
def get_team_players(player_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    if season_id is not None and competition_id is not None and season_id !="" and competition_id !="":
        papi = PlayerAPI(competition_id, season_id)
        result = papi.getPlayerStatistics(player_name=player_name)
        return Response(result, mimetype="application/json", status=200)
    else:
        return json.dumps({
            "error": {
                "title":"Missing competition or season id",
                "detail": "Competition or Season Ids or both is not available!",
                # "status":404 /
                # "type": "OAuthException",
                # "code": 191
            }})


@teams.route("/teams/<name>/players/names", endpoint="team players names")
def get_team_playersnames(name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    if season_id is not None and competition_id is not None:
        team_api = TeamAPI(competition_id, season_id)
        result = team_api.getTeamAllPlayers(teamName=name)
        return Response(result, mimetype="application/json", status=200)
    else:
        return "Competition or Season Ids or both is not available!"


# -------------Get All Player Names in a Team------------------

@teams.route(
    "/teams/<team_name>/all_players",
    endpoint="get all player names"
)
def get_all_player_names(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    tapi = TeamAPI(competition_id, season_id)
    names = tapi.get_all_players_name(team_name=team_name.strip())
    result = dict()
    result[team_name] = names
    result = json.dumps(result, indent=4)
    return Response(result, mimetype="application/json", status=200)


# ----------Get All Players Personal Info in a Team------------------

@teams.route(
    "/teams/<team_name>/all_info",
    endpoint="get all players info"
)
def get_all_player_names(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    tapi = TeamAPI(competition_id, season_id)
    info = tapi.get_all_personal_info(team_name=team_name.strip())
    result = dict()
    result[team_name] = info
    result = json_util.dumps(result, indent=4)

    return Response(result, mimetype="application/json", status=200)


# ----------Get All Played Match Info of a Team------------------

@teams.route(
    "/teams/<team_name>/all_match",
    endpoint="get all match info"
)
def get_all_player_names(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    converter_bool = request.args.get("convert_references")

    if season_id is None or competition_id is None or season_id == "" or competition_id == "":
        raise err.MissingParams()

    if converter_bool.strip().lower() in ["1", "one", "true", "ok"]:
        converter_bool = True
    else:
        converter_bool = False

    tapi = TeamAPI(competition_id, season_id)
    info = tapi.get_all_match_info(team_name=team_name.strip(), convert_reference_ids=converter_bool)
    result = dict()
    result[team_name] = info
    result = json_util.dumps(result, indent=4)
    return Response(result, mimetype="application/json", status=200)


# -----------------Search the Teams wrt Event Parameters----------------------------

@teams.route("/teams/get", endpoint="query on teams")
def get_filtered_teams():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")
    event_collections = request.args.get("collections")
    event_params = request.args.get("params")
    query_conditions = request.args.get("query")
    sort_conditions = request.args.get("sort")
    limit = request.args.get("limit")
    input_file_name = request.args.get("file_name")
    percentile = request.args.get("percentile")

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
        if limit is None:
            raise err.IncorrectParams(message="Example input for limit: 100")

    if percentile:
        percentile = hlp.convert_raw_string_into_bool(percentile)

    tapi = TeamAPI(competition_id, season_id)

    # Calculate the total time it takes to execute the given query.
    from time import time
    query_starting_time = time()

    # Execute the query.
    all_documents = tapi.get_filtered_stats_teams(
        event_collections=event_collections,
        query_conditions=query_conditions,
        event_params=event_params,
        sort_conditions=sort_conditions,
        limit=limit,
        percentile=percentile
        )

    filtered_teams = dict()
    filtered_teams_list = list()

    for document in all_documents:
        filtered_teams_list.append(document)

    # Collect all the result.
    filtered_teams["Total number of teams satisfying the query"] = len(filtered_teams_list)
    filtered_teams["Total time it takes to execute the query"] = time()-query_starting_time
    filtered_teams["teams"] = filtered_teams_list

    result = json_util.dumps(filtered_teams, indent=4)

    # Save the query result as a JSON file.
    if input_file_name:
        file_name = input_file_name
    else:
        file_name = "temp.json"

    with open(path+file_name, "w", encoding="utf8") as f:
        f.write(result)

    return Response(result, mimetype="application/json", status=200)


@teams.route(
    "/teams/get/general_stats",
    endpoint="query on general team stats"
)
def get_general_team_statistics():
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

    papi = TeamAPI(competition_id, season_id)

    all_documents = papi.get_general_team_stats(
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

@teams.route(
    "/statistics/important/teams/<team_name>",
    endpoint="team important statistics"
)
def get_important_team_statistics(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     tapi = TeamAPI(competition_id, season_id)
    #     return tapi.getPlayerStatistics(team_name=team_name, team_name=team_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"


    tapi = TeamAPI(competition_id, season_id)
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


    statistics = tapi.callTeam(team_name=team_name, stat_list=stat_list, get_translated=True)
    statistics = json.dumps(statistics, indent=4)
    response = Response(statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@teams.route(
    "/statistics/essential/teams/<team_name>",
    endpoint="team essential statistics"
)
def get_essential_team_statistics(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
    result = []
    stat_list = [["assistEvent", ["total_assists"]],
                 ["ballControlEvent", ["caught_offside"]],
                 ["cardEvent", ["yellow_card", "second_yellow_card", "red_card"]],
                 ["foulEvent", ["fouls_conceded"]],
                 ["goalkeeperEvent", ["clean_sheet", "goals_against"]],
                 ["passEvent", ["passes_total", "pass_success_rate", "total_corners"]],
                 ["shotEvent", ["goals", "total_shots", "shots_on_target"]]]

    statistics = tapi.callTeam(team_name=team_name, stat_list=stat_list, get_translated=True)
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

    gk = statistics["goalkeeper"]
    for s in gk:
        tmp = dict()
        tmp["stat_type"] = s
        tmp["stat_value"] = gk[s]
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


@teams.route(
    "/statistics/important/teams/stat_name/<stat_name>/stat_type/<stat_type>",
    endpoint="team average important statistics"
)
def get_average_team_statistics(stat_name, stat_type):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
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


    statistics = tapi.callTeamSeasonAverage(
        stat_name=stat_name, stat_type=stat_type,
        stat_list=stat_list, get_translated=True
    )
    statistics = json.dumps(statistics, indent=4)
    response = Response(statistics, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@teams.route(
    "/all/matches/teams/<team_name>",
    endpoint="team matches"
)
def get_all_team_matches(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(int(competition_id), int(season_id))
    position = tapi.get_team_matches(team_name)
    position = json.dumps(position, indent=4)
    response = Response(position, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@teams.route(
    "/statistics/important/teams/average/<team_name>",
    endpoint="team statistics with comparison"
)
def get_important_team_statistics(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    # if season_id is not None and competition_id is not None:
    #     tapi = TeamAPI(competition_id, season_id)
    #     return tapi.getPlayerStatistics(team_name=team_name, team_name=team_name)
    # else:
    #     return "Competition or Season Ids or both is not available!"
    #

    tapi = TeamAPI(competition_id, season_id)
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


    statistics = tapi.callTeam(team_name=team_name, stat_list=stat_list, get_translated=True)

    statistics2 = tapi.callTeamSeasonAverage(stat_name="all_teams", stat_type="mean",
                                              stat_list=stat_list, get_translated=True)
    print(statistics2)
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

@teams.route(
    "/statistics/stat_type/<stat_type>",
    endpoint="get sub_stats"
)
def get_sub_stat_names(stat_type):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
    sub_stats = tapi.get_all_sub_stat_names(stat_type)
    sub_stats = json.dumps(sub_stats, indent=4)
    response = Response(sub_stats, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@teams.route(
    "/statistics/rank/team/stat_type/<stat_type>/detailed/<detailed_stat>/<limit_number>",
    endpoint="rank team"
)
def rank_teams(stat_type, detailed_stat, limit_number):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
    rank_list = tapi.rankLeagueTeams(stat_type, detailed_stat, int(limit_number)   , True)
    rank_list = json.dumps(rank_list, indent=4)
    response = Response(rank_list, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@teams.route(
    "/teams/general/data/team_name/<team_name>",
    endpoint="team general data"
)
def get_all_team_matches(team_name):
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
    team_data = tapi.get_team_data(team_name)
    team_data = json.dumps(team_data, indent=4)
    response = Response(team_data, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@teams.route(
    "/get/team/all/team_names",
    endpoint="all team names"
)
def get_all_team_names():
    competition_id = request.args.get("competition")
    season_id = request.args.get("season")

    tapi = TeamAPI(competition_id, season_id)
    player_list = tapi.get_season_team_name();

    player_list = json.dumps(player_list, indent=4)
    response = Response(player_list, mimetype="application/json", status=200)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response