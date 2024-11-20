import logging

from collections import namedtuple
from typing import Optional

from .grpc_stubs import tunnel_iface_pb2 as stubs, tunnel_iface_pb2_grpc as grpc_stubs
from ..grpc_interface import GRPCInterface
from ...utils import maybe_async

log = logging.getLogger(__name__)
Tunnel = namedtuple("Tunnel", ["address", "url"])


class TunnelInterface(GRPCInterface):
    stub = grpc_stubs.TunnelInterfaceStub

    def __init__(self, tunnel_uri: str = "127.0.0.1:50056", is_async: bool = None):
        super().__init__(tunnel_uri, is_async)

    def process_response(self, stub_call: str, response, *args, **kwargs):
        response = super().process_response(stub_call, response, *args, **kwargs)

        try:
            check_success = kwargs.pop("check_success")
        except KeyError:
            return response

        if check_success and not response.success:
            log.warning(f"Failed to execute {stub_call}. Process returned success failed. {response.message}")
            return None

        return response


    @maybe_async()
    def open_tunnel(
        self,
        address: str,
        protocol: str = "http",
        timeout: int = 15,
        username: str = None,
        password: str = None,
        domain: str = None,
    ) -> Optional[str]:
        """Open a tunnel with the given address and protocol.

        Returns the tunnel URL if opening the tunnel succeeded, None otherwise.
        """
        req = stubs.OpenTunnelRequest(tunnel=stubs.TunnelRequest(
            address=address,
            protocol=protocol,
            timeout=timeout,
            username=username,
            password=password,
            domain=domain,
        ))
        resp = self.make_request("OpenTunnel", req)
        return resp and resp.url

    async def open_tunnel_async(
        self,
        address: str,
        protocol: str = "http",
        timeout: int = 15,
        username: str = None,
        password: str = None,
        domain: str = None,
    ) -> Optional[str]:
        req = stubs.OpenTunnelRequest(tunnel=stubs.TunnelRequest(
            address=address,
            protocol=protocol,
            timeout=timeout,
            username=username,
            password=password,
            domain=domain,
        ))
        resp = await self.make_request_async("OpenTunnel", req)
        return resp and resp.url

    @maybe_async()
    def close_tunnel(self, address: str = None, url: str = None) -> bool:
        """Close tunnel by either address (ie. localhost:5000) or url (ie. https://random.ngrok.io)"""
        if not (address or url):
            raise ValueError("Address or URL required")

        req = stubs.CloseTunnelRequest(address=address, url=url)
        return self.make_request("CloseTunnel", req, check_success=True)

    async def close_tunnel_async(self, address: str = None, url: str = None) -> bool:
        if not (address or url):
            raise ValueError("Address or URL required")

        req = stubs.CloseTunnelRequest(address=address, url=url)
        return await self.make_request_async("CloseTunnel", req, check_success=True)

    @maybe_async()
    def close_all_tunnels(self) -> bool:
        """Close all open tunnels. Returns True if this succeeded, False otherwise."""
        return self.make_request("CloseAllTunnels", stubs.CloseTunnelRequest(), check_success=True)

    async def close_all_tunnels_async(self) -> bool:
        """Close all open tunnels. Returns True if this succeeded, False otherwise."""
        return await self.make_request_async("CloseAllTunnels", stubs.CloseTunnelRequest(), check_success=True)

    @maybe_async()
    def get_tunnel(self, address: str = None, url: str = None) -> Optional[Tunnel]:
        """Get tunnel by either address (ie. localhost:5000) or url (ie. https://random.ngrok.io)

        Returns a namedtuple with address and url attributes.
        """
        if not (address or url):
            raise ValueError("Address or URL required")

        resp = self.make_request("GetTunnel", stubs.GetTunnelRequest(address=address, url=url))
        return resp and Tunnel(resp.tunnel.address, resp.tunnel.url)

    async def get_tunnel_async(self, address: str = None, url: str = None) -> Optional[Tunnel]:
        if not (address or url):
            raise ValueError("Address or URL required")

        resp = await self.make_request_async("GetTunnel", stubs.GetTunnelRequest(address=address, url=url))
        return resp and Tunnel(resp.tunnel.address, resp.tunnel.url)

    @maybe_async()
    def get_all_tunnels(self) -> Optional[list[Tunnel]]:
        """Get all open tunnels. Returns a list of Tunnels with address and url attributes."""
        resp = self.make_request("ListTunnels", stubs.ListTunnelsRequest())
        return resp and [Tunnel(r.address, r.url) for r in resp.tunnels]

    async def get_all_tunnels_async(self) -> Optional[list[Tunnel]]:
        resp = await self.make_request_async("ListTunnels", stubs.ListTunnelsRequest())
        return resp and [Tunnel(r.address, r.url) for r in resp.tunnels]
