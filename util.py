# Contains general utilities for working with graph data

def pack16Bit(hi, lo):
    """
    Packs two 8-bit numbers into a 16-bit number.
    """

    return (hi << 8) + lo