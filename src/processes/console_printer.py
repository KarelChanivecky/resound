from interfaces.process import Process

CLEAR_SCREEN = "\033[2J\033[H"


class ConsolePrinter(Process):

    def run(self, item=None):
        print(f"{CLEAR_SCREEN}Note:\n{item}")
