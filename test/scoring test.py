import pyttanko

import replay_parser

p = pyttanko.parser()

replay = replay_parser.open_file("./temp/wind.osr").replay

with open("./temp/664841/Hard.osu") as f:
    mp = p.map(f)

rep = replay_parser.ScoreReplay(mp, replay)

a = rep.score(mp.od, mp.cs, 1.5)

cir = a[a["object"] == "circle"]
avg = cir.loc[:, "displacement"].sum() / len(cir)
revs = a.iloc[0].loc["displacement"]
u = revs.sum() / len(revs)

print(avg)
print(a)
print(u)
