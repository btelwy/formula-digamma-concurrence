import numpy as np
from sklearn import datasets, linear_model, metrics
import matplotlib as plt
#mean_squared_error, r2_score

model = linear_model.LinearRegression()

model.fit(x, y)
rSq = model.score(x, y)

print(f"intercept: {model.intercept_}")
print(f"slope: {model.coef_}")

yPredicted = model.predict(x)