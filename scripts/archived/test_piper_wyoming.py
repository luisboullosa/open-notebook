import socket
import json

HOST='127.0.0.1'
PORT=10200

header = {"type":"synthesize","data":{"text":"test wyoming synth","voice":"nl_NL-mls_5809-low"}}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)
try:
    s.connect((HOST, PORT))
    s.sendall((json.dumps(header, ensure_ascii=False) + '\n').encode('utf-8'))
    collected = bytearray()
    def read_n(n):
        buf = bytearray()
        while len(buf) < n:
            chunk = s.recv(n - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    while True:
        hdr_bytes = bytearray()
        while True:
            ch = s.recv(1)
            if not ch:
                break
            if ch == b'\n':
                break
            hdr_bytes.extend(ch)
        if not hdr_bytes:
            break
        try:
            hdr = json.loads(hdr_bytes.decode('utf-8'))
        except Exception as e:
            print('Malformed header', e)
            break
        typ = hdr.get('type')
        data_len = int(hdr.get('data_length', 0) or 0)
        if data_len:
            extra = read_n(data_len)
            # ignore extra data for now
        payload_len = int(hdr.get('payload_length', 0) or 0)
        if payload_len:
            payload = read_n(payload_len)
            collected.extend(payload)
        print('Received', typ, 'data_len', data_len, 'payload_len', payload_len)
        if typ == 'audio-stop':
            break

    out_path = 'piper_wyoming_out.raw'
    with open(out_path, 'wb') as f:
        f.write(collected)
    print('Saved', len(collected), 'bytes to', out_path)

except Exception as e:
    print('Error:', e)
finally:
    try:
        s.close()
    except:
        pass
