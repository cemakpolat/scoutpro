"""
@author: Cem Akpolat
@created by cemakpolat at 2021-07-14
"""
# https://www.kaggle.com/typewind/draw-a-radar-chart-with-python-in-a-simple-way

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("./Pokemon.csv")
df.head()
labels = np.array(["HP", "Attack", "Defense", "Sp. Atk", "Sp. Def", "Speed"])
stats = df.loc[386, labels].values

angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
# close the plot
stats = np.concatenate((stats, [stats[0]]))
angles = np.concatenate((angles, [angles[0]]))

fig = plt.figure()
ax = fig.add_subplot(111, polar=True)
ax.plot(angles, stats, "o-", linewidth=2)
ax.fill(angles, stats, alpha=0.25)
ax.set_thetagrids(angles * 180 / np.pi, labels)
ax.set_title([df.loc[386, "Name"]])
ax.grid(True)
plt.show()
