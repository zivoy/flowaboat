from os import listdir
from regex import compile
from utils import sanitize
List = dict()

for i in listdir("./commands"):
    if not i.startswith("__") and not i.startswith(".") and i.endswith(".py"):
        comm = i[:-3]
        exec(f"from .{comm} import Command as {sanitize(comm)}")
        List[eval(comm).command] = [compile(i) for i in eval(comm).synonyms]
