""" Results from ENTSOE two-country model. """
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize
import entsoe_model as em

## Minimization

share_ren_de = 1.0
share_ren_other = 1.0

# Initial guess
x0 = np.array([3e6, 3e6])

# Bounds for each variable
bounds = [(0, None), (0, None)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: em.costs(x[0], x[1], share_ren_de, share_ren_other), x0, method='Nelder-Mead', bounds=bounds)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", optimized_parameters)
print("Minimum value:", minimum_value)

## Plotting

# Create figure and 3D axis
fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

# Plot the optimized solution as a dot
opt_x, opt_y = optimized_parameters
print(opt_x)
print(opt_y)
opt_z = em.costs(opt_x, opt_y, share_ren_de, share_ren_other)

# Generate grid for plotting
# Adjust the range of the grid to better encompass the optimized parameters
x_max = max(5e6, opt_x * 1.2)  # Ensure the grid covers at least 20% beyond the optimized x
y_max = max(5e6, opt_y * 1.2)  # Ensure the grid covers at least 20% beyond the optimized y
x_grid = np.linspace(0.0, x_max, 10)
y_grid = np.linspace(0.0, y_max, 10)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
z_grid = np.array(
    [em.costs(i, j, share_ren_de, share_ren_other) for i in x_grid for j in y_grid]).reshape(len(x_grid), len(y_grid)
)

# Set the elevation and azimuth
elevation = 64  # degrees
azimuth = -142  # degrees
ax.view_init(elev=elevation, azim=azimuth)

# Plot surface
ls = LightSource(270, 45)
ax.plot_surface(x_mesh, y_mesh, z_grid, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False, cmap=cm.coolwarm, zorder=1)
print(opt_x, opt_y, opt_z)
ax.scatter(opt_x, opt_y, opt_z, color='blue', s=50, zorder=2)  # 's' is the size of the dot

# Set labels
ax.set_xlabel("Power line capacity")
ax.set_ylabel("Hydrogen line capacity")
ax.set_zlabel("Total em.costs")

# Show plot
plt.show()

## Minimize all four dimensions

# Initial guess
x0 = np.array([3e6, 5e6, 0.9, 0.9])

# Bounds for each variable
bounds = [(0, None), (0, None), (0, 1), (0, 1)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: em.costs(x[0], x[1], x[2], x[3]), x0, method='Nelder-Mead', bounds=bounds)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", optimized_parameters)
print("Minimum value:", minimum_value)