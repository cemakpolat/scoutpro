"""
Author: Cem Akpolat

"""
import sys

sys.path.append("..")  # Adds higher directory to python modules path.
import requests
from src.restapi import APIHelpers
from src.events import Constructor
import json
import os
import jsonpickle
import time
from src.utils.Utils import get_src_path
from src.utils import config


url = config.url
config_competition_id = config.competition_id
config_season_id = config.season_id
username = config.username
password = config.password
debug = False
API = APIHelpers


class Feeds:
    f1 = "f1"
    f9 = "f9"
    f24 = "f24"
    f40 = "f40"
    feed1 = "feed1"
    feed9 = "feed9"
    feed24 = "feed24"
    feed40 = "feed40"
    feed124 = "feed124"
    feed130 = "feed130"
    feed140 = "feed140"
    feed340 = "feed340"
    feed1DB = "feed1"
    feed9DB = "feed9"
    feed24DB = "feed24"
    feed40DB = "feed40"
    feedConfigs = "feedConfigs"


# Check the codes in https://www.programiz.com/python-programming/json
def getFeed(
        feed_name: str,
        competition_id: int,
        season_id: int,
        game_id: int = None
):
    if feed_name == "feed40":
        feed_name = "f40"
    elif feed_name == "feed1":
        feed_name = "f1"
    elif feed_name == "feed9":
        feed_name = "f9"
    elif feed_name == "feed24":
        feed_name = "f24"
    path1 = get_src_path(
        f"\\src\\data\\feeds\\{competition_id}\\{season_id}\\"
    )
    path2 = get_src_path(
        f"\\src\\data\\feeds\\{season_id}\\{competition_id}\\"
    )
    filename1 = f"{feed_name}_{competition_id}_{season_id}"
    filename2 = f"{feed_name}_{season_id}_{competition_id}"
    parsed_data = dict()
    possible_paths = [
        path1,
        path2
    ]
    possible_file_names = [
        filename1,
        filename2
    ]
    if game_id is not None:
        for index, file_name in enumerate(possible_file_names):
            file_name += f"_{game_id}"
            possible_file_names[index] = file_name
    objective = None
    for path in possible_paths:
        if os.path.exists(path):
            for filename in possible_file_names:
                file = os.path.join(path, filename)
                if os.path.isfile(file):
                    objective = file
                    break
        if objective is not None:
            break
    if objective is None:
        print(
            "Data could not be found in local folder."
            "Please make sure that the data exists in"
            "the one of the following directories: "
        )
        for index, path in enumerate(possible_paths):
            print(
                f"-{index}) {path}"
            )
    else:
        try:
            with open(objective) as f:
                parsed_data = json.load(f)
        except IOError:
            print(
                "File could not be read, please check that the "
                f"data could be parsed in JSON form: {objective}"
            )
    return parsed_data

def getFeedFromOpta(feedName, competition, season_id, gameId=None):
    if debug is False:  # this is not used until now
        URL = url
        if Feeds.feed1 in feedName:
            URL = (
                config.url
                + "feed_type="
                + Feeds.f1
                + "&competition="
                + str(competition)
                + "&season_id="
                + str(season_id)
            )
        elif Feeds.feed9 in feedName:
            print("feed9", gameId)
            URL = (
                config.url24
                + "game_id="
                + str(gameId)
                + "&feed_type="
                + Feeds.f9
                + "&competition="
                + str(competition)
                + "&season_id="
                + str(season_id)
            )
        elif Feeds.feed24 in feedName:
            print("feed24", gameId)
            gameId = gameId.replace("g", "")
            URL = (
                config.url24
                + "game_id="
                + str(gameId)
                + "&feed_type="
                + Feeds.f24
                + "&competition="
                + str(competition)
                + "&season_id="
                + str(season_id)
            )
        elif Feeds.feed40 in feedName:
            URL = (
                config.url
                + "feed_type="
                + Feeds.f40
                + "&competition="
                + str(competition)
                + "&season_id="
                + str(season_id)
            )
        else:
            print("Feed doesn't exist!")
            return

        URL = URL + "&user=" + username + "&psw=" + password + "&json"

        PARAMS = {}
        data = requests.get(url=URL, params=PARAMS)

        return data.json()
    else:
        print("debug mode is enabled, we need to read file")


# Parsing methods
def parseCompetitionData(data):
    competition = API.Competition(
        data["Country"], data["Name"], data["@attributes"]["uID"]
    )
    stats = []
    for key in data["Stat"]:
        stats.append(API.Stat(key["@value"], key["@attributes"]["Type"]))
    competition.setFeature("Stat", stats)
    return competition


