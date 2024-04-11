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

df_bus = pd.read_sql("SELECT * FROM grid.egon_etrago_bus WHERE scn_name = 'eGon2035'", engine)
df_line = pd.read_sql("SELECT * FROM grid.egon_etrago_line WHERE scn_name = 'eGon2035'", engine)
df_link = pd.read_sql("SELECT * FROM grid.egon_etrago_link WHERE scn_name = 'eGon2035'", engine)
df_gen = pd.read_sql("SELECT * FROM grid.egon_etrago_generator WHERE scn_name = 'eGon2035'", engine)
df_load = pd.read_sql("SELECT * FROM grid.egon_etrago_load WHERE scn_name = 'eGon2035'", engine)
df_trans = pd.read_sql("SELECT * FROM grid.egon_etrago_transformer WHERE scn_name = 'eGon2035'", engine)
df_storage = pd.read_sql("SELECT * FROM grid.egon_etrago_storage WHERE scn_name = 'eGon2035'", engine)
df_store = pd.read_sql("SELECT * FROM grid.egon_etrago_store WHERE scn_name = 'eGon2035'", engine)

network = pypsa.Network(crs=4326)

df_line_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_line_timeseries WHERE scn_name = 'eGon2035'", engine)
df_link_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_link_timeseries WHERE scn_name = 'eGon2035'", engine)
df_gen_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_generator_timeseries WHERE scn_name = 'eGon2035'", engine)
df_load_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_load_timeseries WHERE scn_name = 'eGon2035'", engine)
df_store_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_store_timeseries WHERE scn_name = 'eGon2035'", engine)

# print(df_bus.columns.values)
# print(df_line.columns.values)
# print(df_line_ts.columns.values)
# print(df_link_ts.columns.values)
# print(df_gen_ts.columns.values)
# print(df_load_ts.columns.values)
# print(df_store_ts.columns.values)

all_dfs = [df_bus, df_line, df_link, df_gen, df_load, df_trans, df_storage, df_store]
# for df in all_dfs:
#     print(df)
id_names = ["bus_id", "line_id", "link_id", "generator_id", "load_id", "transformer_id", "storage_id", "store_id"]
types = ["Bus", "Line", "Link", "Generator", "Load", "Transformer", "StorageUnit", "Store"]
df_bus.set_index("bus_id", inplace=True, drop=False)
for df, ident, component in zip(all_dfs, id_names, types):
    df.rename(columns={ident: "name"}, inplace=True)
    # FIXME:
    # df.set_index("name", inplace=True, drop=False)
    for attr in ["bus", "bus0", "bus1", "name"]:
        if attr in df.columns:
            df[attr] = df[attr].astype(str)
    # print(df.isnull().sum())
    # print(df.dtypes)
    network.import_components_from_dataframe(
        df, component
    )

print(network.buses)
print(network.lines)

network.lines.loc[
    network.lines.r == 0.0, "r"
] = 0.0001

network.transformers.loc[
    network.transformers.r == 0.0, "r"
] = 0.0001

network.consistency_check()
# correct_index = network.lines[network.lines["name"] == "29213"].iloc[0].bus0
# print(correct_index)
# print(type(correct_index))
# print(network.buses[network.buses["name"] == correct_index])
# print(network.buses[network.buses["name"] == "43775"])
# print(network.lines.index[~network.lines["bus0"].isin(network.buses.index)])
# print(network.buses.index)

all_dfs = [df_line_ts, df_link_ts, df_gen_ts, df_load_ts, df_store_ts]
id_names = ["line_id", "link_id", "generator_id", "load_id", "store_id"]
types = ["Line", "Link", "Generator", "Load", "Store"]

# def assign_default_values(default_value, len_series):
#     return [default_value] * len_series

def expand_lists_and_fillna(df, colname, snapshots):
    expanded_data = []
    for _, row in df.iterrows():
        data = row[colname]
        check = pd.isnull(data)
        if isinstance(check, bool) and check:
            # Replace NaN with a list of default values
            default_value = float(network.component_attrs[component].default[colname])
            data = [default_value] * len(snapshots)
        expanded_data.extend(data)
    
    # Create a new DataFrame with expanded data
    expanded_df = pd.DataFrame(expanded_data, columns=[colname])
    # expanded_df['snapshot'] = snapshots.repeat(len(df))
    return expanded_df

for df, ident, component in zip(all_dfs, id_names, types):
    df.rename(columns={ident: "id"}, inplace=True)
    cols_to_drop = ["scn_name", "lines_t_id", "links_t_id", "generators_t_id", "loads_t_id", "stores_t_id"]
    for colname in df.drop([col for col in cols_to_drop if col in df.columns], axis=1).columns.values:
        if colname in network.component_attrs[component].index:
            # default_value = float(network.component_attrs[component].default[colname])
            # df.loc[df[colname].isnull(), :][colname] = df.loc[df[colname].isnull(), :][colname].apply(
            #     lambda row: assign_default_values(default_value, len(network.snapshots))
                # )
            # Split lists into separate rows and replace NaNs
            expanded_df = expand_lists_and_fillna(df, colname, network.snapshots)

            # Now import the expanded DataFrame into PyPSA
            network.import_series_from_dataframe(expanded_df, component, colname)

            # df.index = self.timeindex

## Save
network.export_to_netcdf(
    "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_02.nc"
)
# network.export_to_csv_folder(
#     "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_02"
# )

# redundant
# df_bus_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_bus_timeseries WHERE scn_name = 'eGon2035'", engine)
# df_trans_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_transformer_timeseries WHERE scn_name = 'eGon2035'", engine)
# df_storage_ts = pd.read_sql("SELECT * FROM grid.egon_etrago_storage_timeseries WHERE scn_name = 'eGon2035'", engine)