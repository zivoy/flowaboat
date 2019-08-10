#!/usr/bin/env bash
git checkout master
git add package-lock.json
git add package.json
git commit -m "cleaning packages"
echo "Packages sent"

git checkout master
git pull origin master
git pull incoming master

git push
echo "synced"