"""
@author: Cem Akpolat, Doruk Sahinel
@created by cemakpolat at 2020-07-11
"""
# A short concept that explains what is the grammar of graphics along with ggplot
# https://towardsdatascience.com/how-to-use-ggplot2-in-python-74ab8adec129

# gglot is presented with a number examples
# https://monashdatafluency.github.io/python-workshop-base/modules/plotting_with_ggplot/

# valuable tools for working with data
# https://monashdatafluency.github.io/python-workshop-base/modules/working_with_data/
# http://ggplot.yhathq.com/


import numpy as np
import pandas as pd
from plotnine import *

survs_df = pd.read_csv("surveys.csv").dropna()
g = ggplot(survs_df, aes(x="weight", y="hindfoot_length")) + geom_point()


b = ggplot(survs_df, aes(x="weight", y="hindfoot_length", size="year")) + geom_point()

g = (
    ggplot(
        survs_df, aes(x="weight", y="hindfoot_length", size="year", color="species_id")
    )
    + geom_point()
)


g = ggplot(survs_df, aes(x="year", fill="species_id")) + geom_bar(stat="count")

print(g)
