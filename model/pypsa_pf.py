import pypsa
import pandas as pd

from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

network = pypsa.Network()

# network.import_from_netcdf("~/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")
# network.import_from_csv_folder("/Users/johannes/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_02")
network.import_from_netcdf("~/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_02.nc")

# # Set snapshot grid
# snapshots = pd.date_range('2023-01-01', periods=24*365, freq='h')
# network.set_snapshots(snapshots)

# Simulate/solve linear powerflow
network.lpf()
# network.lpf_contingency()