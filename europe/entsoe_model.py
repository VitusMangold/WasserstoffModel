""" here we should specify the concrete model """
import entsoe_preprocess as ep
import numpy as np
from scipy.optimize import minimize

# compute difference pro country

time_horizon = 20 # in years
line_length = ... # 
power_fixed_costs = ... #
h2_fixed_costs = ... #
power_variable_costs = ... # per capacity, length
h2_variable_costs = ... # per capacity, length
to_hydrogen_factor = 0.75 # power to hydrogen, \eta_{2,1}
# overproduction_costs_DE = ...
# underproduction_costs_DE = ...
# overproduction_costs_FR = ...
# underproduction_costs_FR = ...
power_price = ... # in kWh

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

def current_net_power_costs(leftover_power):
    """ Cost function for generation/load imbalance between countries """
    # if country == "DE":
    #     factor = overproduction_costs_DE if (net_power >= 0) else underproduction_costs_DE
    # if country == "FR":
    #     factor = overproduction_costs_FR if (net_power >= 0) else underproduction_costs_FR
    # return net_power * factor
    return leftover_power * power_price

def total_net_power_costs(capacity_power, capacity_h2):
    """ Cost function for generation/load imbalances in the countries cumulated over time """
    pointwise_costs = np.vectorize(lambda x, y: max(abs(x - y) - (capacity_power + capacity_h2), 0.0))
    zip_net_power = np.array(list(zip(ep.de_net, ep.fr_net)))
    return pointwise_costs(zip_net_power) * time_horizon

def costs(capacity_power, capacity_h2):
    """ This is our objective function (total costs). """
    building_costs = building_costs_power_line(capacity_power) + building_costs_h2_line(capacity_h2)
    maintenance_costs = costs_power_line(capacity_power) + costs_h2_line(capacity_h2)
    net_power_costs = total_net_power_costs(capacity_power, capacity_h2)
    return building_costs + maintenance_costs + net_power_costs