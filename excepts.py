class AlreadyInDB(Exception):
    """Custom error to readily find duplicate items."""
    pass


class SilentFail(Exception):
    """Custom error to help assist with SilentFails"""
    pass
