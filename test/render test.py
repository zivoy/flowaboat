import pyttanko

import render_utils

t = pyttanko.parser()

with open("./temp/1028267 Backstreet Boys - I Want It That Way/"
          "Backstreet Boys - I Want It That Way (Arkisol) [Insane].osu", "r") as r:
    mp = t.map(r)

perf = render_utils.perfect_play(mp)

ren = render_utils.Replay(mp, perf)
ren.render("./temp/backbys.mp4", 0, 3 * 60 + 36, audio="./temp/1028267 Backstreet Boys - I Want It That Way/audio.mp3")
