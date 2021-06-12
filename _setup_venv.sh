#!/bin/sh

rm -rf .venv/

python3 -m venv .venv
. .venv/bin/activate

pip install -r ./requirements.txt
python3 -m pip install --upgrade pip
