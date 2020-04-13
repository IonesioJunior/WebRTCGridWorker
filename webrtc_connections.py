import asyncio
import json

from codes import MSG_FIELD, GRID_EVENTS,NODE_EVENTS
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import (
    BYE,
    CopyAndPasteSignaling,
    object_to_string,
    object_from_string,
)
import threading


class WebRTCConnection(threading.Thread):

    OFFER = 1
    ANSWER = 2

    def __init__(self, grid_descriptor, origin, destination, conn_type):
        threading.Thread.__init__(self)
        self._conn_type = conn_type
        self._origin = origin
        self._destination = destination
        self._grid = grid_descriptor
        self._msg = ""

    def run(self):
        signaling = CopyAndPasteSignaling()
        pc = RTCPeerConnection()

        if self._conn_type == WebRTCConnection.OFFER:
            # coro = self._set_offer(pc, signaling)
            #asyncio.run(self._set_offer(pc, signaling))
            func = self._set_offer
        else:
            # coro = self._run_answer(pc, signaling)
            #asyncio.run(self._run_answer(pc, signaling))
            func = self._run_answer
       

        try:
            asyncio.run(func(pc,signaling))
        except KeyboardInterrupt:
            pass
        finally:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(pc.close())
            loop.run_until_complete(signaling.close())

        #async def send_pings(self, pc, signaling):
        #print("I'm here")
        #while True:
        #    channel.send( "[ " + self._origin + " ]  Hello World!")
        #    await asyncio.sleep(1)

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
                print("Channel state: ", channel.transport.state)
                print("Sending ping ...")
                channel.send("ping")
                await asyncio.sleep(1)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            print("[ " + self._origin + " ]  Receiving msg from " + self._destination)

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
                print("[ " + self._origin + "] Replying message")
                channel.send("pong")

        await self.consume_signaling(pc, signaling)

    def set_msg(self, content: str):
        self._msg = content


class WebRTCManager:
    def __init__(self, grid_descriptor, node_id):
        self._connections = {}
        self._grid = grid_descriptor
        self._id = node_id
        self._msg = ""

    @property
    def nodes(self):
        return list(self._connections.keys())

    def process_answer(self, destination: str, content: str):
        self._connections[destination].set_msg(content)

    def process_offer(self, destination: str, content: str):
        self._connections[destination] = WebRTCConnection(
            self._grid, self._id, destination, WebRTCConnection.ANSWER
        )
        self._connections[destination].set_msg(content)
        self._connections[destination].start()

    def start_offer(self, destination: str):
        self._connections[destination] = WebRTCConnection(
            self._grid, self._id, destination, WebRTCConnection.OFFER
        )
        self._connections[destination].start()
