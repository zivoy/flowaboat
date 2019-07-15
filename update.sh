#!/usr/bin/env bash
git checkout master
git pull origin master
git pull incoming master
echo "synced"

git add package-lock.json
git add package.json
git commit -m "cleaning packages"
git push
echo "Packages sent"