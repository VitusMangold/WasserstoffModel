import pandas as pd
import matplotlib.pyplot as plt
import json
from io import StringIO

# Read JSON from file
with open('energy_data.json', 'r') as file:
    data = json.load(file)

# Function to convert JSON strings back to DataFrame using StringIO
def json_string_to_df(json_dict):
    df_dict = {}
    for key, df_string in json_dict.items():
        # Wrap the JSON string with StringIO
        json_data = StringIO(df_string)
        try:
            df_dict[key] = pd.read_json(json_data)
        except ValueError as e:
            print(f"Error processing key '{key}':", e)
            continue
    return df_dict

# Conversion back to DataFrames
loads_from_json = json_string_to_df(data['loads'])
gens_from_json = json_string_to_df(data['generation'])
