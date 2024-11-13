#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
python3.11 -m pydoover invoke_local_task on_schedule_update . --agent f5bb4417-32f9-4630-babc-86d5c54dcca3 --enable-traceback