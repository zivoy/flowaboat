import pyttanko

import replay_parser

p = pyttanko.parser()

replay = replay_parser.open_file("./temp/wind.osr").replay

with open("./temp/664841/Hard.osu") as f:
    mp = p.map(f)

rep = replay_parser.ScoreReplay(mp, replay)

a = rep.generate_score(mp.od, mp.cs, 1.5)

cir = a[a["object"] == "circle"]
avg = cir.loc[:, "displacement"].sum() / len(cir)
revs = a.iloc[0].loc["displacement"]
u = revs.sum() / len(revs)

print("miss's", len(a[a["hit"] == 0]) == 0, len(a[a["hit"] == 0]))
print("50's", len(a[a["hit"] == 50]) == 3, len(a[a["hit"] == 50]))
print("100's", len(a[a["hit"] == 100]) == 17, len(a[a["hit"] == 100]))
print("300's", len(a[a["hit"] == 300]) == 224, len(a[a["hit"] == 300]))
print("combo", a["combo"].max() == 429, a["combo"].max())

print(avg)
# print(a)
# print(u)
