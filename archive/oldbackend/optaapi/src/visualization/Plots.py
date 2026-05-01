"""
@author: Doruk Sahinel
@created by doruksahinel at 2020-01-21

This file is used for plotting the player results.
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
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans


class Plots:
    print("Plots Called")

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

    def SimpleBarPlot(self, player_name, filename):
        xls_file = pd.ExcelFile(filename)
        df_kmeans = xls_file.parse("Kmeans")
        column_list = df_kmeans.columns.values.tolist()
        df2 = df_kmeans.transpose()
        df3 = df2.drop(["Shot and Goal Parameter"])
        print(df3)
        # data = [df2[0],df2[1]]
        # print(data)
        x_list = df2[0].tolist()
        y_list = df2[1].tolist()
        title2 = x_list[0]
        title3 = y_list[0]
        row_list = [title2, title3]
        df3.columns = row_list
        df4 = df3.sort_values(by=["percentage of shots headed"], ascending=False)
        print(df4)
        plt.bar(x=np.arange(len(df4)), height=df4["successful take ons"])
        plt.title(
            "Turkish Super League 19-20 Centre Forwards Headed Shots Percentage vs. Shots in Box Percentage"
        )
        plt.xticks(np.arange(len(df4)), df4.index, rotation=90)
        plt.xlabel("Player Name")
        plt.ylabel("Shots heaed")
        plt.show()

    def LollipopBarPlot(self, player_name, filename):
        xls_file = pd.ExcelFile(filename)
        df_kmeans = xls_file.parse("Kmeans")
        column_list = df_kmeans.columns.values.tolist()
        df2 = df_kmeans.transpose()
        df3 = df2.drop(["Take On Parameter"])
        print(df3)
        # data = [df2[0],df2[1]]
        # print(data)
        x_list = df2[0].tolist()
        y_list = df2[1].tolist()
        title2 = x_list[0]
        title3 = y_list[0]
        row_list = [title2, title3]
        df3.columns = row_list
        df4 = df3.sort_values(by=["successful take ons"])
        print(df4)
        plt.hlines(
            y=np.arange(len(df4)),
            xmin=0,
            xmax=df4["successful take ons"],
            color="skyblue",
        )
        plt.plot(df4["successful take ons"], np.arange(len(df4)), "o")
        plt.title("Turkish Super League 19-20 Centre Forwards Succesful Take Ons")
        plt.yticks(np.arange(len(df4)), df4.index, rotation=0)
        # plt.xlabel("Player Name")
        plt.xlabel("Successful Take Ons")
        plt.show()

    def ScatterPlot(self, player_name, filename):
        xls_file = pd.ExcelFile(filename)
        # print(xls_file.sheet_names)
        df_kmeans = xls_file.parse("Kmeans")
        column_list = df_kmeans.columns.values.tolist()
        df2 = df_kmeans.transpose()
        print(df2.shape)
        print(df2)
        df2.drop(["Duel Event Parameter"])
        x_list = df2[0].tolist()
        y_list = df2[1].tolist()
        column_list.pop(0)
        x_list.pop(0)
        y_list.pop(0)
        print(column_list)
        print(x_list)
        print(y_list)
        # bjk_centre_forwards = ['Burak Yilmaz', 'Cenk Tosun', 'ALvaro Negredo', 'Vincent Aboubakar']
        # head_list = [0.21, 0.24, 0.51, 0.13]
        # box_list = [0.73, 0.82, 0.86, 0.85]
        plt.scatter(x_list, y_list, c="b", cmap="viridis")
        # plt.plot([x_list.mean(), x_list.mean()], [90, 20], 'k-', linestyle=":", lw=1)
        # plt.plot([20, 90], [y_list.mean(), y_list.mean()], 'k-', linestyle=":", lw=1)
        plt.title("Beşiktaş 16-17 Duel Comparison")
        plt.xlabel("total duels")
        plt.ylabel("duel success percentage")
        # plt.grid(True)
        # for i, txt in enumerate(column_list):
        #    plt.annotate(txt, (x_list[i], y_list[i]))
        for label, x, y in zip(column_list, x_list, y_list):
            plt.annotate(
                label,
                xy=(x, y),
                xytext=(-5, 5),
                textcoords="offset points",
                fontsize=7,
                ha="right",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.5", fc="w", alpha=0.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )
        # plt.scatter(head_list, box_list, s=200, c='black', cmap='viridis')
        # for label, x, y in zip(bjk_centre_forwards, head_list, box_list):
        #     plt.annotate(
        #         label,
        #         xy=(x, y), xytext=(-5, 5),
        #         textcoords='offset points', fontsize=7, ha='right', va='bottom',
        #         bbox=dict(boxstyle='round,pad=0.3', fc='w', alpha=0.5),
        #         arrowprops=dict(arrowstyle='-', connectionstyle='arc3,rad=0'))
        plt.show()

    def kmeans(self, filename):
        xls_file = pd.ExcelFile(filename)
        df_kmeans = xls_file.parse("kmeans_saves")
        df_data = df_kmeans.drop(columns=["GK Parameter"])
        column_list = df_data.columns.values.tolist()
        df_transposed = df_data.T
        # create kmeans object
        kmeans = KMeans(n_clusters=4)
        print(df_transposed)
        # fit kmeans object to data
        kmeans.fit(df_transposed)
        # print location of clusters learned by kmeans object
        print(kmeans.cluster_centers_)
        # save new clusters for chart
        labels = kmeans.fit_predict(df_transposed)
        print(labels)
        df_centroid = pd.DataFrame(
            kmeans.cluster_centers_, columns=["Clean Sheets", "Saves"]
        )
        print(df_centroid)
        # labels = KMeans(4, random_state=0).fit_predict(df_kmeans)
        x_list = df_transposed.ix[:, 0].tolist()
        y_list = df_transposed.ix[:, 1].tolist()
        plt.scatter(x_list, y_list)
        plt.scatter(
            kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=300, c="red"
        )
        plt.title("Goalkeepers 19-20 K-Means Clustering")
        plt.xlabel("Clean Sheets per game")
        plt.ylabel("Saves per game")
        for label, x, y in zip(column_list, x_list, y_list):
            plt.annotate(
                label,
                xy=(x, y),
                xytext=(-5, 5),
                textcoords="offset points",
                fontsize=7,
                ha="right",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.5", fc="w", alpha=0.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )
        plt.show()
        # self.plotKMeans(df_transposed, kmeans.cluster_centers_, labels, filename)
        # calculateDistanceBetweenSimulationAndCentroid(df_centroid, simDf)

    def plotKMeans(data, centers, labels, filename):
        x_list = data["0"].tolist()
        y_list = data["1"].tolist()
        fig = plt.figure()
        colormap = np.array(["b", "g", "r", "c", "m", "y", "k"])

        for i in range(len(centers)):
            plt.scatter(
                centers[i][0],
                centers[i][1],
                label=getLabel(i),
                c=colormap[i],
                s=100,
                alpha=0.5,
            )
            plt.legend(loc="lower right", prop={"size": 8})
            for j in range(0, len(labels)):
                if i == labels[j]:
                    plt.scatter(
                        x_list[j], y_list[j], c=colormap[i], marker="^", s=20, alpha=0.5
                    )  # , c=colormap[categories][i])

        # plt.set(xlabel='expertise', ylabel='stamina')
        # plt.set_title('Task Clusters for Workers')
        plt.ylabel("Tempo")
        plt.xlabel("Quality")
        plt.title("Product Type Clusters for Workers")
        plt.grid(True)
        # fig.tight_layout()
        fig.savefig(filename + "k-means.png", dpi=fig.dpi)
        plt.close(fig)
        plt.cla()

        # plt.show()

    def getLabel(task_index):
        ds = DataSource()
        label = ""
        task_centroid_df = ds.readCentroids()
        for index, row in task_centroid_df.iterrows():
            if task_index == index:
                if float(row["expertise"]) >= 0.6:
                    label += "High"
                elif float(row["expertise"]) < 0.6 and float(row["expertise"]) >= 0.5:
                    label += "Medium"
                else:
                    label += "Low"
                label += "-Quality \n"

                if float(row["stamina"]) >= 0.45:
                    label += "High"
                elif float(row["stamina"]) < 0.45 and float(row["stamina"]) >= 0.35:
                    label += "Medium"
                else:
                    label += "Low"
                label += "-Workload"

    def kmeansPlusPlus(data):
        wcss = []
        for i in range(1, 14):
            kmeans = KMeans(
                n_clusters=i, init="k-means++", max_iter=100, n_init=10, random_state=0
            )
            kmeans.fit(data)
            wcss.append(kmeans.inertia_)
        plt.plot(range(1, 14), wcss)
        plt.title("Elbow Method")
        plt.xlabel("Number of clusters")
        plt.ylabel("WCSS")
        plt.show()

    def PlotKmeans_readcsv(self, filename, filename2):
        df_csv = pd.read_csv(filename)
        df_csv2 = pd.read_csv(filename2)
        df_name_list1 = df_csv[["lastName"]].copy()
        df_csv_new1 = df_csv[["PsAtt", "PsOppHalf"]].copy()
        df_name_list2 = df_csv2[["lastName"]].copy()
        df_csv_new2 = df_csv2[["PsAtt", "PsOppHalf"]].copy()
        frames1 = [df_name_list1, df_name_list2]
        frames2 = [df_csv_new1, df_csv_new2]
        df_name_list = pd.concat(frames1)
        df_csv_new = pd.concat(frames2)
        print(df_name_list)
        print(df_csv_new)
        column_list = df_name_list.iloc[:, 0].tolist()
        kmeans = KMeans(n_clusters=4)
        # fit kmeans object to data
        kmeans.fit(df_csv_new)
        # print location of clusters learned by kmeans object
        print(kmeans.cluster_centers_)
        # save new clusters for chart
        labels = kmeans.fit_predict(df_csv_new)
        print(labels)
        df_centroid = pd.DataFrame(
            kmeans.cluster_centers_, columns=["PsAtt", "PsOppHalf"]
        )
        print(df_centroid)
        dframe = pd.DataFrame(data=labels)
        df_name_list = df_name_list.append(pd.DataFrame(dframe))
        # writer = pd.ExcelWriter(r'./kmeans' + filename + '.xlsx', engine='xlsxwriter')
        # df_name_list.to_excel(writer)
        # writer.save()
        # labels = KMeans(4, random_state=0).fit_predict(df_kmeans)
        x_list = df_csv_new.iloc[:, 0].tolist()
        y_list = df_csv_new.iloc[:, 1].tolist()
        plt.scatter(x_list, y_list)
        plt.scatter(
            kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=200, c="red"
        )
        plt.title("Pass Attempts vs. Passes Into Oppostion Half p90")
        plt.xlabel("Pass Attempts")
        plt.ylabel("Passes Into Oppostion Half")
        for label, x, y in zip(column_list, x_list, y_list):
            plt.annotate(
                label,
                xy=(x, y),
                xytext=(-5, 5),
                textcoords="offset points",
                fontsize=5,
                ha="right",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.5", fc="w", alpha=0.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )
        plt.show()

        # self.plotKMeans(df_transposed, kmeans.cluster_centers_, labels, filename)
        # calculateDistanceBetweenSimulationAndCentroid(df_centroid, simDf)


plots = Plots()
# player_name = "Atiba Hutchinson"
# file_name = '2016 Besiktas.xlsx'
# file_name = 'GK Comparison 19-20.xlsx'
# plots.kmeans(file_name)
file_name = "Besiktas Defenders Pass.csv"
file_name2 = "Selected Defenders Pass.csv"
plots.PlotKmeans_readcsv(file_name, file_name2)
# plots.SimpleBarPlot(player_name, file_name)
# plots.LollipopBarPlot(player_name, file_name)
