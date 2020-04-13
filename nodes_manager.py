from webrtc_connections import WebRTCConnection


class WebRTCManager:
    def __init__(self, grid_descriptor, syft_worker):
        self._connections = {}
        self._grid = grid_descriptor
        self.worker = syft_worker

    @property
    def nodes(self):
        return list(self._connections.keys())

    @property
    def id(self):
        return self.worker.id

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
