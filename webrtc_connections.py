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
import syft as sy
import torch as th
import time
from syft.workers.base import BaseWorker

hook = sy.TorchHook(th)


class WebRTCConnection(threading.Thread, BaseWorker):

    OFFER = 1
    ANSWER = 2

    def __init__(self, grid_descriptor, worker, destination, conn_type):
        threading.Thread.__init__(self)
        BaseWorker.__init__(self, hook=hook, id=destination)
        self._conn_type = conn_type
        self._origin = worker.id
        self._worker = worker
        self._destination = destination
        self._grid = grid_descriptor
        self._msg = ""
        self._request_pool = queue.Queue()
        self._response_pool = queue.Queue()
        self.channel = None

    # Add a new operation on request_pool
    async def _send_msg(self, message, location=None):
        self._request_pool.put(b"01" + message)
        while self._response_pool.empty():
            await asyncio.sleep(0)
        return self._response_pool.get()

    # Client side
    # Called when someone call syft function locally eg. tensor.send(node)
    def _recv_msg(self, message):
        """ Quando recebe algo local e quer mandar para o worker remoto.
            Necessário retorno após envio.
        """
        return asyncio.run(self._send_msg(message))

    # Running async all time
    async def send(self, channel):
        while True:
            if not self._request_pool.empty():
                channel.send(self._request_pool.get())
            await asyncio.sleep(0)

    # Running async all time
    def process_msg(self, message, channel):
        if message[:2] == b"01":
            decoded_response = self._worker._recv_msg(message[2:])
            channel.send(b"02" + decoded_response)
        else:
            self._response_pool.put(message[2:])

    # Main
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

    # SERVER
    async def _set_offer(self, pc, signaling):
        await signaling.connect()
        channel = pc.createDataChannel("chat")

        self.channel = channel

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(self.send(channel))

        @channel.on("message")
        def on_message(message):
            self.process_msg(message, channel)

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

    # CLIENT
    async def _run_answer(self, pc, signaling):
        await signaling.connect()

        @pc.on("datachannel")
        def on_datachannel(channel):
            asyncio.ensure_future(self.send(channel))

            self.channel = channel

            @channel.on("message")
            def on_message(message):
                self.process_msg(message, channel)

        await self.consume_signaling(pc, signaling)

    async def consume_signaling(self, pc, signaling):
        while True:
            if self._msg == "":
                await asyncio.sleep(0)
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

    def set_msg(self, content: str):
        self._msg = content
