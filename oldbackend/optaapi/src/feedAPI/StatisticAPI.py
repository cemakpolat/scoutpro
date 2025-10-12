# TODO: Get all statistics functions using this API

"""
1.
"""


class Statistics:
    def __init__(self):
        self.db_port = 27000

    def getPlayerStatistics(competition, season, playerId, gameId):

        """
        a single match statistic
        1. check there is available statistics already in the database, if not
        2. initiate the event classes by calling the feed 24
        3. store all data in the database for a single user
        4. return the player result to the requester
        """

    def getPlayerStatistics(competition, season, playerId, gameId, last_x_number_match):
        """
        last x statistics
        0. The request is here to
        1. check there is available statistics already in the database, if not
        2. initiate the event classes by calling the feed 24
        3. store all data in the database for a single user
        4. return the player result to the requester
        """

    def getPlayerStatistics(competition, season, playerId, gameId, frm, to):
        """
        from year to year statistics
        """

    def getPlayerStatistics(playerId):
        """
        the whole statistic
        """

    def getTeamStatistics(competition, season, teamId, gameId):
        """
        a single match statistic
        """

    def getTeamStatistics(competition, season, teamId, gameId, last_x_number_match):
        """
        last x statistics
        """

    def getTeamStatistics(competition, season, teamId, gameId, frm, to):
        """
        from year to year statistics
        """

    def getTeamStatistics(playerId):
        """
        the whole statistic
        """

    # Live Feed Data, just store in a file or keep it in an object
    def getMatchStatistics(self, gameID):
        print("live feed 9 data")
