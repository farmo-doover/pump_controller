#!/bin/bash

curl -v --location --request POST 'https://np2.farmo.com.au/v1.0/add_schedules' \
--header 'X-Auth-Token: DCFC-AFD69G3HYT67GDdsf5' \
--header 'Content-Type: application/json' \
--data '{"imei": "444666444666444", "start_time": 1724721135, "end_time": 1724721535, "frequency": "daily"}'

