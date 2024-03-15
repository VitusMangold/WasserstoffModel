""" Simple two country model (DE/other) """
import entsoe_preprocess as ep
import numpy as np
from scipy.optimize import minimize

time_horizon = 20 # in years
line_length = 2000 # in km
power_building_costs = ... # in kW
h2_building_costs = ((1.0 / (165000e6)) / 1200) * line_length * 7.5e6 # in kW/km,
# extrapolate GWh Nordstream 2 to Spain times costs
to_h2_factor = 0.25 * 0.6 # power to hydrogen
transport_loss_power = 0.05 # per 1000 km
transport_loss_h2 = 0.0 # per 1000 km
power_price_conventional = 0.2000 # in Euro/kWh
power_price_renewable = 0.08 # in Euro/kWh

def conventional_costs(missing_power):
    """ Models the costs arising from having to fill net energy gap by conventional power generation. """
    return missing_power.sum() * power_price_conventional

def renewable_costs(generation):
    """ Power costs of renewables. """
    return generation.sum() * power_price_renewable

def power_line_costs(capacity_power):
    """ Building costs for power line of given capacity. """
    return power_line_costs * capacity_power

def h2_line_costs(capacity_h2):
    """ Building costs for hydrogen line of given capacity. """
    return h2_building_costs * capacity_h2

def costs(capacity_power, capacity_h2, share_renewable):
    """ This is our objective function (total costs). """
    renewable_de = ep.df_gen_de[ep.renewable].sum(axis=1)
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_de = renewable_de * (ep.df_gen_de.sum().sum() / renewable_de.sum()) * share_renewable

    renewable_other = ep.df_gen_other[ep.renewable].sum(axis=1)
    # We scale up our renewables by the current total generation scaled by share_renewable
    hypothetical_other = renewable_other * (ep.df_gen_other.sum().sum() / renewable_other.sum()) * share_renewable

    # there is a missing entry somehow -> average out
    renewable_de = renewable_de.resample('15min').mean()
    renewable_other = renewable_other.resample('15min').mean()
    hypothetical_de = hypothetical_de.resample('15min').mean()
    hypothetical_other = hypothetical_other.resample('15min').mean()

    de_net = hypothetical_de - ep.df_load_de["Actual Load"]
    other_net = hypothetical_other - ep.df_load_other["Actual Load"]#
    print(de_net)
    print(other_net)
    # TODO: this implicitly uses lines which go in either direction, refine!
    def indikator(x, y):
        """ indikator function for one country with positive and one with negative bilance """
        return 1.0 if x * y < 0 else 0.0
    # then send till one of them has net zero or capacity is fully utilized
    pointwise_cross_flow = np.vectorize(lambda x, y: indikator(x, y) * min(capacity_power + to_h2_factor * capacity_h2, abs(x), abs(y)))
    crossborder_flow = pointwise_cross_flow(de_net, other_net) * (other_net > 0.0)
    flow_with_direction = crossborder_flow.mask(de_net < 0, -crossborder_flow)
    missing_power_de = de_net + flow_with_direction
    missing_power_other = other_net - flow_with_direction
    c_costs = conventional_costs(missing_power_de + missing_power_other)
    r_costs = renewable_costs(hypothetical_de + hypothetical_other)
    power_l_costs = power_line_costs(capacity_power)
    h2_l_costs = h2_line_costs(capacity_h2)
    return c_costs + power_l_costs + h2_l_costs + r_costs

# print(costs(1e6, 1e6, 0.9))
print(h2_building_costs)
