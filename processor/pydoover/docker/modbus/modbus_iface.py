#!/usr/bin/env python3

import asyncio
import logging

from typing import Optional

import grpc

from .grpc_stubs import modbus_iface_pb2, modbus_iface_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import call_maybe_async, maybe_async

# just lower case should be fine...
VALID_SERIAL_CONFIG_KEYS = (
    "serial_port", "serial_baud", "serial_method", "serial_bits", "serial_parity", "serial_stop", "serial_timeout",
    "SERIAL_PORT", "SERIAL_BAUD", "SERIAL_METHOD", "SERIAL_BITS", "SERIAL_PARITY", "SERIAL_STOP", "SERIAL_TIMEOUT",
)


def two_words_to_32bit_float(word1, word2, swap=False):
    if swap:
        word1, word2 = word2, word1
    return word1 + (word2 * 65536)


class ModbusInterface(GRPCInterface):
    stub = modbus_iface_pb2_grpc.modbusIfaceStub

    def __init__(self, modbus_uri: str = "127.0.0.1:50054", is_async: bool = None, config_manager=None):
        super().__init__(modbus_uri, is_async)

        self.subscription_tasks = []

        self.setup_task = None
        self.config_complete = True
        if config_manager is not None:
            self.set_config_manager(config_manager=config_manager)
            self.setup_task = asyncio.create_task(self.setup_from_config_manager())


    def set_config_manager(self, config_manager, run_setup=False):
        if self.setup_task is not None:
            logging.warning("Modbus Iface has already been setup, skipping new config manager setup")
            # fixme: should this return None here?

        self.config_complete = False
        self.config_manager = config_manager

        if run_setup:
            self.setup_task = asyncio.create_task(self.setup_from_config_manager())

    async def setup_from_config_manager(self):
        await self.config_manager.await_config()

        # explicitly call async varient because we can
        modbus_config = await self.config_manager.get_config_async('MODBUS_CONFIG')
        logging.info("Setting up modbus iface with following config : " + str(modbus_config))
        if modbus_config is None:
            logging.info("No modbus config found")
            return None
        
        if "SERIAL_PORT" in modbus_config:
            config = {k.lower(): v for k, v in modbus_config.items() if k in VALID_SERIAL_CONFIG_KEYS}
            logging.info("opening new modbus bus on serial port with configuration %s", str(config))
            await self.open_bus_async(bus_type="serial", name="default", **config)

        elif "TCP_URI" in modbus_config:
            tcp_uri = modbus_config.get("TCP_URI", None)
            tcp_timeout = modbus_config.get("TCP_TIMEOUT", None)

            logging.info("opening new tcp modbus bus on uri " + str(tcp_uri))

            await self.open_bus_async(
                bus_type="tcp",
                name="default",
                tcp_uri=tcp_uri,
                tcp_timeout=tcp_timeout,
            )

        elif "BUSES" in modbus_config:

            logging.info("opening multiple modbus buses from config")

            for bus in modbus_config["BUSES"]:
                bus_type = bus.get("BUS_TYPE", None)
                bus_name = bus.get("BUS_NAME", None)

                if bus_type == "serial":
                    serial_port = bus.get("SERIAL_PORT", None)
                    serial_baud = bus.get("SERIAL_BAUD", None)
                    serial_method = bus.get("SERIAL_METHOD", None)
                    serial_bits = bus.get("SERIAL_BITS", None)
                    serial_parity = bus.get("SERIAL_PARITY", None)
                    serial_stop = bus.get("SERIAL_STOP", None)
                    serial_timeout = bus.get("SERIAL_TIMEOUT", None)

                    logging.info("opening new modbus bus on serial port " + str(serial_port))

                    await self.open_bus_async(
                        bus_type="serial",
                        name=bus_name,
                        serial_port=serial_port,
                        serial_baud=serial_baud,
                        serial_method=serial_method,
                        serial_bits=serial_bits,
                        serial_parity=serial_parity,
                        serial_stop=serial_stop,
                        serial_timeout=serial_timeout,
                    )

                elif bus_type == "tcp":
                    tcp_uri = bus.get("TCP_URI", None)
                    tcp_timeout = bus.get("TCP_TIMEOUT")

                    logging.info("opening new tcp modbus bus on uri " + str(tcp_uri))

                    await self.open_bus_async(
                        bus_type="tcp",
                        name=bus_name,
                        tcp_uri=tcp_uri,
                        tcp_timeout=tcp_timeout,
                    )
        
        else:
            logging.info("No modbus buses opened from config")

        self.config_complete = True

    def process_response(self, stub_call: str, response, *args, **kwargs):
        resp = super().process_response(stub_call, response, *args, **kwargs)

        # only for some of the calls we want to ensure a bus is available (e.g. read/write registers)
        # this will fix it for next run but not the current one...
        try:
            configure_bus = kwargs["configure_bus"]
            bus_id = kwargs["bus_id"]

            if not response.response_header.success and configure_bus and not self.ensure_bus_availabe(bus_id, response.response_header):
                logging.warning("Seems bus is not available")
        except KeyError:
            pass

        return resp

    def ensure_bus_availabe(self, bus_id, response_header, configure=True):
        ## if not config_complete, wait for setup to complete
        if not self.config_complete or (self.setup_task is not None and not self.setup_task.done()):
            logging.debug("Waiting for modbus setup to complete")
            return False

        ## check the bus status from the response and if the bus does not exist, and configure is True, rerun the setup
        bus_statusses = response_header.bus_status
        for b in bus_statusses:
            if b.bus_id == bus_id:
                return b.open
            
        logging.warning("Bus " + str(bus_id) + " not found in response")
        if configure:
            logging.info("Reconfiguring modbus iface")
            asyncio.run(self.setup_from_config_manager())
        
        return True


    def close(self):
        logging.info("Closing modbus interface")
        for task in self.subscription_tasks:
            task.cancel()

    @staticmethod
    def _get_bus_request(
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ):
        if bus_type not in ("serial", "tcp"):
            logging.error("Invalid bus type: " + str(bus_type))
            return None

        kwargs = {"bus_id": str(name)}

        if bus_type == "serial":
            kwargs["serial_settings"] = modbus_iface_pb2.serialBusSettings(
                port=serial_port,
                baud=serial_baud,
                modbus_method=serial_method,
                data_bits=serial_bits,
                parity=serial_parity,
                stop_bits=serial_stop,
                timeout=serial_timeout,
            )
        elif bus_type == "tcp":
            ip, port = tcp_uri.split(":")
            kwargs["ethernet_settings"] = modbus_iface_pb2.ethernetBusSettings(
                ip=ip, port=int(port), timeout=tcp_timeout
            )
        else:
            logging.error("Invalid bus type: " + str(bus_type))
            return None

        return modbus_iface_pb2.openBusRequest(**kwargs)

    @maybe_async()
    def open_bus(
        self,
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ) -> bool:
        req = self._get_bus_request(
            bus_type, name, serial_port, serial_baud, serial_method, serial_bits,
            serial_parity, serial_stop, serial_timeout, tcp_uri, tcp_timeout,
        )
        if req is None:
            return

        resp = self.make_request("openBus", req)
        return resp.response_header.success

    async def open_bus_async(
        self,
        bus_type="serial",
        name="default",
        serial_port="/dev/ttyS0",
        serial_baud=9600,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
        tcp_uri="127.0.0.1:5000",
        tcp_timeout=2,
    ) -> bool:
        req = self._get_bus_request(
            bus_type, name, serial_port, serial_baud, serial_method, serial_bits,
            serial_parity, serial_stop, serial_timeout, tcp_uri, tcp_timeout,
        )
        if req is None:
            return False

        resp = await self.make_request_async("openBus", req)
        return resp.response_header.success

    @maybe_async()
    def close_bus(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.closeBusRequest(bus_id=str(bus_id))
        resp = self.make_request("closeBus", req)
        return resp.response_header.success and resp.bus_status.open

    async def close_bus_async(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.closeBusRequest(bus_id=str(bus_id))
        resp = await self.make_request_async("closeBus", req)
        return resp.response_header.success and resp.bus_status.open

    def _validate_read_register_resp(self, resp, bus_id, configure_bus):
        try:
            if not resp.response_header.success:
                logging.error("Error reading registers from bus " + str(bus_id))
                return False
            # return self.ensure_bus_availabe(bus_id, resp.response_header, configure_bus)
            return True
        except Exception as e:
            logging.error("Error validating read register response: " + str(e))
            return False
        
    @maybe_async()
    def get_bus_status(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.busStatusRequest(bus_id=str(bus_id))
        resp = self.make_request("busStatus", req)
        return resp.response_header.success and resp.bus_status.open

    async def get_bus_status_async(self, bus_id: str = "default") -> bool:
        req = modbus_iface_pb2.busStatusRequest(bus_id=str(bus_id))
        resp = await self.make_request_async("busStatus", req)
        return resp.response_header.success and resp.bus_status.open

    getBusStatus = get_bus_status
    getBusStatus_async = get_bus_status_async

    @staticmethod
    def _parse_register_output(values):
        if len(values) == 0:
            return None
        if len(values) == 1:
            return values[0]
        return values

    @maybe_async()
    def read_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> Optional[int | list[int]]:
        req = modbus_iface_pb2.readRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            count=num_registers,
        )
        resp = self.make_request("readRegisters", req, bus_id=bus_id, configure_bus=configure_bus)
        return resp and self._parse_register_output(resp.values)

    async def read_registers_async(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> Optional[int | list[int]]:
        req = modbus_iface_pb2.readRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            count=num_registers,
        )
        resp = await self.make_request_async("readRegisters", req, bus_id=bus_id, configure_bus=configure_bus)
        return resp and self._parse_register_output(resp.values)

    @maybe_async()
    def write_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        values: list[int] = None,
        register_type: int = 4,
        configure_bus=True,
    ) -> bool:
        values = values or []
        req = modbus_iface_pb2.writeRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            values=values,
        )
        resp = self.make_request("writeRegisters", req, bus_id=bus_id, configure_bus=configure_bus)
        return resp and self._validate_read_register_resp(resp, bus_id, configure_bus)

    async def write_registers_async(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        values: list[int] = None,
        register_type: int = 4,
        configure_bus=True,
    ) -> bool:
        values = values or []
        req = modbus_iface_pb2.writeRegisterRequest(
            bus_id=str(bus_id),
            modbus_id=modbus_id,
            register_type=register_type,
            address=start_address,
            values=values,
        )
        resp = await self.make_request_async("writeRegisters", req, bus_id=bus_id, configure_bus=configure_bus)
        return resp and self._validate_read_register_resp(resp, bus_id, configure_bus)


    def add_read_register_subscription(
            self, 
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type=4,
            poll_secs=3,
            callback=None,
        ):

        if callback is None:
            logging.error("No callback provided for read register subscription")
            return None
        
        try:
            new_task = asyncio.create_task(self.run_read_register_subscription_task(
                bus_id=str(bus_id),
                modbus_id=modbus_id,
                start_address=start_address,
                num_registers=num_registers,
                register_type=register_type,
                poll_secs=poll_secs,
                callback=callback,
            ))

            self.subscription_tasks.append(new_task)
            new_task.add_done_callback(self.subscription_tasks.remove)
            return new_task
        
        except Exception as e:
            logging.error("Error adding read register subscription: " + str(e))
            return None


    async def run_read_register_subscription_task(
            self,
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type=4,
            poll_secs=3,
            callback=None,
            configure_bus=True,
        ):

        try:
            async with grpc.aio.insecure_channel(self.uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                request = modbus_iface_pb2.readRegisterSubscriptionRequest(
                    bus_id=str(bus_id),
                    modbus_id=modbus_id,
                    register_type=register_type,
                    address=start_address,
                    count=num_registers,
                    poll_secs=poll_secs,
                )

                try:
                    async for response in stub.readRegisterSubscription(request):
                        
                        success = response.response_header.success
                        if not self._validate_read_register_resp(response, bus_id, configure_bus):
                            values = None
                        elif len(response.values) == 1:
                            values = response.values[0]
                        else:
                            values = response.values

                        logging.debug("recieved new modbus subscription result on bus " + str(bus_id) + ", for modbus_id " + str(modbus_id) + ", result=" + str(success))
                        if callback is not None:
                            await call_maybe_async(callback, values)

                except Exception as e:
                    logging.error("Error in read register subscription task: " + str(e))
                    return None
        
        except Exception as e:
            logging.error("Error in read register subscription task: " + str(e))
            return None



modbus_iface = ModbusInterface
# async def run_test():
    
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    iface = modbus_iface()
    iface.open_bus(
        bus_type="serial",
        name="test",
        serial_port="/dev/ttyk37simOut",
        serial_baud=38400,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
    )

    print(iface.getBusStatus(bus_id="test"))

    result = iface.read_registers(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=23,
    )
    print(result)

    watchdog = result[22] + 1

    result = iface.write_registers(
        bus_id="test",
        modbus_id=1,
        start_address=22,
        values=[watchdog],
    )

    ## define a function to print the results of read register subscription
    def print_results(values):
        print(values)

    loop = asyncio.get_event_loop()

    ## add a read register subscription
    iface.add_read_register_subscription(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=23,
        callback=print_results,
    )

    print("Subscribed to read register subscription")

    ## add a read register subscription
    iface.add_read_register_subscription(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=10,
        callback=print_results,
    )

    # async def run_test():
    #     await asyncio.sleep(20)
    #     iface.close()

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass

    logging.info("Closing modbus interface")
    iface.close()


