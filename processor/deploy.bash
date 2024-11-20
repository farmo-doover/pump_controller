#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf
python3.11 -m pydoover deploy_config ../doover_config.json --agent feaec057-5c8e-4561-9f58-ed671017fe5b --profile staging --enable-traceback