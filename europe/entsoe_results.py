""" Results from ENTSOE two-country model. """
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize
import entsoe_model as em
import itertools

## Minimization

share_ren_de = 1.0
share_ren_other = 1.0

# Initial guess
x0 = np.array([2e6, 2e6])

# Bounds for each variable
bounds = [(0, None), (0, None)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: em.costs(x[0], x[1], share_ren_de, share_ren_other), x0, method='Nelder-Mead', bounds=bounds)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", optimized_parameters)
print("Minimum value:", minimum_value)
print("Sanity check:", em.costs(1e6, 2e6, share_ren_de, share_ren_other))

## Plotting

# Create figure and 3D axis
fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(12, 8))

# Plot the optimized solution as a dot
opt_x, opt_y = optimized_parameters
opt_z = em.costs(opt_x, opt_y, share_ren_de, share_ren_other)
print("Minimum value:", opt_z)

# Adjust the range of the grid to better encompass the optimized parameters
n_grid_points = 40
x_max = max(5e6, opt_x * 1.2)
y_max = max(5e6, opt_y * 1.2)
x_grid = np.linspace(0.0, x_max, n_grid_points)
y_grid = np.linspace(0.0, y_max, n_grid_points)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
z_grid = np.zeros_like(x_mesh)  # Initialize a grid for z values

for i in range(x_mesh.shape[0]):
    for j in range(x_mesh.shape[1]):
        z_grid[i, j] = em.costs(x_mesh[i, j], y_mesh[i, j], share_ren_de, share_ren_other)

# Set the perspective and axis limits
elevation = 20  # degrees
azimuth = -136  # degrees
ax.view_init(elev=elevation, azim=azimuth)
ax.set_xlim([0.0, x_max])
ax.set_ylim([0.0, y_max])

# Plot surface
ls = LightSource(270, 45)
ax.plot_surface(x_mesh, y_mesh, z_grid, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False, cmap=cm.coolwarm, zorder=1)

# Plot the optimized solution as a dot
ax.scatter(opt_x, opt_y, opt_z, color='blue', s=50, zorder=2)

# Draw lines to the axis
ax.plot([opt_x, opt_x], [0, opt_y], [opt_z, opt_z], 'k--', alpha=0.8, linewidth=0.8, zorder=2)
ax.plot([0, opt_x], [opt_y, opt_y], [opt_z, opt_z], 'k--', alpha=0.8, linewidth=0.8, zorder=2)

# Set labels
ax.set_xlabel("Power line capacity in kW")
ax.set_ylabel("Hydrogen line capacity in kW")
ax.set_zlabel("Total costs in Euro")

# Show plot
# plt.show()
plt.savefig("./presentation/termin2/optimization.pdf")

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