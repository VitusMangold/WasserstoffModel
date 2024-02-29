import pandas as pd

mypath = "/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/"

df_line = pd.read_csv(
    mypath + "grid__ego_pf_hv_line/grid__ego_pf_hv_line.csv"
)
print(df_line)

# filter line by >= 200kV
# df_line_filtered = df_line.loc[df_line['Percentage'] > 200]
df_line_filtered = df_line.loc[df_line['Percentage'] > 200]
print(df_line_filtered)


# filter bus by connection to line

# assign loads/generator to nearest bus