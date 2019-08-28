git clone https://github.com/ppy/osu-tools
cd ./osu-tools
rm ./.gitmodules

echo "[submodule \"osu\"]" >> .gitmodules
echo "        path = osu" >> .gitmodules
echo "        url = https://github.com/VINXIS/osu" >> .gitmodules
echo "        branch = joz" >> .gitmodules

git submodule init
git submodule update --remote

# cleanup of files

sh ./build.sh