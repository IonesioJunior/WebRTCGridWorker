from grid import GridNetwork
import time
import sys

if __name__ == "__main__":
    node_id = sys.argv[1]
    connect = int(sys.argv[2])
    destination = sys.argv[3]

    #args = {"max_size": None, "timeout": 444, "url": "ws://openmined-grid.herokuapp.com"}
    args = {"max_size": None, "timeout": 444, "url": "ws://localhost:5000"}
    grid = GridNetwork(node_id, **args)
    grid.start()

    if connect:
        grid.connect(destination)
