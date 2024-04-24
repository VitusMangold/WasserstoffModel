import cProfile, pstats, io
from pstats import SortKey
import entsoe_multiple_model as em
pr = cProfile.Profile()
pr.enable()

for i in range(0,10):
    em.costs(
        {"BE" : 1000, "CH" : 1000, "CZ" : 1000, "DK" : 1000, "FR" : 1000, "LU" : 1000, "NL" : 1000, "PL" : 1000},
        {"BE" : 1.0, "CH" : 1.0, "CZ" : 1.0, "DE" : 1.0, "DK" : 1.0, "FR" : 1.0, "LU" : 1.0, "NL" : 1.0, "PL" : 1.0}
    )

pr.disable()
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print(s.getvalue())