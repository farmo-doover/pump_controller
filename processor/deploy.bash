#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
python3.11 -m pydoover deploy_config ../doover_config.json --agent 44329546-4b52-4dc5-ac1d-6a7d56345b5b