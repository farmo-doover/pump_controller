import threading
import time, logging, traceback, argparse, asyncio, signal
from typing import Optional, Any

from .camera import CameraManager, CameraInterface
from .device_agent import DeviceAgentInterface, device_agent_iface
from .modbus import ModbusInterface, modbus_iface
from .platform import PlatformInterface
from .tunnel import TunnelInterface
from ..ui import UIManager
from ..utils import maybe_async, CaseInsensitiveDict, call_maybe_async, get_is_async


log = logging.getLogger(__name__)

class app_manager_logging_formatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class app_base:

    def __init__(self, manager=None, name=None, is_async: bool = None):
        self.manager = manager

        self._is_async = get_is_async(is_async)
        self.ui_manager: Optional[UIManager] = None

        self._camera_manager: Optional[CameraManager] = None
        self._modbus_iface: Optional[modbus_iface] = None
        self._platform_iface: Optional[PlatformInterface] = None
        self._tunnel_iface: TunnelInterface = None

        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

        self.log_warnings_issued = []

    def set_manager(self, manager):
        self.manager = manager

    def get_app_name(self):
        return self.name

    def get_manager(self):
        return self.manager
    

    ## Agent Interface Functions (DDA)

    def get_agent_iface(self):
        return self.manager.get_agent_iface()
    
    def get_is_dda_available(self):
        return self.get_agent_iface().get_is_dda_available()
    
    def get_is_dda_online(self):
        return self.get_agent_iface().get_is_dda_online()
    
    def get_has_dda_been_online(self):
        return self.get_agent_iface().get_has_dda_been_online()

    def subscribe_to_channel(self, channel_name, callback=None):
        self.get_agent_iface().add_subscription(channel_name, callback)

    def publish_to_channel(self, channel_name, data):
        return self.get_agent_iface().publish_to_channel(channel_name, data)

    def get_channel_aggregate(self, channel_name):
        return self.get_agent_iface().get_channel_aggregate(channel_name)
    

    ## Config Manager Functions

    def get_config_manager(self) -> "deployment_config_manager":
        return self.manager.get_config_manager()
    
    def get_config(self, key_filter=None, wait=None, default=None):
        result = self.get_config_manager().get_config(key_filter, wait)
        if result is None:
            return default
        return result


    ## UI Manager Functions

    def get_ui_manager(self):
        if self.ui_manager is None:
            self.ui_manager: UIManager = UIManager(agent_id=None, client=self.get_agent_iface(), is_async=self._is_async)
        return self.ui_manager
    
    def set_ui_elements(self, elements):
        return self.get_ui_manager().set_children(elements)

    def get_command(self, name):
        return self.get_ui_manager().get_command(name)
    
    def coerce_command(self, name, value):
        return self.get_ui_manager().coerce_command(name, value)
    
    def record_critical_value(self, name, value):
        return self.get_ui_manager().record_critical_value(name, value)

    def set_ui_status_icon(self, icon):
        return self.get_ui_manager().set_status_icon(icon)

    def start_ui_comms(self):
        ui_manager_obj = self.get_ui_manager()
        ui_manager_obj.start_comms()

    def set_ui(self, ui):
        self.get_ui_manager().set_children(ui)

    async def update_ui(self):
        await self.get_ui_manager().handle_comms()


    ## Platform Interface Functions

    @property
    def platform_iface(self):
        if self._platform_iface is None:
            self._platform_iface = self.get_manager().get_platform_iface()
        return self._platform_iface

    def get_platform_iface(self):
        return self.platform_iface

    def get_di(self, di):
        return self.platform_iface.get_di(di)

    def get_ai(self, ai):
        return self.platform_iface.get_ai(ai)

    def get_do(self, do):
        return self.platform_iface.get_do(do)
    
    def set_do(self, do, value):
        return self.platform_iface.set_do(do, value)
    
    def schedule_do(self, do, value, delay_secs):
        return self.platform_iface.schedule_do(do, value, delay_secs)
    
    def get_ao(self, ao):
        return self.platform_iface.get_ao(ao)

    def set_ao(self, ao, value):
        return self.platform_iface.set_ao(ao, value)
    
    def schedule_ao(self, ao, value, delay_secs):
        return self.platform_iface.schedule_ao(ao, value, delay_secs)
    

    ## Modbus Interface Functions

    @property
    def modbus_iface(self):
        if self._modbus_iface is None:
            self._modbus_iface = self.get_manager().get_modbus_iface()
        return self._modbus_iface

    def get_modbus_iface(self):
        return self.modbus_iface
        # return self.get_manager().get_modbus_iface()
    
    def read_modbus_registers(self, address, count, register_type, modbus_id=None, bus_id=None):
        return self.modbus_iface.read_registers(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            num_registers=count,
            register_type=register_type,
        )
    
    def write_modbus_registers(self, address, values, register_type, modbus_id=None, bus_id=None):
        return self.modbus_iface.write_registers(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            values=values,
            register_type=register_type,
        )
    
    def add_new_modbus_read_subscription(self, address, count, register_type, callback, poll_secs=None, modbus_id=None, bus_id=None):
        return self.modbus_iface.add_new_read_subscription(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            num_registers=count,
            register_type=register_type,
            poll_secs=poll_secs,
            callback=callback,
        )


    ## Camera Manager Functions

    @property
    def camera_manager(self):
        if not self._camera_manager:
            logging.info("Creating camera manager")
            self._camera_manager = CameraManager(
                config_manager=self.get_config_manager(),
                dda_iface=self.get_agent_iface(),
                ui_manager=self.ui_manager,
                plt_iface=self.platform_iface,
                app_manager=self.get_manager(),
            )
        return self._camera_manager

    def get_camera_manager(self):
        return self.camera_manager

    @property
    def tunnel_iface(self):
        if not self._tunnel_iface:
            self._tunnel_iface = self.get_manager().tunnel_iface
        return self._tunnel_iface

    ## App Functions

    async def _setup(self):
        log.info("Setting up internal app : " + self.get_app_name())
        await self.get_config_manager().await_config()
        self.start_ui_comms()
        await self.camera_manager.setup()

    async def _main_loop(self):
        log.info("Running internal main_loop : " + self.get_app_name())
        await self.camera_manager.main_loop()
        await self.update_ui()

    def setup(self):
        return NotImplemented

    def main_loop(self):
        return NotImplemented

    def log(self, log_level="info", msg=None):

        ## Allows multiple variants of arguments to be accepted as valid
        if msg is None and log_level is not None:
            msg = log_level
            log_level = None

        if log_level not in ["debug", "info", "warning", "error", "critical"]:
            if log_level not in self.log_warnings_issued:
                logging.warning("Invalid log level '" + str(log_level) + "' , defaulting to 'info'")
                self.log_warnings_issued.append(log_level)
            log_level = "info"
        log_function = getattr(logging, log_level)
        log_function("[" + self.get_app_name() + "] " + str(msg))



