from os import listdir
from utils import sanitize
List = dict()

for i in listdir("./administrating"):
    if not i.startswith("__") and not i.startswith(".") and i.endswith(".py"):
        adm = i[:-3]
        exec(f"from .{adm} import Watcher as {sanitize(adm)}")
        List[eval(adm).name] = eval(adm).trigger
