""" here we should specify the concrete model """
import entsoe_preprocess as ep
import numpy as np
from scipy.optimize import minimize

# Keine laufenden Kosten!!
# J(f_1, f_2) = (d1 + d2) * p_Kohle + p_Leitung * C + P_Wind * (f_1 + f_2) + C_H * p_H
# und C_H + Koeffizient
# p_Wind = 0,10 €/kWh EEG
# p_Kohle = 0,2€
# Status Quo keine Leitung

de_net = ep.de_net.loc['2023-01-01':'2024-01-01']
other_net = ep.other_net.loc['2023-01-01':'2024-01-01']

# compute difference pro country

time_horizon = 20 # in years
line_length = ... # 
h2_building_costs = (165000e6 / (24 * 365) / 1200) * 2000 * 7.5e6 # in kWh, extrapolate GWh Nordstream 2 to Spain times costs
# power_fixed_costs = 10 #
# h2_fixed_costs =  #
# power_variable_costs = time_horizon * 10 # per capacity, length
# h2_variable_costs = time_horizon * 10 # per capacity, length
to_h2_factor = 0.25 * 0.6 # power to hydrogen, \eta_{2,1}
transport_loss_power = 0.05 # per 1000 km
transport_loss_h2 = 0.0 # per 1000 km
power_price_coal = 0.2000 # in Euro/kWh
power_price_renewable = 0.08 # in Euro/kWh

# advanced stuff
storage_costs = ... # in Euro/kWh / h

def costs_power_line(capacity):
    """ Maintenance costs for power line per year. """
    return (1.0 if (capacity > 0) else 0.0) * power_fixed_costs + capacity * power_variable_costs

def costs_h2_line(capacity):
    """ Maintenance costs for hydrogen line per year. """
    return (1.0 if (capacity > 0) else 0.0) * h2_fixed_costs + capacity * h2_variable_costs

def building_costs_power_line(capacity):
    """ Building costs for power line. """
    return capacity

def building_costs_h2_line(capacity):
    """ Building costs for hydrogen line. """
    return capacity

def storage_costs_h2(storage):
    """ Current storage costs of hydrogen """
    return storage

def current_net_power_costs(leftover_power):
    """ Cost function for generation/load imbalance between countries """
    return leftover_power * power_price

def total_net_power_costs(capacity_power, capacity_h2):
    """ Cost function for generation/load imbalances in the countries cumulated over time
    We use abs(x - y) and one greater 0 of the net powers x and y of two countries
    """
    pointwise_costs = np.vectorize(lambda x, y: max(abs(x - y) - (capacity_power + capacity_h2), 0.0))
    return pointwise_costs(np.array(de_net), np.array(other_net)).sum() * time_horizon

def costs(capacity_power, capacity_h2):
    """ This is our objective function (total costs). """
    building_costs = building_costs_power_line(capacity_power) + building_costs_h2_line(capacity_h2)
    maintenance_costs = costs_power_line(capacity_power) + costs_h2_line(capacity_h2)
    net_power_costs = total_net_power_costs(capacity_power, capacity_h2)
    return building_costs + maintenance_costs + net_power_costs

print(de_net)
print(other_net)
costs(100, 100)
