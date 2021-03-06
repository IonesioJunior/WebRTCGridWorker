from grid import GridNetwork
from model import Model
import time
import sys

import syft as sy
import torch as th
import asyncio

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
        node = grid.connect(destination)
    else:
        time.sleep(5)
        node = grid._connection_handler.get("bill")

    x = th.tensor([1, 2, 3, 4, 5, 6, 7]).tag("#X", "#test").describe("My Little obj")

    x_s = x.send(node)

    for i in range(10):
        x_s = x_s + x_s
        print("X_S: ", x_s)

    if not connect:
        print("Disconnecting ... ")
        node.disconnect()
    else:
        time.sleep(15)

    grid.stop()
    """
    model = Model(
        model=None,
        model_id="mnist",
        description="Model trained with MNIST dataset",
        input_size=(10, 10),
        output_size=(1, 9),
        iterations=1000,
        lr=0.001,
        accuracy=0.85,
        nodes=[],
    )

    print(grid.host_model(model))
    print(grid.host_dataset(x))
    """
