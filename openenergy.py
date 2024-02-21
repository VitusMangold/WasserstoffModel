
from requests import get
import pandas as pd
from shapely import wkb
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx


print("test")
# result = get('https://openenergy-platform.org/api/v0/schema/grid/tables/ego_dp_lv_griddistrict/rows')

result = get('https://openenergy-platform.org/api/v0/schema/grid/tables/ego_dp_ehv_griddistrict/rows')
print("test")
data = result.json()
df = pd.DataFrame(data)
# print(df.describe())
print(df)

# Assuming 'df' is your DataFrame with the 'geom' column in WKB format
df['geometry'] = df['geom'].apply(lambda x: wkb.loads(bytes.fromhex(x)))

# # Convert DataFrame to GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry='geometry')

# gdf.set_crs(epsg=3857, inplace=True)
# gdf = gdf.to_crs(epsg=3857)

# ax = gdf.plot(cmap='viridis', alpha=0.5)
# # ctx.add_basemap(ax, crs=gdf.crs.to_string())
# ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
# plt.show()  # Displays the plot

gdf.set_crs(epsg=4326, inplace=True)
gdf = gdf.to_crs(epsg=3857)

# Create a subplot
fig, ax = plt.subplots(figsize=(10, 10))

# Plot the geometries
gdf.plot(ax=ax, cmap='viridis', alpha=0.4)

# Set the extent of the plot to the bounds of your geometries
minx, miny, maxx, maxy = gdf.total_bounds
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)

# Add OSM basemap
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

plt.show()  # Displays the plot
