import pyttanko
import replay_parser

p = pyttanko.parser()

replay = replay_parser.open_file("../temp/wind.osr").replay

with open("../temp/664841/Hard.osu") as f:
    mp = p.map(f)

rep = replay_parser.ScoreReplay(mp, replay)

a = rep.score(mp.od, mp.cs)

avg = a.loc[:, "displacement"].sum() / len(a)
print(avg)
print(a)
