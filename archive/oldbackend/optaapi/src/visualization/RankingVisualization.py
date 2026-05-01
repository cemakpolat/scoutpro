"""
@author: Doruk Sahinel
@created by doruksahinel at 2020-01-21

This file reads a list of player data from an excel file,
checks if the searched player has the maximum values for a data type,
and returns an excel sheet with the parameters in which the player is first in player rankings.
"""

from __future__ import division
import requests
import json
import sys
import os
import sys
import csv
import xlrd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class RankingVisaulization:
    print("Player Ranking Called")

    def __init__(self):
        self.data = []
        self.comparison_row = []
        self.df_player = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_aerial = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_assist = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_ballcontrol = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_cards = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_duels = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_fouls = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_passes = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_shots = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_takeon = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_touch = pd.DataFrame(self.data, columns=["Parameter"])
        self.df_aerial_max = pd.DataFrame(self.data, columns=["Parameter"])

    def ReadExcelFile(self, player_name, filename):
        xls_file = pd.ExcelFile(filename)
        # print(xls_file.sheet_names)
        self.df_aerial = xls_file.parse("Aerial Duels")
        df_aerial_ranking = self.CreateBarPlot(player_name, self.df_aerial)
        # self.df_assist = xls_file.parse('Assist')
        # df_assist_ranking = self.CreateBarPlot(player_name, self.df_assist)
        # self.df_ballcontrol = xls_file.parse('Ball Control')
        # df_ballcontrol_ranking = self.CreateBarPlot(player_name, self.df_ballcontrol)
        # self.df_cards = xls_file.parse('Cards')
        # df_cards_ranking = self.CreateBarPlot(player_name, self.df_cards)
        # self.df_duels = xls_file.parse('Duels')
        # df_duels_ranking = self.CreateBarPlot(player_name, self.df_duels)
        # self.df_fouls = xls_file.parse('Fouls')
        # df_fouls_ranking = self.CreateBarPlot(player_name, self.df_fouls)
        # self.df_passes = xls_file.parse('Passes')
        # df_passes_ranking = self.CreateBarPlot(player_name, self.df_passes)
        # self.df_shots = xls_file.parse('Shots and Goals')
        # df_shots_ranking = self.CreateBarPlot(player_name, self.df_shots)
        # self.df_takeon = xls_file.parse('Take On')
        # df_takeon_ranking = self.CreateBarPlot(player_name, self.df_takeon)
        # self.df_touch = xls_file.parse('Touches')
        # df_touch_ranking = self.CreateBarPlot(player_name, self.df_touch)
        # self.WritetoExcel(player_name,
        #                   df_aerial_ranking, df_assist_ranking, df_ballcontrol_ranking,
        #                   df_cards_ranking, df_duels_ranking, df_fouls_ranking,
        #                   df_passes_ranking, df_shots_ranking, df_takeon_ranking,
        #                   df_touch_ranking)

    def CreateBarPlot(self, player_name, df):
        height = []
        df_parameters = pd.DataFrame(self.data, columns=["Parameter"])
        column_list = df.columns.values.tolist()
        del column_list[0]
        # ax = df.iloc[2].plot.bar(x='Aerial Duel Parameter', y='aerial duels lost', rot=90)
        del df[column_list[0]]
        # height = df.iloc[2].values.tolist()
        # Make a fake dataset:
        height = [
            3,
            12,
            5,
            18,
            45,
            3,
            12,
            5,
            18,
            45,
            3,
            12,
            5,
            18,
            45,
            3,
            12,
            5,
            18,
            45,
            3,
            12,
        ]
        bars = ("A", "B", "C", "D", "E")
        y_pos = np.arange(len(height))
        # Create bars
        plt.bar(y_pos, height)

        # Create names on the x-axis
        plt.xticks(y_pos, column_list, rotation=90)
        plt.subplots_adjust(bottom=0.4, top=0.99)

        plt.show()

        # data = []
        # df_parameters = pd.DataFrame(self.data, columns=['Parameter'])
        # df2 = df#.transpose()
        # column_list = df.columns.values.tolist()
        # df_parameters['Parameter'] = df[column_list[0]]
        # del df2[column_list[0]]
        # print(df2)
        # df3 = pd.DataFrame(np.sort(df2.values)[:, -3:], columns=['3rd-largest', '2nd-largest', 'largest'])
        # df3[column_list[0]] = df_parameters['Parameter']
        # df3[player_name] = df[player_name]
        # df3['First'] = np.where(df3['largest'] == df3[player_name],
        #                                    df3['largest'], np.nan)
        # df3['Second'] = np.where(df3['2nd-largest'] == df3[player_name],
        #                         df3['2nd-largest'], np.nan)
        # df3['Third'] = np.where(df3['3rd-largest'] == df3[player_name],
        #                          df3['3rd-largest'], np.nan)
        # cols = list(df3)
        # cols.insert(0, cols.pop(cols.index(column_list[0])))
        # df3 = df3.ix[:, cols]
        # print(df3)
        # return df3
        # # column_list = df.columns.values.tolist()
        # # print(column_list[0])
        # # maxValuesObj = df.max(axis=1)
        # # #maxValuesObj = df.min(axis=1)
        # # df_comparison = pd.DataFrame(maxValuesObj, columns=['Max Values'])
        # # df_comparison[player_name] = df[player_name]
        # # df_comparison[column_list[0]] = df[column_list[0]]
        # # df_comparison['Result'] = np.where(df_comparison['Max Values'] == df_comparison[player_name], df_comparison['Max Values'], np.nan)
        # # del df_comparison['Max Values']
        # # del df_comparison[player_name]
        # # self.df_player = df_comparison.dropna()
        # # print(self.df_player)
        # # return self.df_player

    def WritetoExcel(
        self,
        player_name,
        df_aerial_ranking,
        df_assist_ranking,
        df_ballcontrol_ranking,
        df_cards_ranking,
        df_duels_ranking,
        df_fouls_ranking,
        df_passes_ranking,
        df_shots_ranking,
        df_takeon_ranking,
        df_touch_ranking,
    ):
        Path("PlayerComparison").mkdir(parents=True, exist_ok=True)
        writer = pd.ExcelWriter(
            r"C:\Users\user\Dropbox\docs\Events\PlayerComparison\\"
            + player_name
            + " First 3 Rankings.xlsx",
            engine="xlsxwriter",
        )
        df_aerial_ranking.to_excel(writer, sheet_name="Aerial Duels", index=None)
        df_assist_ranking.to_excel(writer, sheet_name="Assist", index=None)
        df_ballcontrol_ranking.to_excel(writer, sheet_name="Ball Control", index=None)
        df_cards_ranking.to_excel(writer, sheet_name="Cards", index=None)
        df_duels_ranking.to_excel(writer, sheet_name="Duels", index=None)
        df_fouls_ranking.to_excel(writer, sheet_name="Fouls", index=None)
        df_passes_ranking.to_excel(writer, sheet_name="Passes", index=None)
        df_shots_ranking.to_excel(writer, sheet_name="Shots and Goals", index=None)
        df_takeon_ranking.to_excel(writer, sheet_name="Take On", index=None)
        df_touch_ranking.to_excel(writer, sheet_name="Touches", index=None)
        writer.save()


player_ranking = RankingVisaulization()
player_name = "Vedat Muriqi"
file_name = "2019 CentreForwards.xlsx"
df_player = player_ranking.ReadExcelFile(player_name, file_name)
