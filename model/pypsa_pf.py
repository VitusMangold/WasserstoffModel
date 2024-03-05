import pypsa
import pandas as pd

network = pypsa.Network()

network.import_from_netcdf("~/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")

# Set snapshot grid
snapshots = pd.date_range('2023-01-01', periods=24, freq='h')
network.set_snapshots(snapshots)

# Simulate/solve linear powerflow
network.lpf()