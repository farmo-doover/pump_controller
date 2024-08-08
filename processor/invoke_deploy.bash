#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
python3.11 -m pydoover invoke_local_task on_deploy . --agent 02d46f84-c753-4583-b064-ae0d2329df32 --enable-traceback