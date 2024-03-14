import numpy as np
from sklearn import datasets, linear_model, metrics
import matplotlib as plt
from matplotlib import pyplot

#mean_squared_error, r2_score

model = linear_model.LinearRegression()

model.fit(x, y)
rSq = model.score(x, y)

print(f"intercept: {model.intercept_}")
print(f"slope: {model.coef_}")

yPredicted = model.predict(x)




#heatmap of 2D array
# Function to show the heat map
plt.pyplot.imshow( data , cmap = 'magma' )

# Adding details to the plot
plt.title( "2-D Heat Map" )
plt.xlabel('x-axis')
plt.ylabel('y-axis')

# Adding a color bar to the plot
plt.colorbar()

# Displaying the plot
plt.show()