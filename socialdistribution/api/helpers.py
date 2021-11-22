import re


def remove_uuid_dashes(uuid_str: str):
    """Removes the dashes from uuid strings, because DRF can't do that apparently."""
    return re.sub('([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})', '\\1\\2\\3\\4\\5', uuid_str)
