import asyncio
import json
import logging
import time

from typing import Optional, Any

DEFAULT_WAKE_DELAY = 5


class SnapshotInProgress(Exception):
    def __init__(self):
        super().__init__("There is already a snapshot in progress for this camera.")


class PowerContext:
    def __init__(self, camera_rtsp: str, manager: "CameraPowerManagement"):
        self.camera = camera_rtsp
        self.manager = manager

    async def __aenter__(self):
        if not self.manager.plt_iface:
            # early exit if we don't define the platform interface (testing, etc.)
            return

        await self.manager.power_on()
        if not self.manager.is_powered:
            return  # something went wrong with trying to turn the power on...

        wake_delay = await self.manager.get_wake_delay(self.camera)
        to_sleep = wake_delay - (time.time() - self.manager.start_powered)
        if to_sleep > 0:
            await asyncio.sleep(to_sleep)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.manager.handle_cam_done(self.camera)


class CameraPowerManagement:
    def __init__(self, plt_iface=None, config_manager=None, default_config=None):
        self.plt_iface = plt_iface
        self.config_manager = config_manager
        self.default_config = default_config

        self.is_powered: bool = False
        self.start_powered = None

        self.active_cameras = set()

    async def get_config(self) -> Optional[dict[str, Any]]:
        if not self.config_manager and not self.default_config:
            logging.warning("No config_manager or default_config supplied.")
            return
        elif not self.config_manager:
            config = self.default_config
        else:
            config = await self.config_manager.get_config_async('camera_config')

        if not config:
            logging.warning("No camera config found.")
            return

        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                logging.warning("Unable to parse camera config as valid JSON from config manager")
                return config  # might still be a valid string?

        return config

    async def get_power_pin(self) -> Optional[int]:
        config = await self.get_config()
        if not config:
            return

        try:
            return config['POWER_PIN']
        except KeyError:
            logging.warning("Unable to parse camera power pin from config")

        return None

    async def get_wake_delay(self, rtsp_uri) -> Optional[int]:
        config = await self.get_config()
        if not config:
            return DEFAULT_WAKE_DELAY

        try:
            return [c["WAKE_DELAY"] for c in config["CAMERAS"].values() if c["URI"] == rtsp_uri][0]
        except (TypeError, KeyError, IndexError):
            return DEFAULT_WAKE_DELAY

    async def power_on(self):
        if self.is_powered:
            return

        pin = await self.get_power_pin()
        if pin is None:
            return

        logging.info("Powering cameras on")
        # todo: add awaits when asyncify platform iface
        self.plt_iface.set_do(pin, True)
        self.is_powered = True
        self.start_powered = time.time()

    async def power_off(self):
        if not self.is_powered:
            return

        pin = await self.get_power_pin()
        if pin is None:
            return

        logging.info("Powering cameras off")
        self.plt_iface.set_do(pin, False)
        self.is_powered = False
        self.start_powered = None

    async def handle_cam_done(self, camera_to_handle: str):
        self.active_cameras.remove(camera_to_handle)

        if len(self.active_cameras) == 0:
            await self.power_off()

    def acquire(self, camera_to_manage: str):
        if camera_to_manage in self.active_cameras:
            raise SnapshotInProgress()

        self.active_cameras.add(camera_to_manage)
        return PowerContext(camera_to_manage, self)
