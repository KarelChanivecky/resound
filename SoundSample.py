class SoundSample:
    """
    Models a sound sample.
    """
    def __init__(self, sample_rate, sample_duration, samples):
        """
        Construct an instance of SoundSample
        :param sample_rate: the number of samples per second
        :param sample_duration: the duration in seconds
        :param samples: the samples taken
        """
        self.__sample_rate = sample_rate
        self.__sample_duration = sample_duration
        self.__samples = samples

    def get_sample_rate(self):
        return self.__sample_rate

    def get_sample_duration(self):
        return self.__sample_duration

    def get_samples(self):
        return self.__samples
