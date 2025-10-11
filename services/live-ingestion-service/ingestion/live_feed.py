"""
This code aims at handling the real time data
Author: Cem Akpolat

"""
import sys

sys.path.append("..")  # Adds higher directory to python modules path.
from src.parse import Parser
from datetime import date
import requests

# todo: Test this class for live tracking
class LiveDataHandler:
    def __init__(self, data):
        self.data = data

    def handler(self, feedName, feed, request):
        if feedName == Parser.Feeds.feed9:
            self.handleFeed9(feed)
        elif feedName == Parser.Feeds.feed24:
            self.handleFeed24(feed)

    def handleFeed9(self, feed, request):
        print("live feed 9 is being handled ...")

    # Live Data
    def getTeamKey(self, feed, team_name):
        number_of_teams = len(feed.teams)
        for team in feed.teams:
            if team.name == team_name:
                team_key = str(team.uID).strip("t")
                print(team_name + " team key is: " + team_key)
                return team_key

    def getGameBeingPlayed(self, feed):
        for game in feed.matchData:
            today = date.today()
            dt = date.datetime.strptime(
                game.matchInfo.date, "%Y-%m-%d %H:%M:%S"
            )  # https://stackabuse.com/converting-strings-to-datetime-in-python/
            print("Date:", dt.date())
            print("Time:", dt.time())
            print("Date-time:", dt)
            if today > dt:
                print("game should be started")
                return game.uID
        return None

    def getChosenTeamID(self, feed, team_name):
        self.team_info["name"] = team_name
        self.team_info["team_id"] = self.getTeamKey(feed, team_name)
        return self.team_info["team_id"]

    # todo: test the following function
    def getGameKeys(self, feed, team_id):
        team_key = "t" + team_id
        # self.game_keys = ["" for x in range(fixtures)]
        # self.goals_for = ["" for x in range(fixtures)]
        # self.goals_against = ["" for x in range(fixtures)]
        counter = 0
        for game in feed.matchData:
            for item in game:
                if item.teamRef == team_key:
                    self.game_keys[counter] = game.uID
                    self.goals_for[counter] = item.score
                else:
                    self.game_keys[counter] = game.uID
                    self.goals_against[counter] = item.score
            counter = counter + 1
        print(self.goals_for)
        print(self.goals_against)
        return self.game_keys

    # return feed 9
    def getLiveGameData(self, seasonID, competitionID, team_name):
        feed1 = Parser.getFeed(seasonID, competitionID)
        teamID = self.getChosenTeamID(feed1, team_name)
        gameID = self.getGameBeingPlayed(feed1, teamID)

        if gameID is not None:
            return Parser.getFeed(Parser.Feeds.feed9, seasonID, competitionID, gameID)
        else:
            print("there is no actual game for today!")
            return None

    def getLiveGameEvents(self, seasonID, competitionID, teamID, gameID):
        feed = Parser.getFeed(Parser.Feeds.feed24, seasonID, competitionID, gameID)
        events = []
        for event in feed.game.events:
            if event.teamID == teamID:
                events.append(event)
        return events

    def getEventsGameBeingPlayedByPlayer(
        self, seasonID, competitionID, gameID, playerID
    ):
        feed = Parser.getFeed(Parser.Feeds.feed24, seasonID, competitionID, gameID)
        events = []
        for event in feed.game.events:
            if event.playerID == playerID:
                events.append(event)
        return events

    # current
    def getEventsOfPlayer(self, seasonID, competitionID, teamName, playerName):
        feed = Parser.getFeed(Parser.Feeds.feed40, seasonID, competitionID)

        playerID = None
        teamID = None
        events = []
        for team in feed.teams:
            if team.name == teamName:
                teamID = team.uID
                for player in team.players:
                    if player.name == playerName:
                        playerID = player.uID
                        break
        gameID = self.getGameBeingPlayed(
            Parser.getFeed(Parser.Feeds.feed24, seasonID, competitionID), teamID
        )
        return self.getEventsGameBeingPlayedByPlayer(
            seasonID, competitionID, gameID, playerID
        )

    # todo: test
    def getAllEventsOfTeam(self, seasonID, competitionID, teamName):
        feed = Parser.getFeed(Parser.Feeds.feed40, seasonID, competitionID)
        teamID = None
        for team in feed.teams:
            if team.name == teamName:
                teamID = team.uID
                break
        gameID = self.getGameBeingPlayed(
            Parser.getFeed(Parser.Feeds.feed24, seasonID, competitionID), teamID
        )
        return self.getLiveGameEvents(seasonID, competitionID, teamID, gameID)

    def handleFeed24(self, feed, request):
        print("live feed 24 is being handled ...")
