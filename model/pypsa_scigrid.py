import pypsa
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

network = pypsa.examples.scigrid_de(from_master=True)

fig, ax = plt.subplots(
    1, 1, subplot_kw={"projection": ccrs.EqualEarth()}, figsize=(8, 8)
)

load_distribution = (
    network.loads_t.p_set.loc[network.snapshots[0]].groupby(network.loads.bus).sum()
)
network.plot(bus_sizes=1e-5 * load_distribution, ax=ax, title="Load distribution")
plt.show()