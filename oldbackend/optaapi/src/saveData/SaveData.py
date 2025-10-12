from src.feedAPI import Connector
from src.feedAPI import GameAPI
from src.feedAPI import PlayerAPI
from src.feedAPI import TeamAPI
from src.feedAPI import EventAPI
from src.parse import Parser
import json


class SaveData:

    def __init__(
            self,
            competition_id: int,
            season_id: int,
            game_id_start_int: int,
            index_norm: int,
            name="statsfabrik",
            port=27017,
            host="localhost",
            alias="default"
    ):
        # Season variables
        self.competition_id = competition_id
        self.season_id = season_id
        self.game_id_start_int = game_id_start_int
        self.index_norm = index_norm

        # Feed names
        self.feed = Parser.Feeds

        # Connection variable
        self.conn = Connector.main_conn
        self.conn.update_connection(
            name=name, port=port, host=host, alias=alias
        )

        # Flags for feed status
        self.feed1_status = False
        self.feed40_status = False
        self.feed24_status = False
        self.player_minutes_status = False
        self.player_stats_status = False
        self.team_stats_status = False

        # Determine each flags for feed status
        self._determine_flags()

    def _determine_flags(self):
        self.conn.connect()
        flag_dict = {
            "feed1_status": self.feed.feed1,
            "feed40_status": self.feed.feed40,
            "feed24_status": self.feed.feed124,
            "player_minutes_status": self.feed.feed130,
            "player_stats_status": self.feed.feed140,
            "team_stats_status": self.feed.feed340
        }
        for flag, feed_key in flag_dict.items():
            self.conn.assign_feed_vars(
                feed_name=feed_key, competition_id=self.competition_id, season_id=self.season_id
            )
            setattr(self, flag, bool(self.conn.isFeedAvailable(log=False)))
        self.conn.disconnect()
        return self

    def papi(self):
        return PlayerAPI.PlayerAPI(competitionID=self.competition_id, seasonID=self.season_id)

    def gapi(self):
        return GameAPI.GameAPI(competitionID=self.competition_id, seasonID=self.season_id)

    def tapi(self):
        return TeamAPI.TeamAPI(competitionID=self.competition_id, seasonID=self.season_id)

    def evapi(self):
        return EventAPI.EventAPI(competition_id=self.competition_id, season_id=self.season_id)

    def save_feed_1(self):
        if self.feed1_status:
            return self
        self.conn.connect()
        self.conn.getFeed(
            feed_name=self.feed.feed1, competition_id=self.competition_id, season_id=self.season_id
        )
        self.feed1_status = True
        self.conn.disconnect()
        return self

    def save_feed_40(self):
        if self.feed40_status:
            return self
        self.conn.connect()
        self.conn.getFeed(
            feed_name=self.feed.feed40, competition_id=self.competition_id, season_id=self.season_id
        )
        self.feed40_status = True
        self.conn.disconnect()
        return self

    def save_feed_24(self):
        if self.feed24_status:
            return self
        self.conn.connect()
        for index in range(self.index_norm):
            self.conn.getFeed(
                feed_name=self.feed.feed24, competition_id=self.competition_id, season_id=self.season_id,
                game_id=self.game_id_start_int + index
            )
        self.conn.assign_feed_vars(
            feed_name=self.feed.feed124, competition_id=self.competition_id, season_id=self.season_id
        ).addFeedToFeedTable()
        self.feed24_status = True
        self.conn.disconnect()
        return self

    def save_feeds(self):
        self.save_feed_1().save_feed_40().save_feed_24()
        return self

    def save_player_stats(self):
        if self.player_stats_status:
            return self
        elif self.player_minutes_status:
            self.conn.connect()
            teams = self.tapi().get_all_team_names()
            for team_name in teams:
                players = self.tapi().get_all_players_name(team_name=team_name)
                for player_name in players:
                    self.papi().getPlayerStatistics(player_name)

            self.conn.assign_feed_vars(
                feed_name=self.feed.feed140, competition_id=self.competition_id, season_id=self.season_id
            ).addFeedToFeedTable()
            self.player_stats_status = True
            self.conn.disconnect()

        else:
            print("In order to save player_statistics, first the players_total_time_statistics must be saved!")
            print("Trying to save the feeds ...")
            return self.save_player_total_played_time_stats()

    def save_player_total_played_time_stats(self):
        if self.player_minutes_status:
            return self
        elif self.feed1_status and self.feed24_status and self.feed40_status:
            self.conn.connect()
            for index in range(self.index_norm):
                temp_game_id = int(self.game_id_start_int) + index
                self.gapi().get_total_game_minutes_stats(game_id=temp_game_id)
            self.conn.assign_feed_vars(
                feed_name=self.feed.feed130, competition_id=self.competition_id, season_id=self.season_id
            ).addFeedToFeedTable()
            self.player_minutes_status = True
            self.conn.disconnect()
        else:
            print("In order to save players_total_time_statistics, first the feed1, feed40, and feed24 must be saved!")
            print("Trying to save the feeds ...")
            return self.save_feeds()

    def save_player_per90_stats(self):
        if self.player_stats_status:
            self.conn.connect()
            all_team_ids = self.tapi().get_all_team_ids()
            for team_id in all_team_ids:
                all_player_ids = self.tapi().get_all_players_ids(team_id=team_id)
                for player_id in all_player_ids:
                    self.papi().get_players_per90_stats(player_id=player_id)
            self.conn.disconnect()
        else:
            print("In order to save players_total_time statistics, first the feed1, feed40, and feed24 must be saved!")
            print("Trying to save the feeds ...")
            return self.save_player_stats()

    def save_player_percentile_stats(self):
        if self.player_stats_status:
            self.conn.connect()
            events = self.evapi().getEventDict()
            for event_name, event_obj in events.items():
                all_fields = self.evapi().getDocumentFields(document_obj=event_obj)["fields"]
                all_fields.remove("id")
                for field in all_fields:
                    self.papi().get_percentile_stats(
                        event=event_name, field=field, check_event_field=False
                    )
            self.conn.disconnect()
        else:
            print("In order to save player_percentile_statistics, "
                  "first the player_statistics must be saved!")
            return self.save_player_stats()

    def save_general_player_stats(
            self,
            player_ids=None,
            doc_name: str = "all_players",
            per90: bool = False
    ):
        if self.player_stats_status:
            self.conn.connect()

            if player_ids is None:
                all_players = self.papi().get_filtered_total_play_time_stats(project="playerID")
                player_ids = set()
                for player in all_players:
                    player_ids.add(int(player["playerID"]))

            all_positions = ["Goalkeeper", "Midfielder", "Defender", "Forward"]
            position_dict = dict()
            for position in all_positions:
                temp_query = {"position": position}
                temp_players = self.papi().get_filtered_stats_players(
                    query_conditions=temp_query, event_params=["playerID"], per90=per90
                )
                temp_position_players = set()
                for temp_player in temp_players:
                    temp_position_players.add(temp_player["playerID"])
                position_dict[position] = temp_position_players

            for position, player_ids in position_dict.items():
                temp_players = list(player_ids.intersection(player_ids))
                temp_player_ids = list()
                for temp_player in temp_players:
                    temp_player_ids.append(temp_player)

                temp_doc_name = str(position).lower().strip() + "_" + doc_name

                if per90:
                    temp_doc_name += "_per90"

                self.papi().get_general_player_stats(
                    doc_name=temp_doc_name, player_ids=temp_player_ids, per90=per90
                )
                self.conn.disconnect()
            return self

        else:
            print("In order to save save_general_player_statistics_in_season statistics, ",
                  "first the save_player_statistics must be saved!")
            print("Trying to save the player_statistics ...")
            return self.save_player_stats()

    def save_dominant_player_general_stats(
            self,
            min_play_time: int = 1500,
            per90=False
    ):
        if self.player_stats_status:
            self.conn.connect()
            pre_match = {"total_played_time": {"$gte": min_play_time}}

            dominant_players = self.papi().get_filtered_total_play_time_stats(
                query_after_group=pre_match, project="playerID"
            )

            all_player_ids = set()
            for player in dominant_players:
                all_player_ids.add(int(player["playerID"]))

            self.conn.disconnect()

            return self.save_general_player_stats(player_ids=all_player_ids, doc_name="dominant", per90=per90)

        else:
            print("In order to save save_general_player_statistics_in_season statistics, ",
                  "first the save_player_statistics must be saved!")
            print("Trying to save the player_statistics ...")
            return self.save_player_stats()

    def save_team_stats(self):
        if self.team_stats_status:
            return self
        elif self.feed1_status and self.feed24_status and self.feed40_status:
            self.conn.connect()
            teams = self.tapi().get_all_team_names()
            for team_name in teams:
                print(team_name)
                self.tapi().getTeamStatistics(team_name=team_name, event_type=None)
            self.conn.assign_feed_vars(
                feed_name=self.feed.feed340, competition_id=self.competition_id, season_id=self.season_id
            ).addFeedToFeedTable()
            self.team_stats_status = True
            self.conn.disconnect()
        else:
            print("In order to save team statistics, "
                  "first the feeds must be saved!")
            print("Trying to save the feeds ...")
            return self.save_feeds()

    def save_team_percentile_stats(self):
        if self.player_stats_status:
            self.conn.connect()
            events = self.evapi().getEventDict()
            for event_name, event_obj in events.items():
                all_fields = self.evapi().getDocumentFields(document_obj=event_obj)["fields"]
                all_fields.remove("id")
                for field in all_fields:
                    self.tapi().get_percentile_stats(
                        event=event_name, field=field, check_event_field=False
                    )
            self.conn.disconnect()
        else:
            print("In order to save player_percentile_statistics, "
                  "first the player_statistics must be saved!")
            return self.save_team_stats()

    def save_general_team_stats(
            self,
            team_ids=None,
            doc_name=None
    ):
        if self.team_stats_status:
            self.conn.connect()
            if doc_name is None:
                doc_name = "all_teams"
            self.tapi().get_general_team_stats(doc_name=doc_name, team_ids=team_ids)
            self.conn.disconnect()
            return self
        else:
            print("In order to save save_general_team_statistics_in_season statistics, ",
                  "first the save_team_statistics must be saved!")
            print("Trying to save the team_statistics ...")
            return self.save_team_stats()

    def save_all_main(self):
        self.save_feeds()
        self.save_player_total_played_time_stats()
        self.save_player_stats()
        self.save_team_stats()
        return self

    def save_all_general(self):
        self.save_general_player_stats()
        self.save_dominant_player_general_stats()
        self.save_player_percentile_stats()
        self.save_player_per90_stats()
        self.save_general_player_stats(per90=True)
        self.save_dominant_player_general_stats(per90=True)
        self.save_general_team_stats()
        self.save_team_percentile_stats()
        return self


if __name__ == '__main__':
    competition_id_super_league = 115
    competition_id_la_liga = 23
    season_id_2018 = 2018
    season_id_2019 = 2019
    season_id_2017 = 2017
    season_id_2016 = 2016

    saver_2019 = SaveData(
        competition_id=competition_id_super_league, season_id=season_id_2019, game_id_start_int=1080974, index_norm=252
    )
    saver_2018 = SaveData(
        competition_id=competition_id_super_league, season_id=season_id_2018, game_id_start_int=1002148, index_norm=18
    )
    saver_2017 = SaveData(
        competition_id=competition_id_super_league, season_id=season_id_2017, game_id_start_int=935586, index_norm=306
    )
    saver_2016 = SaveData(
        competition_id=competition_id_super_league, season_id=season_id_2016, game_id_start_int=871375, index_norm=306
    )

    la_liga_2018 = SaveData(
        competition_id=competition_id_la_liga, season_id=season_id_2018, game_id_start_int=1009316, index_norm=380
    )
    saver_2018.save_team_stats()
    saver_2018.save_team_percentile_stats()
