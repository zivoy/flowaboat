import pyttanko

import render_utils

t = pyttanko.parser()

with open("../temp/664841/Hard.osu", "r") as r:
    mp = t.map(r)

perf = render_utils.perfect_play(mp)

print(perf)
