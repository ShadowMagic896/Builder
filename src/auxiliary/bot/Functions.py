import bson


def fmtDict(d: dict):
    """
    Formats a dictionary to be placeable into a PostgreSQL DB.
    """
    return str(d).replace("'", '"')