def parseTeams(teamData):
    teams = []
    for data in teamData:
        team = API.Team(data["Name"], data["@attributes"]["uID"])
        if "Country" in data:
            team.setFeature("Country", data["Country"])
        if "Player" in data:
            players = []
            for key in data["Player"]:
                known = None

                if "Known" in key["PersonName"]:
                    known = key["PersonName"]["Known"]
                players.append(
                    API.Player(key["@attributes"]["Position"])
                    .setFeature("uID", key["@attributes"]["uID"])
                    .setFeature("First", key["PersonName"]["First"])
                    .setFeature("Last", key["PersonName"]["Last"])
                    .setFeature("Known", known)
                )

            team.setFeature("Player", players)

        if "Kit" in data:
            kit = API.Kit(
                data["Kit"]["@attributes"]["id"],
                data["Kit"]["@attributes"]["colour1"],
                data["Kit"]["@attributes"]["type"],
            )
            if "colour2" in data["Kit"]["@attributes"]:
                kit.setSecondColour(data["Kit"]["@attributes"]["colour2"])
            team.setFeature("Kit", kit)

        if "TeamOfficial" in data:
            if isinstance(data["TeamOfficial"], list):
                officials = []
                for official in data["TeamOfficial"]:
                    officials.append(
                        API.TeamOfficial(
                            official["PersonName"]["First"],
                            official["PersonName"]["Last"],
                            official["@attributes"]["Type"],
                            official["@attributes"]["uID"],
                        )
                    )
                # team officials
                team.setFeature("TeamOfficial", officials)
            elif isinstance(data["TeamOfficial"], dict):
                team.setFeature(
                    "TeamOfficial",
                    API.TeamOfficial(
                        data["TeamOfficial"]["PersonName"]["First"],
                        data["TeamOfficial"]["PersonName"]["Last"],
                        data["TeamOfficial"]["@attributes"]["Type"],
                        data["TeamOfficial"]["@attributes"]["uID"],
                    ),
                )
        teams.append(team)
    return teams


def parseMatchInfo(item):
    minfo = API.MatchInfo(item["MatchInfo"]["Date"])
    if "TZ" in item["MatchInfo"]:
        minfo.setFeature("TZ", item["MatchInfo"]["TZ"])
    if "Result" in item["MatchInfo"]:
        result = API.Result(item["MatchInfo"]["Result"]["@attributes"]["Type"])
        if "Winner" in item["MatchInfo"]["Result"]["@attributes"]:
            result.setWinner(item["MatchInfo"]["Result"]["@attributes"]["Winner"])
        minfo.setResult(result)

    mitemp = item["MatchInfo"]["@attributes"]
    minfo.setFeature("MatchType", mitemp["MatchType"]).setFeature(
        "Period", mitemp["Period"]
    )

    if "MatchDay" in mitemp:
        minfo.setFeature("MatchDay", mitemp["MatchDay"])
    if "Venue_id" in mitemp:
        minfo.setFeature("Venue_id", mitemp["Venue_id"])
    if "MatchWinner" in mitemp:
        minfo.setFeature("MatchWinner", mitemp["MatchWinner"])
    if "PlayerRef" in mitemp:
        minfo.setFeature("PlayerRef", mitemp["PlayerRef"])
    if "Status" in mitemp:
        minfo.setFeature("Status", mitemp["Status"])
    if "TeamRef" in mitemp:
        minfo.setFeature("TeamRef", mitemp["TeamRef"])
    if "TimeStamp" in mitemp:
        minfo.setFeature("TimeStamp", mitemp["TimeStamp"])
    if "VAR_Reason" in mitemp:
        minfo.setFeature("VAR_Reason", mitemp["VAR_Reason"])
    if "Leg" in mitemp:
        minfo.setFeature("Leg", mitemp["Leg"])
    if "FirstLegId" in mitemp:
        minfo.setFeature("FirstLegId", mitemp["FirstLegId"])
    if "LegWinner" in mitemp:
        minfo.setFeature("LegWinner", mitemp["LegWinner"])
    if "NextMatch" in mitemp:
        minfo.setFeature("NextMatch", mitemp["NextMatch"])
    if "NextMatchLoser" in mitemp:
        minfo.setFeature("NextMatchLoser", mitemp["NextMatchLoser"])
    if "RoundNumber" in mitemp:
        minfo.setFeature("RoundNumber", mitemp["RoundNumber"])
    if "RoundType" in mitemp:
        minfo.setFeature("RoundType", mitemp["RoundType"])
    if "GroupName" in mitemp:
        minfo.setFeature("GroupName", mitemp["GroupName"])
    if "GameWinner" in mitemp:
        minfo.setFeature("GameWinner", mitemp["GameWinner"])
    if "GameWinnerType" in mitemp:
        minfo.setFeature("GameWinnerType", mitemp["GameWinnerType"])
    if "Timestamp" in mitemp:
        minfo.setFeature("Timestamp", mitemp["Timestamp"])

    return minfo


