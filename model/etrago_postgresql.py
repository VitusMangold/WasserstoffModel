# import psycopg2
import pandas as pd
import pypsa
from sqlalchemy import create_engine
import saio
# import oedialect

# Define your connection parameters
dialect = "psycopg2"
user = "johannes"
host = "localhost"
port = "5432"  # Default port for PostgreSQL
db = "mydb"

# Create the engine
engine = create_engine(f"postgresql+{dialect}://{user}@{host}:{port}/{db}")

# query = "SELECT * FROM grid.egon_etrago_transformer"
# df = pd.read_sql("SELECT * FROM grid.egon_etrago_transformer", engine)

df_bus = pd.read_sql("SELECT * FROM grid.egon_etrago_bus WHERE scn_name = 'eGon2035'", engine)
df_line = pd.read_sql("SELECT * FROM grid.egon_etrago_line WHERE scn_name = 'eGon2035'", engine)
df_link = pd.read_sql("SELECT * FROM grid.egon_etrago_link WHERE scn_name = 'eGon2035'", engine)
df_gen = pd.read_sql("SELECT * FROM grid.egon_etrago_generator WHERE scn_name = 'eGon2035'", engine)
df_load = pd.read_sql("SELECT * FROM grid.egon_etrago_load WHERE scn_name = 'eGon2035'", engine)
df_trans = pd.read_sql("SELECT * FROM grid.egon_etrago_transformer WHERE scn_name = 'eGon2035'", engine)
df_storage = pd.read_sql("SELECT * FROM grid.egon_etrago_storage WHERE scn_name = 'eGon2035'", engine)
df_store = pd.read_sql("SELECT * FROM grid.egon_etrago_store WHERE scn_name = 'eGon2035'", engine)

# df_bus_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_bus_timeseries WHERE scn_name = 'eGon2035'", engine)
# df_trans_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_transformer_timeseries WHERE scn_name = 'eGon2035'", engine)
# df_storage_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_storage_timeseries WHERE scn_name = 'eGon2035'", engine)

df_line_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_line_timeseries WHERE scn_name = 'eGon2035'", engine)
df_link_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_link_timeseries WHERE scn_name = 'eGon2035'", engine)
df_gen_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_generator_timeseries WHERE scn_name = 'eGon2035'", engine)
df_load_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_load_timeseries WHERE scn_name = 'eGon2035'", engine)
df_store_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_store_timeseries WHERE scn_name = 'eGon2035'", engine)


print(df_bus)
print(df_bus.columns.values)
print(df_line_ts)
print(df_link_ts)
print(df_gen_ts)
print(df_load_ts)
print(df_store_ts)