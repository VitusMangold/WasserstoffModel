""" Results from ENTSOE two-country model. """
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize
import entsoe_multiple_model as em

capacities = {"BE" : 1000, "CH" : 1000, "CZ" : 1000, "DK" : 1000, "FR" : 1000, "LU" : 1000, "NL" : 1000, "PL" : 1000}
shares = {"BE" : 1.0, "CH" : 1.0, "CZ" : 1.0, "DE" : 1.0, "DK" : 1.0, "FR" : 1.0, "LU" : 1.0, "NL" : 1.0, "PL" : 1.0}

## Minimize in all (2n - 1) dimensions

# Initial guess
x0 = [*[1e6 for _ in capacities], *[1.0 for _ in shares]]

# Bounds for each variable
bounds = [*[(0, None) for _ in capacities], *[(0, 5) for _ in shares]] # (min, max) for x and y

def transform(x):
    return {key: x[i] for i, key in enumerate(capacities)}, {key: x[i] for i, key in enumerate(shares, len(capacities))}

# Perform the optimization
result = minimize(
    lambda x: em.costs(*transform(x)),
    x0,
    method='Nelder-Mead',
    bounds=bounds
)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", transform(optimized_parameters))
print("Minimum value:", minimum_value)