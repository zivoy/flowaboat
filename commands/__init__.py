from os import listdir
from utils import sanitize
List = dict()

for i in listdir("./commands"):
    if not i.startswith("__"):
        comm = i.replace(".py", "")
        exec(f"from .{comm} import Command as {sanitize(comm)}")
        List[eval(comm).command] = eval(comm).synonyms
