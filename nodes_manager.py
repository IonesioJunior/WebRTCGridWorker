from webrtc_connections import WebRTCConnection
from syft.workers.base import BaseWorker


class WebRTCManager(BaseWorker):
    def __init__(self, grid_descriptor, syft_worker):
        self._connections = {}
        self._grid = grid_descriptor
        self.worker = syft_worker

    @property
    def nodes(self):
        return list(self._connections.keys())

    def _recv_msg(self, message):
        raise NotImplementedError

    def _send_msg(self, message: bin, location):
        return asyncio.run(self._connection[location.id].send(message))

    def get(self, node_id: str):
        return self._connections.get(node_id, None)

    def process_answer(self, destination: str, content: str):
        self._connections[destination].set_msg(content)

    def process_offer(self, destination: str, content: str):
        self._connections[destination] = WebRTCConnection(
            self._grid, self.worker, destination, WebRTCConnection.ANSWER
        )
        self._connections[destination].set_msg(content)
        self._connections[destination].start()

    def start_offer(self, destination: str):
        self._connections[destination] = WebRTCConnection(
            self._grid, self.worker, destination, WebRTCConnection.OFFER
        )
        self._connections[destination].start()
