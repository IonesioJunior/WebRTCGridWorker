import threading
import websocket
import json
from codes import NODE_EVENTS, GRID_EVENTS, MSG_FIELD
from nodes_manager import WebRTCManager
from grid_routes import (
    _monitor,
    _create_webrtc_scope,
    _accept_offer,
    _process_webrtc_answer,
)

import syft as sy
import torch as th
import time


class GridNetwork(threading.Thread):

    EVENTS = {
        NODE_EVENTS.MONITOR: _monitor,
        NODE_EVENTS.WEBRTC_SCOPE: _create_webrtc_scope,
        NODE_EVENTS.WEBRTC_OFFER: _accept_offer,
        NODE_EVENTS.WEBRTC_ANSWER: _process_webrtc_answer,
    }

    def __init__(self, node_id: str, **kwargs):
        threading.Thread.__init__(self)
        self._connect(**kwargs)
        self._worker = self._update_node_infos(node_id)
        self._worker.models = {}
        self._connection_handler = WebRTCManager(self._ws, self._worker)

    def run(self):
        # Join
        self._join()

        # Listen
        self._listen()

    def _update_node_infos(self, node_id: str):
        sy.local_worker.id = node_id
        sy.local_worker._known_workers[node_id] = sy.local_worker
        del sy.local_worker._known_workers["me"]
        sy.local_worker.is_client_worker = False
        return sy.local_worker

    def _listen(self):
        while True:
            message = self._ws.recv()
            msg = json.loads(message)
            response = self._handle_messages(msg)
            if response:
                self._ws.send(json.dumps(response))

    def _handle_messages(self, message):
        msg_type = message.get(MSG_FIELD.TYPE, None)
        if msg_type in GridNetwork.EVENTS:
            return GridNetwork.EVENTS[msg_type](message, self._connection_handler)

    def _send(self, message: dict):
        self._ws.send(json.dumps(message))
        return json.loads(self._ws.recv())

    def _connect(self, **kwargs):
        self._ws = websocket.create_connection(**kwargs)

    @property
    def id(self):
        return self._worker.id

    def connect(self, destination_id: str):
        webrtc_request = {
            MSG_FIELD.TYPE: NODE_EVENTS.WEBRTC_SCOPE,
            MSG_FIELD.FROM: self.id,
        }

        forward_payload = {
            MSG_FIELD.TYPE: GRID_EVENTS.FORWARD,
            MSG_FIELD.DESTINATION: destination_id,
            MSG_FIELD.CONTENT: webrtc_request,
        }

        self._ws.send(json.dumps(forward_payload))
        while not self._connection_handler.get(destination_id):
            time.sleep(1)

        return self._connection_handler.get(destination_id)

    def host_dataset(self, dataset, access="plain-text", privacy="private"):
        dataset.access = access
        dataset.privacy = privacy
        return dataset.send(self._worker)

    def host_model(self, model):
        model.nodes.append(self._worker.id)
        self._worker.models[model.id] = model
        return model._model

    def _join(self):
        # Join into the network
        join_payload = {
            MSG_FIELD.TYPE: GRID_EVENTS.JOIN,
            MSG_FIELD.NODE_ID: self._worker.id,
        }
        self._ws.send(json.dumps(join_payload))
        response = json.loads(self._ws.recv())
        return response
