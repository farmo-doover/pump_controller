#!/usr/bin/env python3

import logging

from typing import Any, Union, Callable, overload, Literal, Optional, TypeVar
import enum
import uuid
from datetime import datetime, timedelta

from client import Client

class ScheduleFrequency(enum.Enum):
    daily = "daily"
    weekly = "weekly"
    once = "once"


class ScheduleItem:

    def __init__(self, 
                client: Optional[Client] = None, 
                json_data: Optional[dict] = None,

                imei: Optional[str] = None,
                schedule_id: Optional[int] = None,
                start_time: Optional[Any] = None, ## Either Epoch UTC Secs or Python datetime
                end_time: Optional[Any] = None, ## Either Epoch UTC Secs or Python datetime
                duration: Optional[Any] = None, ## Either Seconds or Python timedelta
                frequency: Optional[ScheduleFrequency] = None, 

            ) -> None:

        ## Ensure we are given either a json_data or all the required fields
        if not json_data:
            if not all([imei, start_time, frequency]):
                raise ValueError("Either json_data or all required fields must be provided")
            elif not end_time and not duration:
                raise ValueError("Either end_time or duration must be provided")

        self.client = client

        if not schedule_id:
            schedule_id = uuid.uuid4().int

        if isinstance(start_time, datetime):
            start_time = start_time.timestamp()
        if end_time and isinstance(end_time, datetime):
            end_time = end_time.timestamp()

        if duration and isinstance(duration, timedelta):
            duration = duration.total_seconds()
            end_time = start_time + duration

        self.imei = imei # type: str
        self.schedule_id = schedule_id # type: int
        self.start_time = start_time # type: int, epoch secs UTC
        self.end_time = end_time # type: int, epoch secs UTC
        self.frequency = frequency # type: str, ["Daily", "Weekly", "Once"]

        if json_data:
            self.from_json(json_data)

    def set_client(self, client: Client) -> None:
        self.client = client

    def from_json(self, json_data: dict) -> None:
        self.imei = json_data.get("imei")
        self.schedule_id = json_data.get("schedule_id")
        self.start_time = json_data.get("start_time")
        self.end_time = json_data.get("end_time")

        if json_data.get("frequency"):
            self.frequency = ScheduleFrequency(json_data.get("frequency"))

    def to_json(self) -> dict:
        return {
            "imei": self.imei,
            "schedule_id": self.schedule_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "frequency": self.frequency
        }
    
    def pretty_print(self) -> str:
        return f"Schedule ID: {self.schedule_id}, IMEI: {self.imei}, Start Time: {self.start_time}, End Time: {self.end_time}, Frequency: {self.frequency}"
    
    def _api_add(self) -> None:
        return self.client.add_schedules(
            imei=self.imei,
            data=self.to_json(),
        )

    def _api_update(self) -> None:
        return self.client.update_schedules(
            data=self.to_json(),
        )

    def _api_delete(self) -> None:
        return self.client.delete_schedules(
            data=self.to_json(),
        )
    

class ScheduleManager:

    def __init__(self,
                client: Client,
                imei: Optional[str] = None,
                json_data: Optional[dict] = None
            ) -> None:
        
        self.client = client
        self.imei = imei

        self.schedule_items = [] # type: List[ScheduleItem]

        if json_data:
            self.from_json(json_data)


    @classmethod
    def get_schedule(cls, client: Client, imei: str) -> "ScheduleManager":
        data = client.get_schedules(imei)
        return cls(client, imei, data)

    def from_json(self, json_data: dict) -> None:
        self.schedule_items = [ScheduleItem(item) for item in json_data]

        if not self.imei and self.schedule_items:
            self.imei = self.schedule_items[0].imei

    def to_json(self) -> dict:
        return [item.to_json() for item in self.schedule_items]
    
    def pretty_print(self) -> str:
        return "\n".join([item.pretty_print() for item in self.schedule_items])

    def pull(self) -> None:
        self.from_json(self.client.get_schedules(self.imei))
    
    def get_schedule_item(self, id: int) -> None:
        for item in self.schedule_items:
            if item.schedule_id == id:
                return item
        return None
    
    def add_schedule_item(self, item: ScheduleItem) -> None:
        item.set_client(self.client)
        try:
            item._api_add()
            self.schedule_items.append(item)
        except Exception as e:
            logging.error(f"Failed to add schedule item: {e}")
        
    def update_schedule_item(self, item: ScheduleItem) -> None:
        item.set_client(self.client)
        try:
            item._api_update()
        except Exception as e:
            logging.error(f"Failed to update schedule item: {e}")

    def delete_schedule_item(self, item: Optional[ScheduleItem] = None, id: Optional[int] = None) -> None:
        ## Ensure we have either an item or an id
        if not item and not id:
            raise ValueError("Either item or id must be provided")
        if item and id:
            raise ValueError("Only one of item or id must be provided")
        
        if id:
            item = self.get_schedule_item(id)
            if not item:
                raise ValueError(f"Schedule item with id {id} not found")
        
        item.set_client(self.client)
        try:
            item._api_delete()
            self.schedule_items.remove(item)
        except Exception as e:
            logging.error(f"Failed to delete schedule item: {e}")



if __name__ == "__main__":
    
    logging.getLogger().setLevel(logging.DEBUG)

    client = Client()

    ## Run some tests
    # test_imei = "33355533355533"
    test_imei = "444666444666444"

    ## Get the schedule manager
    schedule_manager = ScheduleManager.get_schedule(client, test_imei)
    ## print out the schedule manager
    print(schedule_manager.pretty_print())

    ## Add a schedule item
    new_item = ScheduleItem(
        imei=test_imei,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        frequency=ScheduleFrequency.daily
    )
    schedule_manager.add_schedule_item(new_item)

    ## Check that this new item is in the schedule manager
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())
    ## assert that the new_item's schedule_id is in the schedule_manager
    assert new_item.schedule_id in [item.schedule_id for item in schedule_manager.schedule_items]
    
    ## Update the new item
    new_item.frequency = ScheduleFrequency.weekly
    schedule_manager.update_schedule_item(new_item)
    ## Check that this new item is in the schedule manager
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())
    ## assert that the new_item's frequency is now weekly
    resulting_item = schedule_manager.get_schedule_item(new_item.schedule_id)
    assert resulting_item.frequency == ScheduleFrequency.weekly

    ## Delete the new item
    schedule_manager.delete_schedule_item(new_item)
    ## Check that this new item is in the schedule manager
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())
    ## assert that the new_item's schedule_id is not in the schedule_manager
    assert new_item.schedule_id not in [item.schedule_id for item in schedule_manager.schedule_items]

    print("\n\n\n    All tests passed!")