# Contains general utilities for working with the CAN Data

def pack_16bit(hi, lo):
    """
    Packs two 8-bit numbers into a 16-bit number.
    """

    return (hi << 8) + lo