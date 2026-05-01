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
        # realDf = realDf.drop(columns="aerial duels")
        # realDf = realDf.drop(columns="take on")
        labels, centers = self.kmeans(realDf, clusterNumber, column_list)
        print("labels", labels)
        dictionary = dict(zip(team_list, labels))
        df = pd.DataFrame(dictionary.items(), columns=["Team Name", "Cluster"])
        df2 = pd.DataFrame(
            centers,
            columns=[
                "crosses",
                "long passes",
                "take ons",
                "aerial duels",
                "shot in box",
                "shot out box",
                "no pass shots",
                "short pass shots",
                "long possession shots",
            ],
        )
        # df = (df.T)
        # print(df)
        self.WritetoExcel(df, df2)

    def kmeans(self, data, clusterNum, column_list):
        # create kmeans object and fit the data
        kmeans = KMeans(n_clusters=clusterNum, random_state=0).fit(data)
        labels = KMeans(clusterNum, random_state=0).fit_predict(data)
        # distortions.append(kmeanModel.inertia_)
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

    def plotKMeans(self, data, centers, labels, column_list):
        x_list = data["cross_seq_shot_ratio"].tolist()
        y_list = data["cross_seq_cross_ratio"].tolist()
        fig = plt.figure()
        colormap = np.array(["b", "g", "r", "c", "m", "y", "k"])

        for i in range(len(centers)):
            plt.scatter(centers[i][0], centers[i][1], color="r", s=100, alpha=0.5)
            plt.legend(loc="lower right", prop={"size": 8})
            for j in range(0, len(labels)):
                if i == labels[j]:
                    plt.scatter(
                        x_list[j], y_list[j], c=colormap[i], marker="^", s=20, alpha=0.5
                    )  # , c=colormap[categories][i])
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

        # plt.set(xlabel='expertise', ylabel='stamina')
        # plt.set_title('Task Clusters for Workers')
        plt.ylabel("Shot Creating Cross Percentage in Shots")
        plt.xlabel("Shot Creating Cross Percentage in Crosses")
        plt.title(
            "Shot Creating Cross Percentage in Shots vs. Shot Creating Cross Percentage in Crosses"
        )
        plt.grid(True)
        # fig.tight_layout()
        fig.savefig("cross-shot-sequence-clusters.png", dpi=fig.dpi)
        plt.show()
        plt.close(fig)
        plt.cla()

        # plt.show()

    def WritetoExcel(self, df, df1):
        writer_total = pd.ExcelWriter(
            "./results/ClusteringResults6WithClusters.xlsx", engine="xlsxwriter"
        )
        df.to_excel(writer_total, sheet_name="results", index=None)
        df1.to_excel(writer_total, sheet_name="clusters", index=None)
        writer_total.save()


km = Kmeans()
cluster_number = 6
km.runKMeans(cluster_number)
