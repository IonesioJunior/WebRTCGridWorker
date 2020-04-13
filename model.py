class Model:
    def __init__(
        self,
        model_id: str,
        model,
        description: str,
        input_size: tuple,
        output_size: tuple,
        iterations: int,
        lr: float,
        accuracy: float,
        nodes: list,
        privacy: str = "plain-text",
        access: str = "public",
    ):
        self.id = model_id
        self._model = model
        self.description = description
        self.privacy = privacy
        self._input_size = input_size
        self._output_size = output_size
        self._access = access
        self._iterations = iterations
        self._lr = lr
        self._accuracy = accuracy
        self.nodes = nodes

    def json(self):
        return {
            "description": self.description,
            "privacy": self.privacy,
            "input": self._input_size,
            "output": self._output_size,
            "access": self._access,
            "iterations": self._iterations,
            "lr": self._lr,
            "accuracy": self._accuracy,
            "nodes": self.nodes,
        }
