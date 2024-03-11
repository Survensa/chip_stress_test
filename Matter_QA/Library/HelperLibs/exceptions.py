
class ReliabiltyTestError(Exception):
    """A base class for MyProject exceptions."""

class IterationError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.custom_kwarg = kwargs.get('custom_kwarg')