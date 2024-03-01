import pandas as pd
from shapely import wkb
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"

def plot_df(df):
    # Assuming 'df' is your DataFrame with the 'geom' column in WKB format
    df['geometry'] = df['geom'].apply(lambda x: wkb.loads(bytes.fromhex(x)))

    # # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf.set_crs(epsg=4326, inplace=True)
    gdf = gdf.to_crs(epsg=3857)

    # Create a subplot
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot the geometries
    gdf.plot(ax=ax, color='red', alpha=0.4)

    # Set the extent of the plot to the bounds of your geometries
    minx, miny, maxx, maxy = gdf.total_bounds
    ax.set_xlim(minx, maxx)
    print(maxy)
    ax.set_ylim(miny, 7.5 * 1e6) # maxy

    # Add OSM basemap
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

df_bus = pd.read_parquet(mypath + "bus.parquet")
df_transformer = pd.read_parquet(mypath + "transformer.parquet")
df_line = pd.read_parquet(mypath + "line.parquet")
# plot_df(df_bus)
# plt.show()
# plot_df(df_transformer)
# plt.show()
print(df_line["scn_name"].unique())
df_line_filtered = df_line.loc[(df_line["scn_name"] == "Status Quo") & (df_line["version"] == "v0.4.6")]
plot_df(df_line_filtered)
plt.show()

# filtered by kV>200
df_bus_200kV = df_bus.loc[(df_bus['v_nom'] > 200) & (df_bus["scn_name"] == "Status Quo") & (df_bus["version"] == "v0.4.6")]
bus_ids_220kV = set(df_bus_200kV['bus_id'])
print(df_bus_200kV)
df_line_filtered = df_line_filtered[df_line_filtered['bus0'].isin(bus_ids_220kV) | df_line_filtered['bus1'].isin(bus_ids_220kV)]
plot_df(df_line_filtered)
plt.show()
# plt.savefig("./presentation/termin1/line.png")