import logging, json, time
from datetime import datetime, timezone, timedelta

from pydoover.cloud import ProcessorBase

from ui import construct_ui


class target(ProcessorBase):

    def setup(self):

        # Get the required channels
        self.ui_state_channel = self.api.create_channel("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.create_channel("ui_cmds", self.agent_id)
        
        self.significant_event_channel = self.api.create_channel("significantEvent", self.agent_id)
        # self.activity_log_channel = self.api.create_channel("activity_log", self.agent_id)

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


    def assess_lower_warning(self, value, prev_value, min):
        if value is not None and value < min:
            if prev_value is not None and prev_value > min:
                return True
        return False
    
    def assess_upper_warning(self, value, prev_value, max):
        if value is not None and value > max:
            if prev_value is not None and prev_value < max:
                return True
        return False

    ## This gets called before ui manager is constructed
    def get_connection_period(self):
        try:
            sleep_time_hrs = self.ui_manager.get_interaction("sleepTime").current_value
        except:
            sleep_time_hrs = 4

        return sleep_time_hrs * 60 * 60

    def get_previous_level(self, key):

        if not isinstance(key, list):
            keys = [key]
        else:
            keys = key

        state_messages = self.ui_state_channel.fetch_messages()

        ## Search through the last few messages to find the last battery level
        if len(state_messages) < 3:
            logging.info("Not enough data to get previous levels")
            return None

        ### The device published a new message,
        # Then we just published a message to update rssi, snr, etc
        # so we need the message one before that
        prev_levels = {}
        for k in keys:
            i = 2
            prev_levels[k] = None
            while prev_levels[k] is None and i < 10 and i < len(state_messages):
                prev_level = None
                try:
                    prev_state_payload = state_messages[i].fetch_payload()
                    if not isinstance(prev_state_payload, dict):
                        prev_state_payload = json.loads( prev_state_payload )
                    prev_level = prev_state_payload['state']['children'][k]['currentValue']
                    logging.info("Found previous level for " + str(k) + " of " + str(prev_level) + ", " + str(i) + " messages ago : " + str(state_messages[i].id))
                except Exception as e:
                    logging.info("Could not get previous level - " + str(k) + " from error: " + str(e))
                    pass
                prev_levels[k] = prev_level
                i = i + 1

            if prev_levels[k] is None:
                logging.info("Could not get previous level - " + str(k))
            
        return prev_levels