def parseMatchOfficials(item):
    if "OfficialName" in item:
        if "MatchOfficials" in item:
            officials = []
            for official in item["MatchOfficials"]["MatchOfficial"]:
                officials.append(
                    API.MatchOfficial(
                        official["OfficialName"]["First"],
                        official["OfficialName"]["Last"],
                        official["@attributes"]["uID"],
                        official["OfficialData"]["OfficialRef"]["@attributes"]["Type"],
                    )
                )
            return officials
        elif "MatchOfficial" in item:
            mofffical = API.MatchOfficial(
                item["MatchOfficial"]["OfficialName"]["First"],
                item["MatchOfficial"]["OfficialName"]["Last"],
                item["MatchOfficial"]["@attributes"]["uID"],
                item["MatchOfficial"]["OfficialData"]["OfficialRef"]["@attributes"][
                    "Type"
                ],
            )
        return mofffical
    else:
        officials = []
        if "MatchOfficials" in item:
            for official in item["MatchOfficials"]["MatchOfficial"]:
                officials.append(
                    API.MatchOfficial(
                        official["@attributes"]["FirstName"],
                        official["@attributes"]["LastName"],
                        official["@attributes"]["uID"],
                        official["@attributes"]["Type"],
                    )
                )
            return officials
        elif "MatchOfficial" in item:
            mofffical = API.MatchOfficial(
                item["MatchOfficial"]["OfficialName"]["First"],
                item["MatchOfficial"]["OfficialName"]["Last"],
                item["MatchOfficial"]["@attributes"]["uID"],
                item["MatchOfficial"]["OfficialData"]["OfficialRef"]["@attributes"][
                    "Type"
                ],
            )
            return mofffical


def parseAssistantOfficials(data):
    officals = []
    for official in data["AssistantOfficials"]["AssistantOfficial"]:
        officals.append(
            API.AssistantOfficial(
                official["@attributes"]["FirstName"],
                official["@attributes"]["LastName"],
                official["@attributes"]["Type"],
                official["@attributes"]["uID"],
            )
        )
    return officals


def parseStats(item):
    item = item["Stat"]
    if isinstance(item, list):
        stats = []
        for stat in item:
            stats.append(API.Stat(stat["@value"], stat["@attributes"]["Type"]))
        return stats
    elif isinstance(item, dict):
        statItem = API.Stat(item["@value"], item["@attributes"]["Type"])
        return statItem


