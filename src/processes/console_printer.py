from interfaces.process import Process


class ConsolePrinter(Process):

    def run(self, item=None):
        print(f"Note:\n{item}")
