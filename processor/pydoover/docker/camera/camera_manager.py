import asyncio
import logging
import time
import typing

from .camera import CameraInterface
from ...ui import Camera as UICamera, SlimCommand

if typing.TYPE_CHECKING:
    from ...utils import CaseInsensitiveDict


class Camera:
    def __init__(self, config: "CaseInsensitiveDict[str, str]"):
        self.config = config

        self.name = config.get("name", "camera").lower().replace(' ', '_')
        self.display_name = config.get("display_name") or self.name
        self.uri = config.get("uri")
        self.mode = config.get("mode", "mp4")
        self.snapshot_secs = config.get("snapshot_secs", 6)
        self.wake_delay = config.get("wake_delay", 10)


    def __eq__(self, other):
        return other is not None and isinstance(other, self.__class__) and self.config == other.config

    async def trigger_snapshot(self, cam_iface: "CameraInterface"):
        return await cam_iface.get_camera_snapshot_async(self.uri, self.name, self.mode, self.snapshot_secs)


## CONFIG WILL LOOK LIKE THE FOLLOWING
#
# {
#     "camera_config": {
#         "power_pin" : 1,
#         "cameras": {
#             "cam_1" : {
#                 "name": "cam_1",
#                 "display_name": "Camera 1",
#                 "uri": "rtsp://192.168.50.120:544",
#                 "mode": "mp4",
#                 "snapshot_secs": 6
#             },
#             "cam_2" : {

#             }
#         }
#     }
# }


class CameraManager:
    def __init__(self,
                camera_config=None,
                config_manager=None,
                dda_iface=None,
                ui_manager=None,
                plt_iface=None,
                app_manager=None,
                is_active=True,
            ):
        self.camera_config = camera_config
        self.config_manager = config_manager
        self.dda_iface = dda_iface
        self.ui_manager = ui_manager
        self.plt_iface = plt_iface
        self.app_manager = app_manager

        self._is_active = is_active

        self.last_camera_snapshot = time.time()
        self.iter_counter = 0
        self.snapshot_task = None

        self.camera_snap_cmd_name = "camera_snapshots"
        self.last_snapshot_cmd_name = "last_cam_snapshot"

        self.cameras: list[Camera] = []

    async def load_camera_config(self):
        if self.config_manager is not None:
            self.camera_config = await self.config_manager.get_config_async("camera_config")

    def load_cameras(self):
        try:
            if not self.camera_config:
                logging.warning("No cameras found in config")
                return
            self.cameras = [Camera(cam_config) for cam_config in self.camera_config["CAMERAS"].values()]
        except (KeyError, AttributeError):
            logging.warning("Unable to parse cameras from config")

    @property
    def is_active(self):
        return self._is_active and self.camera_config is not None

    def get_is_active(self):
        return self.is_active

    def get_camera_snapshot_period(self):
        if not self.is_active:
            return None

        try:
            return self.camera_config["SNAPSHOT_PERIOD"]
        except KeyError:
            logging.warning("Unable to parse camera snapshot period from config")
        return None

    def fetch_ui_elements(self):
        if not self.is_active:
            return []

        return [UICamera(c.name, c.display_name, c.uri) for c in self.cameras]

    def update_ui_elements(self):
        pass

    async def setup(self):
        await self.load_camera_config()
        self.load_cameras()

        self.ui_manager.add_children(*self.fetch_ui_elements())
        self.ui_manager._add_interaction(SlimCommand(self.camera_snap_cmd_name, callback=self.on_snapshot_command))

    async def main_loop(self):
        self.iter_counter += 1
        if self.iter_counter > 999999999:
            self.iter_counter = 0

        if self.iter_counter % 10 == 0: ## Only check if cameras overdue on every 10th cycle
            self.assess_snapshot_due()

    def assess_snapshot_due(self):
        if not self.get_is_active():
            return False
        if self.snapshot_task is not None:
            return False ## Snapshot currently running
        snap_period = self.get_camera_snapshot_period()
        if snap_period is None:
            return False
        if time.time() - self.last_camera_snapshot > snap_period:
            self.trigger_all_snapshots()
            return True
        return False

    async def on_snapshot_command(self, new_value: str):
        if new_value != "get_immediate_snapshot":
            return

        self.ui_manager.coerce_command(self.camera_snap_cmd_name, None)
        if self.snapshot_task is None:
            self.trigger_all_snapshots()

    def set_last_snapshot_time(self, ts=None):
        ts = ts or time.time()

        self.last_camera_snapshot = ts
        self.ui_manager.coerce_command(self.last_snapshot_cmd_name, ts)

    def trigger_all_snapshots(self):
        if self.snapshot_task is not None:
            logging.info("Skipping trigger snapshot request, snapshot task already running")
            return

        self.set_last_snapshot_time()
        self.snapshot_task = asyncio.create_task(self.run_all_snapshots_task())
        self.snapshot_task.add_done_callback(self._on_snapshot_done)

    def _on_snapshot_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            exc = None

        if exc:
            logging.error(f"Snapshot task failed: {exc}", exc_info=exc)

        self.snapshot_task = None

    async def run_all_snapshots_task(self):
        if len(self.cameras) < 1:
            logging.warning("No cameras found for snapshot task.")
            return

        for c in self.cameras:
            await c.trigger_snapshot(self.app_manager.get_camera_iface())

        logging.info("Camera take all snapshots complete")

    async def is_snapshot_running(self):
        return await self.app_manager.get_camera_iface().is_snapshot_running_async()


camera_manager = CameraManager
camera = Camera