def parseTeamData(item):
    teams = []
    for tdata in item["TeamData"]:

        tattrs = tdata["@attributes"]

        teamData = API.TeamData(tattrs["TeamRef"])

        if "Score" in tattrs:
            teamData.setFeature("Score", tattrs["Score"])
        if "Side" in tattrs:
            teamData.setFeature("Side", tattrs["Side"])
        if "HalfScore" in tattrs:
            teamData.setFeature("HalfScore", tattrs["HalfScore"])

        # score
        if "NinetyScore" in tdata:
            teamData.setFeature("NinetyScore", tattrs["NinetyScore"])
        if "ExtraScore" in tdata:
            teamData.setFeature("ExtraScore", tattrs["ExtraScore"])
        if "PenaltyScore" in tdata:
            teamData.setFeature("PenaltyScore", tattrs["PenaltyScore"])

        # booking
        if "Booking" in tdata:
            bookings = []
            for booking in tdata["Booking"]:
                if isinstance(booking, dict):
                    sTemp = booking["@attributes"]
                    bookingobj = API.Booking()
                    bookingobj.setFeature("EventID", sTemp["EventID"]).setFeature(
                        "EventNumber", sTemp["EventNumber"]
                    ).setFeature("Period", sTemp["Period"]).setFeature(
                        "Reason", sTemp["Reason"]
                    ).setFeature(
                        "Card", sTemp["Card"]
                    ).setFeature(
                        "CardType", sTemp["CardType"]
                    ).setFeature(
                        "uID", sTemp["uID"]
                    )
                    if "Sec" in sTemp:
                        bookingobj.setFeature("Sec", sTemp["Sec"])
                    if "Min" in sTemp:
                        bookingobj.setFeature("Min", sTemp["Min"])
                    if "PlayerRef" in sTemp:
                        bookingobj.setFeature("PlayerRef", sTemp["PlayerRef"])
                    if "TimeStamp" in sTemp:
                        bookingobj.setFeature("TimeStamp", sTemp["TimeStamp"])

                    bookings.append(bookingobj)

            # add to team data
            teamData.setBooking(bookings)

        # playerlineup

        if "PlayerLineUp" in tdata:
            mplayer = []
            for mplayerStat in tdata["PlayerLineUp"]["MatchPlayer"]:
                mp = API.MatchPlayer(
                    mplayerStat["@attributes"]["PlayerRef"],
                    mplayerStat["@attributes"]["Position"],
                    mplayerStat["@attributes"]["ShirtNumber"],
                    mplayerStat["@attributes"]["Status"],
                )
                if "Captain" in mplayerStat["@attributes"]:
                    mp.setCaptain(mplayerStat["@attributes"]["Captain"])

                stats = []
                if isinstance(mplayerStat["Stat"], list):
                    for stat in mplayerStat["Stat"]:
                        if stat["@attributes"] != None:
                            type = stat["@attributes"]["Type"]
                            value = stat["@value"]
                            stats.append(API.Stat(value, type))
                    mp.setStat(stats)
                elif isinstance(mplayerStat["Stat"], dict):
                    stat = mplayerStat["Stat"]
                    mp.setStat(API.Stat(stat["@value"], stat["@attributes"]["Type"]))
                mplayer.append(mp)

                # add to team data
                teamData.setFeature("PlayerLineUp", mplayer)

        # stats
        if "Stat" in tdata:
            if isinstance(tdata["Stat"], list):
                tdStats = []
                for stat in tdata["Stat"]:
                    sattr = stat["@attributes"]
                    statforTeam = API.TeamStat(stat["@value"], sattr["Type"])

                    if "SH" in sattr and "FH" in sattr:
                        statforTeam.setFeature("SH", stat["@attributes"]["SH"])
                        statforTeam.setFeature("FH", stat["@attributes"]["FH"])

                    tdStats.append(statforTeam)
                # add to team data
                teamData.setStats(tdStats)
            elif isinstance(tdata["Stat"], dict):
                stat = tdata["Stat"]
                sattr = stat["@attributes"]
                # the following must be single
                statforTeam = API.TeamStat(stat["@value"], sattr["Type"])

                if "SH" in sattr and "FH" in sattr:
                    statforTeam.setFeature("SH", stat["@attributes"]["SH"])
                    statforTeam.setFeature("FH", stat["@attributes"]["FH"])

                # add to team data
                teamData.setStats(statforTeam)

        # substitution

        if "Substitution" in tdata:
            substitutions = []
            for subs in tdata["Substitution"]:
                if isinstance(subs, dict):
                    sTemp = subs["@attributes"]
                    s = API.Substitution(
                        sTemp["EventID"],
                        sTemp["EventNumber"],
                        sTemp["Period"],
                        sTemp["TimeStamp"],
                        sTemp["uID"],
                    )
                    if "Reason" in sTemp:
                        s.setFeature("Reason", sTemp["Reason"])
                    if "SubOn" in sTemp:
                        s.setFeature("SubOn", sTemp["SubOn"])
                    if "SubOff" in sTemp:
                        s.setFeature("SubOff", sTemp["SubOff"])
                    if "SubstitutePosition" in sTemp:
                        s.setFeature("SubstitutePosition", sTemp["SubstitutePosition"])
                    if "Retired" in sTemp:
                        s.setFeature("Retired", sTemp["Retired"])
                    if "Time" in sTemp:
                        s.setFeature("Time", sTemp["Time"])
                    if "Min" in sTemp:
                        s.setFeature("Min", sTemp["Min"])
                    if "Sec" in sTemp:
                        s.setFeature("Sec", sTemp["Sec"])
                    substitutions.append(s)
            # add to team data
            teamData.setSubstitution(substitutions)

        # goals
        if "Goal" in tdata:

            if isinstance(tdata["Goal"], list):
                # print("array", tdata["Goal"])
                goals = []
                for goal in tdata["Goal"]:
                    g = None
                    if "@attributes" in goal:
                        gTemp = goal["@attributes"]
                        g = API.Goal()
                        g.setFeature("Period", gTemp["Period"]).setFeature(
                            "PlayerRef", gTemp["PlayerRef"]
                        ).setFeature("Type", gTemp["Type"])

                        if "EventID" in gTemp:
                            g.setFeature("EventID", gTemp["EventID"])
                        if "EventNumber" in gTemp:
                            g.setFeature("EventNumber", gTemp["EventNumber"])
                        if "Min" in gTemp:
                            g.setFeature("Min", gTemp["Min"])
                        if "Sec" in gTemp:
                            g.setFeature("Sec", gTemp["Sec"])
                        if "TimeStamp" in gTemp:
                            g.setFeature("TimeStamp", gTemp["TimeStamp"])
                        if "Time" in gTemp:
                            g.setFeature("Time", gTemp["Time"])
                        if "uID" in gTemp:
                            g.setFeature("uID", gTemp["uID"])

                    if "Assist" in goal:
                        assist = API.Assist(goal["Assist"]["@attributes"])
                        g.setAssist(assist)
                    goals.append(g)

                teamData.setGoals(goals)
            elif isinstance(tdata["Goal"], dict):
                # print("single", tdata["Goal"])
                g = None
                goal = tdata["Goal"]
                if "@attributes" in goal:
                    gTemp = goal["@attributes"]
                    g = API.Goal()
                    g.setFeature("Period", gTemp["Period"]).setFeature(
                        "PlayerRef", gTemp["PlayerRef"]
                    ).setFeature("Type", gTemp["Type"])

                    if "EventID" in gTemp:
                        g.setFeature("EventID", gTemp["EventID"])
                    if "EventNumber" in gTemp:
                        g.setFeature("EventNumber", gTemp["EventNumber"])
                    if "Min" in gTemp:
                        g.setFeature("Min", gTemp["Min"])
                    if "Sec" in gTemp:
                        g.setFeature("Sec", gTemp["Sec"])
                    if "TimeStamp" in gTemp:
                        g.setFeature("TimeStamp", gTemp["TimeStamp"])
                    if "Time" in gTemp:
                        g.setFeature("Time", gTemp["Time"])
                    if "uID" in gTemp:
                        g.setFeature("uID", gTemp["uID"])

                if "Assist" in goal:
                    assist = API.Assist(goal["Assist"]["@attributes"])
                    if assist:
                        g.setAssist(assist)
                teamData.setGoals(g)

        teams.append(teamData)

    return teams


