#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
python3.11 -m pydoover invoke_local_task on_downlink . --agent feaec057-5c8e-4561-9f58-ed671017fe5b --profile staging --enable-traceback