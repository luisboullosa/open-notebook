import asyncio
from pathlib import Path
from api.audio_service import AudioService

async def main():
    svc = AudioService()
    audio = Path('test_whisper.wav')
    print('Calling _whisper_transcribe with autodetect...')
    text = await svc._whisper_transcribe(audio)
    print('Transcription result:', repr(text))

if __name__ == '__main__':
    asyncio.run(main())
