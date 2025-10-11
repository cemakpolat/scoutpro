from src.feedAPI import TeamAPI
from src.feedAPI import PlayerAPI
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import requests
from src.utils.Utils import get_optimal_user_agent


class TransfermarktConverter:
    def __init__(self, competition_id, season_id):

        self.competition_id = competition_id
        self.season_id = season_id

        self.mapper = {"player": "player",
                       "birth_date": "birth_date",
                       "position": "position",
                       "team": "team",
                       "value": "value"}

        self.mapper_error = """
                Assume that our transfermarkt_data_frame object has the following format;
                             player_name    Position     birthDate    Position    team_name
                0       Fernando Muslera  Goalkeeper  Jun 16, 1986  Goalkeeper  Galatasaray
                1            Ismail Cipe  Goalkeeper   Jan 5, 1995  Goalkeeper  Galatasaray
                2            Batuhan Sen  Goalkeeper     Feb 3, 99  Goalkeeper  Galatasaray
                3             Ozan Kabak    Defender  Mar 25, 2000    Defender  Galatasaray
                4    Christian Luyindama    Defender   Jan 8, 1994    Defender  Galatasaray
                ..                   ...         ...           ...         ...          ...
                716            Onur Ayik      Attack    Jan , 1990      Attack  Akhisarspor
                717     Sokol Cikalleshi      Attack    Jul , 1990      Attack  Akhisarspor
                718     Yevgen Seleznyov      Attack  Jul 20, 1985      Attack  Akhisarspor
                719       Daniel Larsson      Attack  Jan 25, 1987      Attack  Akhisarspor
                720        Jeremy Bokila      Attack  Nov 14, 1988      Attack  Akhisarspor

                then, our mapper variable should be as follows;
                mapper = {
                    "player": "player_name", 
                    "birth_date": "birthDate", 
                    "position": "Position", 
                    "team": "team_name"
                    }
                """

    def get_dict_between_opta_transfermarkt_teams(self, transfermarkt_team_names):

        tapi = TeamAPI.TeamAPI(competitionID=self.competition_id, seasonID=self.season_id)
        all_team_names_opta = tapi.get_all_team_names()

        if all_team_names_opta in [None, list(), dict(), tuple(), set(), str()]:
            print(
                "CAUTION: The league does not exists in the opta data base, please check competition and season ids. ")
            return dict()

        distinct_team_names_tm = set(transfermarkt_team_names).difference(set(all_team_names_opta))
        distinct_team_names_opta = set(all_team_names_opta).difference(set(transfermarkt_team_names))

        temp_dict_object = dict()
        transfermarkt_to_opta_dict = dict()

        user_agent = get_optimal_user_agent(browser_name="google chrome", test_url="https://en.soccerwiki.org/")

        headers = {"User-Agent": user_agent}

        main_url = 'https://en.soccerwiki.org/search.php?type=club&q='

        for opta_team in distinct_team_names_opta:
            temp_url = main_url + urllib.parse.quote_plus(str(opta_team).strip().lower())
            temp_response = requests.get(temp_url, headers=headers)
            temp_soup = BeautifulSoup(temp_response.text, 'html.parser')
            try:
                result = str(temp_soup.find_all("td", {"class": "text-left"})[0].text)
            except IndexError:
                try:
                    result = str(temp_soup.find_all("div", {"class": "col-12 col-md-6 mt-0 mb-3"})[0].text).replace(
                        "Clubs",
                        "")
                except IndexError:
                    continue
            temp_dict_object[result] = opta_team

        non_matched_teams_in_tm = list()
        for tm_team in distinct_team_names_tm:
            temp_url = main_url + urllib.parse.quote_plus(str(tm_team).strip().lower())
            temp_response = requests.get(temp_url, headers=headers)
            temp_soup = BeautifulSoup(temp_response.text, 'html.parser')
            try:
                result = str(temp_soup.find_all("td", {"class": "text-left"})[0].text)
            except IndexError:
                try:
                    result = str(temp_soup.find_all("div", {"class": "col-12 col-md-6 mt-0 mb-3"})[0].text).replace(
                        "Clubs",
                        "")
                except IndexError:
                    continue

            if result in temp_dict_object:
                transfermarkt_to_opta_dict[tm_team] = temp_dict_object[result]
                del temp_dict_object[result]
            else:
                non_matched_teams_in_tm.append(tm_team)

        if 0 < len(non_matched_teams_in_tm):
            print("CAUTION: There are non matched teams in transfermarkt data; ", non_matched_teams_in_tm)

        return transfermarkt_to_opta_dict

    def get_dict_between_opta_transfermarkt_team_players(self, team_name, transfermarkt_players_data_frame,
                                                         mapper=None):

        papi = PlayerAPI.PlayerAPI(competitionID=self.competition_id, seasonID=self.season_id)
        tapi = TeamAPI.TeamAPI(competitionID=self.competition_id, seasonID=self.season_id)
        all_player_names_opta = tapi.get_all_players_name(team_name=team_name)

        if all_player_names_opta in [None, list(), dict(), set(), tuple()]:
            print("CAUTION: The team does not exists in the opta data base: ", team_name)
            return dict()

        if mapper is None:
            mapper = self.mapper

        transfermarkt_player_names = list(transfermarkt_players_data_frame[mapper["player"]])

        distinct_player_names_tm = list(set(transfermarkt_player_names).difference(set(all_player_names_opta)))

        transfermarkt_to_opta_dict = dict()
        for tm_player in distinct_player_names_tm.copy():
            tm_player_data_frame = transfermarkt_players_data_frame.loc[
                transfermarkt_players_data_frame["player"] == tm_player]
            tm_player_birth_date = tm_player_data_frame[mapper["birth_date"]].values

            if 0 < len(tm_player_birth_date):
                tm_player_birth_date = tm_player_birth_date[0]
                tm_player_birth_date = self._birth_date_converter_transfermarkt_to_opta(tm_player_birth_date)
            else:
                tm_player_birth_date = None

            tm_player_position = tm_player_data_frame[mapper["position"]].values
            if 0 < len(tm_player_position):
                tm_player_position = tm_player_position[0]
                tm_player_position = self._position_converter_transfermarkt_to_opta(tm_player_position)
            else:
                tm_player_position = None

            temp_query = {'$and': [{'birth_date': {'$eq': tm_player_birth_date}},
                                   {'position': {'$eq': tm_player_position}}]}

            possible_opta_player = list(
                papi.get_filtered_personal_players(query_conditions=temp_query, team_names=[team_name],
                                                   event_params=["first_name", "last_name",
                                                                 "known_name"], limit=1))
            if len(possible_opta_player) == 1:
                opta_player_first_name = str()
                opta_player_last_name = str()
                opta_player_known_name = str()
                for player_info in possible_opta_player[0]["player_info"]:
                    if "type" in player_info and "value" in player_info:
                        if player_info["type"] == "first_name":
                            opta_player_first_name = player_info["value"]
                        elif player_info["type"] == "last_name":
                            opta_player_last_name = player_info["value"]
                        elif player_info["type"] == "known_name":
                            opta_player_known_name = player_info["value"]
                        else:
                            continue
                if opta_player_known_name != str():
                    transfermarkt_to_opta_dict[tm_player] = opta_player_known_name
                    distinct_player_names_tm.remove(tm_player)
                elif opta_player_first_name != str() and opta_player_last_name != str():
                    transfermarkt_to_opta_dict[tm_player] = opta_player_first_name + " " + opta_player_last_name
                    distinct_player_names_tm.remove(tm_player)
                else:
                    continue
            else:
                continue

        if 0 < len(distinct_player_names_tm):
            print("CAUTION: There are non matched players in transfermarkt data: ", distinct_player_names_tm)

        return transfermarkt_to_opta_dict

    @staticmethod
    def _birth_date_converter_transfermarkt_to_opta(birth_day_string):
        if isinstance(birth_day_string, str):
            month_dict = {'Jan': "01", 'Feb': "02", 'Mar': "03", 'Apr': "04", 'May': "05", 'Jun': "06", 'Jul': "07",
                          'Aug': "08", 'Sep': "09", 'Oct': "10", 'Nov': "11", 'Dec': "12"}

            year_month_day = birth_day_string.strip().split(",")
            if len(year_month_day) == 1:
                try:
                    year = int(year_month_day[0])
                    if year < 100:
                        year += 1900
                except ValueError:
                    return None
                return str(year) + "-01-01"

            elif len(year_month_day) == 2:
                try:
                    year = int(year_month_day[1])
                    if year < 100:
                        year += 1900
                except ValueError:
                    return None

                month_day = year_month_day[0].split(" ")

                if len(month_day) == 1:
                    month = month_day[0]
                    if month in month_dict:
                        month = month_dict[month]
                    else:
                        month = "01"

                    return str(year) + "-" + str(month) + "-" + "01"

                elif len(month_day) == 2:
                    month = month_day[0]
                    if month in month_dict:
                        month = month_dict[month]
                    else:
                        month = "01"

                    try:
                        day = int(month_day[1])
                        if day > 31:
                            day = "01"
                        elif day < 10:
                            day = "0" + str(day)
                    except ValueError:
                        day = "01"

                    return str(year) + "-" + str(month) + "-" + str(day)

                else:
                    return None
            else:
                return None
        else:
            return None

    @staticmethod
    def _position_converter_transfermarkt_to_opta(position_string):
        position_dict = {
            "Goalkeeper": "Goalkeeper",
            "Defender": "Defender",
            "Midfield": "Midfielder",
            "Attack": "Forward",
            "Forward": "Forward"
        }
        if position_string in position_dict:
            return position_dict[position_string]
        else:
            return None

    def get_value_diff_players_data_frame(self, left_data_frame, right_data_frame, mapper=None):
        if mapper is None:
            mapper = self.mapper
        else:
            error_flag = True
            for attribute in self.mapper.keys():
                if attribute in mapper:
                    if mapper[attribute] is None:
                        error_flag = False
                        break
                    else:
                        if mapper[attribute] in left_data_frame and mapper[attribute] in right_data_frame:
                            continue
                        else:
                            error_flag = False
                            break
                else:
                    error_flag = False
                    break

            if error_flag:
                raise KeyError(self.mapper_error)

        merged_data_frame = pd.merge(left=left_data_frame[[mapper["player"], mapper["value"]]],
                                     right=right_data_frame[[mapper["player"], mapper["value"]]],
                                     on=mapper["player"], how="left").dropna()

        merged_data_frame["value_diff"] = merged_data_frame["value_y"] - merged_data_frame["value_x"]

        main_data = pd.merge(left=merged_data_frame, right=right_data_frame[[mapper["player"], mapper["team"],
                                                                             mapper["position"], mapper["birth_date"]]],
                             on="player", how="left")

        return main_data.dropna().drop_duplicates().reset_index(drop=True)

    def convert_transfermarkt_data_to_opta_data(self, transfermarkt_data_frame, mapper=None):
        if mapper is None:
            mapper = self.mapper
        else:
            error_flag = True
            for attribute in self.mapper.keys():
                if attribute in mapper:
                    if mapper[attribute] is None:
                        error_flag = False
                        break
                    else:
                        if mapper[attribute] in transfermarkt_data_frame:
                            continue
                        else:
                            error_flag = False
                            break
                else:
                    error_flag = False
                    break

            if error_flag:
                raise KeyError(self.mapper_error)

        transfermarkt_teams = list(transfermarkt_data_frame[mapper["team"]])

        team_convert_dict = self.get_dict_between_opta_transfermarkt_teams(transfermarkt_teams)

        if 0 < len(team_convert_dict):
            transfermarkt_data_frame[mapper["team"]].replace(team_convert_dict, inplace=True)
            transfermarkt_teams = list(transfermarkt_data_frame[mapper["team"]].unique())

        else:
            return transfermarkt_data_frame

        for team in transfermarkt_teams:
            temp_transfermarkt_players_data_frame = transfermarkt_data_frame.loc[
                transfermarkt_data_frame["team"] == team].copy()

            temp_player_convert_dict = self.get_dict_between_opta_transfermarkt_team_players(
                team_name=team, mapper=mapper, transfermarkt_players_data_frame=temp_transfermarkt_players_data_frame
            )

            if 0 < len(temp_player_convert_dict):
                transfermarkt_data_frame[mapper["player"]].replace(temp_player_convert_dict, inplace=True)

        return transfermarkt_data_frame


if __name__ == "__main__":

    def run():
        dc = TransfermarktConverter(115, 2018)
        df1 = pd.read_excel("super_lig_2017_all_players.xlsx")
        df2 = pd.read_excel("super_lig_2018_all_players.xlsx")
        main_data = pd.merge(df2, df1, how="left", on="player").dropna().drop_duplicates()
        main_data = main_data[["player", "position_y", "birth_date_y", "team_x", "value_y", "value_x"]]
        main_data.rename({
            "position_y": "position", "birth_date_y": "birth_date", "team_x": "team"
        }, axis=1, inplace=True)
        main_data["value_diff"] = main_data["value_x"] - main_data["value_y"]
        new_main_data = dc.convert_transfermarkt_data_to_opta_data(main_data)
        main_data.to_excel("temp.xlsx", index=False)
        new_main_data.to_excel("new_temp.xlsx", index=False)

    run()
