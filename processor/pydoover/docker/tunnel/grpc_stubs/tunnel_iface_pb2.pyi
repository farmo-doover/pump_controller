from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

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

class TunnelRequest(_message.Message):
    __slots__ = ("address", "protocol", "timeout", "username", "password", "domain", "remote_addr", "allow_cidrs")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    REMOTE_ADDR_FIELD_NUMBER: _ClassVar[int]
    ALLOW_CIDRS_FIELD_NUMBER: _ClassVar[int]
    address: str
    protocol: str
    timeout: int
    username: str
    password: str
    domain: str
    remote_addr: str
    allow_cidrs: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, address: _Optional[str] = ..., protocol: _Optional[str] = ..., timeout: _Optional[int] = ..., username: _Optional[str] = ..., password: _Optional[str] = ..., domain: _Optional[str] = ..., remote_addr: _Optional[str] = ..., allow_cidrs: _Optional[_Iterable[str]] = ...) -> None: ...

class TunnelResponse(_message.Message):
    __slots__ = ("address", "url")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    address: str
    url: str
    def __init__(self, address: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class OpenTunnelRequest(_message.Message):
    __slots__ = ("tunnel",)
    TUNNEL_FIELD_NUMBER: _ClassVar[int]
    tunnel: TunnelRequest
    def __init__(self, tunnel: _Optional[_Union[TunnelRequest, _Mapping]] = ...) -> None: ...

class CloseTunnelRequest(_message.Message):
    __slots__ = ("address", "url")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    address: str
    url: str
    def __init__(self, address: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class CloseAllTunnelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetTunnelRequest(_message.Message):
    __slots__ = ("address", "url")
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    address: str
    url: str
    def __init__(self, address: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class ListTunnelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OpenTunnelResponse(_message.Message):
    __slots__ = ("response_header", "success", "url")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    success: bool
    url: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., success: bool = ..., url: _Optional[str] = ...) -> None: ...

class CloseTunnelResponse(_message.Message):
    __slots__ = ("response_header", "success")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    success: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., success: bool = ...) -> None: ...

class CloseAllTunnelsResponse(_message.Message):
    __slots__ = ("response_header", "success")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    success: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., success: bool = ...) -> None: ...

class GetTunnelResponse(_message.Message):
    __slots__ = ("response_header", "tunnel")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    tunnel: TunnelResponse
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., tunnel: _Optional[_Union[TunnelResponse, _Mapping]] = ...) -> None: ...

class ListTunnelsResponse(_message.Message):
    __slots__ = ("response_header", "tunnels")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    TUNNELS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    tunnels: _containers.RepeatedCompositeFieldContainer[TunnelResponse]
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., tunnels: _Optional[_Iterable[_Union[TunnelResponse, _Mapping]]] = ...) -> None: ...

class SyncTunnelsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SyncTunnelsResponse(_message.Message):
    __slots__ = ("response_header", "success")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    success: bool
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., success: bool = ...) -> None: ...
