from interfaces.process import Process


class PeaksGUIProcess(Process):
    """
    Forwards a DetectedPeaks object to the GUI and returns it unchanged,
    so this process can be used as either a ThreadedConsumer sink or a
    ConsumerProducer pass-through stage.
    """

    def __init__(self, gui) -> None:
        self._gui = gui

    def run(self, detected_peaks=None):
        if detected_peaks is not None:
            self._gui.give_peaks(detected_peaks)
        return detected_peaks


class NoteGUIProcess(Process):
    """
    Forwards a MusicalNote to the GUI and returns it unchanged.
    """

    def __init__(self, gui) -> None:
        self._gui = gui

    def run(self, note=None):
        if note is not None:
            self._gui.give_note(note)
        return note