def parseVARData(data):
    if "VARData" in data:
        vData = data["VARData"]
        if isinstance(vData, list):  # Feed1
            varDataList = []
            for item in vData:
                temp = item["VAREvent"]["@attributes"]
                varData = API.VARData(
                    temp["Decision"],
                    temp["EventID"],
                    temp["EventNumber"],
                    temp["Min"],
                    temp["Outcome"],
                    temp["Period"],
                    temp["PlayerRef"],
                    temp["Reason"],
                    temp["Sec"],
                    temp["TeamRef"],
                )
                varDataList.append(varData)
            return varDataList
        elif isinstance(vData, dict):
            vevent = vData["VAREvent"]
            if isinstance(vevent, list):  # Feed1
                varDataList = []
                for item in vevent:
                    temp = item["@attributes"]
                    varData = API.VARData(
                        temp["Decision"],
                        temp["EventID"],
                        temp["EventNumber"],
                        temp["Min"],
                        temp["Outcome"],
                        temp["Period"],
                        temp["PlayerRef"],
                        temp["Reason"],
                        temp["Sec"],
                        temp["TeamRef"],
                    )
                    varDataList.append(varData)
                return varDataList
            elif isinstance(vevent, dict):
                temp = vData["@attributes"]
                varData = API.VARData(
                    temp["Decision"],
                    temp["EventID"],
                    temp["EventNumber"],
                    temp["Min"],
                    temp["Outcome"],
                    temp["Period"],
                    temp["PlayerRef"],
                    temp["Reason"],
                    temp["Sec"],
                    temp["TeamRef"],
                )
                return varData
    else:
        return None


def parseMatchData(data):
    all_res = 0
    if isinstance(data, list):  # Feed1
        matchDataList = []
        for item in data:
            matchData = API.MatchData()
            minfo = parseMatchInfo(item)
            if "MatchOfficials" in item or "MatchOfficial" in item:
                mofficials = parseMatchOfficials(item)
                matchData.setFeature("MatchOfficials", mofficials)
            stats = parseStats(item)
            teams = parseTeamData(item)

            for team in teams:
                if team.goals:
                    try:
                        all_res += len(team.goals)
                    except:
                        # print(team.goals)
                        all_res+=1
            # print(all_res)

            attrs = item["@attributes"]
            matchData.setFeature("MatchInfo", minfo).setFeature(
                "Stat", stats
            ).setFeature("TeamData", teams).setFeature(
                "timing_id", attrs["timing_id"]
            ).setFeature(
                "timestamp_accuracy_id", attrs["timestamp_accuracy_id"]
            ).setFeature(
                "detail_id", attrs["detail_id"]
            ).setFeature(
                "last_modified", attrs["last_modified"]
            ).setFeature(
                "uID", attrs["uID"]
            )
            matchDataList.append(matchData)
        return matchDataList

    elif isinstance(data, dict):  # Feed9

        matchData = API.MatchData()
        minfo = parseMatchInfo(data)  # match info

        if "MatchOfficials" in data or "MatchOfficial" in data:
            mofficials = parseMatchOfficials(data)
            #print(mofficials)
            matchData.setFeature("MatchOfficials", mofficials)
        else:
            matchData.setFeature("MatchOfficials", [])

        assistants = parseAssistantOfficials(data)  # assistant officials
        stats = parseStats(data)  # stats
        varData = parseVARData(data)  # VAR data
        teamData = parseTeamData(data)  # team data

        matchData.setFeature("AssistantOfficials", assistants).setFeature(
            "Stat", stats
        ).setFeature("TeamData", teamData).setFeature("MatchInfo", minfo).setFeature(
            "VARData", varData
        )

        if "@attributes" in data:
            attrs = data["@attributes"]
            matchData.setFeature("timing_id", attrs["timing_id"]).setFeature(
                "timestamp_accuracy_id", attrs["timestamp_accuracy_id"]
            ).setFeature("last_modified", attrs["last_modified"]).setFeature(
                "uID", attrs["uID"]
            )

        return matchData


