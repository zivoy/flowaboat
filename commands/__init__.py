List = list()
from os import listdir

for i in listdir("./commands"):
    if not i.startswith("__"):
        comm = i.replace(".py", "")
        List.append(comm)
        exec(f"from .{comm} import {comm}")
