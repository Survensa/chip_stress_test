
class ReliabiltyTestError(Exception):
    """A base class for MyProject exceptions."""

class IterationError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.iteration_kwarg = kwargs.get('iteration_kwarg')
        

class TestCaseError(ReliabiltyTestError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.test_case_kwarg = kwargs.get('test_case_kwarg')
        