def parseTeam(data):
    # Team Data
    teams = []
    teamData = data["SoccerFeed"]["SoccerDocument"]["Team"]
    for td in teamData:
        team = API.Team(td["Name"], td["@attributes"]["uID"])
        attr = td["@attributes"]
        if "official_club_name" in attr:
            team.setFeature("official_club_name", attr["official_club_name"])

        team.setFeature("country", attr["country"]).setFeature(
            "country_id", attr["country_id"]
        ).setFeature("country_iso", attr["country_iso"]).setFeature(
            "region_id", attr["region_id"]
        ).setFeature(
            "region_name", attr["region_name"]
        )

        if "short_club_name" in attr:
            team.setFeature("short_club_name", attr["short_club_name"])
        if "Founded" in td:
            team.setFeature("Founded", td["Founded"])

        team.setFeature("SYMID", td["SYMID"]).setFeature(
            "Player", parsePlayer(td)
        ).setFeature("Stadium", parseStadium(td)).setFeature(
            "Kit", parseKits(td)
        ).setFeature(
            "TeamOfficial", parseTeamOfficial(td)
        )

        teams.append(team)
    return teams


def parsePlayer(td):
    players = []
    if "Player" in td:
        for p in td["Player"]:
            try:
                if "uID" in p["@attributes"]:  # check uid is in the p
                    player = API.Player(p["Position"])
                    player.setFeature("Name", p["Name"])
                    player.setFeature("uID", p["@attributes"]["uID"])
                    stats = []
                    if isinstance(p["Stat"], list):
                        for st in p["Stat"]:
                            stat = API.Stat(st["@value"], st["@attributes"]["Type"])
                            stats.append(stat)
                    elif isinstance(player["Stat"], dict):
                        stat = API.Stat(
                            p["Stat"]["@value"], p["Stat"]["@attributes"]["Type"]
                        )
                        stats.append(stat)
                    player.setFeature("Stat", stats)
                    players.append(player)
                else:
                    print("uid is not available")
            except (KeyError, TypeError):
                continue
    return players


def parsePlayerChanges(data):
    p_changes = []
    pc_team = data["SoccerFeed"]["SoccerDocument"]["PlayerChanges"]["Team"]
    for t in pc_team:
        team = API.Team(t["Name"], t["@attributes"]["uID"])
        # Assign the players
        team.setFeature(feature="Player", value=parsePlayer(t))
        # Assign the team officials player
        team.setFeature(feature="TeamOfficial", value=parseTeamOfficial(t))
        # Assign the UID
        team.setFeature(feature="uID", value=t["@attributes"]["uID"])
        p_changes.append(team)
    return p_changes


def parseStadium(td):
    stadium = API.Stadium(td["Stadium"]["Name"], td["Stadium"]["@attributes"]["uID"])
    if "Capacity" in td["Stadium"]:
        stadium.setCapacity(td["Stadium"]["Capacity"])
    return stadium


def parseKits(td):
    kits = []
    all_kits = None
    if "TeamKits" in td:
        all_kits = td["TeamKits"]["Kit"]

    if isinstance(all_kits, list):
        for k in all_kits:
            kit = API.Kit(
                k["@attributes"]["id"],
                k["@attributes"]["colour1"],
                k["@attributes"]["type"],
            )
            if "colour2" in k["@attributes"]:
                kit.setSecondColour(k["@attributes"]["colour2"])
            kits.append(kit)
    elif isinstance(all_kits, dict):
        kit = API.Kit(
            all_kits["@attributes"]["id"],
            all_kits["@attributes"]["colour1"],
            all_kits["@attributes"]["type"],
        )
        if "colour2" in all_kits:
            kit.setSecondColour(all_kits["@attributes"]["colour2"])
        kits.append(kit)
    return kits


def parseTeamOfficial(t):
    officials = []
    if "TeamOfficial" in t:
        officials_data = t["TeamOfficial"]
        if isinstance(officials_data, list):
            for person in officials_data:
                p = person["PersonName"]
                attr = person["@attributes"]
                of_obj = API.TeamOfficial(
                    p["First"], p["Last"], attr["Type"], attr["uID"]
                )
                if "BirthDate" in p:
                    of_obj.setFeature("BirthDate", p["BirthDate"])
                if "BirthPlace" in p:
                    of_obj.setFeature("BirthPlace", p["BirthPlace"])
                if "country" in attr:
                    of_obj.setFeature("country", attr["country"])
                if "join_date" in p:
                    of_obj.setFeature("join_date", p["join_date"])
                officials.append(of_obj)

        elif isinstance(officials_data, dict):
            p = officials_data["PersonName"]
            attr = officials_data["@attributes"]
            of_obj = API.TeamOfficial(p["First"], p["Last"], attr["Type"], attr["uID"])
            if "BirthDate" in p:
                of_obj.setFeature("BirthDate", p["BirthDate"])
            if "BirthPlace" in p:
                of_obj.setFeature("BirthPlace", p["BirthPlace"])
            if "country" in attr:
                of_obj.setFeature("country", attr["country"])
            if "join_date" in p:
                of_obj.setFeature("join_date", p["join_date"])
            officials.append(of_obj)

    return officials


