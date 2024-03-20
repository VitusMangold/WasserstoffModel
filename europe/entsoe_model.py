""" Simple two country model (DE/other) """
import entsoe_preprocess as ep
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from scipy.optimize import minimize

renewable_de = ep.df_gen_de[ep.renewable].sum(axis=1)
renewable_other = ep.df_gen_other[ep.renewable].sum(axis=1)

# there is a missing entry somehow -> average out
renewable_de = renewable_de.resample('15min').mean()
renewable_other = renewable_other.resample('15min').mean()

time_horizon = 20 # in years
line_length = 2000 # in km
power_building_costs = 42e9 / (4e6) # in €/kW, Nord-Sued-Link
h2_building_costs = (7.5e9 / (165e9 / (365 * 24))) * (line_length / 1230) # in €/kW
# extrapolate GW Nordstream 2 to Spain times costs
# 165000 GWh und wir betrachten ein Jahr; 7.5 Mrd Euro Baukosten
to_h2_factor = 0.25 * 0.6 # power to hydrogen
transport_loss_power = 0.05 # per 1000 km
transport_loss_h2 = 0.0 # per 1000 km
# power_price_conventional = 0.3000 # in Euro/kWh
power_price_conventional = 0.9 # in Euro/kWh
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

def costs(capacity_power, capacity_h2, share_renewable):
    """ 
    This is our objective function (total costs).
    
    Right now we don't calculated the loss of the net positive country since it will never go under 0.0;
    therefore no costs from missing power arise
    """
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_de = renewable_de * (ep.df_gen_de.sum().sum() / renewable_de.sum()) * share_renewable
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_other = renewable_other * (ep.df_gen_other.sum().sum() / renewable_other.sum()) * share_renewable

    hypothetical_de = hypothetical_de.resample('15min').mean()
    hypothetical_other = hypothetical_other.resample('15min').mean()

    de_net = hypothetical_de - ep.df_load_de["Actual Load"]
    other_net = hypothetical_other - ep.df_load_other["Actual Load"]
    # then send till one of them has net zero or capacity is fully utilized
    pointwise_inflow = np.vectorize(
        lambda x, y: real_in(x, y, capacity_power, capacity_h2)
    )
    absolute_inflow = pointwise_inflow(de_net, other_net)
    # masked_positive = absolute_inflow.mask(de_net > 0.0, 0.0)
    # masked_negative = absolute_inflow.mask(de_net < 0.0, 0.0)

    # print("de_net:\n", de_net)
    # print("de_net bool:\n", de_net > 0.0)
    # print("de_net bool:\n", de_net < 0.0)
    # print("Original Series:\n", absolute_inflow)
    # print("Masked (de_net > 0):\n", masked_positive)
    # print("Masked (de_net < 0):\n", masked_negative)
    # print("Original Series modified:\n", absolute_inflow)


    missing_power_de = -(de_net.mask(de_net < 0.0, 0.0).to_numpy() + np.where(de_net < 0.0, absolute_inflow, 0.0))
    # print(missing_power_de)
    # where cond is true, keep value
    missing_power_other = -(other_net.mask(other_net < 0.0, 0.0).to_numpy() + np.where(other_net < 0.0, absolute_inflow, 0.0))
    # print(missing_power_de + missing_power_other)
    # print(pd.DataFrame(missing_power_de + missing_power_other).describe())
    c_costs = conventional_costs(missing_power_de + missing_power_other)
    # print(c_costs)
    # print(np.count_nonzero(np.isnan(missing_power_de + missing_power_other)))
    # FIXME: are we in correct unit??
    r_costs = renewable_costs(hypothetical_de + hypothetical_other)
    power_l_costs = power_line_costs(capacity_power)
    h2_l_costs = h2_line_costs(capacity_h2)
    # power_l_costs = 0.0
    # h2_l_costs = 0.0
    return c_costs + power_l_costs + h2_l_costs + r_costs

share_ren = 0.9

# Initial guess
x0 = np.array([1.0, 1.0])

# Bounds for each variable
bounds = [(0, None), (0, None)]  # (min, max) for x and y

# Perform the optimization
result = minimize(lambda x: costs(x[0], x[1], share_ren), x0, bounds=bounds)

# Extract the results
optimized_parameters = result.x
minimum_value = result.fun

print("Optimized parameters:", optimized_parameters)
print("Minimum value:", minimum_value)

# Generate grid for plotting
x_grid = np.linspace(0.0, 2e3, 10)
y_grid = np.linspace(0.0, 2e3, 10)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)
z_grid = np.array([costs(i, j, share_ren) for i in x_grid for j in y_grid]).reshape(len(x_grid), len(y_grid))

# Create figure and 3D axis
fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

# Plot surface
ls = LightSource(270, 45)
ax.plot_surface(x_mesh, y_mesh, z_grid, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)

# Plot the optimized solution as a dot
opt_x, opt_y = optimized_parameters
opt_z = costs(opt_x, opt_y, 0.9)
ax.scatter(opt_x, opt_y, opt_z, color='red', s=50)  # 's' is the size of the dot

# Set labels
ax.set_xlabel("Power line capacity")
ax.set_ylabel("Hydrogen line capacity")
ax.set_zlabel("Total costs")

# Show plot
plt.show()
