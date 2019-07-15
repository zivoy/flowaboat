#!/usr/bin/env bash
git checkout master
git pull origin master
git pull incoming master
echo "synced"