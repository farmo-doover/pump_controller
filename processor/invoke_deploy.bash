#!/bin/bash

export PYTHONDONTWRITEBYTECODE=1
python3.11 -m pydoover invoke_local_task on_deploy . --agent 37706318-6019-4115-9064-bcc727e17c3d --profile staging --enable-traceback