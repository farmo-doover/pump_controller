#!/usr/bin/env python3
import logging

from typing import Any, Union, Callable, overload, Literal, Optional, TypeVar
from urllib.parse import quote, urlencode

import requests


class Route:
    def __init__(self, method, route, *args, **kwargs):
        self.method = method

        self.url = route
        if args:
            self.url = route.format(*[quote(a) for a in args])

        if kwargs:
            self.url = f"{self.url}?{urlencode(kwargs)}"


## An enum for the pump modes
class PumpMode:
    OFF = "off"
    ON = "on_forever"
    SCHEDULE = "schedule"
    TANK_LEVEL = "tank_level"
    TANK_LEVEL_SCHEDULE = "tank_level_schedule"


class Client:

    def __init__(self,
            token: str = "DCFC-AFD69G3HYT67GDdsf5",
            host: str = "np2.farmo.com.au",
            port: Optional[int] = None
        ) -> None:
            
            self.token = token
            self.host = host
            self.port = port

            self.request_timeout = 10
            self.request_retries = 2

            self.session = requests.Session()
            self.update_headers()


    def update_headers(self):
        self.session.headers.update({"X-Auth-Token": f"{self.token}"})
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.verify = True

    def _construct_url(self, location: Optional[Route] = None):
        url = f"https://{self.host}/v1.0/"
        if self.port:
            url = f"https://{self.host}:{self.port}/v1.0/"

        if location:
            return url + location.url
        
        return url


    def _request(self, route: Route, **kwargs):
        url = self._construct_url(route)

        attempt_counter = 0
        retries = self.request_retries if route.method == "GET" else 0

        data = None
        while attempt_counter <= retries:
            attempt_counter += 1

            logging.debug(f"Making {route.method} request to {url} with kwargs {kwargs}")
            resp = self.session.request(route.method, url, timeout=self.request_timeout, allow_redirects=True, **kwargs)

            data = None
            try:
                data = resp.json()
            except ValueError:
                data = resp.text

            if resp.status_code == 200:
                ## if we get a 200, we're good to go
                break
            elif resp.status_code == 403:
                msg = "403 - Access Denied"
                if data:
                    msg = msg + f": {data}"
                raise Exception(msg)
            elif resp.status_code == 404:
                msg = "404 - Not Found"
                if data:
                    msg = msg + f": {data}"
                raise Exception(msg)
            elif resp.status_code != 200:
                logging.info(f"Failed to make request to {url}. Status code: {resp.status_code}, message: {resp.text}")
                if attempt_counter > retries:
                    raise Exception(resp.text)

        logging.debug(f"{url} has received {data}")
        return data
        
    def get_pump_mode(self, imei: str):
        raise NotImplementedError
        return self._request(Route("GET", "get_pump_mode/{}", imei))

    def set_pump_mode(self, imei: str, mode: str):
        ## Check if the mode is valid
        if mode not in [PumpMode.OFF, PumpMode.ON, PumpMode.SCHEDULE, PumpMode.TANK_LEVEL, PumpMode.TANK_LEVEL_SCHEDULE]:
            raise ValueError(f"Invalid pump mode: {mode}")
        
        return self._request(Route("POST", "set_pump_mode"),
            json={
                "rpc_imei": imei,
                "pump_mode": mode
            }
        )
    
    ## Is this set_name or get_name ??
    def get_name(self, imei: str):
        return self._request(Route("POST", "get_name"),
            json={
                "imei": imei,
            }
        )
    
    def get_tank_level(self, imei: str):
        return self._request(Route("GET", "get_tank_level"),
            json={
                "imei": imei
            }
        )

    def set_pump_tank_sensor(self, pump_imei: str, tank_sensor_imei: str):
        return self._request(Route("POST", "update_tank"),
            json={
                "pump_imei": pump_imei,
                "tank_imei": tank_sensor_imei
            }
        )
    
    def set_tank_threshold(self, imei: str, low_threshold: int, high_threshold: int):
        return self._request(Route("POST", "set_tank_threshold"),
            json={
                "tank_imei": imei,
                "low_threshold": low_threshold,
                "high_threshold": high_threshold
            }
        )
    
    def pump_start_now(self, imei: str):
        return self._request(Route("POST", "start_now"),
            json={
                "imei": imei
            }
        )
    
    def pump_stop_now(self, imei: str):
        return self._request(Route("POST", "stop_now"),
            json={
                "imei": imei
            }
        )

    def get_schedules(self, imei: str):
        return self._request(Route("GET", "get_schedules/{}", imei))

    def get_timeslots(self, imei: str):
        return self._request(Route("GET", "get_timeslots/{}", imei))

    def add_schedules(self, data: dict):
        return self._request(Route("POST", "add_schedules"), json=data)
    
    def update_schedules(self, data: dict):
        return self._request(Route("POST", "update_schedules"), json=data)
    
    def delete_schedule(self, data: dict):
        return self._request(Route("POST", "delete_schedule"), json=data)

    def add_schedules_manual(self, data: dict):
        return self._request(Route("POST", "add_schedules_manual"), json=data)
    


if __name__ == "__main__":

    ## Test the client
    client = Client()
    print(client.set_pump_mode("333555333555333", PumpMode.OFF))
    # print(client.get_pump_mode("333555333555333"))