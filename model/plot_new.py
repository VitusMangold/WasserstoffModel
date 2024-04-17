# pylint: disable=no-member
import pypsa_pf as pypsa_pf
import matplotlib.pyplot as plt
from matplotlib import animation
import matplotlib as mpl
import cartopy.crs as ccrs
import pandas as pd
network = pypsa_pf.network

network.consistency_check()

fig, ax = plt.subplots(subplot_kw={"projection": ccrs.EqualEarth()}, figsize=(9, 9))
def animate(i, what):
    now = network.snapshots[i]
    loading = network.lines_t.p0.loc[now] / network.lines.s_nom
    print(abs(loading[abs(loading) > 1.0]),)
    gen_distribution = (
        network.generators_t.p_set.loc[now].groupby(network.generators.bus).sum()
    )
    print(network.generators_t.p_set.loc[now].head())
    print(network.loads_t.p_set.loc[now].head())
    load_distribution = (
        network.loads_t.p_set.loc[now].groupby(network.loads.bus).sum()
    )
    ax.cla() # clear the previous image
    if what == "lines":
        network.plot(
            ax=ax,
            line_colors=abs(loading[abs(loading) <= 1.0]),
            # line_colors=abs(loading[abs(loading) > 1.0]),
            # line_colors=loading.abs() / loading.abs().max(),
            line_cmap=mpl.colormaps['jet'],
            title="Line overloading {}".format(i + 1),
            bus_sizes=5e-4,
            bus_alpha=0.7,
        )
    if what == "generation":
        network.plot(bus_sizes=1e-5 * gen_distribution, ax=ax, title="Generator distribution {}".format(i + 1))
    if what == "load":
        network.plot(bus_sizes=1e-5 * load_distribution, ax=ax, title="Generator distribution {}".format(i + 1))
    if what == "lg":
        network.plot(
            ax=ax,
            line_colors=abs(loading[abs(loading) <= 1.0]),
            # line_colors=abs(loading[abs(loading) > 1.0]),
            # line_colors=loading.abs() / loading.abs().max(),
            line_cmap=mpl.colormaps['jet'],
            title="Line loading under 100 percent and power generation {}".format(i + 1),
            bus_sizes=1e-5 * gen_distribution,
            bus_alpha=0.7,
        )
    fig.tight_layout()
anim = animation.FuncAnimation(fig, lambda x: animate(x, "lines"), interval=1000, frames = 24, blit = False)
# anim = animation.FuncAnimation(fig, lambda x: animate(x, "load"), interval=1000, frames = 24, blit = False)
plt.show()
anim.save("./model/test.gif", writer="imagemagick", fps=1)

network.consistency_check()