class deployment_config_manager:
    def __init__(self, dda_iface=None, auto_start=True, update_callback=None):
        self.dda_iface = dda_iface
        
        self.deployment_channel_name = 'deployment_config'

        self.is_subscribed = False
        self.has_recv_message = False
        self.last_deployment_config = {}
        self.update_callback = update_callback

        self.is_ready_event = asyncio.Event()

        if auto_start and self.dda_iface is not None:
            self.setup()


    def set_dda_iface(self, dda_iface):
        self.dda_iface = dda_iface

    def setup(self):
        if self.is_subscribed:
            return ## already setup

        self.is_subscribed = True
        self.dda_iface.add_subscription(self.deployment_channel_name, self.recv_updates)

    async def await_config(self, wait_period: int = 20):
        logging.info("Awaiting deployment config...")

        self.setup()
        try:
            await asyncio.wait_for(self.is_ready_event.wait(), wait_period)
            logging.info("Received deployment config")
        except asyncio.TimeoutError:
            logging.warning("Failed to receive deployment config due to timeout.")

        return self.last_deployment_config

    async def recv_updates(self, channel_name, last_aggregate):
        if channel_name is not self.deployment_channel_name:
            return ## Not the correct channel - something weird here
        
        if 'deployment_config' not in last_aggregate:
            logging.info("No deployment_config field in last deployment_config channel aggregate")
            return

        self.last_deployment_config = CaseInsensitiveDict.from_dict(last_aggregate["deployment_config"])
        logging.debug(f"Received deployment config: {self.last_deployment_config}")

        self.has_recv_message = True
        self.is_ready_event.set()

        if self.update_callback is not None:
            await call_maybe_async(self.update_callback, self.last_deployment_config)


    def _do_get_config(self, key_filter: str | list[str]) -> Optional[Any]:
        # When this goes up for review feel free to disagree with me,
        # but I don't see a reason for case sensitivity in the config lookup
        # I'm pretty sure the site turns everything to UPPER anyway
        config = self.last_deployment_config
        if config is None or len(config.keys()) == 0:
            return None

        if isinstance(key_filter, str):
            # fast route
            try:
                return config[key_filter.lower()]
            except KeyError:
                return None

        key_filter = [k.lower() for k in key_filter if isinstance(k, str)]
        if not key_filter:
            return None

        # fixme: not sure what to do here, the old code would return the
        #  last matching key, and if any didn't exist return None.

        # in the interim I'm just going to return the first matching instance.
        for key in key_filter:
            try:
                return config[key]
            except KeyError:
                continue

    @maybe_async()
    def get_config(self, key_filter=None, wait=True, wait_period=10, case_sensitive=False):
        if wait and not self.has_recv_message:
            wait_start = time.time()
            while not self.has_recv_message and (time.time() - wait_start < wait_period):
                time.sleep(0.25)

        return self._do_get_config(key_filter)

    async def get_config_async(self, key_filter=None, wait=True, wait_period=10, case_sensitive=False):
        if wait and not self.has_recv_message:
            await self.await_config(wait_period)

        return self._do_get_config(key_filter)