def parseTimingTypes(timingTypes):
    detailTypes = timingTypes["DetailTypes"]["DetailType"]
    tsAccTypes = timingTypes["TimestampAccuracyTypes"]["TimestampAccuracyType"]
    ttypes = timingTypes["TimingType"]["TimingType"]

    dTypeList = []
    tsAccTypeList = []
    tTypeList = []

    for dt in detailTypes:
        dTypeList.append(
            API.DetailType(dt["@attributes"]["detail_id"], dt["@attributes"]["name"])
        )

    for ts in tsAccTypes:
        tsAccTypeList.append(
            API.TimestampAccuracyType(
                ts["@attributes"]["name"], ts["@attributes"]["timestamp_accuracy_id"]
            )
        )

    for tt in ttypes:
        tTypeList.append(
            API.TimingType(tt["@attributes"]["name"], tt["@attributes"]["timing_id"])
        )

    allTimingTypes = API.TimingTypes()
    allTimingTypes.setDetailTypes(dTypeList)
    allTimingTypes.setTSAccuracyTypes(tsAccTypeList)
    allTimingTypes.setTimingTypes(tTypeList)

    return allTimingTypes


def parseEvents(gEvents):
    events = []
    for event in gEvents:
        event_attr = event["@attributes"]
        event_object = API.Event(event_attr["id"], event_attr["event_id"])

        # check the feature is available
        event_object.setFeature("type_id", event_attr["type_id"]).setFeature(
            "period_id", event_attr["period_id"]
        ).setFeature("min", event_attr["min"]).setFeature(
            "sec", event_attr["sec"]
        ).setFeature(
            "team_id", event_attr["team_id"]
        ).setFeature(
            "outcome", event_attr["outcome"]
        ).setFeature(
            "x", event_attr["x"]
        ).setFeature(
            "y", event_attr["y"]
        ).setFeature(
            "last_modified", event_attr["last_modified"]
        )

        if "version" in event_attr:
            event_object.setFeature("version", event_attr["version"])

        if "player_id" in event_attr:
            event_object.setFeature("player_id", event_attr["player_id"])

        q_events = []
        if "Q" in event:  # some items don't include this feature
            event_q = event["Q"]
            if isinstance(event_q, list):
                for q in event_q:
                    attr = q["@attributes"]
                    q_object = API.QEvent(
                        q["@attributes"]["id"], q["@attributes"]["qualifier_id"]
                    )
                    if "value" in attr:
                        q_object.setValue(attr["value"])
                    q_events.append(q_object)
            elif isinstance(event_q, dict):
                q_object = API.QEvent(
                    q["@attributes"]["id"], q["@attributes"]["qualifier_id"]
                )
                attr = q["@attributes"]
                if "value" in q:
                    q_object.setValue(attr["value"])
                q_events.append(q_object)
        event_object.setFeature("QEvent", q_events)
        events.append(event_object)
    return events


def parseVenue(data):
    venue = API.Venue()
    if "uID" in data["@attributes"]:
        venue.setFeature("uID", data["@attributes"]["uID"])
    if "Name" in data:
        venue.setFeature("Name", data["Name"])
    if "Country" in data:
        venue.setFeature("Country", data["Country"])
    return venue


def parse_feed_1(competition_id, season_id, online):
    # get feed
    data = getFeed(Feeds.feed1, competition_id, season_id)

    # parse data

    matchData = data["SoccerFeed"]["SoccerDocument"]["MatchData"]
    teamData = data["SoccerFeed"]["SoccerDocument"]["Team"]
    ttypes = data["SoccerFeed"]["SoccerDocument"]["TimingTypes"]
    features = data["SoccerFeed"]["SoccerDocument"]["@attributes"]

    parsedTeams = parseTeams(teamData)
    parsedMatchData = parseMatchData(matchData)
    parsedTTimes = parseTimingTypes(ttypes)
    # create feed object
    feed = API.Feed1(
        parsedMatchData,
        features["Type"],
        features["competition_code"],
        features["competition_id"],
        features["competition_name"],
        features["game_system_id"],
        features["season_id"],
        features["season_name"],
        parsedTeams,
        parsedTTimes,
    )
    # store in DB
    # jsonSerializer(feed)
    # if online is True:
    #     return feed
    # else:
    feed.storeInDB()  # store in the database


def parse_feed_9(competition_id, season_id, game_id, online):
    print("Feed 9 is being parsed")
    # get feed
    data = getFeed(Feeds.feed9, competition_id, season_id, game_id)

    # parse data
    timestamp = data["SoccerFeed"]["@attributes"][
        "TimeStamp"
    ]  # retrieved timestamp, this is actually not required
    competitionData = data["SoccerFeed"]["SoccerDocument"]["Competition"]
    matchData = data["SoccerFeed"]["SoccerDocument"]["MatchData"]
    teamData = data["SoccerFeed"]["SoccerDocument"]["Team"]
    venue = data["SoccerFeed"]["SoccerDocument"]["Venue"]
    features = data["SoccerFeed"]["SoccerDocument"]["@attributes"]

    # create feed object
    feed = API.Feed9(
        timestamp,
        parseMatchData(matchData),
        parseVenue(venue),
        features["Type"],
        parseTeams(teamData),
        game_id,
        parseCompetitionData(competitionData),
        competition_id,
        season_id,
    )
    if "detail_id" in features:
        feed.setFeature("detail_id", features["detail_id"])

    jsonSerializer(feed)

    if online is True:
        return feed
    else:
        feed.storeInDB()  # store in the database
        print("Feed 9 is parsed and stored in the database")


