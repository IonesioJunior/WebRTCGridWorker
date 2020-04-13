from codes import MSG_FIELD, GRID_EVENTS
import json


def _monitor(message: dict, conn_handler):
    response ={MSG_FIELD.TYPE: GRID_EVENTS.MONITOR_ANSWER,
               MSG_FIELD.NODES: conn_handler.nodes, 
               MSG_FIELD.MODELS: {},
               MSG_FIELD.DATASETS: {} }
    return response

def _create_webrtc_scope(message: dict, conn_handler):
    dest = message[MSG_FIELD.FROM]
    conn_handler.start_offer(dest)


def _accept_offer(message: dict, conn_handler):
    dest = message.get(MSG_FIELD.FROM, None)
    content = message.get(MSG_FIELD.PAYLOAD, None)
    conn_handler.process_offer(dest, content)


def _process_webrtc_answer(message: dict, conn_handler):
    dest = message.get(MSG_FIELD.FROM, None)
    content = message.get(MSG_FIELD.PAYLOAD, None)
    conn_handler.process_answer(dest, content)
