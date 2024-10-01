#!/usr/bin/env python3

import logging

from typing import Any, Union, Callable, overload, Literal, Optional, TypeVar
import enum
import uuid
import time
from datetime import datetime, timedelta

from farmo_client.client import Client, PumpMode


## Define a decorator that, if it finds an appropriately named attr on the class, will return it, otherwise will call the function and set the attr to the
## result of the function
def cached_property(func):
    def wrapper(self, *args, **kwargs):
        ## if ignore_cache is set, return the result of the function
        cached_name = f"_{func.__name__}__cached"
        if not kwargs.get("ignore_cache", False):
            if hasattr(self, cached_name):
                return getattr(self, cached_name)
        result = func(self, *args, **kwargs)
        setattr(self, cached_name, result)
        return result
    return wrapper



class Device:

    def __init__(self, client: Client, imei: str) -> None:
        self.client = client
        self.imei = imei


    @cached_property
    def get_farmo_display_name(self) -> str:
        result = self.client.get_name(self.imei)
        self.farmo_display_name = result
        return result
    


class TankSensor(Device):

    def set_tank_threshold(self, low_threshold: int, high_threshold: int) -> bool:
        return self.client.set_tank_threshold(self.imei, low_threshold, high_threshold)

class PumpController(Device):

    @cached_property
    def get_pump_mode(self) -> str:
        return self.client.get_pump_mode(self.imei)
    
    def set_pump_mode(self, mode: str) -> bool:
        return self.client.set_pump_mode(self.imei, mode)
    
    def set_tank_sensor(self, tank_sensor: TankSensor) -> bool:
        return self.client.set_pump_tank_sensor(self.imei, tank_sensor.imei)
    
    @cached_property
    def get_tank_level(self) -> int:
        result = self.client.get_tank_level(self.imei)
        if result is not None and 'percent_full' in result:
            return result['percent_full']
        return None

    def start_pump(self) -> bool:
        return self.client.pump_start_now(self.imei)
    
    def stop_pump(self) -> bool:
        return self.client.pump_stop_now(self.imei)