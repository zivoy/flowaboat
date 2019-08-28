git clone https://github.com/ppy/osu-tools
cd .\osu-tools
rm .\.gitmodules

Add-Content .\.gitmodules "[submodule `"osu`"]"
Add-Content .\.gitmodules "`tpath = osu"
Add-Content .\.gitmodules "`turl = https://github.com/VINXIS/osu"
Add-Content .\.gitmodules "`tbranch = joz"

git submodule init
git submodule update --remote

# cleanup of files

& .\build.ps1