def parse_feed_24(competition_id, season_id, game_id, online):
    # get feed
    start_time = time.time()
    data = getFeed(Feeds.feed24, competition_id, season_id, game_id)

    # parse data
    gameData = data["Games"]["Game"]
    game_attr = gameData["@attributes"]
    constructor = Constructor.Constructor()
    game_events = constructor.event_handler(data=parseEvents(gameData["Event"]))

    game = API.Game(game_attr["id"])

    if "away_score" in game_attr:
        game.setFeature("away_score", game_attr["away_score"])
    if "home_score" in game_attr:
        game.setFeature("home_score", game_attr["home_score"])

    game.setFeature(
        "away_team_id", game_attr["away_team_id"]
    ).setFeature(
        "away_team_name", game_attr["away_team_name"]
    ).setFeature(
        "competition_id", game_attr["competition_id"]
    ).setFeature(
        "competition_name", game_attr["competition_name"]
    ).setFeature(
        "game_date", game_attr["game_date"]
    ).setFeature(
        "home_team_id", game_attr["home_team_id"]
    ).setFeature(
        "home_team_name", game_attr["home_team_name"]
    ).setFeature(
        "matchday", game_attr["matchday"]
    ).setFeature(
        "period_1_start", game_attr["period_1_start"]
    ).setFeature(
        "period_2_start", game_attr["period_2_start"]
    ).setFeature(
        "season_id", game_attr["season_id"]
    ).setFeature(
        "season_name", game_attr["season_name"]
    ).setFeature(
        "Event", game_events
    )
    end_time = time.time()
    print("parsing operation", end_time - start_time)
    # create feed object
    feed = API.Feed24(competition_id, season_id, game)
    # jsonSerializer(feed)

    # if online is True:
    #     return feed
    # else:
    start_time = time.time()
    feed.storeInDB()  # store in the database
    end_time = time.time()
    print("storing operation", end_time-start_time)


def parse_feed_40(competition_id, season_id, online=None):
    # get feed
    data = getFeed(Feeds.feed40, competition_id, season_id)

    # parse data
    teams = parseTeam(data)  # teams
    pchanges = parsePlayerChanges(data)  # player Changes
    # attributes
    attrs = data["SoccerFeed"]["SoccerDocument"]["@attributes"]
    # create feed object
    feed = API.Feed40(
        teams,
        pchanges,
        attrs["Type"],
        attrs["competition_id"],
        attrs["competition_name"],
        attrs["competition_code"],
        attrs["season_id"],
        attrs["season_name"],
        None,
    )

    jsonSerializer(feed)
    if online is True:
        return feed
    else:
        feed.storeInDB()


def jsonSerializer(feed, file_name="feedjson.json"):
    """
    Converts the given feed into the serialized json object.

    :param feed:
    :return:
    """
    # print("Encode Object into JSON formatted Data using jsonpickle")
    empJSON = jsonpickle.encode(feed, unpicklable=False)

    print("Writing JSON Encode data into Python String")
    jsondata = json.dumps(empJSON, indent=4)
    # print(jsondata)
    feedjson = jsonpickle.decode(jsondata)
    # print(feedjson)
    f = open(file_name, "a")
    f.write(feedjson)
    f.close()


def parseFeed(feedName, competitionID, seasonID, gameID=None, online=None):
    print("Parsing operation is started...")
    if feedName is Feeds.feed1:
        if online is True:
            return parse_feed_1(competitionID, seasonID, True)
        parse_feed_1(competitionID, seasonID, False)
    elif feedName is Feeds.feed9:
        if online is True:
            return parse_feed_9(competitionID, seasonID, gameID, True)
        parse_feed_9(competitionID, seasonID, gameID, False)
    elif feedName is Feeds.feed24:
        if online is True:
            return parse_feed_24(competitionID, seasonID, gameID, True)
        parse_feed_24(competitionID, seasonID, gameID, False)
    elif feedName is Feeds.feed40:
        if online is True:
            return parse_feed_40(competitionID, seasonID, True)
        parse_feed_40(competitionID, seasonID, False)


if __name__ == '__main__':
#  data = parseFeed("feed1","115","2018")
#  print("data",data["SoccerFeed"]["SoccerDocument"]["MatchData"])
#  data1 = getFeedFromFile("f9","115","2016")
#  print("data-1:\n", data1)
#  data2 = getFeedFromFile("f24", "115", "2016","871376")
#  print(data2["Games"]["Game"])
#

# feed = parseFeed("feed40","115","2018")
#
#    print(data)
    pass
