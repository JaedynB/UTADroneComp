"""
Routines for reliably decompressing gzip streams
in iterables.
"""

import zlib
import itertools

from more_itertools.more import peekable

from . import buffer


def read_chunks(stream, block_size=2 ** 10):
    """
    Given a byte stream with reader, yield chunks of block_size
    until the stream is consusmed.
    """
    while True:
        chunk = stream.read(block_size)
        if not chunk:
            break
        yield chunk


def load_stream(dc, chunks):
    """
    Given a decompression stream and chunks, yield chunks of
    decompressed data until the compression window ends.
    """
    while not dc.eof:
        res = dc.decompress(dc.unconsumed_tail + next(chunks))
        yield res


def load_streams(chunks):
    """
    Given a gzipped stream of data, yield streams of decompressed data.
    """
    chunks = peekable(chunks)
    while chunks:
        dc = zlib.decompressobj(wbits=zlib.MAX_WBITS | 16)
        yield load_stream(dc, chunks)
        if dc.unused_data:
            chunks = peekable(itertools.chain((dc.unused_data,), chunks))


def lines_from_stream(chunks):
    """
    Given data in chunks, yield lines of text
    """
    buf = buffer.DecodingLineBuffer()
    for chunk in chunks:
        buf.feed(chunk)
        yield from buf
