class MSG_FIELD:
    TYPE = "type"
    FROM = "from"
    DESTINATION = "destination"
    CONTENT = "content"
    NODE_ID = "node_id"
    PAYLOAD = "payload"
    NODES = "nodes"
    MODELS = "models"
    DATASETS = "datasets"

class GRID_EVENTS:
    JOIN = "join"
    FORWARD = "grid-forward"
    MODEL_METADATA_ANSWER = "get-models-answeer"
    DATASETS_METADATA_ANSWER = "get-datasets-answer"
    NODES_METADATA_ANSWER = "get-nodes-answer"
    FORWARD = "forward"
    MONITOR_ANSWER = "monitor-answer"

class NODE_EVENTS:
    MONITOR = "monitor"
    WEBRTC_SCOPE = "create-webrtc-scope"
    WEBRTC_OFFER = "webrtc-offer"
    WEBRTC_ANSWER = "webrtc-answer"
