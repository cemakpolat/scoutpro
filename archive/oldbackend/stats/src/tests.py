
#
import json

from src import sb
from src import statsb_apis as api
competitions = sb.competitions(fmt="json")
print(competitions)

matches = sb.matches(competition_id=43, season_id=3, fmt="json")
#matches = sb.matches(competition_id=49, season_id=3,fmt="json")

print(matches)

lineups = sb.lineups(match_id=7494, fmt= "json")

# list = []
# for key in lineups:
#     item = lineups[key]
#     lup = api.LineUp(item["team_id"], item["team_name"])
#     lup.add_players(item["lineup"])
#     list.append(lup)

# print(list[0].team_id,list[0].lineup[0].to_string())

events = sb.events(match_id=7494, fmt="json")
print(events)
f = open("events.txt", "w")
f.write(json.dumps(events))
f.close()
