from abstracts_interfaces.process import Process


class Runnable:

    def __init__(self, process: Process) -> None:
        self._process = process
        self._running = False

    def start(self):
        pass

    def stop(self):
        pass

    def _run(self):
        pass

    def set_process(self, process: Process):
        if self._running:
            raise RuntimeError("Cannot change process while running")
        self._process = process
