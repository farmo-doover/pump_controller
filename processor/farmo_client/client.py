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
        
    def get_schedules(self, imei: str):
        return self._request(Route("GET", "get_schedules/{}", imei))
    
    def add_schedules(self, data: dict):
        return self._request(Route("POST", "add_schedules"), json=data)
    
    def update_schedules(self, data: dict):
        return self._request(Route("POST", "update_schedules"), json=data)
    
    def delete_schedules(self, data: dict):
        return self._request(Route("POST", "delete_schedules"), json=data)