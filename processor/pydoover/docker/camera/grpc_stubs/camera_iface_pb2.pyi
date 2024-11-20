from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamSettings(_message.Message):
    __slots__ = ("fps", "scale")
    FPS_FIELD_NUMBER: _ClassVar[int]
    SCALE_FIELD_NUMBER: _ClassVar[int]
    fps: int
    scale: str
    def __init__(self, fps: _Optional[int] = ..., scale: _Optional[str] = ...) -> None: ...

class ResponseHeader(_message.Message):
    __slots__ = ("success", "response_code", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    response_code: int
    message: str
    def __init__(self, success: bool = ..., response_code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class TestCommsRequest(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class TestCommsResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class SnapshotRequest(_message.Message):
    __slots__ = ("rtsp_uri", "snapshot_type", "snapshot_length", "output_channel", "camera_name", "stream_settings")
    RTSP_URI_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_LENGTH_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    CAMERA_NAME_FIELD_NUMBER: _ClassVar[int]
    STREAM_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    rtsp_uri: str
    snapshot_type: str
    snapshot_length: int
    output_channel: str
    camera_name: str
    stream_settings: StreamSettings
    def __init__(self, rtsp_uri: _Optional[str] = ..., snapshot_type: _Optional[str] = ..., snapshot_length: _Optional[int] = ..., output_channel: _Optional[str] = ..., camera_name: _Optional[str] = ..., stream_settings: _Optional[_Union[StreamSettings, _Mapping]] = ...) -> None: ...

class SnapshotResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class IsSnapshotRunningRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class IsSnapshotRunningResponse(_message.Message):
    __slots__ = ("response_header", "is_running")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    IS_RUNNING_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    is_running: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., is_running: bool = ...) -> None: ...
