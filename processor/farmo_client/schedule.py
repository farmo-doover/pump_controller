#!/usr/bin/env python3

import logging

from typing import Any, Union, Callable, overload, Literal, Optional, TypeVar
import enum
import uuid
from datetime import datetime, timedelta

from farmo_client.client import Client

class ScheduleFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    once = "once"

    def __str__(self):
        return self.value


def time_to_epoch(time: Union[datetime, int, str]) -> int:
    if time:
        if isinstance(time, datetime):
            time = int(time.timestamp())
        elif isinstance(time, str):
            try:
                time = datetime.fromisoformat(time).timestamp()
            except ValueError:
                raise ValueError("time must be either a datetime, epoch seconds or ISO formatted string")
        elif isinstance(time, (int, float)):
            time = int(time)
        else:
            raise ValueError("time must be either a datetime, epoch seconds or ISO formatted string")
    return time


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
            # schedule_id = int(str(uuid.uuid4().int)[:8])

        ## Define the private fields, these are used to calculate the start_time and end_time from whatever type is provided
        self._start_time = None
        self._duration = None

        self.imei = imei # type: str
        self.schedule_id = schedule_id # type: int
        self.start_time = start_time # type: int, epoch secs UTC
        self.end_time = end_time # type: int, epoch secs UTC
        self.frequency = frequency # type: ScheduleFrequency

        if json_data:
            self.from_json(json_data)

    def set_client(self, client: Client) -> None:
        self.client = client

    @property
    def start_time(self) -> Optional[int]:
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: Any) -> None:
        self._start_time = time_to_epoch(start_time)

    @property
    def end_time(self) -> Optional[int]:
        return self._start_time + self._duration if self._start_time and self._duration else None

    @end_time.setter
    def end_time(self, end_time: Any) -> None:
        end_time = time_to_epoch(end_time)
        self._duration = end_time - self._start_time if self._start_time else None

    @property
    def duration(self) -> Optional[int]:
        return self._duration
    
    @duration.setter
    def duration(self, duration: Any) -> None:
        if duration:
            if isinstance(duration, timedelta):
                duration = int(duration.total_seconds())
            elif not isinstance(duration, (int, float)):
                raise ValueError("duration must be either a timedelta or seconds")
        self._duration = duration

    def from_json(self, json_data: dict) -> None:
        self.imei = json_data.get("imei")
        self.schedule_id = json_data.get("schedule_id")
        self.start_time = json_data.get("start_time")
        self.end_time = json_data.get("end_time")
        if json_data.get("frequency"):
            self.frequency = ScheduleFrequency(json_data.get("frequency"))

    def to_json(self, field_filters=[]) -> dict:
        result = {
            "imei": self.imei,
            "schedule_id": self.schedule_id,
            "start_time": int(self.start_time) if self.start_time else None,
            "end_time": int(self.end_time) if self.end_time else None,
            "frequency": self.frequency
        }
        for field in field_filters:
            result.pop(field, None)
        return result
    
    def pretty_print(self) -> str:
        return f"Schedule ID: {self.schedule_id}, IMEI: {self.imei}, Start Time: {self.start_time}, End Time: {self.end_time}, Frequency: {self.frequency}"
    
    def _api_add(self) -> None:
        return self.client.add_schedules(
            data=self.to_json(field_filters=["schedule_id"]),
        )

    def _api_update(self) -> None:
        return self.client.update_schedules(
            data=self.to_json(field_filters=["frequency"]),
        )

    def _api_delete(self) -> None:
        return self.client.delete_schedules(
            data=self.to_json(field_filters=["start_time", "end_time", "frequency"]),
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
        self.schedule_items = [ScheduleItem(json_data=item) for item in json_data]

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

    def clear_schedules(self) -> None:
        while self.schedule_items:
            self.delete_schedule_item(item=self.schedule_items[0])




if __name__ == "__main__":
    
    logging.getLogger().setLevel(logging.INFO)

    client = Client()

    ## Run some tests
    # test_imei = "33355533355533"
    test_imei = "444666444666444"

    ## Get the schedules
    logging.info(f"\n\n################ Getting the schedule for IMEI: {test_imei}")
    schedule_manager = ScheduleManager.get_schedule(client, test_imei)
    ## print out the schedule manager
    print(schedule_manager.pretty_print())

    ## Clear all current schedules
    logging.info(f"\n\n################ Clearing the schedule for IMEI: {test_imei}")
    schedule_manager.clear_schedule()
    ## Check that the schedule is empty
    schedule_manager.pull()
    ## print out the schedule manager
    print(schedule_manager.pretty_print())
    ## assert that the schedule is empty
    assert not schedule_manager.schedule_items

    ## Add a schedule item
    logging.info(f"\n\n################ Adding a schedule for IMEI: {test_imei}")
    new_item = ScheduleItem(
        imei=test_imei,
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=1),
        frequency=ScheduleFrequency.daily
    )
    assert new_item.duration == 3600
    schedule_manager.add_schedule_item(new_item)

    ## Check that this new item is in the schedule manager
    logging.info(f"\n\n################ Check the new schedule for IMEI: {test_imei}")
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())

    ## assert that the new_item's schedule_id is in the schedule_manager, test this by checking that the new_items start_time is in the schedule_manager
    newly_created_item = None
    target_start_time = int(new_item.start_time)
    for item in schedule_manager.schedule_items:
        if item.start_time == target_start_time:
            newly_created_item = item
            break
    else:
        raise ValueError("New item not found in schedule manager")

    
    ## Update the new item
    logging.info(f"\n\n################ Update the schedule for IMEI: {test_imei}")
    assert newly_created_item.duration == 3600
    newly_created_item.start_time = datetime.now() + timedelta(days=2)
    assert newly_created_item.duration == 3600
    # newly_created_item.end_time = datetime.now() + timedelta(days=2, hours=1)
    schedule_manager.update_schedule_item(newly_created_item)
    ## Check that this new item is in the schedule manager
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())
    ## assert that the new_item's frequency is now weekly
    resulting_item = schedule_manager.get_schedule_item(newly_created_item.schedule_id)
    assert resulting_item.start_time == newly_created_item.start_time
    assert resulting_item.end_time == newly_created_item.end_time

    ## Delete the new item
    logging.info(f"\n\n################ Delete the schedule for IMEI: {test_imei}")
    schedule_manager.delete_schedule_item(resulting_item)
    ## Check that this new item is in the schedule manager
    schedule_manager.pull()
    ## print out the new schedule item
    print(schedule_manager.pretty_print())
    ## assert that the new_item's schedule_id is not in the schedule_manager
    assert resulting_item.schedule_id not in [item.schedule_id for item in schedule_manager.schedule_items]

    logging.info("\n\n\n    All tests passed!")