""" Simple two country model (DE/other) """
import entsoe_preprocess as ep
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize

# mw_to_kw = 1000.0
mw_to_kw = 1000.0
renewable_de = ep.df_gen_de[ep.renewable].sum(axis=1) * mw_to_kw
renewable_other = ep.df_gen_other[ep.renewable].sum(axis=1) * mw_to_kw
df_gen_de = ep.df_gen_de * mw_to_kw
df_gen_other = ep.df_gen_other * mw_to_kw
df_load_de = ep.df_load_de * mw_to_kw
df_load_other = ep.df_load_other * mw_to_kw

# there is a missing entry somehow -> average out
renewable_de = renewable_de.resample('15min').mean()
renewable_other = renewable_other.resample('15min').mean()

time_horizon = 20 # in years
line_length = 2000.0 # in km
power_building_costs = 42e9 / (4e6) # in €/kW, Nord-Sued-Link
h2_building_costs = (7.5e9 / (165e9 / (365 * 24))) * (line_length / 1230) # in €/kW
# extrapolate GW Nordstream 2 to Spain times costs
# 165000 GWh und wir betrachten ein Jahr; 7.5 Mrd Euro Baukosten
to_h2_factor = 0.25 * 0.6 # power to hydrogen
transport_loss_power = 0.05 # per 1000 km
transport_loss_h2 = 0.0 # per 1000 km
# power_price_conventional = 0.3000 # in Euro/kWh
power_price_conventional = 0.8 # in Euro/kWh
power_price_renewable = 0.08 # in Euro/kWh

def conventional_costs(missing_power):
    """ Models the costs arising from having to fill net energy gap by conventional power generation. """
    # FIXME:
    return np.sum(missing_power[~np.isnan(missing_power)]) * power_price_conventional

def renewable_costs(generation):
    """ Power costs of renewables. """
    return generation.sum() * power_price_renewable

def power_line_costs(capacity_power):
    """ Building costs for power line of given capacity. """
    return power_building_costs * capacity_power

def h2_line_costs(capacity_h2):
    """ Building costs for hydrogen line of given capacity. """
    return h2_building_costs * capacity_h2

def positive_negative(x, y):
    """ Order net balances in positive and negative part. If both have the same sign we do nothing. """
    if x * y < 0:
        return (x, y) if x > y else (y, x)
    return 0.0, 0.0

def possible_out(high, capacity_power, capacity_h2):
    """ Possible outflow for a country with positive bilance. """
    def order(x, y, cap_x, cap_y):
        if x > y:
            return x, y, cap_x, cap_y
        return y, x, cap_y, cap_x
    better, worse, better_cap, worse_cap = order(
        (1.0 - transport_loss_power)**(line_length/1000.0),
        (1.0 - transport_loss_h2)**(line_length/1000.0) * to_h2_factor,
        capacity_power,
        capacity_h2
    )
    resid = max(high - better_cap/better, 0.0)
    return min((high - resid) * worse, worse_cap) + min(high * better, better_cap)

def real_in(x, y, capacity_power, capacity_h2):
    """ Realisation of inflow considering limited capacity """
    (high, low) = positive_negative(x, y)
    return min(possible_out(high, capacity_power, capacity_h2), abs(low))

# TODO: share_renewables per country
def costs(capacity_power, capacity_h2, share_renewable_de, share_renewable_other):
    """ 
    This is our objective function (total costs).
    
    Right now we don't calculated the loss of the net positive country since it will never go under 0.0;
    therefore no costs from missing power arise
    """
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_de = renewable_de * (df_gen_de.sum().sum() / renewable_de.sum()) * share_renewable_de
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_other = renewable_other * (df_gen_other.sum().sum() / renewable_other.sum()) * share_renewable_other

    hypothetical_de = hypothetical_de.resample('15min').mean()
    hypothetical_other = hypothetical_other.resample('15min').mean()

    de_net = hypothetical_de - df_load_de["Actual Load"]
    other_net = hypothetical_other - df_load_other["Actual Load"]
    # then send till one of them has net zero or capacity is fully utilized
    pointwise_inflow = np.vectorize(
        lambda x, y: real_in(x, y, capacity_power, capacity_h2)
    )
    absolute_inflow = pointwise_inflow(de_net, other_net)

    missing_power_de = -(de_net.mask(de_net > 0.0, 0.0).to_numpy() + np.where(de_net < 0.0, absolute_inflow, 0.0))
    # where cond is true, keep value
    missing_power_other = -(other_net.mask(other_net > 0.0, 0.0).to_numpy() + np.where(other_net < 0.0, absolute_inflow, 0.0))
    # print(pd.DataFrame(missing_power_de + missing_power_other).describe())
    # print(np.count_nonzero(np.isnan(missing_power_de + missing_power_other)))
    c_costs = conventional_costs(missing_power_de + missing_power_other)
    r_costs = renewable_costs(hypothetical_de + hypothetical_other)
    power_l_costs = power_line_costs(capacity_power)
    h2_l_costs = h2_line_costs(capacity_h2)
    # r_costs = 0.0
    # power_l_costs = 0.0
    # h2_l_costs = 0.0
    return c_costs + power_l_costs + h2_l_costs + r_costs

## Minimization

share_ren_de = 1.0
share_ren_other = 1.0

# Initial guess
x0 = np.array([3e6, 3e6])

# Bounds for each variable
bounds = [(0, None), (0, None)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: costs(x[0], x[1], share_ren_de, share_ren_other), x0, method='Nelder-Mead', bounds=bounds)

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
opt_z = costs(opt_x, opt_y, share_ren_de, share_ren_other)

# Generate grid for plotting
# Adjust the range of the grid to better encompass the optimized parameters
x_max = max(5e6, opt_x * 1.2)  # Ensure the grid covers at least 20% beyond the optimized x
y_max = max(5e6, opt_y * 1.2)  # Ensure the grid covers at least 20% beyond the optimized y
x_grid = np.linspace(0.0, x_max, 10)
y_grid = np.linspace(0.0, y_max, 10)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
z_grid = np.array(
    [costs(i, j, share_ren_de, share_ren_other) for i in x_grid for j in y_grid]).reshape(len(x_grid), len(y_grid)
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
ax.set_zlabel("Total costs")

# Show plot
plt.show()

## Minimize all four dimensions

# Initial guess
x0 = np.array([3e6, 5e6, 0.9, 0.9])

# Bounds for each variable
bounds = [(0, None), (0, None), (0, 1), (0, 1)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: costs(x[0], x[1], x[2], x[3]), x0, method='Nelder-Mead', bounds=bounds)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", optimized_parameters)
print("Minimum value:", minimum_value)