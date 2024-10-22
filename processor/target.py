import logging, json, time
# from datetime import datetime, timezone, timedelta

from pydoover.cloud.processor import ProcessorBase
from pydoover import ui

from farmo_client import Client as FarmoClient
# from farmo_client import ScheduleManager as FarmoScheduleManager
# from farmo_client import ScheduleItem as FarmoScheduleItem

from farmo_client import PumpMode, TankSensor, PumpController

from ui import construct_ui


class target(ProcessorBase):

    def setup(self):

        self.uplink_channel_name = "farmo_uplink_recv"

        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)
        
        self.significant_event_channel = self.api.create_channel("significantEvent", self.agent_id)
        # self.activity_log_channel = self.api.create_channel("activity_log", self.agent_id)
        self.uplink_channel = self.api.create_channel(self.uplink_channel_name, self.agent_id)

        self.pump_schedules_channel = self.api.create_channel("schedules", self.agent_id)

        self.construct_ui()

    def construct_ui(self):
        # Construct the UI
        self.ui_manager.pull()
        self._ui_elements = construct_ui(self)
        self.ui_manager.set_children(self._ui_elements)

    def get_imei(self):
        imei = str(self.get_agent_config("FARMO_IMEI"))
        if not imei:
            logging.error("IMEI not found in agent config")
            raise Exception("IMEI not found in agent config")
        else:
            logging.info(f"IMEI: {imei}")
        return imei

    def get_farmo_client(self):
        if not hasattr(self, "_farmo_client"):
            self._farmo_client = FarmoClient()
        return self._farmo_client

    def get_pump_controller_obj(self):
        if not hasattr(self, "_pump_controller"):
            imei = self.get_imei()
            self._pump_controller = PumpController(self.get_farmo_client(), imei)
        return self._pump_controller

    def get_tank_sensor_obj(self):
        target_tank_imei = self.ui_manager.get_command("targetSensor").current_value
        if not target_tank_imei:
            logging.error("Target tank sensor not found in UI")
            return None
            
        ## Check if target tank sensor (which is an imei) is in the list of available tank sensors
        available_tank_sensors = self.get_available_tank_sensors()
        if not available_tank_sensors:
            logging.error("No available tank sensors found")
            return None
        
        ## Check if target tank sensor is in the list of available tank sensors
        if target_tank_imei not in map(lambda x: str(x["IMEI"]), available_tank_sensors):
            logging.error(f"Target tank sensor {target_tank_imei} not found in available tank sensors")
            return None

        logging.info(f"Target tank sensor: {target_tank_imei}")
        if not hasattr(self, "_tank_sensor") or self._tank_sensor.imei != target_tank_imei:
            self._tank_sensor = TankSensor(self.get_farmo_client(), target_tank_imei)
        return self._tank_sensor

    def get_available_tank_sensors(self):
        tank_sensors = self.get_agent_config("TANK_SENSORS")
        if not tank_sensors:
            logging.error("Tank sensors not found in agent config")
            return
        else:
            logging.info(f"Tank sensors: {tank_sensors}")
        return tank_sensors

    def get_pump_mode(self):
        pump_mode_obj = self.ui_manager.get_command("pumpMode")
        if not pump_mode_obj:
            return None
        pump_mode = pump_mode_obj.current_value
        return pump_mode

    def get_tank_level_triggers(self):
        tank_level_trigger_obj = self.ui_manager.get_command("tankLevelTriggers")
        if not tank_level_trigger_obj:
            return None
        tank_level_triggers = self.ui_manager.get_command("tankLevelTriggers").current_value
        return tank_level_triggers

    def update_imei(self):
        imei = self.get_imei()
        self.ui_manager.update_variable("imei", imei)

    def get_pump_state(self):
        pump_state_obj = self.ui_manager.get_from_ui_state("pumpState")
        if not pump_state_obj:
            return None
        if 'currentValue' not in pump_state_obj:
            return None
        return pump_state_obj['currentValue']

    def set_pump_state(self, state):
        logging.info(f"Setting pump state to: {state}")
        # self.ui_manager.coerce_command("_pumpState", state)
        ## Update the 'startStopNow' button
        ss_button = self.ui_manager.get_interaction("startStopNow")
        if state:
            ss_button.display_name = "Stop Now"
            ss_button.colour = "red" 
        else:
            ss_button.display_name = "Start Now"
            ss_button.colour = "green"
        self.ui_manager.update_interaction("startStopNow", ss_button)

    def get_warning_indicator(self):
        return ui.WarningIndicator("pendingCommand", "Waiting for pump controller to receive command")

    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "UPLINK":
            # self.on_uplink()
            self.on_downlink()
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

        ## Get the current pump state
        pump_state = self.get_pump_state()
        ## Get the current pump mode command
        pump_mode = self.get_pump_mode()

        logging.info(f"Pump state: {pump_state}")
        logging.info(f"Pump mode: {pump_mode}")

        ## Handle an update of the target tank sensor from the UI
        tank_sensor_obj = self.get_tank_sensor_obj()
        if tank_sensor_obj:
            result = self.get_pump_controller_obj().set_tank_sensor(self.get_tank_sensor_obj())
            logging.info(f"Result of setting tank sensor: {result}")
        else:
            logging.warning("No available tank sensors found")

        ## Handle an update of the tank thresholds from the UI
        tank_level_triggers = self.get_tank_level_triggers()
        logging.info(f"Tank level triggers: {tank_level_triggers}")
        if tank_level_triggers:
            tank_sensor_obj = self.get_tank_sensor_obj()
            if not tank_sensor_obj:
                logging.warning("Tank sensor not found.")
                return
            result = tank_sensor_obj.set_tank_threshold(tank_level_triggers[0], tank_level_triggers[1])
            logging.info(f"Result of setting tank thresholds: {result}")

        logging.info(f"checking that startButton has been pressed: {self.ui_manager.get_command('startStopNow').current_value}")
        ## Handle a pending start/stop pump command from the UI
        button_pressed = False
        if self.ui_manager.get_command("startStopNow") and self.ui_manager.get_command("startStopNow").current_value:
            button_pressed = True
            ## Get the current pump state
            pump_state = self.get_pump_state()
            ## Get the current pump mode command
            pump_mode = self.get_pump_mode()

            logging.info(f"Pump state: {pump_state}")
            logging.info(f"Pump mode: {pump_mode}")

            if pump_state:
                result = self.get_pump_controller_obj().stop_pump()
                logging.info(f"Result of stopping pump: {result}")
                if pump_mode == PumpMode.ON:
                    ## Coerce the pump state to off
                    self.ui_manager.coerce_command("pumpMode", PumpMode.OFF)
                self.set_pump_state(False)
            else:
                result = self.get_pump_controller_obj().start_pump()
                logging.info(f"Result of starting pump: {result}")
                if pump_mode == PumpMode.OFF:
                    ## Coerce the pump state to on
                    self.ui_manager.coerce_command("pumpMode", PumpMode.ON)
                self.set_pump_state(True)
            
            # ## Clear the pending command
            self.ui_manager.coerce_command("startStopNow", None)
            button_pressed = True

        ## Handle an update of the pump state from the UI
        if not button_pressed:
            pump_mode = self.get_pump_mode()
            logging.info(f"Pump mode: {pump_mode}") 
            if pump_mode:
                result = self.get_pump_controller_obj().set_pump_mode(pump_mode)
                logging.info(f"Result of setting pump mode: {result}")
                if pump_mode == PumpMode.ON:
                    self.set_pump_state(True)
                elif pump_mode == PumpMode.OFF:
                    self.set_pump_state(False)

        ## If trigger message is not from the owner_agent, set the pending command warning
        if self.message and self.message.agent_id != self.agent_id:
            ## Add a warning to show that a pending command is in progress
            ## This can be removed once the command has been processed
            self.ui_manager.add_children([
                self.get_warning_indicator()
            ])

        ## Recompute the UI values
        self.on_uplink(from_downlink=True)


    def on_uplink(self,from_downlink = False):

        ## Example uplink message
        # {
        #     "unitID": "354513596466486",
        #     "message": {
        #         "timestamp": 1727851754,
        #         "farmo_device_name": "RPC-6486",
        #         "farmo_device_type": "remote_pump_control_v1",
        #         "imei": "354513596466486",
        #         "switch_state": 0
        #     }
        # }

        save_log_required = True

        # Run any uplink processing code here
        if not (self.message and self.message.id) or not (self.message.channel_name == self.uplink_channel_name):
            
            logging.info("No trigger message passed - fetching last message")
            self.message = self.uplink_channel.last_message

            if not self.message:
                logging.info("No message found - skipping processing")
                return

            save_log_required = False ## We don't want to show the device updating if we are just fetching the last message

        raw_message = self.message.fetch_payload()
        logging.info(f"Raw message: {raw_message}")
        if raw_message is None:
           logging.info("No payload found in message - skipping processing")
           return
        
        ## Get the pump state
        if not from_downlink:
            pump_running = None
            if "message" in raw_message:
                pump_running = raw_message["message"].get("switch_state")
                logging.info(f"Pump state: {pump_running}")
                if pump_running is not None:
                    pump_running = bool(pump_running)
                    self.set_pump_state(pump_running)

        ## Get the tank level
        target_tank_level = None
        tank_sensor = self.get_tank_sensor_obj()
        if tank_sensor:
            target_tank_level = self.get_pump_controller_obj().get_tank_level()
            logging.info(f"Tank level: {target_tank_level}")

        ## Update the UI Values
        if not from_downlink:
            self.ui_manager.update_variable("targetTankLevel", target_tank_level)
            self.ui_manager.update_variable("pumpState", pump_running)

        self.update_imei()

        ## If this is an update from the uplink channel, clear any pending commands
        if save_log_required:
            ## Clear the pending command
            self.ui_manager.coerce_command("startStopNow", None)
            self.ui_manager.remove_children([self.get_warning_indicator()])

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
        imei = str(self.get_imei())
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
        return 60 * 5 ## 5 mins