import json
import threading
import http.server
import urllib.request
import textwrap
import io
import gzip as stdgzip
import socket

import pytest
from more_itertools.recipes import flatten, consume

from jaraco.stream import gzip


@pytest.fixture
def gzipped_json():
    """
    A gzipped json doc.
    """
    payload = textwrap.dedent(
        """
        [
            {"id": 1, "data": "foo"},
            {"id": 2, "data": "bar"}
        ]
        """
    ).lstrip()
    buffer = io.BytesIO()
    gz = stdgzip.GzipFile(mode='w', fileobj=buffer)
    gz.write(payload.encode())
    gz.close()
    return bytes(buffer.getbuffer())


# copied from CPython 3.10
def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


class BestFamilyServer(http.server.HTTPServer):
    address_family, _ = _get_best_family(None, 8080)


@pytest.fixture
def gzip_server(gzipped_json):
    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(s):
            s.send_response(200)
            s.send_header("Content-type", "application/octet-stream")
            s.end_headers()
            s.wfile.write(gzipped_json)

    host = ''
    port = 8080
    addr = host, port
    httpd = BestFamilyServer(addr, MyHandler)
    url = 'http://localhost:{port}/'.format(**locals())
    try:
        threading.Thread(target=httpd.serve_forever).start()
        yield url
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture
def gzip_stream(gzip_server):
    return urllib.request.urlopen(gzip_server)


def test_lines_from_stream(gzip_stream):
    chunks = gzip.read_chunks(gzip_stream)
    streams = gzip.load_streams(chunks)
    lines = flatten(map(gzip.lines_from_stream, streams))
    first_line = next(lines)
    assert first_line == '['
    second_line = next(lines)
    result = json.loads(second_line.rstrip('\n,'))
    assert isinstance(result, dict)
    assert 'id' in result


def test_lines_completes(gzip_stream):
    """
    When reading lines from a gzip stream, the operation should complete
    when the stream is exhausted.
    """
    chunks = gzip.read_chunks(gzip_stream)
    streams = gzip.load_streams(chunks)
    lines = flatten(map(gzip.lines_from_stream, streams))
    consume(lines)
