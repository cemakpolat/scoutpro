from mongoengine import *
from src.dbase import DBHelper
from src.parse import Parser
from src.utils import Utils
import time


logger = Utils.Logger(__name__).get_connector_logger()


class Connector:
    def __init__(self, name="statsfabrik", port=27017, host="localhost", alias="default"):
        logger.info("Connector is initiated...")
        self.db_name = name
        self.db_port = port
        self.host = host
        self.alias = alias
        self.online = False

        # Feed Variables
        self.feed_name = None
        self.feed_id = None
        self.game_id = None
        self.competition_id = None
        self.season_id = None

    def connect(self):
        connect(db=self.db_name, host=self.host, port=self.db_port, alias=self.alias)
        return self

    def disconnect(self):
        disconnect(self.alias)
        return self

    def update_connection(self, name, port, host, alias):
        conn_dict = {
            "db_name": name,
            "db_port": port,
            "host": host,
            "alias": alias
        }
        for key, value in conn_dict.items():
            temp_value = self.__dict__[key]
            if value == temp_value:
                continue
            else:
                logger.info(f"Connection updated: {temp_value} ---> {value}")
                setattr(self, key, value)
        return self

    def disconnect_all(self):
        disconnect_all()
        return self

    def setOnline(self, online):
        self.online = online
        return self

    def assign_feed_vars(self, feed_name: str, competition_id: int, season_id: int, game_id: int = None):
        self.feed_name = feed_name
        self.competition_id = competition_id
        self.season_id = season_id
        self.game_id = game_id
        self.feed_id = Utils.feed_dict(self.feed_name)
        return self

    def getFeed(self, feed_name: str, competition_id: int, season_id: int, game_id: int = None):

        self.assign_feed_vars(feed_name, competition_id, season_id, game_id)

        if self.online is True:
            return Parser.parseFeed(
                feed_name, competition_id, season_id, game_id, True
            )  # just return the online feed data
        else:
            if self.isFeedAvailable() is False:
                start_time = time.time()
                Parser.parseFeed(
                    feed_name, competition_id, season_id, game_id, False
                )  # this stores in the DB as well
                self.addFeedToFeedTable()  # add the feed in the feed table
                end_time = time.time()
                logger.info(f"parsing total duration {end_time-start_time}")
                return self.fetchDBObject()
            else:
                return self.fetchDBObject()

    def fetchDBObject(self):
        start_time = time.time()
        feed = None
        if self.feed_name is Parser.Feeds.feed1:
            feed = DBHelper.F1_Root.objects(
                Q(competitionID=self.competition_id) & Q(seasonID=self.season_id)
            ).first()
        elif self.feed_name is Parser.Feeds.feed9:
            if self.game_id:
                feed = DBHelper.F9_Root.objects(
                    Q(competitionID=self.competition_id) & Q(seasonID=self.season_id) & Q(uID=self.game_id)
                ).first()
            else:
                feed = DBHelper.F9_Root.objects(
                    Q(competitionID=self.competition_id) & Q(seasonID=self.season_id)
                ).first()
        elif self.feed_name is Parser.Feeds.feed24:
            feed = DBHelper.F24_Root.objects(
                Q(competitionID=self.competition_id) & Q(seasonID=self.season_id) & Q(gameID=self.game_id)
            ).first()
        elif self.feed_name is Parser.Feeds.feed40:
            feed = DBHelper.F40_Root.objects(
                Q(competitionID=self.competition_id) & Q(seasonID=self.season_id)
            ).first()
        end_time = time.time()
        logger.info(f"total duration {end_time - start_time}")
        return feed

    def addFeedToFeedTable(self):
        feedTable = DBHelper.FeedTable(
            feedID=self.feed_id,
            seasonID=self.season_id,
            competitionID=self.competition_id,
            gameID=self.game_id,
        )
        feedTable.save()

    def isFeedAvailable(self, log: bool = True):
        availableFeeds = DBHelper.FeedTable.objects(Q(feedID=self.feed_id))
        availableFeeds.filter(competitionID=self.competition_id)
        availableFeeds.filter(seasonID=self.season_id)

        if len(availableFeeds) == 0:
            if log:
                logger.error("Feed Table is empty!")
        else:
            for feed in availableFeeds:
                if (feed.seasonID == self.season_id) and (
                    feed.competitionID == self.competition_id
                ):
                    if self.feed_name == "feed24" or self.feed_name == "feed9":
                        if feed.gameID == self.game_id:
                            if log:
                                logger.info("The requested feed does exist!")
                            return True
                    else:
                        if log:
                            logger.info("The requested feed does exist!")
                        return True
        if log:
            logger.info("Feed is not available, it will be stored...")
        return False


main_conn = Connector()
