import wave, math, array
fr = 16000
dur = 1.0
freq = 440.0
n = int(fr * dur)
amp = 16000
data = array.array('h', (int(amp * math.sin(2 * math.pi * freq * i / fr)) for i in range(n)))
with wave.open('test_whisper.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(fr)
    w.writeframes(data.tobytes())
print('WAV written: test_whisper.wav')
