import pypsa

network = pypsa.Network()

network.import_from_netcdf("~/Nextcloud/Documents/Uni/FSS_2024/Seminar_Wasserstoff/net_01.nc")

# Simulate/solve linear powerflow
network.lpf()