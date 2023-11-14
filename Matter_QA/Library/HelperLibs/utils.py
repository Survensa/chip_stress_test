import signal


class CommissionTimeoutError(Exception):
    pass


def convert_args_dict(args: list):
    """
    This function is used to convert arguments passed via cmd line to dict format
    """
    keys = []
    values = []
    for arg in args:
        if "--" in arg and arg.startswith("--"):
            keys.append(arg)
        else:
            values.append(arg)
    return dict(zip(keys, values))

def timeouterror(signum, frame):
    raise CommissionTimeoutError("timed out, Failed to commission the dut")


def timer(function):
    def wrapper(*args, **kwargs):
        # Set the alarm for the timeout
        timeout = kwargs.pop('timeout', 60)
        signal.signal(signal.SIGALRM, timeouterror)
        signal.alarm(timeout)
        try:
            result = function(*args, **kwargs)
        finally:
            # Cancel the alarm after the function finishes
            signal.alarm(0)
        return result

    return wrapper
