""" Results from ENTSOE two-country model. """
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize
import entsoe_multiple_model as em

def count_leaves(nested_dict):
    total_leaves = 0
    for sub_dict in nested_dict.values():
        total_leaves += len(sub_dict)
    return total_leaves

capacities = {
    "DE" : { "NL" : 1000, "BE": 1000, "LU": 1000, "FR": 1000, "CH": 1000, "AT": 1000, "DK": 1000, "PL": 1000, "CZ": 1000},
    "NL" : {"BE" : 1000, "DK" : 1000},
    "BE" : {"LU" : 1000, "FR" : 1000},
    "LU": {"FR" : 1000},
    "FR": {"ES" : 1000, "IT" : 1000, "CH" : 1000},
    "ES" : { },
    "IT" : {"AT" : 1000, "CH" : 1000},
    "CH": {"AT" : 1000},
    "AT" : {"CZ" : 1000},
    "CZ" : {"PL" : 1000},
    "PL" : { },
    "DK" : { }
}
shares = {"BE" : 1.0, "CH" : 1.0, "CZ" : 1.0, "DE" : 1.0, "DK" : 1.0, "FR" : 1.0, "LU" : 1.0, "NL" : 1.0, "PL" : 1.0, "AT" : 1.0, "IT" : 1.0, "ES" : 1.0}

## Minimize in all (2n - 1) dimensions

# Initial guess
x0 = [*[1e6 for _ in range(count_leaves(capacities))], *[1.0 for _ in shares]]

# Bounds for each variable, (min, max) for x and y
bounds = [*[(0, None) for _ in range(count_leaves(capacities))], *[(0, 5) for _ in shares]]

def transform(x):
    cap_iterator = iter(x[:count_leaves(capacities)])
    for _, neighbors in capacities.items():
        # Iteration über die Nachbarländer jedes Landes
        for neighbor, _ in neighbors.items():
            # Überprüfung, ob das Nachbarland bereits im ursprünglichen dictionary vorhanden ist
            if neighbor in capacities:
                neighbors[neighbor] = next(cap_iterator)
    return capacities, {key: x[i + count_leaves(capacities) - 1] for i, key in enumerate(shares)}

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