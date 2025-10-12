"""
@author: Doruk Sahinel
@created by doruksahinel at 2021-06-15
"""

from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Kmeans:
    def runKMeans(self, clusterNumber):
        labels = []
        sequencedata = pd.read_excel(
            r"./Shot Chain Study 6 Leagues.xlsx", usecols=lambda x: "Unnamed" not in x
        )
        column_list = [
            "League",
            "team_name",
            "team_ranking",
            "total_shots",
            "total_crosses",
            "crosses",
            "long passes",
            "take ons",
            "aerial duels",
            "shot in box",
            "shot out box",
            "no pass shots",
            "short pass shots",
            "long possession shots",
        ]

        realDf = pd.DataFrame(sequencedata)
        print(realDf)
        team_list = realDf.team_name
        # column_list = realDf['team_name']
        realDf = realDf.drop(columns="League")
        realDf = realDf.drop(columns="team_name")
        realDf = realDf.drop(columns="team_ranking")
        realDf = realDf.drop(columns="total_shots")
        realDf = realDf.drop(columns="total_crosses")
        # realDf = realDf.drop(columns="crosses")
        # realDf = realDf.drop(columns="long passes")
        # realDf = realDf.drop(columns="take ons")
        # realDf = realDf.drop(columns="aerial duels")
        # realDf = realDf.drop(columns="shot in box")
        # realDf = realDf.drop(columns="shot out box")
        # realDf = realDf.drop(columns="no pass shots")
        # realDf = realDf.drop(columns="short pass shots")
        # realDf = realDf.drop(columns="long possession shots")
        labels, centers = self.kmeans(realDf, clusterNumber, column_list)
        print("labels", labels)
        dictionary = dict(zip(team_list, labels))
        df = pd.DataFrame(dictionary.items(), columns=["Team Name", "Cluster"])
        # df2 = pd.DataFrame(centers, columns=['crosses', 'long passes', 'take ons', 'aerial duels',
        #     'shot in box', 'shot out box', 'no pass shots', 'short pass shots', 'long possession shots'
        #                                      ])

    def kmeans(self, data, clusterNum, column_list):
        # create kmeans object and fit the data
        kmeans = KMeans(n_clusters=clusterNum, random_state=0).fit(data)
        labels = KMeans(clusterNum, random_state=0).fit_predict(data)
        distortions.append(kmeans.inertia_)
        print("labels", labels)
        print("data", data)
        print("cluster centers", kmeans.cluster_centers_)
        # df_centroid = pd.DataFrame(kmeans.cluster_centers_, columns=['cross_seq_shot_ratio', 'cross_seq_cross_ratio'])
        # util.prepareTrainingDataForExcel(df_centroid, "centroids");
        # self.plotKMeans(data, kmeans.cluster_centers_, labels, column_list)
        return labels, kmeans.cluster_centers_
        # add labels to the excel list with the data
        # data2 = transposeList(pd.DataFrame(data), labels)
        # util.prepareTrainingDataForExcel(data2, "concatenate");


km = Kmeans()
K = range(1, 30)
distortions = []
for k in K:
    cluster_number = k
    km.runKMeans(cluster_number)
plt.figure(figsize=(16, 8))
plt.plot(K, distortions, "bx-")
plt.xlabel("k")
plt.ylabel("Distortion")
plt.title("The Elbow Method showing the optimal k")
plt.show()
