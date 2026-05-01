# from src.feedAPI import PlayerAPI
from src.feedAPI import TeamAPI
from src.feedAPI import Connector as Con
from src.events.Events import EventTypes
from src.events.QTypes import QTypes_PassEvents, QTypes_ShortLocationDescriptor, QTypes_FoulCardEvents, \
    QTypes_GoalkeeperEvents


def print_test(funct_name, result, param1, param2):  # * to print well test results
    print("<----------------------------------------------------------------------------->")
    print("test for {} has been started".format(funct_name))
    print("with {} and {} parameters {} function returns: \n \t-->{}".format(param1, param2, funct_name, result))


if __name__ == "__main__":
    con = Con.Connector()
    con.connect()
    team_obj = TeamAPI.TeamAPI("115", "2018")

    # -----------------------------------------------Test1-----------------------------------------------

    # result1 = team_obj.getTeamEvents("Galatasaray")
    # print_test("getTeamEvents()", result1, "Galatasaray", None)
    # print(f"length is {len((result1))}")

    # -----------------------------------------------Test2-----------------------------------------------

    # result2 = team_obj.getTeamID("Galatasaray")
    # print_test("getTeamID()", result2, "Galatasaray", None)

    # -----------------------------------------------Test3-----------------------------------------------
    # team_obj.calculateStatistics("Akhisarspor")
    # team_obj.calculateStatistics("Antalyaspor")
    # team_obj.calculateStatistics("Konyaspor")
    # team_obj.calculateStatistics("Alanyaspor")

    # -----------------------------------------------Test4-----------------------------------------------

    result4 = team_obj.getTeamStatistics("Galatasaray")
    # result5 = team_obj.getTeamStatistics("Besiktas")
    # result6 = team_obj.getTeamStatistics("Fenerbahçe")

    print_test("getTeamStatistics()", result4, "Galatasaray", None)
    # print_test("getTeamStatistics()", result5, "Besiktas", None)
    # print_test("getTeamStatistics()", result5, "Fenerbahçe", None)

    # -----------------------------------------------Test5-----------------------------------------------

    # -----------------------------------------------Test6-----------------------------------------------

    # res6 = team_obj.getTeamEventGroup("Galatasaray", "shotEvent", None)
    # print_test("getTeamEventGroup", res6, "Galatasaray", "shotEvent")
    #
    # res6 = team_obj.getTeamEventGroup("Besiktas", "shotEvent", ["goals", "total_shots", "shots_on_target"])
    # print_test("getPlayerEventGroup", res6, "Besiktas", ["goals", "total_shots", "shots_on_target"])
    #
    # res6 = team_obj.getTeamEventGroup("Galatasaray", "goalkeeperEvent")
    # print_test("getTeamEventGroup", res6, "Galatasaray", "goalkeeperEvent")
    #
    # res6 = team_obj.getTeamEventGroup("Fenerbahçe", "foulEvent", None)
    # print_test("getPlayerEventGroup", res6, "Fenerbahçe", "foulEvent")
    #
    # res6 = team_obj.getTeamEventGroup("Trabzonspor", None, None)
    # print_test("getPlayerEventGroup", res6, "Trabzonspor", None)
    #
    # # -----------------------------------------------Test7-----------------------------------------------
    # stat_list3 = [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
    #               ("shotEvent", ("goals", "total_shots", "shots_on_target")),
    #               ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
    #               ["ast"], ["passEvent", ["passes_total", "pass_success_rate"]],
    #               ["aerialEvent"]]
    #
    # res7 = team_obj.callTeam("Galatasaray", stat_list3)
    # print_test("callTeam()", res7, "Galatasaray", stat_list3)
    #
    res7 = team_obj.callTeam("Bursaspor")
    print_test("callTeam()", res7, "Bursaspor", None)
    #
    # # -----------------------------------------------Test8-----------------------------------------------
    #
    # res8 = team_obj.compareTeams("Galatasaray", ["Besiktas", "Bursaspor", "Akhisarspor", "Trabzonspor"])
    # for i in range(len(res8)):
    #     print_test("comparePlayers_V3:->", res8[i], res8[i]["team_name"], None)
    #
    # res8 = team_obj.compareTeams("Galatasaray", ["Besiktas", "Bursaspor", "Akhisarspor", "Trabzonspor"], stat_list3)
    # for i in range(len(res8)):
    #     print_test("comparePlayers_V3:->", res8[i], res8[i]["team_name"], stat_list3)
    #
    # # -----------------------------------------------Test9-----------------------------------------------
    #
    # res9 = team_obj.rankLeagueTeams("shotEvent", "goals", 18)
    # print_test("rankLeaguePlayers_V2()", res9, "shotEvent", "goals")
    #
    # # -----------------------------------------------Test10-----------------------------------------------
    #
    # res10 = team_obj.rankLeagueTeams("shotEvent", "own_goal", 18)
    # print_test("rankLeaguePlayers_V2()", res10, "shotEvent", "own_goal")

    # -----------------------------------------------Test11-----------------------------------------------

    # res11 = team_obj.getTeamName("t2136")
    # print_test("getTeamName()", res11, "t2136", None)

    # -----------------------------------------------Test12------0-----------------------------------------

    # res12 = team_obj.getTeamAllPlayerNames("Galatasaray", "all")
    # print_test("getTeamAllPlayerNames()", res12, "Galatasaray", "all")

    # -----------------------------------------------Test13-----------------------------------------------

    # res13 = team_obj.getTransferredPlayerNames("Galatasaray")
    # print_test("getTransferredPlayerNames()", res13, "Galatasaray", None)

    # -----------------------------------------------Test14-----------------------------------------------

    # res14 = team_obj.compareTeamEventStatistics(["Galatasaray", "Besiktas", "Fenerbahçe"])
    # print_test("compareTeamEventStatistics()", res14, ["Galatasaray", "Besiktas", "Fenerbahçe"], None)

    # -----------------------------------------------Test15-----------------------------------------------

    # res15 = team_obj.getTeamEvents("Galatasaray")
    # res15_1 = team_obj.getTeamEventsByMinSec("Galatasaray", 0, 90)

    # print(f"length of getTeamEvents result: {len(res15)}")
    # print(f"length of getTeamEventsByMinSec result: {len(res15_1)}")

    # -----------------------------------------------Test16-----------------------------------------------

    # res16 = team_obj.getTeamKey("Galatasaray")
    # print_test("getTeamKey()", res16, "Galatasaray", None)

    # -----------------------------------------------Test16-----------------------------------------------

    # res16 = team_obj.getTeamGamesEvent("Galatasaray", 4, 3)
    # print_test("getTeamGamesEvent()", res16, "Galatasaray", "4, 3")
    # print(len(res16[0].events))
    # print(len(res16[1].events))
    # print(len(res16[2].events))

    # -----------------------------------------------Test17-----------------------------------------------

    # print(res16)
    # # print(res16[3])
    # print(len(res16))
    # print(len(res16[3]))

    # res17 = team_obj.getTeamGamesStatistics("Galatasaray", 17, 3)
    # print_test("getTeamGamesStatistics()", res17, "Galatasaray", "17, 3")
    # print(type(res17))

    # -----------------------------------------------Test18-----------------------------------------------

    # res18 = team_obj.getTeamGamesEventWithGameIDs("Galatasaray", [1002148, 1002163])
    # res18 = team_obj.getTeamGamesEventWithGameIDs("Galatasaray", [1002148])
    # print(res18)
    # for game in res18:
    #     print(game.ID)
    #     print(len(game.events))
    # res18 = team_obj.getTeamGamesStatisticsWithGameIDs("Galatasaray", [1002148, 1002163])
    # print_test("getTeamGamesStatisticsWithGameIDs", res18, "Galatasaray", [1002148])

    # -----------------------------------------------Test19-----------------------------------------------



    # res19 = team_obj.getTeamGamesStatisticsWithDate("Galatasaray", "2018-08-10", "2019-03-03")
    # print_test("getTeamGamesStatisticsWithDate()", res19, "Galatasaray", "2018-08-10, 2019-03-03")

    # -----------------------------------------------Test20-----------------------------------------------
    #
    # res20 = team_obj.getTeamGamesEventSeperatedHalf("Galatasaray", [1002148, 1002163])
    # print_test("getTeamGamesEventSeperatedHalf()", res20, "Galatasaray", [1002148, 1002163])

    # res20_1 = team_obj.getTeamGamesStatisticsSeperatedHalf("Galatasaray", [1002148])
    # print_test("getTeamGamesStatisticsSeperatedHalf()", res20_1, "Galatasaray", [1002148])
    # print(res20_1["FirstHalves"])

    # -----------------------------------------------Test21-----------------------------------------------

    # res21 = team_obj.getTeamGamesEventSeperatedMins("Galatasaray", [1002148], team_obj.minute_parser([4, 7, 45]))
    # print(res21)
    #
    # res21_1 = team_obj.getTeamGamesStatisticsSeperatedMins("Galatasaray", [1002148, 1002173], [])
    # print_test("getTeamGamesStatisticsSeperatedMins()", res21_1, "Galatasaray", "[1002148, 1002173], [15, 35, 65]")

    # -----------------------------------------------Test22-----------------------------------------------

    # res22 = team_obj.getTeamGamesEventSeperatedByRedCards("Galatasaray", 1002180)
    # print_test("getTeamGamesEventSeperatedByRedCards()", res22, "Galatasaray", 1002180)
    #
    # res22_1 = team_obj.getTeamGamesStatisticsSeperatedByRedCards("Galatasaray", 1002180)
    # print_test("getTeamGamesStatisticsSeperatedByRedCards()", res22_1, "Galatasaray", 1002180)

    # -----------------------------------------------Test23-----------------------------------------------

    # res23 = team_obj.getTeamGamesEventSeperatedByGoals("Galatasaray", 1002186)
    # print_test("getTeamGamesEventSeperatedByGoals()", res23, "Galatasaray", 1002186)
    #
    # res23_1 = team_obj.getTeamGamesStatisticsSeperatedByGoals("Galatasaray", 1002186)
    # print_test("getTeamGamesStatisticsSeperatedByGoals()", res23_1, "Galatasaray", 1002186)

    # -----------------------------------------------Test24-----------------------------------------------

    # res24 = team_obj.getTeamGamesEventWithGameIDs("Galatasaray", [1002270])
    # teamID = int(team_obj.getTeamID("Galatasaray")[1:])
    # events = []
    # start_events = []
    # end_events = []
    # team_counter = 0
    # counter = 0
    # ball_opponent = False
    # for event in res24[0].events:
    #     counter += 1
    #     if event.teamID == teamID:
    #         events.append(event)
    #         # if EventTypes[str(event.typeID)] == "Pass":
    #         team_counter += 1
    #         qEvents = event.qEvents
    #         print(str(team_counter) + ": " + "TeamID: " + str(event.teamID) + ", " + EventTypes[
    #             str(event.typeID)] + " , min:" + str(event.min) + " sec: " + str(event.sec) + " , outcome: " + str(
    #             event.outcome))
    #         for qevent in qEvents:
    #             try:
    #                 print(f"\t->{QTypes_PassEvents[str(qevent.qualifierID)]}: {qevent.value}")
    #             except Exception as err:
    #                 try:
    #                     print(f"\t->{QTypes_GoalkeeperEvents[str(qevent.qualifierID)]}: {qevent.value}")
    #                 except Exception as err2:
    #                     continue
    #         if EventTypes[str(event.typeID)] in ["Attempt Saved", "Miss", "Post", "Goal"]:
    #             end_events.append(event)
    #
    # print(len(events))
    # print(f"length of end events is {len(end_events)}")
    # print(f"end events: {end_events}")

    # res24_1 = team_obj.getTeamGamesStatisticsWithGameIDs("Akhisarspor", [1002152])
    # print_test("getTeamGamesStatisticsWithGameIDs()", res24_1, "Akhisarspor", [1002152])
    #
    res24_2 = team_obj.getTeamGamesStatisticsWithGameIDs("Galatasaray", [1002301], "goalkeeper")
    print_test("getTeamGamesStatisticsWithGameIDs()", res24_2, "Galatasaray", [1002301])


    # team_obj.calculateTeamStatistics("Galatasaray")
    # team_obj.calculateStatistics("Galatasaray")
    # res24_3 = team_obj.try_smt("Besiktas", 1002152)

    # -----------------------------------------------Test25-----------------------------------------------

    # res25 = team_obj.getTeamGamesStatisticsSeperatedByGoals("Galatasaray", 1002270)
    # res25_1 = team_obj.getTeamGamesStatisticsSeperatedByGoals("Besiktas", 1002270)

    # res25 = team_obj.attack_sequence_analysis("Galatasaray", 1002270)
    # res25_1 = team_obj.attack_sequence_analysis("Besiktas", 1002270)

    # print(res25)
    # print_test("getTeamGamesStatisticsSeperatedByGoals()", res25, "Galatasaray", 1002270)

    # for stat in res25:
    #     for stat_type in stat:
    #         if stat_type == "pass":
    #             temp = dict()
    #             temp['Total passes attempted'] = stat[stat_type]['Total passes attempted']
    #             temp['Average pass distance'] = stat[stat_type]['Average pass distance']
    #             temp['Total passes attempted in defensive third'] = stat[stat_type][
    #                 'Total passes attempted in defensive third']
    #             temp['Total passes attempted in middle third'] = stat[stat_type][
    #                 'Total passes attempted in middle third']
    #             temp['Total passes attempted in attacking third'] = stat[stat_type][
    #                 'Total passes attempted in attacking third']
    #             temp_result = dict()
    #             temp_result["pass"] = temp
    #             print(temp_result)
    #         elif stat_type == "shot":
    #             temp = dict()
    #             temp['Goals'] = stat[stat_type]['Goals']
    #             temp['otal shots (excluding blocks)'] = stat[stat_type]['otal shots (excluding blocks)']
    #             temp['Shots from inside the box'] = stat[stat_type]['Shots from inside the box']
    #             temp['Shots from outside the box'] = stat[stat_type]['Shots from outside the box']
    #             temp['Total shots on target'] = stat[stat_type]['Total shots on target']
    #             temp['Total big chances'] = stat[stat_type]['Total big chances']
    #             temp['Shots on target from big chances'] = stat[stat_type]['Shots on target from big chances']
    #             temp['Shots off target from big chances'] = stat[stat_type]['Shots off target from big chances']
    #             temp_result = dict()
    #             temp_result["shot"] = temp
    #             print(temp_result)
    #         elif stat_type == "touch":
    #             temp = dict()
    #             temp['total touches'] = stat[stat_type]['total touches']
    #             temp['touches in defensive third'] = stat[stat_type]['touches in defensive third']
    #             temp['touches in middle third'] = stat[stat_type]['touches in middle third']
    #             temp['touches in attacking third'] = stat[stat_type]['touches in attacking third']
    #             temp_result = dict()
    #             temp_result["touch"] = temp
    #             print(temp_result)
    #         elif stat_type == "assist":
    #             temp = dict()
    #             temp['total assists'] = stat[stat_type]['total assists']
    #             temp['total intentional assists'] = stat[stat_type]['total intentional assists']
    #             temp['total key passes for first touch shot'] = stat[stat_type][
    #                 'total key passes for first touch shot']
    #             temp_result = dict()
    #             temp_result["assist"] = temp
    #             print(temp_result)
    #         elif stat_type == "goalkeeper":
    #             temp = dict()
    #             temp['crosses faced'] = stat[stat_type]['crosses faced']
    #             temp['goals against'] = stat[stat_type]['goals against']
    #             temp['Saves'] = stat[stat_type]['Saves']
    #             temp['Shots against'] = stat[stat_type]['Shots against']
    #             temp['Shots on target against'] = stat[stat_type]['Shots on target against']
    #             temp_result = dict()
    #             temp_result["goalkeeper"] = temp
    #             print(temp_result)
    #         else:
    #             print(stat)
    #
    # for stat in res25_1:
    #     for stat_type in stat:
    #         if stat_type == "pass":
    #             temp = dict()
    #             temp['Total passes attempted'] = stat[stat_type]['Total passes attempted']
    #             temp['Average pass distance'] = stat[stat_type]['Average pass distance']
    #             temp['Total passes attempted in defensive third'] = stat[stat_type][
    #                 'Total passes attempted in defensive third']
    #             temp['Total passes attempted in middle third'] = stat[stat_type][
    #                 'Total passes attempted in middle third']
    #             temp['Total passes attempted in attacking third'] = stat[stat_type][
    #                 'Total passes attempted in attacking third']
    #             temp_result = dict()
    #             temp_result["pass"] = temp
    #             print(temp_result)
    #         elif stat_type == "shot":
    #             temp = dict()
    #             temp['Goals'] = stat[stat_type]['Goals']
    #             temp['otal shots (excluding blocks)'] = stat[stat_type]['otal shots (excluding blocks)']
    #             temp['Shots from inside the box'] = stat[stat_type]['Shots from inside the box']
    #             temp['Shots from outside the box'] = stat[stat_type]['Shots from outside the box']
    #             temp['Total shots on target'] = stat[stat_type]['Total shots on target']
    #             temp['Total big chances'] = stat[stat_type]['Total big chances']
    #             temp['Shots on target from big chances'] = stat[stat_type]['Shots on target from big chances']
    #             temp['Shots off target from big chances'] = stat[stat_type]['Shots off target from big chances']
    #             temp_result = dict()
    #             temp_result["shot"] = temp
    #             print(temp_result)
    #         elif stat_type == "touch":
    #             temp = dict()
    #             temp['total touches'] = stat[stat_type]['total touches']
    #             temp['touches in defensive third'] = stat[stat_type]['touches in defensive third']
    #             temp['touches in middle third'] = stat[stat_type]['touches in middle third']
    #             temp['touches in attacking third'] = stat[stat_type]['touches in attacking third']
    #             temp_result = dict()
    #             temp_result["touch"] = temp
    #             print(temp_result)
    #         elif stat_type == "assist":
    #             temp = dict()
    #             temp['total assists'] = stat[stat_type]['total assists']
    #             temp['total intentional assists'] = stat[stat_type]['total intentional assists']
    #             temp['total key passes for first touch shot'] = stat[stat_type][
    #                 'total key passes for first touch shot']
    #             temp_result = dict()
    #             temp_result["assist"] = temp
    #             print(temp_result)
    #         elif stat_type == "goalkeeper":
    #             temp = dict()
    #             temp['crosses faced'] = stat[stat_type]['crosses faced']
    #             temp['goals against'] = stat[stat_type]['goals against']
    #             temp['Saves'] = stat[stat_type]['Saves']
    #             temp['Shots against'] = stat[stat_type]['Shots against']
    #             temp['Shots on target against'] = stat[stat_type]['Shots on target against']
    #             temp_result = dict()
    #             temp_result["goalkeeper"] = temp
    #             print(temp_result)
    #         else:
    #             print(stat)
    #



    # team_obj.attack_sequence_analysis("Besiktas", 1002388)
    # team_obj.attack_sequence_analysis("Galatasaray", 1002301)
    # team_obj.attack_sequence_analysis("Galatasaray", 1002367)

    # res26 = team_obj.getTeamAverageEventGroup("all_teams", "average", None, None)
    #
    # print_test("getTeamAverageEventGroup()", res26, "all_teams", "average")
    #
    # res27 = team_obj.get_general_team_stats(doc_name="all_teams", team_ids=team_obj.getTeamID("Galatasaray"))
    # print(res27)

    # print(team_obj.getGamesPlayedByTeam(team_obj.getTeamID("Galatasaray")))
    #
    # print(team_obj.get_team_matches("Akhisarspor"))


    # team_obj.get_team_data("Galatasaray")

    print(len(team_obj.getTeamGamesEventWithDate("Galatasaray", "2018-08-10", "2019-03-03")))
