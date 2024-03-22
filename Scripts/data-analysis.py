import numpy as np
from sklearn import datasets, linear_model, metrics
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

#TODO: Clean all of this up

"""model = linear_model.LinearRegression()

model.fit(x, y)
rSq = model.score(x, y)

print(f"intercept: {model.intercept_}")
print(f"slope: {model.coef_}")

yPredicted = model.predict(x)"""

customParams = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", palette="pastel", rc=customParams)

data = pd.read_csv("Data/Output Data/Analysis/FormulasByLength.csv")
split = data.iloc[:, [0, 1]]
data = data.drop(columns=["Source", "Book"])

multiIndex = pd.MultiIndex.from_frame(split, names=["Source", "Book"])
multiIndex.name = "Location"
data = data.set_index(multiIndex)
print(data)

#data = data.pivot(index=multiIndex, columns=["2", "3", "4", "5", "6", "7"])

#Heat map of 2D array
fig, ax = plt.subplots(figsize=(9, 6))
ax.xaxis.tick_top()

sns.heatmap(data, ax=ax, annot=False, cmap="magma", fmt="d", \
            linewidths=0.5, annot_kws={"size": 7})
plt.show()