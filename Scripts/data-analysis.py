import numpy as np
from sklearn import datasets, linear_model, metrics
import matplotlib.pyplot as plt
import seaborn as sns

#TODO: Clean all of this up

"""model = linear_model.LinearRegression()

model.fit(x, y)
rSq = model.score(x, y)

print(f"intercept: {model.intercept_}")
print(f"slope: {model.coef_}")

yPredicted = model.predict(x)"""


data = np.random.random((16, 16))

#Heat map of 2D array
plt.imshow(data, cmap = "magma")

#Add details to the plot
plt.title("2D Heat Map")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")

#Add a color bar to the plot
plt.colorbar()

#Display the plot
plt.show()