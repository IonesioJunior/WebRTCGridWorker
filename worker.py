from grid import GridNetwork
import time
import sys

import syft as sy
import torch as th

hook = sy.TorchHook(th)

if __name__ == "__main__":
    node_id = sys.argv[1]
    connect = int(sys.argv[2])
    destination = sys.argv[3]

    # args = {"max_size": None, "timeout": 444, "url": "ws://openmined-grid.herokuapp.com"}
    args = {"max_size": None, "timeout": 444, "url": "ws://localhost:5000"}
    grid = GridNetwork(node_id, hook, **args)
    grid.start()

    if connect:
        grid.connect(destination)

    x = th.tensor([1, 2, 3, 4, 5, 6, 7]).tag("#X", "#test").describe("My Little obj")
    print(grid.host_dataset(x))
