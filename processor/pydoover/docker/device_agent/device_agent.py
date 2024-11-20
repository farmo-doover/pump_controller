import datetime
import json, logging, asyncio, grpc
from typing import Optional

from .grpc_stubs import device_agent_pb2, device_agent_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import maybe_async, call_maybe_async


class DeviceAgentInterface(GRPCInterface):
    stub = device_agent_pb2_grpc.deviceAgentStub

    def __init__(
        self,
        dda_uri: str = "127.0.0.1:50051",
        is_async: bool = None,
        dda_timeout: int = 7,
        max_conn_attempts: int = 5,
        time_between_connection_attempts: int = 10,
    ):
        super().__init__(dda_uri, is_async, dda_timeout)
        
        self.dda_timeout = dda_timeout
        self.max_connection_attempts = max_conn_attempts
        self.time_between_connection_attempts = time_between_connection_attempts

        self.is_dda_available = False
        self.is_dda_online = False
        self.has_dda_been_online = False

        self.subscriptions = {}
        # this is a list of channels that the agent interface will subscribe to,
        # and a list of callbacks that will be called when a message is received,
        # as well as the aggregate data that is received from the channel
        ## for channel in default_subscriptions:
            # #self.subscriptions[channel] = {"callbacks": [], "aggregate": None, is_synced: False}

        self.subscription_handlers = []
        # this is a list of async functions that will be called when the agent interface starts a subscription

    def get_is_dda_available(self):
        return self.is_dda_available
    
    def get_is_dda_online(self):
        return self.is_dda_online
    
    def get_has_dda_been_online(self):
        return self.has_dda_been_online

    def add_subscription(self, channel_name, callback=None):
        existing_channel_subs = self.subscriptions.keys()
        if not channel_name in existing_channel_subs:
            logging.debug("Adding subscription to channel: " + channel_name)
            listener = asyncio.ensure_future(self.start_subscription_listener(channel_name))
            self.subscription_handlers += [listener]
            self.subscriptions[channel_name] = {"listener": listener, "callbacks": [], "aggregate": None, "is_synced": False}
        else:
            logging.debug("Subscription already exists for channel: " + channel_name)

        if callback is not None:
            logging.debug("Adding new callback for subscription to " + channel_name)
            self.subscriptions[channel_name]["callbacks"].append(callback)

    async def start_subscription_listener(self, channel_name):
        while True:
            try:
                logging.debug("Starting subscription to channel: " + channel_name)
                await self.recv_channel_msgs(channel_name)
            except Exception as e:
                logging.error("Error starting subscription listener for " + str(channel_name) + ": " + str(e), exc_info=e)
                await asyncio.sleep(self.time_between_connection_attempts)

    async def recv_update_callback(self, channel_name, response):
        logging.debug("Received response from subscription request: " + str(response)[:100])
        resp = await self.make_request_async("GetChannelDetails", device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name))
        if resp is None:
            logging.warning("Failed to get aggregate from channel: " + channel_name)
            return

        aggregate = resp.channel.aggregate
        ## validate aggregate is valid json
        try:
            json_aggregate = json.loads(aggregate)
            aggregate = json_aggregate
            logging.debug("Parsed aggregate from channel: " + channel_name + " : " + str(json_aggregate)[:100])
        except:
            logging.debug("Failed to parse aggregate from channel: " + channel_name)

        logging.debug("Received aggregate from channel: " + channel_name)
        self.subscriptions[channel_name]["aggregate"] = aggregate

        ## invoke all callbacks
        tasks = []
        for callback in self.subscriptions[channel_name]["callbacks"]:
            task = await call_maybe_async(callback, channel_name, aggregate, as_task=True)
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def recv_channel_msgs(self, channel_name):

        ## Setup the connection to the doover device agent (DDA)
        async with grpc.aio.insecure_channel(self.uri) as channel:

            channel_stream = device_agent_pb2_grpc.deviceAgentStub(channel).GetChannelSubscription( device_agent_pb2.ChannelSubscriptionRequest(channel_name=channel_name))
            while True:
                try:
                    response = await channel_stream.read()
                    logging.debug("Received response from subscription request on " + str(channel_name) + " : " + str(response).replace("\n", " ")[:120])
                    self.update_dda_status(response.response_header)
                    if not response.response_header.success:
                        logging.error("Failed to subscribe to channel " + str(channel_name) + ": " + response.response_header.error_message)
                        return False
                    else:
                        logging.debug("Calling callback with subscription response for " + str(channel_name) + "...")
                        await self.recv_update_callback(channel_name, response)
                except StopAsyncIteration:
                    logging.debug("Channel stream ended.")
                    break

    def process_response(self, stub_call: str, response, *args, **kwargs):
        self.update_dda_status(response.response_header)
        return super().process_response(stub_call, response, *args, **kwargs)

    def update_dda_status(self, header):
        if header.success:
            self.is_dda_available = True
        else:
            self.is_dda_available = False

        if header.cloud_synced:
            self.is_dda_online = True
            if not self.has_dda_been_online:
                logging.info("Device Agent is online")
            self.has_dda_been_online = True
        else:
            self.is_dda_online = False

    @maybe_async()
    def get_channel_aggregate(self, channel_name):
        resp = self.make_request("GetChannelDetails", device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name))
        return resp and resp.channel.aggregate

    async def get_channel_aggregate_async(self, channel_name):
        resp = await self.make_request_async("GetChannelDetails", device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name))
        return resp and resp.channel.aggregate

    @maybe_async()
    def publish_to_channel(self, channel_name, message, record_log=True, save_aggregate=False):
        if isinstance(message, dict):
            message = json.dumps(message)

        req = device_agent_pb2.ChannelWriteRequest(channel_name=channel_name, message_payload=message, save_log=record_log)
        resp = self.make_request("WriteToChannel", req)
        return resp and resp.response_header.success or False

    async def publish_to_channel_async(self, channel_name, message, record_log=True, save_aggregate=False):
        if isinstance(message, dict):
            message = json.dumps(message)

        req = device_agent_pb2.ChannelWriteRequest(channel_name=channel_name, message_payload=message, save_log=record_log)
        resp = await self.make_request_async("WriteToChannel", req)
        return resp and resp.response_header.success or False

    @staticmethod
    def _parse_get_token_response(response) -> Optional[tuple[str, datetime.datetime, str]]:
        if response is None:
            return None

        try:
            return response.token, datetime.datetime.fromtimestamp(float(response.valid_until)), response.endpoint
        except (ValueError, Exception) as e:
            logging.error("Failed to parse output from get_temp_token", exc_info=e)
            return None

    @maybe_async()
    def get_temp_token(self) -> Optional[tuple[str, datetime.datetime, str]]:
        resp = self.make_request("GetTempAPIToken", device_agent_pb2.TempAPITokenRequest())
        return self._parse_get_token_response(resp)

    async def get_temp_token_async(self) -> Optional[tuple[str, datetime.datetime, str]]:
        resp = await self.make_request_async("GetTempAPIToken", device_agent_pb2.TempAPITokenRequest())
        return self._parse_get_token_response(resp)

    def close(self):
        for listener in self.subscription_handlers:
            listener.cancel()
        logging.info("Closing device agent interface...")


device_agent_iface = DeviceAgentInterface