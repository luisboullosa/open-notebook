#!/usr/bin/env python3
"""
Simple HTTP proxy for Piper: exposes /api/tts and forwards to Piper WYOMING TCP.
Runs in a separate container and talks to the `piper` container on the compose network.
"""
import http.server
import json
import socket
from urllib.parse import urlparse

HOST = '0.0.0.0'
PORT = 5000
PIPER_HOST = 'piper'
PIPER_PORT = 10200

class Handler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/api/tts':
            self._set_headers(404)
            self.wfile.write(b'{}')
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode('utf-8'))
            text = payload.get('text', '')
            voice = payload.get('voice', '')
        except Exception:
            self._set_headers(400)
            self.wfile.write(b'{"error":"invalid json"}')
            return

        try:
            audio = synthesize_wyoming(text=text, voice=voice)
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # Return audio bytes as an MP3
        self._set_headers(200, 'audio/mpeg')
        self.wfile.write(audio)

def synthesize_wyoming(text: str, voice: str) -> bytes:
    # connect to wyoming server
    host = PIPER_HOST
    port = PIPER_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))

    header = {"type": "synthesize", "data": {"text": text, "voice": voice}}
    header_line = json.dumps(header, ensure_ascii=False) + '\n'
    sock.sendall(header_line.encode('utf-8'))

    collected = bytearray()
    def read_n(n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    while True:
        # read header line
        header_bytes = bytearray()
        while True:
            ch = sock.recv(1)
            if not ch:
                break
            if ch == b'\n':
                break
            header_bytes.extend(ch)
        if not header_bytes:
            break
        hdr = json.loads(header_bytes.decode('utf-8'))
        data_len = int(hdr.get('data_length', 0) or 0)
        if data_len:
            _ = read_n(data_len)
        payload_len = int(hdr.get('payload_length', 0) or 0)
        if payload_len:
            payload = read_n(payload_len)
            collected.extend(payload)
        if hdr.get('type') == 'audio-stop':
            break

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        pass
    sock.close()

    return bytes(collected)

if __name__ == '__main__':
    server = http.server.HTTPServer((HOST, PORT), Handler)
    print('Piper HTTP proxy listening on', HOST, PORT)
    server.serve_forever()
