# pylint: disable=no-member
import pypsa_pf as pypsa_pf
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
network = pypsa_pf.network

# plot network
fig, ax = plt.subplots(
    1, 1, subplot_kw={"projection": ccrs.EqualEarth()}, figsize=(10, 10)
)
load_distribution = (
    network.loads_t.p_set.loc[network.snapshots[0]].groupby(network.loads.bus).sum()
)
gen_distribution = (
    network.generators.groupby("bus").sum()["p_nom"].reindex(network.buses.index, fill_value=0.0)
)
# sanity checks
if load_distribution.empty:
    print("load_distribution is empty")
print(sum(load_distribution))
print(sum(gen_distribution))

network.plot(bus_sizes=1e-5 * load_distribution, ax=ax, title="Load distribution")
plt.savefig("./model/load_distribution.png")
network.plot(bus_sizes=1e-5 * gen_distribution, ax=ax, title="Generator distribution")
plt.savefig("./model/generator_distribution.png")
# plt.show()

print(network.generators_t.p.sum(axis=1).head)
p_gen = network.generators_t.p.sum(axis=1)
# c = [colors[col] for col in p_by_carrier.columns]
c = ["red", "blue"]

fig, ax = plt.subplots(figsize=(12, 6))
(p_gen / 1e3).plot(ax=ax, linewidth=4) #kind="area", color=c, alpha=0.7)
ax.legend(ncol=4, loc="upper left")
ax.set_ylabel("GW")
ax.set_xlabel("")
fig.tight_layout()
plt.savefig("./model/gen.png")

p_loads = network.loads_t.p.sum(axis=1)
# c = [colors[col] for col in p_by_carrier.columns]
c = ["red", "blue"]

fig, ax = plt.subplots(figsize=(12, 6))
(p_loads / 1e3).plot(ax=ax, linewidth=4) #kind="area", color=c, alpha=0.7)
ax.legend(ncol=4, loc="upper left")
ax.set_ylabel("GW")
ax.set_xlabel("")
fig.tight_layout()
plt.savefig("./model/load.png")