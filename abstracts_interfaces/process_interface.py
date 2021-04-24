class ProcessInterface:
    """
    Exposes run method
    """

    def run(self, obj: any = None) -> any:
        """
        Run the process on the given obj.

        May cause side-effects.

        :param obj: Any obj, including None
        :return: Any obj, including None
        """
        pass
