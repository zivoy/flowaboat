from os import listdir
List = dict()

for i in listdir("./commands"):
    if not i.startswith("__"):
        comm = i.replace(".py", "")
        exec(f"from .{comm} import {comm}")
        List[comm] = eval(comm).synonyms
