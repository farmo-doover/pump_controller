import logging, json, time
from datetime import datetime, timezone, timedelta

from pydoover.cloud import ProcessorBase

from farmo_client import Client as FarmoClient
from farmo_client import ScheduleManager as FarmoScheduleManager
from farmo_client import ScheduleItem as FarmoScheduleItem

from ui import construct_ui


class target(ProcessorBase):

    def setup(self):

        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)
        
        self.significant_event_channel = self.api.create_channel("significantEvent", self.agent_id)
        # self.activity_log_channel = self.api.create_channel("activity_log", self.agent_id)

        self.pump_schedules_channel = self.api.create_channel("pump_schedules", self.agent_id)

        # Construct the UI
        self._ui_elements = construct_ui(self)
        self.ui_manager.set_children(self._ui_elements)
        self.ui_manager.pull()


    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "UPLINK":
            self.on_uplink()
        elif message_type == "SCHEDULE_UPDATE":
            self.on_schedule_update()


    def on_deploy(self):
        ## Run any deployment code here

        # Construct the UI
        self.ui_manager.push()

        ## Publish a dummy message to ui_cmds to trigger a full refresh
        self.ui_cmds_channel.publish(
            {},
            save_log=False
        )

    def on_downlink(self):
        # Run any downlink processing code here
        return

    def on_uplink(self):

        save_log_required = True

        # Run any uplink processing code here
        if not (self.message and self.message.id) or not (self.message.channel_name == self.uplink_channel_name):
            
            logging.info("No trigger message passed - fetching last message")
            self.message = self.uplink_channel.last_message

            save_log_required = False ## We don't want to show the device updating if we are just fetching the last message

        raw_message = self.message.fetch_payload()
        if raw_message is None:
            logging.info("No payload found in message - skipping processing")
            return
        
        
        target_tank_level = None
        pump_running = None
        pump_pressure = None

        ## Update the UI Values
        self.ui_manager.update_variable("targetTankLevel", target_tank_level)
        self.ui_manager.update_variable("pumpState", pump_running)
        self.ui_manager.update_variable("pumpPressure", pump_pressure)

        ## Update the UI
        self.ui_manager.push(record_log=save_log_required, even_if_empty=True)



    def on_schedule_update(self):

        schedule_aggregate = self.pump_schedules_channel.fetch_aggregate()
        if schedule_aggregate is None:
            logging.info("No schedule aggregate found - skipping processing")
            return
        
        if len(schedule_aggregate) == 0:
            logging.info("No schedule found - skipping processing")
            return
        
        # Create the Farmo Client
        imei = self.get_agent_config("IMEI")
        farmo_client = FarmoClient()
        schedule_manager = FarmoScheduleManager(farmo_client, imei)

        ## Clear the schedules
        schedule_manager.clear_schedules()

        ## for each 'schedule', iterate each 'time_slot' and add it
        for schedule in schedule_aggregate:
            for time_slot in schedule["timeslots"]:
                
                new_item = FarmoScheduleItem(
                    imei=imei,
                    start_time=time_slot["start_time"],
                    end_time=time_slot["end_time"],
                    frequency=time_slot["frequency"],
                )
                schedule_manager.add_schedule_item(new_item)
        