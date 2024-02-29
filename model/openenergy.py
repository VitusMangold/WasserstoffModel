
from requests import get
import pandas as pd
from shapely import wkb
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pc
import numpy as np
from ast import literal_eval
import json

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"

# base_url = "https://openenergy-platform.org/api/v0/schema/grid/tables/ego_pf_hv_generator_pq_set/rows"

# result = get("https://openenergy-platform.org/api/v0/schema/grid/tables/ego_pf_hv_generator_pq_set/rows/?where=version=v0.4.6&where=scn_name=Status%20Quo")

# data = result.json()
# with open(mypath + "gen_pq.json", 'w') as f:
#     json.dump(data, f)

# df = pd.DataFrame(data)
# print(df.describe())
# print(df)

# Process csv data

# has_geom
# df_bus = pd.read_csv(
#     mypath + "grid__ego_pf_hv_bus/grid__ego_pf_hv_bus.csv"
# )
# df_bus.to_parquet('bus.parquet', engine='pyarrow')
# print(df_bus)

# df_gen = pd.read_csv(
#     mypath + "grid__ego_pf_hv_generator/grid__ego_pf_hv_generator.csv"
# )
# df_gen.to_parquet('gen.parquet', engine='pyarrow')
# print(df_gen)

# df_gen_pq = pd.read_csv(
#     mypath + "grid__ego_pf_hv_generator_pq_set/grid__ego_pf_hv_generator_pq_set.csv"
# )
# df_gen_pq.to_parquet('gen_pq.parquet', engine='pyarrow')
# print(df_gen)

# df_load = pd.read_csv(
#     mypath + "grid__ego_pf_hv_load/grid__ego_pf_hv_load.csv"
# )
# df_load.to_parquet('load.parquet', engine='pyarrow')
# print(df_load)

# df_load_pq = pd.read_csv(
#     mypath + "grid__ego_pf_hv_load_pq_set/grid__ego_pf_hv_load_pq_set.csv",
#     engine="pyarrow"
# )
# df_load_pq.to_parquet('load_pq_set.parquet', engine='pyarrow')
# print(df_load_pq)

# chunksize = 1000
# def custom_parse(array_str):
#     # Implement a method to parse your specific string format
#     return np.fromstring(array_str.strip("[]"), sep=',')

# with pd.read_csv(mypath + "grid__ego_pf_hv_load_pq_set/grid__ego_pf_hv_load_pq_set.csv", chunksize=chunksize) as reader:
#     for chunk in reader:
#         # chunk['p_set'] = chunk['p_set'].apply(custom_parse)
#         chunk['p_set'] = chunk['p_set'].apply(json.loads)
#         print("hallo")

file_path = mypath + "grid__ego_pf_hv_load_pq_set/grid__ego_pf_hv_load_pq_set.csv"

# writer = None
# with pyarrow.csv.open_csv(mypath + "grid__ego_pf_hv_load_pq_set/grid__ego_pf_hv_load_pq_set.csv", convert_options=convert_options) as reader:
#     for next_chunk in reader:
#         if next_chunk is None:
#             break
#         if writer is None:
#             writer = pq.ParquetWriter('load_pq_set.parquet', next_chunk.schema, compression='snappy')
#         next_table = pa.Table.from_batches([next_chunk])
#         writer.write_table(next_table)

# if writer:
#     writer.close()

# pf = pq.ParquetFile('load_pq_set.parquet')
# first_ten_rows = next(pf.iter_batches(batch_size = 10)) 
# df_load_pq = pa.Table.from_batches([first_ten_rows]).to_pandas() 
# print(df_load_pq)
# print(df_load_pq["p_set"][0])
# # print(len(df_load_pq["p_set"][0]))
# data = df_load_pq["p_set"].iloc[0]
# print(type(data))
# plt.plot(range(0,data.size), data)
# plt.show()

# df_storage = pd.read_csv(
#     mypath + "grid__ego_pf_hv_storage/grid__ego_pf_hv_storage.csv"
# )
# df_storage.to_parquet('storage.parquet', engine='pyarrow')
# print(df_storage)

# # has_geom
# df_transformer = pd.read_csv(
#     mypath + "grid__ego_pf_hv_transformer/grid__ego_pf_hv_transformer.csv"
# )
# df_transformer.to_parquet('transformer.parquet', engine='pyarrow')
# print(df_transformer)

# # has_geom
# df_line = pd.read_csv(
#     mypath + "grid__ego_pf_hv_line/grid__ego_pf_hv_line.csv"
# )
# df_line.to_parquet('line.parquet', engine='pyarrow')
# print(df_line)

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
    gdf.plot(ax=ax, cmap='viridis', alpha=0.4)

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
plot_df(df_line)
# plt.show()
plt.savefig("./presentation/termin1/line.png")