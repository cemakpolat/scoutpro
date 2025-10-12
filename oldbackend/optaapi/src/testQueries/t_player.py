from src.feedAPI import PlayerAPI
from src.dbase import DBHelper
from src.feedAPI import Connector
from src.events.Events import EventIDs

 # from mongoengine import *


 # TODO import time and calculate fetching time for functions
 # TODO import random to give random parameters to functions

def getTeamName(playerName):
    teams = DBHelper.F40_Team.objects.fields(name=1, players=1)
    for i in range(len(teams)):
        for j in range(len(teams[i].players)):
            if playerName == teams[i].players[j].name:
                return teams[i].name


def name_extract_stat(data):  # for map function
    return data.playerName


def name_extract_player(data):  # for map function
    return data.name


def print_test(functName, result, param1= None, param2= None):  # * to print well test results
    print("<----------------------------------------------------------------------------->")
    print("test for {} has been started".format(functName))
    print("with {} and {} parameters {} function returns: \n \t-->{}".format(param1, param2, functName, result))


if __name__ == "__main__":
    con = Connector.main_conn
    con.connect()
    plObj = PlayerAPI.PlayerAPI("115", "2018")
    # -----------------------------------------------Test1-----------------------------------------------

    # res1 = plObj.getPlayerID_Alt("Milan Lukac")
    # print_test("getPlayerID_Alt()", res1, "Milan Lukac", "empty")
    #
    # res1_2 = plObj.getPlayerID("Milan Lukac", getTeamName("Milan Lukac"))
    # print_test("getPlayerID()", res1_2, "Milan Lukac", getTeamName("Milan Lukac"))
    #
    # # -----------------------------------------------Test2-----------------------------------------------

    # res2_2 = plObj.getAllPlayerIDs("Galatasaray")
    # print_test("getAllPlayerIDs()", res2_2, "Galatasaray", "empty")
    #
    # res2 = plObj.getAllPlayerIDs_Alt("Galatasaray")
    # print_test("getAllPlayerIDs_Alt()", res2, "Galatasaray", "empty")
    #
    # res2 = plObj.getAllPlayerIDs_Alt("Galatasaray", "left")
    # print_test("getAllPlayerIDs_Alt()", res2, "Galatasaray", "left")
    #
    # res2 = plObj.getAllPlayerIDs_Alt("Galatasaray", "all")
    # print_test("getAllPlayerIDs_Alt()", res2, "Galatasaray", "all")

    # # -----------------------------------------------Test3-----------------------------------------------
    #
    # res3 = plObj.getTeamID_Alt("Akhisarspor")
    # print_test("getTeamID_Alt()", res3, "Akhisarspor", "empty")
    #
    # res3_2 = plObj.getTeamID("Akhisarspor")
    # print_test("getTeamID()", res3_2, "Akhisarspor", "empty")
    #
    # # -----------------------------------------------Test4-----------------------------------------------
    #
    # res4 = plObj.getAllTeamIDs()
    # print_test("getAllTeamID()", res4, "empty", "empty")
    #
    # # -----------------------------------------------Test5-----------------------------------------------
    #
    # # res5 = plObj.getAllPlayersInTeam_Alt("Besiktas") # printing this cost a lot of time
    # # print("length of getAllPlayer_Alt is {} and length of list of F24_ev is {} ".format(len(res5), len(res5[0])))
    # # print_test("getAllPlayersInTeam_Alt()", res5, "empty", "empty")
    #
    # # res5_2 = plObj.getAllPlayersInTeam("Besiktas") #not run this every time it is too costly
    # # print("length of getAllPlayer is {} and length of list of F24_ev is {} ".format(len(res5_2),len(res5_2[0])))
    # # print_test("getAllPlayersInTeam()", res5_2, "Besiktas", "empty")
    #
    # # -----------------------------------------------Test6-----------------------------------------------
    # res6_2 = plObj.getTeamAllPlayerNames("Galatasaray")
    # print_test("getTeamAllPlayerNames()", res6_2, "Galatasaray", "empty")
    #
    # res6 = plObj.getTeamAllPlayerNames_Alt("Galatasaray")
    # print_test("getTeamAllPlayerNames_Alt()", res6, "Galatasaray", "empty")
    #
    # res6 = plObj.getTeamAllPlayerNames_Alt("Galatasaray", "left")
    # print_test("getTeamAllPlayerNames_Alt()", res6, "Galatasaray", "left")
    #
    # res6 = plObj.getTeamAllPlayerNames_Alt("Galatasaray", "all")
    # print_test("getTeamAllPlayerNames_Alt()", res6, "Galatasaray", "all")



    # # -----------------------------------------------Test7-----------------------------------------------
    #
    # # res7 = plObj.getPlayerEvents_Alt("Galatasaray", "Mbaye Diagne")
    # # print_test("getPlayerEvents_Alt()", res7, "Galatasaray", "Mbaye Diagne")
    # # print("length of obj is {}".format(len(res7)))
    # #
    # # res7_2 = plObj.getPlayerEvents("Galatasaray", "Mbaye Diagne")
    # # print_test("getPlayerEvents()", res7_2, "Galatasaray", "Mbaye Diagne")
    # # print("length of obj is {}".format(len(res7_2)))
    # #
    # # res7_3 = plObj.getPlayerEvents("Galatasaray", "Fernando Muslera")
    # # print_test("getPlayerEvents()", res7_3, "Galatasaray", "Fernando Muslera")
    # # print("length of obj is {}".format(len(res7_3)))
    #
    # # -----------------------------------------------Test8-----------------------------------------------
    #
    # res8 = plObj.getDuplicatePlayersID()
    # print_test("getDuplicatePlayersID()", res8, "empty", "empty")


    # res8_2 = plObj.getDiffPlayers()
    # print_test("getDiffPlayers()", res8_2, "empty", "empty")

    # res8_3 = plObj.getDuplicatePlayersName()
    # print_test("getDuplicatePlayersName()", res8_3, "empty", "empty")

    # # -----------------------------------------------Test9-----------------------------------------------
    #
    # print("<--------------------------------------Test For Duplicate Players-------------------------------------->")
    # print("length of return array of getDuplicatePlayersID() is: {}".format(len(res8)))
    # print("length of return array of getDiffPlayers()      is: {}".format(len(res8_2)))
    # print("length of return array of getDiffPlayersNames()      is: {}".format(len(res8_3)))
    # res8.sort()
    # res8_2.sort()
    # print("sorted list returned by getDuplicatePlayersID() is:\n{}".format(res8))
    # print("sorted list returned by getDiffPlayers() is:\n{}".format(res8_2))
    #
    # # -----------------------------------------------Test10-----------------------------------------------
    #
    # # gids = plObj.getGameKeys(plObj.getTeamKey("Galatasaray"),34)
    # # print(gids)
    #
    # # res10_2 = plObj.getAllPlayerNames("Yeni Malatyaspor")
    # # print_test("getAllPlayerNames()", res10_2, "Besiktas", "empty")
    #
    # # -----------------------------------------------Test11-----------------------------------------------
    #
    # data11 = {
    #     "event": "aerial",
    #     "filters": ['totalDuels', 'won', 'lost', 'wonPercentage', 'attackingHalf']
    # }
    # res11 = plObj.getAerial_Alt("Adem Ljajic", data11["filters"])
    # print_test("getAerial_Alt()", res11, "Adem Ljajic", data11["filters"])
    # print(type(res11))
    #
    # # -----------------------------------------------Test12-----------------------------------------------
    #
    # data12 = {
    #     "event": "asist",
    #     "filters": ['total_assists', 'intentional_assists', 'assist_for_first_touch_goal', 'key_passes', 'minutes_per_chance']
    # }
    # res12 = plObj.getAsist("Edin Visca", data12["filters"])  #* I tested asist leader in this season, and it matched with the real value
    # print_test("getAsist()", res12, "Edin Visca", data12["filters"])
    #
    # res12_2 = plObj.getAsist("Ricardo Quaresma", data12["filters"])  # * I tested 2nd asist leader in this season, and it matched with the real value
    # print_test("getAsist()", res12_2, "Ricardo Quaresma", data12["filters"])
    #
    # res12_3 = plObj.getAsist("Adem Ljajic", data12["filters"])  # * I tested 3rd asist leader in this season, and it matched with the real value
    # print_test("getAsist()", res12_3, "Adem Ljajic", data12["filters"])
    #
    # # -----------------------------------------------Test13-----------------------------------------------
    #
    # data13 = {
    #     "event": "ball control",
    #     "filters": ['total_dispossessed', 'errors', 'error_led_to_goal', 'error_led_to_shot', 'error_led_to_shot', 'caught_offside', 'ball_touch', 'ball_hit_the_player', 'unsuccessful_control']
    # }
    #
    # res13 = plObj.getBallControl("Edin Visca", data13["filters"])
    # print_test("getBallControl()", res13, "Edin Visca", data13["filters"])
    #
    # # -----------------------------------------------Test14-----------------------------------------------
    #
    # data14 = {
    #     "event": "foul",
    #     "filters": ['fouls_won', 'fouls_conceded', 'penalty_conceded', 'penalty_won', 'fouls_won_in_attacking_third', 'fouls_committed_in_defending_third']
    # }
    #
    # res14 = plObj.getFoul("Tiago Lopes", data14["filters"])
    # print_test("getFoul()", res14, "Tiago Lopes", data14["filters"])
    #
    # res14_2 = plObj.getFoul("Ricardo Quaresma", data14["filters"])
    # print_test("getFoul()", res14_2, "Ricardo Quaresma", data14["filters"])
    #
    # res14_3 = plObj.getFoul("Burak Yilmaz", data14["filters"])  # * it has a duplicate entry in db, but because of first() in db, probably it does not give error
    # print_test("getFoul()", res14_3, "Burak Yilmaz", data14["filters"])
    #
    # # -----------------------------------------------Test15-----------------------------------------------
    #
    # data15 = {
    #     "event": "card",
    #     "filters": ['total_cards', 'yellow_card', 'second_yellow_card', 'red_card', 'card_rescinded']
    # }
    # res15 = plObj.getCard("Tiago Lopes", data15["filters"])
    # print_test("getCard()", res15, "Tiago Lopes", data15["filters"])  # * I tested card leader in this season, and it matched with the real value
    #
    # res15_2 = plObj.getCard("Sadik Ciftpinar", data15["filters"])
    # print_test("getCard()", res15_2, "Sadik Ciftpinar", data15["filters"])  # ! I tested 2nd card leader in this season and it !did not match with the real value
    #
    # res15_3 = plObj.getCard("Thievy", data15["filters"])
    # print_test("getCard()", res15_3, "Thievy", data15["filters"])  # ! I tested 3rd card leader in this season and it !did not match with the real value
    #
    # # -----------------------------------------------Test16-----------------------------------------------
    #
    # data16 = {
    #     "event": "take on",
    #     "filters": ['total_take_ons', 'take_ons_successful', 'take_ons_unsuccessful', 'take_on_success_rate',
    #                 'take_on_success_rate_attacking_third',  'successful_take_ons_in_box', 'tackled']
    # }
    #
    # res16 = plObj.getTakeOn("Edin Visca", data16["filters"])
    # print_test("getTakeOn()", res16, "Edin Visca", data16["filters"])
    #
    # # -----------------------------------------------Test17-----------------------------------------------
    #
    # data17 = {
    #     "event": "touch",
    #     "filters": ['total_touches', 'total_touches_in_defensive_third', 'total_touches_in_box', 'total_tackles',
    #                 'total_successful_tackles', 'total_challenges', 'tackle_attempts', 'total_interceptions_in_attacking_third']}
    #
    # res17 = plObj.getTouch("Edin Visca", data17["filters"])
    # print_test("getTouch()", res17, "Edin Visca", data17["filters"])
    #
    # # -----------------------------------------------Test18-----------------------------------------------
    #
    # data18 = {
    #     "event": "duel",
    #     "filters": ['total_duels', 'successful_duels', 'unsuccessful_duels', 'duel_success_rate']
    # }
    #
    # res18 = plObj.getDuel("Edin Visca", data18["filters"])
    # print_test("getDuel()", res18, "Edin Visca", data18["filters"])
    #
    # # -----------------------------------------------Test19-----------------------------------------------
    #
    # data19 = {
    #     "event": "shoot and goal",
    #     "filters": ['goals', 'goals_inside_the_box', 'goals_outside_the_box', 'non_penalty_goals', 'total_shots',
    #                 'shots_off_target', 'shots_on_target', 'chance_missed', 'shooting_percentage']
    # }
    #
    # res19 = plObj.getShotAndGoal("Mbaye Diagne", data19["filters"])          # duplicate goes Kasimpasa to Galatasaray
    # print_test("getShotAndGoal()", res19, "Mbaye Diagne", data19["filters"]) # ! I tested goal leader in this season and it !did not match with the real value
    #
    # res19_2 = plObj.getShotAndGoal("Vedat Muriqi", data19["filters"])
    # print_test("getShotAndGoal()", res19_2, "Vedat Muriqi", data19["filters"]) # * I tested 2nd goal leader in this season, and it matched with the real value
    #
    # # -----------------------------------------------Test20-----------------------------------------------
    #
    # data20 = {
    #     "event": "goalkeeping",
    #     "filters": ['clean_sheet', 'crosses_faced', 'cross_percentage_gk', 'goal_kicks', 'successful_gk_throws',
    #                 'save_percentage', 'save_1on1', 'saves', 'save_penalty']
    # }
    #
    # res20 = plObj.getGoalKeeping("Fernando Muslera", data20["filters"])
    # print_test("getGoalKeeping()", res20, "Fernando Muslera", data20["filters"])
    #
    # res20_1 = plObj.getGoalKeeping("Ugurcan Cakir", data20["filters"])
    # print_test("getGoalKeeping()", res20_1, "Ugurcan Cakir", data20["filters"])
    #
    # res20_2 = plObj.getGoalKeeping("Onur Kivrak", data20["filters"]) #! tehere is no playerstat object for this player :(
    # print_test("getGoalKeeping()", res20_2, "Onur Kivrak", data20["filters"]) # ! he was retired at the half season
    #
    # res20_3 = plObj.getGoalKeeping("Loris Karius", data20["filters"])
    # print_test("getGoalKeeping()", res20_3, "Loris Karius", data20["filters"])

    # # -----------------------------------------------Test21-----------------------------------------------

    # ? Test to find players whose teams are at first half and second half.
        # ? If second one is None playes (should) is not transferred to other team

    # res21 = plObj.getOldTeamWithName("Loris Karius")
    # print_test("getOldTeamWithName()", res21, "Loris Karius", "empty")
    #
    # res21_2 = plObj.getCurrentTeamWithName("Loris Karius")
    # print_test("getCurrentTeamWithName()", res21_2, "Loris Karius", "empty")
    #
    # res21_3 = plObj.getOldTeamWithName("Burak Yilmaz")
    # print_test("getOldTeamWithName()", res21_3, "Burak Yilmaz", "empty")
    #
    # res21_4 = plObj.getCurrentTeamWithName("Burak Yilmaz")
    # print_test("getCurrentTeamWithName()", res21_4, "Burak Yilmaz", "empty")
    #
    # res21_5 = plObj.getOldTeamWithName("Mbaye Diagne")
    # print_test("getOldTeamWithName()", res21_5, "Mbaye Diagne", "empty")
    #
    # res21_6 = plObj.getCurrentTeamWithName("Mbaye Diagne")
    # print_test("getCurrentTeamWithName()", res21_6, "Mbaye Diagne", "empty")
    #
    # res21_7 = plObj.getOldTeamWithName("Onur Kivrak")
    # print_test("getOldTeamWithName()", res21_7, "Onur Kivrak", "empty")
    #
    # res21_8 = plObj.getCurrentTeamWithName("Onur Kivrak")
    # print_test("getCurrentTeamWithName()", res21_8, "Onur Kivrak", "empty")  # * This player has been retired at the half

    # !!! This is really important
    # ! I taught the small list hold the new transferred player, but it is not. It holds the player who left the team.

    # # -----------------------------------------------Test22-----------------------------------------------
    #
    # # res22 = plObj.getPlayerBothTeam(plObj.getDuplicatePlayersName())
    # # print_test("getPlayerBothTeam()", res22, plObj.getDuplicatePlayersName(), "empty") # normally using funct at 2 time is bad practice in terms of performance
    # # print(len(res22))
    #
    # # -----------------------------------------------Test23-----------------------------------------------
    # # ---------------------------------------Test for some players statistics---------------------------------------
    # playerArray = [
    #     "Avdija Vrsajevic",
    #     "Hélder Barbosa",
    #     "Adrien Regattin",
    #     "Yavuz Özbakan",
    #     "Ufuk Ceylan",
    #     "Ceyhun Gülselam",
    #     "Lucas Villafañez",  # ! 1 assist lost (5-6) <- (ourData,original).
    #     "Kerem Göcen",
    #     "Héctor Canteros",
    #     "Ender Aygören",
    #     "Ozan Özenc",
    #     "Nazim Sangaré",
    #     "Mevlüt Erdinc",
    #     "Léo Schwechlen",
    #     "Moussa Koné",
    #     "Aurélien Chedjou",
    #     "Stéphane Badji",
    #     "Berke Özer",
    #     "Roman Neustädter",
    #     "Martin Skrtel",
    #     "Sadik Ciftpinar",  # ! He transferred from Yeni Malatyaspor to Fenerbahçe at half. His statistics are wrong
    #     "Eljif Elmas",
    #     "Marcão",
    #     "André Castro",  # ! 1 assist lost (8-9) <- (ourData,original).
    #     "Gaël Clichy",
    #     "Ugur Uçar",
    #     "Edin Visca",
    #     "Márcio Mossoró",  # ! 1 assist lost (3-4) <- (ourData,original).
    #     "Mattias Bjärsmyr",
    #     "João Pereira",
    #     "Yusuf Yazici",
    #     "Ertac Özbir",
    #     "Muenfuh Sincere",
    #     "Thievy",  # ! He transferred from Ankaragücü to Yeni Malatyaspor at half. His statistics are wrong
    #     "Josué",
    #     "Trézéguet",
    #     "Bobô",
    #     "Nicolas Isimat-Mirin",
    #     "Fehmi Mert Günok",
    #     "Fabrice N'Sakala",
    #     "Brice Dja Djédjé",
    #     "Papiss Demba Cissé",
    #     "Jean-Armel Drole",
    #     "Silviu Lung Jr.",
    #     "Jean-Armel Kana-Biyik",
    #     "Onur Kivrak"  # ! He has been retired at half. His statistics are not even exists.
    #     ]
    # for player in playerArray:
    #     plObj.printEverythingPlayer(player)
    #
    # # -----------------------------------------------Test24-----------------------------------------------
    #
    # # res24 = plObj.getPlayerData("Galatasaray", "Henry Onyekuru")
    # # print_test("getPlayerData()", res24, "Henry Onyekuru", "Galatasaray")
    # #
    # # res24_2 = plObj.getPlayerData("Galatasaray", "Fernando Muslera")
    # # print_test("getPlayerData()", res24_2, "Fernando Muslera", "Galatasaray")
    # #
    # # res24_3 = plObj.getPlayerData("Besiktas", "Burak Yilmaz")
    # # print_test("getPlayerData()", res24_3, "Burak Yilmaz", "Besiktas")
    # #
    # # res24_4 = plObj.getPlayerData("Antalyaspor", "Mevlüt Erdinc")
    # # print_test("getPlayerData()", res24_4, "Mevlüt Erdinc", "Antalyaspor")
    # #
    # # res24_5 = plObj.getPlayerData("Galatasaray", "Mbaye Diagne")
    # # print_test("getPlayerData()", res24_5, "Mbaye Diagne", "Galatasaray")
    # #
    # # res24_6 = plObj.getPlayerData("Bursaspor", "Aurélien Chedjou")
    # # print_test("getPlayerData()", res24_6, "Aurélien Chedjou", "Bursaspor")
    # #
    # # res24_7 = plObj.getPlayerData("Trabzonspor", "Onur Kivrak")  #! this player is extremely problematic. Its any type of statistics can not be reached.
    # # print_test("getPlayerData()", res24_7, "Onur Kivrak", "Trabzonspor")
    #
    # # -----------------------------------------------Test25-----------------------------------------------
    # # ? Result: This function works correctly for player who referenced by big F40_Team document.
    # # ? However, for duplicate name player we should pass big F40_Team document team as a parameter and
    # # ? For player who left the Superlig at the half we can not get ID although there is uID for all players.
    # # ! I am suspecting the F40_root Object. It has f40 team reference only for non transferred (big f40_team) document.
    #
    # # res25 = plObj.getPlayerID("Henry Onyekuru", "Galatasaray")
    # # print_test("getPLayerID()", res25, "Henry Onyekuru", "Galatasaray")
    # #
    # # res25 = plObj.getPlayerID("Mbaye Diagne", "Galatasaray")
    # # print_test("getPLayerID()", res25, "Mbaye Diagne", "Galatasaray")
    # #
    # # res25 = plObj.getPlayerID("Onur Kivrak", "Trabzonspor")
    # # print_test("getPLayerID()", res25, "Onur Kivrak", "Trabzonspor")
    # # ! this player is extremely problematic. Its any type of statistics can not be reached.
    #
    # # res25 = plObj.getPlayerID("Álvaro Negredo", "Besiktas")
    # # print_test("getPLayerID()", res25, "Álvaro Negredo", "Besiktas")
    # #
    # # res25 = plObj.getPlayerID("Alican Özfesli", "Istanbul Basaksehir")
    # # print_test("getPLayerID()", res25, "Alican Özfesli", "Istanbul Basaksehir")
    # #
    # # res25 = plObj.getPlayerID("Bafétimbi Gomis", "Galatasaray")
    # # print_test("getPLayerID()", res25, "Bafétimbi Gomis", "Galatasaray")
    #
    # # -----------------------------------------------Test26-----------------------------------------------
    #
    # res26 = plObj.getProblematicPlayers()  # * extremely slow function. Not optimal, just for test purpose
    # print_test("getProblematicPlayers()", res26, "None", "None")
    #
    # # -----------------------------------------------Test27-----------------------------------------------
    #
    # # res27 = plObj.getAllPlayerIDs("Galatasaray") #! Do not contain Bafétimbi Gomis. But should it contain? He left at Aug 23, 2018
    # # print_test("getAllPLayerIDs()", res27, "Galatasaray", None)
    #
    # # -----------------------------------------------Test28-----------------------------------------------
    #
    # # ! this function is probably wrong. Parameter problem.
    # # feed = con.getFeed(
    # #     "feed1", plObj.competitionID, plObj.seasonID
    # # )
    # # res28 = plObj.getAllPlayedGamesBy(feed, "Galatasaray", "p42864")
    # # print_test("getAllPlayedGamesBy()", res28, "p42864", "Galatasaray")
    #
    # # -----------------------------------------------Test29-----------------------------------------------
    #
    # # ! I can not call this function properly because of feed9
    # # res29 = plObj.getGamesPlayedBy("1002163", "Galatasaray", "p42864")
    # # print_test("getGamesPlayedBy()", res29, "Galatasaray", "p42864")
    #
    # # -----------------------------------------------Test30-----------------------------------------------
    #
    # # res30 = plObj.getTeamID("Galatasaray")
    # # print_test("getTeamID()", res30, "Galatasaray", None)
    # #
    # # res30 = plObj.getTeamID("Besiktas")
    # # print_test("getTeamID()", res30, "Besiktas", None)
    # #
    # # res30 = plObj.getTeamID("Fenerbahçe")
    # # print_test("getTeamID()", res30, "Fenerbahçe", None)
    # #
    # # res30 = plObj.getTeamID("Trabzonspor")
    # # print_test("getTeamID()", res30, "Trabzonspor", None)
    # #
    # # res30 = plObj.getTeamID("BB Erzurumspor")
    # # print_test("getTeamID()", res30, "BB Erzurumspor", None)
    #
    # # -----------------------------------------------Test31-----------------------------------------------
    #
    # # res31 = plObj.getGoalKeeperEvents("Galatasaray", "Fernando Muslera")
    # # print_test("getGoalKeeperEvents()", res31, "Fernando Muslera", "Galatasaray")
    #
    # # res31_2 = plObj.getAllEventsByIds(plObj.getTeamID("Galatasaray"), plObj.getPlayerID("Henry Onyekuru", "Galatasaray"))
    #
    #
    # # -----------------------------------------------Test32-----------------------------------------------
    #
    # # plObj.getPlayerKeys("Kasimpasa S.K.")
    # # res32 = plObj.getTransferredPlayerKeys("Kasimpasa S.K.")
    # # print_test("getTransferredPlayerKeys()",res32, "Kasimpasa S.K.", None)
    #
    # # -----------------------------------------------Test33-----------------------------------------------

    # plObj.getPlayerStatistics("Galatasaray", "Mbaye Diagne", None)

    # res33 = plObj.getGoalLeaders(18)
    # print_test("getGoalLeaders()", res33, None, None)

    # # -----------------------------------------------Test34-----------------------------------------------
    #
    # statGroup = [
    #         EventIDs.TouchEvents, EventIDs.ID_17_Card, EventIDs.ShotandGoalEvents, EventIDs.ID_44_Aerial,
    #         EventIDs.GamesandMinutesEvents, EventIDs.ID_4_Foul, EventIDs.BallControlEvents, EventIDs.ID_3_Take_On,
    #         EventIDs.AssistEvents, EventIDs.ID_1_Pass_Events
    #              ]
    #
    goalKeeping = EventIDs.GoalkeeperEvents
    #
    # res34 = []
    # stats = []
    #
    # # res34_0 = plObj.callPlayer("Galatasaray", "Henry Onyekuru", EventIDs.GamesandMinutesEvents)
    # #
    # # for requiredStat in statGroup:
    # #     res34 = res34 + [plObj.callPlayer("Galatasaray", "Mbaye Diagne", requiredStat)]
    # #     stats = stats + [requiredStat]
    # #
    # # res34_2 = plObj.callPlayer("Kayserispor", "Tiago Lopes", EventIDs.ID_17_Card)
    # #
    # res34_3 = plObj.callPlayer("Istanbul Basaksehir", "Fehmi Mert Günok", EventIDs.GoalkeeperEvents)
    # #
    # # res34_4 = plObj.callPlayer("Trabzonspor", "Onur Kivrak", EventIDs.GoalkeeperEvents)
    # #
    # res34_5 = plObj.callPlayer("Galatasaray", "Mbaye Diagne")  # * if requiredStat==None call handle_all_event
    # res34_6 = plObj.callPlayer("Galatasaray", "Mbaye Diagne", EventIDs.AssistEvents)
    # # res34_7 = plObj.callPlayer("Istanbul Basaksehir", "Edin Visca", EventIDs.ID_3_Take_On)
    # #
    # # for i in range(len(stats)):
    # #     print_test("callPlayer()", res34[i], "Mbaye Diagne", stats[i])
    # #
    # # print_test("callPlayer()", res34_0, "Henry Onyekuru", EventIDs.GamesandMinutesEvents)
    # # print_test("callPlayer()", res34_2, "Tiago Lopes", EventIDs.ID_17_Card)
    # print_test("callPlayer()", res34_3, "Fehmi Mert Günok", EventIDs.GoalkeeperEvents)
    # # print_test("callPlayer()", res34_4, "Onur Kivrak", EventIDs.GoalkeeperEvents)
    # print_test("callPlayer()", res34_5, "Mbaye Diagne", "Galatasaray")  # * if requiredStat==None return handle_all_event
    # print_test("callPlayer()", res34_6, "Mbaye Diagne", EventIDs.AssistEvents)
    # # print_test("callPlayer()", res34_7, "Edin Visca", EventIDs.ID_3_Take_On)
    #
    # # -----------------------------------------------Test35-----------------------------------------------

    # res35 = plObj.getAllGames()
    # print_test("getAllGames()", res35, None, None)
    # print(len(res35))

    # # -----------------------------------------------Test36-----------------------------------------------

    # res36 = plObj.getSeasonPlayerPKs()
    # print_test("getSeasonPlayerPKs()", res36, None, None)
    # print(f"length is {len(res36)}")
    #
    # res36_1, res36_2, res36_3 = plObj.getSeasonTeamPKs()
    # print_test("getSeasonTeamPKs()", res36_1, "Main Team IDs: ", None)
    # print(f"length is {len(res36_1)}")
    # print_test("getSeasonTeamPKs()", res36_2, "Left Team IDs: ", None)
    # print(f"length is {len(res36_2)}")
    # print_test("getSeasonTeamPKs()", res36_3, "All Team IDs: ", None)
    # print(f"length is {len(res36_3)}")

    # # -----------------------------------------------Test37-----------------------------------------------

    # ! res37 = plObj.getPlayerData_Alt("Fernando Muslera")  # None teamName parameter only work for player transferred

    # res37_0 = plObj.getPlayerID("Hakan Arslan", "BB Erzurumspor")
    # res37_1 = plObj.getPlayerID("Hakan Arslan", "Sivasspor")
    #
    #
    # print_test("getPlayerID()", res37_0, "Hakan Arslan", "BB Erzurumspor")
    # print_test("getPlayerID()", res37_1, "Hakan Arslan", "Sivasspor")
    #
    # res37_2 = plObj.getPlayerData("Sivasspor", "Hakan Arslan")
    # print_test("getPlayerData()", res37_2, "Hakan Arslan", "Sivasspor")
    #
    # res37_2 = plObj.getPlayerData_Alt("Hakan Arslan", "Sivasspor")
    # print_test("getPlayerData_Alt()", res37_2, "Hakan Arslan", "Sivasspor")
    #
    # res37_2 = plObj.getPlayerData("Trabzonspor", "Onur Kivrak")
    # print_test("getPlayerData()", res37_2, "Onur Kivrak", "Trabzonspor")
    #
    # res37_2 = plObj.getPlayerData_Alt("Onur Kivrak", "Trabzonspor")
    # print_test("getPlayerData_Alt()", res37_2, "Onur Kivrak", "Trabzonspor")
    #
    # res37_2 = plObj.getPlayerData_Alt("Onur Kivrak")
    # print_test("getPlayerData_Alt()", res37_2, "Onur Kivrak", "Trabzonspor")

    # # -----------------------------------------------Test38-----------------------------------------------

    # res38 = plObj.getPositionPlayer("Onur Kivrak")
    # print_test("getPositionPlayer()", res38, "Onur Kivrak", None)
    #
    # res38 = plObj.getPositionPlayer_Alt("Onur Kivrak")
    # print_test("getPositionPlayer_Alt()", res38, "Onur Kivrak", None)
    #
    # res38 = plObj.getPositionPlayer_Alt("Edin Visca", "Istanbul Basaksehir")
    # print_test("getPositionPlayer_Alt()", res38, "Edin Visca", "Istanbul Basaksehir")
    #
    # res38 = plObj.getPositionPlayer_Alt("Edin Visca")  #! I am expecting it will not work.
    # print_test("getPositionPlayer_Alt()", res38, "Edin Visca", None)
    #
    # res38 = plObj.getPositionPlayer("Edin Visca")  # * I am expecting it will work.
    # print_test("getPositionPlayer()", res38, "Edin Visca", None)

    # -----------------------------------------------Test39-----------------------------------------------

    # res39 = plObj.tryLookup()

    # -----------------------------------------------Test40-----------------------------------------------

    # res40 = plObj.comparePlayers("Galatasaray", "Henry Onyekuru", "Mbaye Diagne")
    # print_test("comparePlayers()", res40, "Henry Onyekuru", "Mbaye Diagne")

    # -----------------------------------------------Test41-----------------------------------------------

    # res41 = plObj.getAerial_Alt("Adem Ljajic", [])
    # print_test("getAerial_Alt()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getAsist("Adem Ljajic")
    # print_test("getAsist()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getFoul("Adem Ljajic")
    # print_test("getFoul()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getCard("Adem Ljajic")
    # print_test("getCard()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getDuel("Adem Ljajic")
    # print_test("getDuel()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getTouch("Adem Ljajic")
    # print_test("getTouch()", res41, "Adem Ljajic", None)
    #
    # res41 = plObj.getShotAndGoal("Adem Ljajic")
    # print_test("getShotAndGoal()", res41, "Adem Ljajic", None)
    #
    res41 = plObj.getGoalKeeping("Fernando Muslera")
    print_test("getGoalKeeping()", res41, "Fernando Muslera", None)

    # -----------------------------------------------Test42-----------------------------------------------
    stat_list = [["AssistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                 ("ShotandGoalEvent", ("goals", "total_shots", "shots_on_target")),
                 ("CardEvent", ["total_cards", "yellow_card", "red_card"])]

    stat_list2 = [["AerialEvent"], 30, [1], ("PassEvent", ()), ["FoulEvent"],   ["CardEvent"],
                  ["BallControlEvent"], ["TakeOnEvent"], ["TouchEvent"], ["DuelEvent"],
                  ["ShotandGoalEvent"], ["AssistEvent"], ["GoalkeeperEvent"]]

    stat_list3 = [["assistEvent", ["total_assists", "intentional_assists", "key_passes"]],
                 ("shotEvent", ("goals", "total_shots", "shots_on_target")),
                 ("cardEvent", ["total_cards", "yellow_card", "red_card"]),
                   ["ast"], ["passEvent", ["passes_total",  "pass_success_rate"]],
                  ["aerialEvent"]]

    event_groups = ['aerialEvent', 'passEvent', 'foulEvent', 'cardEvent', 'ballControlEvent', 'takeOnEvent',
                    'touchEvent', 'duelEvent', 'shotEvent', 'assistEvent', 'goalkeeperEvent']
    # res42 = plObj.callPlayer("Istanbul Basaksehir", "Edin Visca", EventIDs.AssistEvents)  # ! slow function
    # res42_1 = plObj.callPlayer_Fast("Edin Visca", "AssistEvent")
    # res42_2 = plObj.callPlayer_Fast("Edin Visca", "AssistEvent", ["total_assists", "intentional_assists", "key_passes"])
    # res42_3 = plObj.callPlayer_Fast_V2("Edin Visca", stat_list)
    # res42_5 = plObj.callPlayer_Fast_V3("Edin Visca", stat_list)
    # res42_6 = plObj.callPlayer_Fast_V3("Mbaye Diagne", stat_list2)  # function can ignore garbage parameters
    # res42_4 = plObj.getPlayerStatistics("Galatasaray", "Mbaye Diagne", None)
    # res42_7 = plObj.callPlayer_Fast_V3("Mbaye Diagne")
    # res42_8 = plObj.callPlayer_Fast_V2("Mbaye Diagne")
    # res42_9 = plObj.callPlayer_Fast_V4("Mbaye Diagne")
    res42_10 = plObj.callPlayer_Fast_V4("Mbaye Diagne", stat_list3)
    res42_11 = plObj.callPlayer_Fast_V4("Thievy")
    #
    #
    #
    # # print_test("callPlayer()", res42, "Edin Visca", EventIDs.AssistEvents)
    # print_test("callPlayer_Fast()", res42_1, "Edin Visca", "AssistEvent")
    # print_test("callPlayer_Fast()", res42_2, "Edin Visca", ["total_assists", "intentional_assists", "key_passes"])
    # print_test("callPlayer_Fast_V2()", res42_3, "Edin Visca", stat_list)
    # print_test("callPlayer_Fast_V3()", res42_5, "Edin Visca", stat_list)
    # print_test("callPlayer_Fast_V3()", res42_6, "Mbaye Diagne", stat_list2)
    # print_test("getPlayerStatistics()", res42_4, "Galatasaray", "Mbaye Diagne")
    # print_test("callPlayer_Fast_V3()", res42_7, "Mbaye Diagne", None)
    # print_test("callPlayer_Fast_V2()", res42_8, "Mbaye Diagne", None)
    # print_test("callPlayer_Fast_V4()", res42_9, "Mbaye Diagne", None)
    print_test("callPlayer_Fast_V4()", res42_10, "Mbaye Diagne", stat_list3)
    print_test("callPlayer_Fast_V4()", res42_11, "Thievy", None)

    # -----------------------------------------------Test43-----------------------------------------------

    # team_players = []
    # team_player1 = dict()
    # team_player1["team"] = "Galatasaray"
    # team_player1["player"] = "Henry Onyekuru"
    # team_players.append(team_player1)
    # team_player2 = dict()
    # team_player2["team"] = "Istanbul Basaksehir"
    # team_player2["player"] = "Edin Visca"
    # team_players.append(team_player2)
    # res43 = plObj.comparePlayersEventStatistics(team_players)
    # print_test("comparePlayersEventStatistics()", res43, team_players, None)

    # -----------------------------------------------Test44-----------------------------------------------

    # res44 = plObj.callPlayer_Fast_V4("Mbaye Diagne")
    # print_test("callPlayer_Fast_V4()", res44, "Mbaye Diagne", None)
    #
    # res44 = plObj.callPlayer_Fast_V4("Edin Visca")
    # print_test("callPlayer_Fast_V4()", res44, "Edin Visca", None)
    #
    # res44 = plObj.callPlayer_Fast_V4("Henry Onyekuru")
    # print_test("callPlayer_Fast_V4()", res44, "Henry Onyekuru", None)
    #
    # res44 = plObj.callPlayer_Fast_V4("Burak Yilmaz")
    # print_test("callPlayer_Fast_V4()", res44, "Burak Yilmaz", None)
    #
    # res44 = plObj.callPlayer_Fast_V4("Vedat Muriqi")
    # print_test("callPlayer_Fast_V4()", res44, "Vedat Muriqi", None)
    #
    # res44_1 = plObj.comparePlayers_V3("Mbaye Diagne", ["Edin Visca", "Henry Onyekuru", "Burak Yilmaz", "Vedat Muriqi"])
    # for diff in res44_1:
    #     print_test("comparePlayers_V3:->", diff, None, None)
    #
    # res44_1 = plObj.comparePlayers_V3("Mbaye Diagne", ["Edin Visca", "Henry Onyekuru", "Burak Yilmaz", "Vedat Muriqi"], stat_list3)
    # for diff in res44_1:
    #     print_test("comparePlayers_V3:->", diff, None, None)

    # res44_3 = plObj.comparePlayers_V3("Mbaye Diagne", ["Henry Onyekuru"])
    # print_test("comparePlayers_V3()", res44_3, "Mbaye Diagne", ["Henry Onyekuru"])


    # -----------------------------------------------Test45-----------------------------------------------




    # res45 = plObj.getPlayerEventGroup("Vedat Muriqi", "shotEvent", None)
    # print_test("getPlayerEventGroup", res45, "Vedat Muriqi", "shotEvent")
    # #
    # res45 = plObj.getPlayerEventGroup("Vedat Muriqi", "shotEvent", ["goals", "total_shots", "shots_on_target"])
    # print_test("getPlayerEventGroup", res45, "Vedat Muriqi", ["goals", "total_shots", "shots_on_target"])
    # #
    # res45 = plObj.getPlayerEventGroup("Vedat Muriqi", "assistEvent", None)
    # print_test("getPlayerEventGroup", res45, "Vedat Muriqi", "assistEvent")
    # #
    # res45 = plObj.getPlayerEventGroup("Vedat Muriqi", "foulEvent", None)
    # print_test("getPlayerEventGroup", res45, "Vedat Muriqi", "foulEvent")
    # #
    # res45 = plObj.getPlayerAverageEventGroup("forward_dominant_players", "average")
    # print_test("getPlayerAverageEventGroup", res45, "average", "forward_dominant_players")

    # -----------------------------------------------Test46-----------------------------------------------

    # res46 = plObj.rankLeaguePlayers_V2("assist", "total_assists", 698, True)
    # print_test("rankLeaguePlayers_V2()", res46, "shotEvent", "goals")
    #
    # res46 = plObj.rankLeaguePlayers_V2("assistEvent", "total_assists", 100)
    # print_test("rankLeaguePlayers_V2()", res46, "assistEvent", "total_assists")
    #
    # res46 = plObj.rankLeaguePlayers_V2("passEvent", "passes_total", 10)
    # print_test("rankLeaguePlayers_V2()", res46, "passEvent", "passes_total")
    #
    # res46 = plObj.rankLeaguePlayers_V2("cardEvent", "total_cards", 10)
    # print_test("rankLeaguePlayers_V2()", res46, "cardEvent", "total_cards")
    #
    # res46 = plObj.rankLeaguePlayers_V2("cardEvent", "red_card", 10)
    # print_test("rankLeaguePlayers_V2()", res46, "cardEvent", "red_card")
    #
    # res46 = plObj.rankLeaguePlayers_V2("aerialEvent", "won", 10)
    # print_test("rankLeaguePlayers_V2()", res46, "aerialEvent", "won")

    # res46 = plObj.rankLeaguePlayers_V2("goalkeeperEvent", "goals_against", 20)

    # -----------------------------------------------Test47-----------------------------------------------

    # res47 = plObj.getPlayerName("p451251")
    # print_test("getPlayerName", res47, "p451251", None)

    # -----------------------------------------------Test48-----------------------------------------------
    #
    # plObj.getTotalGoalkeeping("Istanbul Basaksehir")
    # plObj.getTotalGoalkeeping("Fenerbahçe")
    # res48 = plObj.getTotalGoalkeeping("Galatasaray")
    # print_test("getTotalGoalkeeping()", res48, "Galatasaray", None)
    #
    # print_test("callPlayer", plObj.callPlayer("Galatasaray", "Fernando Muslera", EventIDs.GoalkeeperEvents), None, None)
    # -----------------------------------------------Test49-----------------------------------------------

    # res49 = plObj.getPlayerGamesStatistics("Henry Onyekuru", 18, 1)
    # print_test("getPlayerGamesStatistics()", res49, "Henry Onyekuru", "18, 1")

    # res49_2 = plObj.getPlayerGamesStatistics("Fernando Muslera", 4, 1)
    # print_test("getPlayerGamesStatistics()", res49_2, "Fernando Muslera", "4, 1")

    # res49_3= plObj.getPlayerGamesStatistics("Eren Derdiyok", 17, 1)
    # print_test("getPlayerGamesStatistics()", res49_3, "Eren Derdiyok", "17, 1")

    # res49_4 = plObj.getPlayerGamesStatistics("Mbaye Diagne", 17, 5, EventIDs.ShotandGoalEvents)
    # print_test("getPlayerGamesStatistics()", res49_4, "Mbaye Diagne", "17, 5")

    # -----------------------------------------------Test50-----------------------------------------------

    # res50 = plObj.getPlayerGamesStatisticsWithGameIDs("Henry Onyekuru", [1002301])
    # print_test("getPlayerGamesStatisticsWithGameIDs()", res50, "Henry Onyekuru", [1002301])

    # -----------------------------------------------Test51-----------------------------------------------
    #
    # res51 = plObj.get_team_fast("Henry Onyekuru", True)
    # print_test("get_team_fast()", res51, "Henry Onyekuru", True)
    # print(type(res51))
    #
    # res51 = plObj.get_team_fast("Hakan Arslan", True)
    # print_test("get_team_fast()", res51, "Hakan Arslan", True)
    # print(type(res51))
    #
    # res51 = plObj.get_team_fast("Mbaye Diagne", True)
    # print_test("get_team_fast()", res51, "Hakan Arslan", True)
    # print(type(res51))
    #
    # res51 = plObj.get_team_fast("Mbaye Diagne", False)
    # print_test("get_team_fast()", res51, "Hakan Arslan", False)
    # print(type(res51))

    # -----------------------------------------------Test52-----------------------------------------------

    # res52 = plObj.getPlayerGamesStatisticsWithDate("Mbaye Diagne", "2018-08-10", "2019-03-03")
    # print_test("getPlayerGamesStatisticsWithDate()", res52, "Mbaye Diagne", "2018-08-10, 2019-03-03")

    # -----------------------------------------------Test53-----------------------------------------------
    #
    # res53 = plObj.getPlayerGamesStatisticsSeperatedHalf("Henry Onyekuru", [1002301], EventIDs.ShotandGoalEvents)
    # print_test("getPlayerGamesStatisticsSeperatedHalf()", res53, "Henry Onyekuru", [1002301])
    #
    # -----------------------------------------------Test54-----------------------------------------------

    # res54 = plObj.getPlayerGamesStatisticsSeperatedMins("Henry Onyekuru", [1002301], [21, 35, 59, 61, 75],
    #                                                     EventIDs.ShotandGoalEvents)
    # print_test("getPlayerGamesStatisticsSeperatedMins()", res54, "Henry Onyekuru", "[1002301], [20, 60, 75]")

    # -----------------------------------------------Test55-----------------------------------------------

    # res55 = plObj.getPlayerGamesStatisticsSeperatedByRedCards("Anthony Nuatuzor Nwakaeme", 1002180,
    #                                                      EventIDs.ShotandGoalEvents)
    # print_test("getPlayerGamesStatisticsSeperatedByRedCards()", res55, "Anthony Nuatuzor Nwakaeme", 1002180)

    # -----------------------------------------------Test56-----------------------------------------------

    # res56 = plObj.getPlayerGamesStatisticsSeperatedByGoals("Anthony Nuatuzor Nwakaeme", 1002180,
    #                                                      EventIDs.ShotandGoalEvents)
    # print_test("getPlayerGamesStatisticsSeperatedByGoals()", res56, "Anthony Nuatuzor Nwakaeme", 1002180)

    # -----------------------------------------------Test56-----------------------------------------------

    # print(plObj.getPlayerStatistics("Galatasaray", "Henry Onyekuru"))

    # print(plObj.getPlayerData_Alt("Mbaye Diagne", "Galatasaray"))

    # plObj.get_all_sub_stat_names("aerial")

    # print(plObj.getPlayerData_Alt("Mbaye Diagne"))

    pipeline = [
        {
            "$match": {
                "name": "team_name"
            }
        },
        {
            "$addFields": {
                "teamName": "$name"
            }
        },
        {
            "$project": {
                "teamName": 1, "players": 1
            }
        },
        {
            "$unset": "_id"
        },
        {
            "$lookup": {
                "from": "f40__player",
                "localField": "players",
                "foreignField": "_id",
                "as": "players"
            }
        },
        {
            "$unwind": "$players"
        },
        {
            "$addFields": {
                "name": "$players.name",
                "position": "$players.position"
            }
        },
        {
            "$unset": "players"
        },
        {
            "$match": {
                "position": "Goalkeeper"
            }
        },
        {
            "$lookup": {
                "from": "player_statistics",
                "localField": "name",
                "foreignField": "playerName",
                "as": "statistics"
            }
        },
        {
            "$lookup": {
                "from": "goalkeeper_event",
                "localField": "statistics.goalkeeperEvent",
                "foreignField": "_id",
                "as": "goalkeeping"
            }
        },
        {
            "$unwind": "$goalkeeping"
        },
        {
            "$unset": ["statistics", "name", "position", "goalkeeping._id"]
        },
        {
            "$match": {
                "goalkeeping.crosses_faced": {
                    "$nin": [0],
                }
            }
        }
    ]

    # plObj.get_player_data_fast("Mbaye Diagne")

    # for player in plObj.getTeamAllPlayerNames_Alt("Galatasaray", "all"):
    #     print("--------------------------------------")
    #     plObj.get_player_data_fast(player)
    #     print("--------------------------------------")


    # plObj.get_player_data_fast("Dogukan Nelik")

    # plObj.get_player_data_fast("Adem Ljajic")

    # res57 = plObj.callPlayerPer90("Mbaye Diagne")
    # print_test("callPlayerPer90()", res57, "Mbaye Diagne", None);

    # res_58 = plObj.get_player_all_matches("Edin Visca")
    # res_58_1 = plObj.get_player_all_matches("Mbaye Diagne")
    # res_58_3 = plObj.get_player_all_matches("Burak Yilmaz")
    # res_58_2 = plObj.get_player_all_matches("Onur Kivrak")
    #
    # print_test("get_player_all_matches()", res_58, "Edin Visca")
    # print_test("get_player_all_matches()", res_58_1, "Mbaye Diagne")
    # print_test("get_player_all_matches()", res_58_3, "Burak Yilmaz")
    # print_test("get_player_all_matches()", res_58_2, "Onur Kivrak")

    # print(plObj.get_player_data_fast("Onur Kivrak"))


    # res59 = plObj.get_player_total_play_time(plObj.getPlayerID_Alt("Mbaye Diagne"))
    # print_test("get_player_total_play_time()", res59, "Mbaye Diagne", None)
    #
    # res60 = plObj.get_filtered_total_play_time_stats(
    #     query_after_group={"total_played_time": {"$gte": 1500}},
    #     project='playerName'
    # )
    # print_test("get_filtered_total_play_time_stats()", res60, "Mbaye Diagne", None)
    # for doc in res60:
    #     print(doc)

    # res61 = plObj.get_filtered_stats_players(
    #     query_conditions={"position": "Forward"}
    # )
    # for doc in res61:
    #     print(doc)


    # res62 = plObj.get_player_name_filtered(
    #     team_name="Kasimpasa S.K."
    # )
    #
    # print_test("get_player_name_filtered()", res62, 1500, "Galatasaray")
    #

    # print(plObj.get_season_all_player_and_team_name())


    print(plObj.get_season_all_player_name())