class app_manager:

    def __init__(
        self,
        loop_obj=None,
        device_agent=None,
        platform_iface=None,
        modbus_iface=None,
        camera_iface=None,
        tunnel_iface: TunnelInterface = None
    ):
        self.loop_obj = loop_obj
        self.device_agent = device_agent
        self.platform_iface = platform_iface
        self.modbus_iface = modbus_iface
        self.camera_iface = camera_iface
        self.tunnel_iface = tunnel_iface

        self.restart_all_on_error = True
        self.error_wait_period = 10
        self.should_stop = False
        self.setup_functions = []
        self.loop_functions = []

        if self.loop_obj is None:
            self.create_loop()
        if self.device_agent is None:
            self.device_agent = DeviceAgentInterface()

        self.config_manager = deployment_config_manager(dda_iface=self.device_agent)

        if self.platform_iface is None:
            self.platform_iface = platform_iface()


    def register_loop(self, callable):
        self.loop_functions.append(callable)

    def register_setup_function(self, callable):
        self.setup_functions.append(callable)


    async def main_loop(self):

        ## ensure config is recieved before starting
        await self.config_manager.await_config()

        ## trigger modbus iface setup
        self.modbus_iface.set_config_manager(self.config_manager)
        await self.modbus_iface.setup_from_config_manager()

        while not self.should_stop:
            restart_loop = False

            for setup in self.setup_functions:
                try:
                    await call_maybe_async(setup)
                except Exception as e:
                    logging.error("Error in setup function: " + str(e))
                    # logging.error("Setup: " + str(setup))
                    logging.error(traceback.format_exc())
                    if self.restart_all_on_error:
                        logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before closing app\n\n")
                    else:
                        logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before restarting app\n\n")
                    await asyncio.sleep(self.error_wait_period)
                    
                    restart_loop = True
                    break

            ## allow for other async tasks to run between setup and loop
            await asyncio.sleep(0.2)

            while not self.should_stop and not restart_loop:
                for loop in self.loop_functions:
                    try:
                        await call_maybe_async(loop)
                    except Exception as e:
                        logging.error("Error in loop function: " + str(e))
                        # logging.error("Loop: " + str(loop))
                        logging.error(traceback.format_exc())
                        if self.restart_all_on_error:
                            logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before closing app\n\n")
                        else:
                            logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before restarting app\n\n")
                        await asyncio.sleep(self.error_wait_period)

                        restart_loop = True
                        break

                ## Allow for other async tasks to run
                await asyncio.sleep(0.2)

            if self.restart_all_on_error:
                self.close()
                return

    def start_task(self, function):
        logging.warning("app_manager.start_task is deprecated. Use an async task instead!")
        thread = threading.Thread(target=asyncio.run, args=(function(), ))
        thread.start()
        return thread

    def create_loop(self):
        if self.loop_obj is None:
            self.loop_obj = asyncio.get_event_loop()
            
            self.loop_obj.add_signal_handler(signal.SIGINT, self.close)
            self.loop_obj.add_signal_handler(signal.SIGTERM, self.close)

            asyncio.set_event_loop(self.loop_obj)

    def get_loop(self):
        return self.loop_obj
    
    def get_agent_iface(self):
        return self.device_agent

    def get_config_manager(self):
        return self.config_manager

    @maybe_async()
    def get_config(self, key_filter: str, wait: bool = True):
        return self.config_manager.get_config(key_filter=key_filter, wait=wait)

    async def get_config_async(self, key_filter: str, wait: bool = True):
        return await self.config_manager.get_config_async(key_filter=key_filter, wait=wait)

    def get_platform_iface(self):
        return self.platform_iface
    
    def get_modbus_iface(self):
        return self.modbus_iface
    
    def get_camera_iface(self):
        return self.camera_iface

    async def run(self):
        try:
            await self.main_loop()
        except asyncio.CancelledError:
            logging.info("Main loop cancelled")
        except Exception as e:
            logging.error("Error in main loop: " + str(e))
            logging.error(traceback.format_exc())

    def close(self):
        if not self.should_stop:
            logging.info("\n########################################\n\nClosing app manager...\n\n########################################\n")
            self.should_stop = True
            if self.device_agent is not None:
                self.device_agent.close()

            if self.platform_iface is not None:
                self.platform_iface.close()

            def stop_loop():
                loop_obj = asyncio.get_event_loop()
                tasks = asyncio.all_tasks(loop_obj)
                for task in tasks:
                    task.cancel()
                # loop_obj.stop()

            self.loop_obj.call_soon_threadsafe(stop_loop)


