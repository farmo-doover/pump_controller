from .grpc_stubs import camera_iface_pb2, camera_iface_pb2_grpc
from ..grpc_interface import GRPCInterface
from ...utils import maybe_async


class CameraInterface(GRPCInterface):
    stub = camera_iface_pb2_grpc.cameraIfaceStub

    def __init__(self, camera_iface_uri: str = "127.0.0.1:50055", is_async: bool = None):
        super().__init__(camera_iface_uri, is_async)

    @maybe_async()
    def get_camera_snapshot(self, camera_uri, channel_name, snapshot_type='mp4', snapshot_length: int = 6):
        req = camera_iface_pb2.SnapshotRequest(
            rtsp_uri=camera_uri,
            snapshot_type=snapshot_type,
            snapshot_length=int(snapshot_length),
            output_channel=channel_name,
        )
        return self.make_request("RunSnapshot", req)

    async def get_camera_snapshot_async(self, camera_uri, channel_name, snapshot_type='mp4', snapshot_length: int = 6):
        req = camera_iface_pb2.SnapshotRequest(
            rtsp_uri=camera_uri,
            snapshot_type=snapshot_type,
            snapshot_length=int(snapshot_length),
            output_channel=channel_name,
        )
        return await self.make_request_async("RunSnapshot", req)

    @maybe_async()
    def is_snapshot_running(self):
        resp = self.make_request("IsSnapshotRunning", camera_iface_pb2.IsSnapshotRunningRequest())
        return resp and resp.is_running

    async def is_snapshot_running_async(self):
        resp = await self.make_request_async("IsSnapshotRunning", camera_iface_pb2.IsSnapshotRunningRequest())
        return resp and resp.is_running


camera_iface = CameraInterface
