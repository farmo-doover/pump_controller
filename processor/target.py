import logging, json, time
from datetime import datetime, timezone, timedelta

from pydoover.cloud.processor import ProcessorBase

from farmo_client import Client as FarmoClient
from farmo_client import ScheduleManager as FarmoScheduleManager
from farmo_client import ScheduleItem as FarmoScheduleItem

from ui import construct_ui

import uuid

class target(ProcessorBase):

    def setup(self):

        self.uplink_channel_name = "uplinks"

        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)
        
        self.significant_event_channel = self.api.create_channel("significantEvent", self.agent_id)
        # self.activity_log_channel = self.api.create_channel("activity_log", self.agent_id)
        self.uplink_channel = self.api.create_channel(self.uplink_channel_name, self.agent_id)

        self.pump_schedules_channel = self.api.create_channel("schedules", self.agent_id)

        # Construct the UI
        self._ui_elements = construct_ui(self)
        self.ui_manager.set_children(self._ui_elements)
        self.ui_manager.pull()
        self.update_imei()

    def update_imei(self):
        ## Retrieve the IMEI from the agent config
        imei = str(self.get_agent_config("IMEI"))
        if not imei:
            logging.error("IMEI not found in agent config")
            return
        else:
            logging.info(f"IMEI: {imei}")
        self.ui_manager.update_variable("imei", imei)

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
        
        ## Handle an update of the pump state from the UI
        pump_mode = self.ui_manager.get_variable("pumpMode")
        if pump_mode:
            imei = str(self.get_agent_config("IMEI"))
            if not imei:
                logging.error("IMEI not found in agent config")
                return
            else:
                logging.info(f"IMEI: {imei}")
            farmo_client = FarmoClient()
            farmo_client.set_pump_mode(imei, pump_mode)


    def on_uplink(self):

        save_log_required = True

        # Run any uplink processing code here
        if not (self.message and self.message.id) or not (self.message.channel_name == self.uplink_channel_name):
            
            logging.info("No trigger message passed - fetching last message")
            self.message = self.uplink_channel.last_message

            save_log_required = False ## We don't want to show the device updating if we are just fetching the last message

        #raw_message = self.message.fetch_payload()
        #if raw_message is None:
        #    logging.info("No payload found in message - skipping processing")
        #    return
        
        
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

        # farmo_client = FarmoClient()

        # logging.info(f"Before add : {farmo_client.get_timeslots('333555333555333')}")

        # test = {
        #     "imei": "333555333555333",
        #     "start_time": 1725096590,
        #     "end_time": 1725100190,
        #     "frequency": "daily",
        #     "repeat_until": 1725834211,
        #     "test": "test"
        # }

        #"repeat_until": 1725834211

        # logging.info(f"Test: {farmo_client.add_schedules(test)}")

        # logging.info(f"After add : {farmo_client.timeslots('333555333555333')}")


        schedule_aggregate = self.pump_schedules_channel.fetch_aggregate()
        if schedule_aggregate is None:
            logging.info("No schedule aggregate found - skipping processing")
            return
        
        if len(schedule_aggregate["schedules"]) == 0:
            logging.info("No schedules found - skipping processing")
            return

        # Create the Farmo Client
        imei = str(self.get_agent_config("IMEI"))
        #imei = "333555333555333"
        if not imei:
            logging.error("IMEI not found in agent config")
            return
        else:
            logging.info(f"IMEI: {imei}")
        farmo_client = FarmoClient()
        #schedule_manager = FarmoScheduleManager(farmo_client, imei)

        #schedule_manager.clear_schedules()

        payload = farmo_client.get_schedules(imei)
        logging.info(f"Payload: {payload}")
        for i in payload:
            farmo_client.delete_schedule({
                "imei":imei,
                "schedule_id":i['schedule_id'],
                })
        
        current_time = int(time.time())

        logging.info(f"schedules to add from UI: {schedule_aggregate['schedules']}")

        for schedule in schedule_aggregate['schedules']:

                if schedule["start_time"] <= current_time + 30:
                    if schedule["frequency"] == "once":
                        logging.info("shcedule is in the past and is a once off schedule - skipping") 
                        continue
                        
                    elif schedule["frequency"] == "daily":
                        rawdiff = current_time + 30 - schedule["start_time"]
                        incdiff = ((rawdiff // (24 * 3600)) + 1) * 24 * 3600
                        start_time = schedule["start_time"] + incdiff

                    elif schedule["frequency"] == "weekly":
                        rawdiff = current_time + 30 - schedule["start_time"]
                        incdiff = ((rawdiff // (24 * 3600 * 7)) + 1) * 24 * 3600 * 7
                        start_time = schedule['start_time'] + incdiff

                    if start_time >= schedule["end_time"]:
                        logging.info("schedule has expired - skipping")
                        continue

                    end_time = start_time + (schedule["duration"] * 3600)

                else:
                    start_time = schedule["start_time"]
                    end_time = start_time + (schedule["duration"] * 3600)

                if schedule["edited"] == 0:
                    new_item = {
                        "imei":imei,
                        "start_time":start_time,
                        "end_time":end_time,
                        "frequency":schedule["frequency"],
                        "repeat_until":schedule["end_time"]
                    }
                    farmo_client.add_schedules(new_item)

                else:
                    new_item = {
                        "imei":imei,
                        "timeslots":[]
                    }
                    for timeslot in schedule["timeslots"]:
                        if timeslot["start_time"] <= current_time + 30:
                            logging.info("timeslot is in the past - skipping")
                            continue
                        new_item["timeslots"].append({
                            "start_time":timeslot["start_time"],
                            "end_time":timeslot["end_time"],
                        })

                    farmo_client.add_schedules_manual(new_item)

                test = farmo_client.get_schedules(imei)
                logging.info(f"Updated schedules: {test}")
                test2 = farmo_client.get_timeslots(imei)
                # logging.info(f"Page BREAK FOR EYES")

                # schedule["edited"] == 1:
                #     plainSlots = []
                #     editSlots = []
                #     for i in 

                # logging.info(f"Timeslots: {farmo_client.get_timeslots(imei)}")
                logging.info(f"Timeslots: {test2}")    

    def get_connection_period(self):
        return 60 * 60 * 12 ## 12 hours