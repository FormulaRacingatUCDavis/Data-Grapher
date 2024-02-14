# Contains general utilities for working with graph data

def pack16Bit(hi, lo):
    """
    Packs two 8-bit numbers into a 16-bit number.
    """

    return (hi << 8) + lo

def convertTime(value):
    """
    Converts the time from the CAN message to seconds.
    """

    return value / 1_000_000