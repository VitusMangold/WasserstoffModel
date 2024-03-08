import ast
from requests import get
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pc
import json

keyFile = open('.path', 'r')
mypath = keyFile.readline().rstrip()

base_url = "https://openenergy-platform.org/api/v0/schema/grid/tables/"

# result = get(base_url + "ego_pf_hv_generator_pq_set/rows?where=version=v0.4.6&where=scn_name=Status%20Quo")
# data = result.json()
# with open(mypath + "gen_pq_Status_Quo.json", 'w') as f:
#     json.dump(data, f)

# result = get(base_url + "ego_pf_hv_load_pq_set/rows?where=version=v0.4.6&where=scn_name=Status%20Quo")
# data = result.json()
# with open(mypath + "load_pq_Status_Quo.json", 'w') as f:
#     json.dump(data, f)

result = get(base_url + "ego_pf_hv_generator_pq_set/rows?where=version=v0.4.6&where=scn_name=NEP%202035")
data = result.json()
with open(mypath + "gen_pq_2035.json", 'w') as f:
    json.dump(data, f)

result = get(base_url + "ego_pf_hv_load_pq_set/rows?where=version=v0.4.6&where=scn_name=NEP%202035")
data = result.json()
with open(mypath + "load_pq_2035.json", 'w') as f:
    json.dump(data, f)

# df_load = pd.read_json(mypath + "load_pq.json")
# df_gen_pq = pd.read_json(mypath + "gen_pq.json")
# print(df_load)
# print(df_gen_pq)

# df_load.to_hdf(mypath + "ego.h5", key='load_pq', mode='w')
# df_gen_pq.to_hdf(mypath + "ego.h5", key='gen_pq', mode='w'); # pylint: disable=no-member

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

# file_path = mypath + "grid__ego_pf_hv_load_pq_set/grid__ego_pf_hv_load_pq_set.csv"

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