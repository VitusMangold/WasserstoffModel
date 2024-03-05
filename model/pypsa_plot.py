# pylint: disable=no-member
import pypsa_ehv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
network = pypsa_ehv.network

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
plt.show()

# gdf.set_crs(epsg=4326, inplace=True)
# gdf = gdf.to_crs(epsg=3857)

# # Create a subplot
# fig, ax = plt.subplots(figsize=(10, 10))

# # Plot the geometries
# gdf.plot(ax=ax, color='red', alpha=0.4)

# # Set the extent of the plot to the bounds of your geometries
# minx, miny, maxx, maxy = gdf.total_bounds
# ax.set_xlim(minx, maxx)
# print(maxy)
# ax.set_ylim(miny, 7.5 * 1e6) # maxy

# # Add OSM basemap
# ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
