import multiprocess as mp


class ProcessManager:

    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.process = None

    def start(self):
        """
        (Re)starts a new process with the given target and args

        Returns:

        """
        self.process = mp.Process(target=self.target, args=self.args)
        self.process.start()
        return self.process
