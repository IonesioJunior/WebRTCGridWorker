import asyncio
import json

from codes import MSG_FIELD, GRID_EVENTS, NODE_EVENTS
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import (
    BYE,
    CopyAndPasteSignaling,
    object_to_string,
    object_from_string,
)
import threading
import queue


class WebRTCConnection(threading.Thread):

    OFFER = 1
    ANSWER = 2

    def __init__(self, grid_descriptor, syft_worker, destination, conn_type):
        threading.Thread.__init__(self)
        self._conn_type = conn_type
        self._origin = syft_worker.id
        self._destination = destination
        self._grid = grid_descriptor
        self._msg = ""
        self.worker = syft_worker
        self._request_pool = queue.Queue()
        self._response_pool = queue.Queue()

    def send(self, message: str):
        self._request_pool.put(message)

    def run(self):
        signaling = CopyAndPasteSignaling()
        pc = RTCPeerConnection()

        if self._conn_type == WebRTCConnection.OFFER:
            func = self._set_offer
        else:
            func = self._run_answer

        try:
            asyncio.run(func(pc, signaling))
        except KeyboardInterrupt:
            pass
        finally:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(pc.close())
            loop.run_until_complete(signaling.close())

    async def consume_signaling(self, pc, signaling):
        while True:
            if self._msg == "":
                await asyncio.sleep(1)
                continue

            obj = object_from_string(self._msg)

            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)

                if obj.type == "offer":
                    # send answer
                    await pc.setLocalDescription(await pc.createAnswer())
                    local_description = object_to_string(pc.localDescription)

                    response = {
                        MSG_FIELD.TYPE: NODE_EVENTS.WEBRTC_ANSWER,
                        MSG_FIELD.FROM: self._origin,
                        MSG_FIELD.PAYLOAD: local_description,
                    }

                    forward_payload = {
                        MSG_FIELD.TYPE: GRID_EVENTS.FORWARD,
                        MSG_FIELD.DESTINATION: self._destination,
                        MSG_FIELD.CONTENT: response,
                    }
                    self._grid.send(json.dumps(forward_payload))
            elif isinstance(obj, RTCIceCandidate):
                pc.addIceCandidate(obj)
            elif obj is BYE:
                print("Exiting")
                break
            self._msg = ""

    async def _set_offer(self, pc, signaling):
        await signaling.connect()
        channel = pc.createDataChannel("chat")

        async def send_pings():
            while True:
                if not self._request_pool.empty():
                    channel.send(self._request_pool.get())
                await asyncio.sleep(0)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            print(
                "[ "
                + self._origin
                + " ]  Receiving msg <"
                + self._destination
                + "> "
                + message
            )

        await pc.setLocalDescription(await pc.createOffer())
        local_description = object_to_string(pc.localDescription)

        response = {
            MSG_FIELD.TYPE: NODE_EVENTS.WEBRTC_OFFER,
            MSG_FIELD.PAYLOAD: local_description,
            MSG_FIELD.FROM: self._origin,
        }

        forward_payload = {
            MSG_FIELD.TYPE: GRID_EVENTS.FORWARD,
            MSG_FIELD.DESTINATION: self._destination,
            MSG_FIELD.CONTENT: response,
        }

        self._grid.send(json.dumps(forward_payload))
        await self.consume_signaling(pc, signaling)

    async def _run_answer(self, pc, signaling):
        await signaling.connect()

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                if not self._request_pool.empty():
                    channel.send(self._request_pool.get())
                print(
                    "[ "
                    + self._origin
                    + " ]  Receiving msg <"
                    + self._destination
                    + "> "
                    + message
                )

        await self.consume_signaling(pc, signaling)

    def set_msg(self, content: str):
        self._msg = content