async def main(app, dda_iface=None, plt_iface=None, mb_iface=None, cam_iface=None, tunnel_iface: TunnelInterface = None, debug=False):
    parser = argparse.ArgumentParser(description='Doover Docker App Manager')

    parser.add_argument('--remote-dev', type=str, default=None, help='Remote device URI')
    parser.add_argument('--dda-uri', type=str, default="localhost:50051", help='Doover Device Agent URI')
    parser.add_argument('--plt-uri', type=str, default="localhost:50053", help='Platform Interface URI')
    parser.add_argument('--modbus-uri', type=str, default="localhost:50054", help='Modbus Interface URI')
    parser.add_argument('--cam-uri', type=str, default="localhost:50055", help='Camera Interface URI')
    parser.add_argument('--tunnel-uri', type=str, default="localhost:50056", help='Tunnel Interface URI')
    parser.add_argument('--dds-sys-sock', type=str, default="/var/lib/dds/dds_sys.sock", help='DDS System Socket File Path')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug Mode')

    args = parser.parse_args()

    if args.debug or debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(app_manager_logging_formatter())
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)

    dda_uri = args.dda_uri
    plt_uri = args.plt_uri
    modbus_uri = args.modbus_uri
    cam_uri = args.cam_uri
    tunnel_uri = args.tunnel_uri

    user_is_async = asyncio.iscoroutinefunction(app.setup) or asyncio.iscoroutinefunction(app.main_loop)
    app._is_async = get_is_async(user_is_async)

    if args.remote_dev is not None:
        dda_uri = args.dda_uri.replace("localhost", args.remote_dev)
        plt_uri = args.plt_uri.replace("localhost", args.remote_dev)
        modbus_uri = args.modbus_uri.replace("localhost", args.remote_dev)
        cam_uri = args.cam_uri.replace("localhost", args.remote_dev)
        tunnel_uri = args.tunnel_uri.replace("localhost", args.remote_dev)

    if dda_iface is None:
        dda_iface = device_agent_iface(dda_uri, user_is_async)

    if plt_iface is None:
        plt_iface = PlatformInterface(plt_uri, user_is_async)

    if mb_iface is None:
        mb_iface = ModbusInterface(modbus_uri, user_is_async)

    if cam_iface is None:
        cam_iface = CameraInterface(cam_uri, user_is_async)

    if tunnel_iface is None:
        tunnel_iface = TunnelInterface(tunnel_uri, user_is_async)

    app_manager_obj = app_manager(
        device_agent=dda_iface,
        platform_iface=plt_iface,
        modbus_iface=mb_iface,
        camera_iface=cam_iface,
        tunnel_iface=tunnel_iface,
    )
    app.set_manager(app_manager_obj)

    # register internal varients of setup and main_loop to stop possibility of user overriding them.
    # if they try hard enough they can override them but the average Joe shouldn't be...

    # this also allows us to raise an error if they haven't implemented either.
    app_manager_obj.register_setup_function(app._setup)
    app_manager_obj.register_loop(app._main_loop)

    app_manager_obj.register_setup_function(app.setup)
    app_manager_obj.register_loop(app.main_loop)

    await app_manager_obj.run()


def run_app(app, *args, **kwargs):
    asyncio.run(main(app, *args, **kwargs))


if __name__ == "__main__":

    run_app(app_base())