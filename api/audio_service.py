"""
Audio service for Anki flashcards.

This service handles:
1. Text-to-speech generation using Piper
2. Speech-to-text transcription using Whisper
3. IPA phonetic transcription using phonemizer
4. Phonetic distance scoring for pronunciation practice
"""

import asyncio
import hashlib
import httpx
import os
from datetime import datetime, timedelta
from loguru import logger
from pathlib import Path
from phonemizer import phonemize
from phonemizer.backend import EspeakBackend
from typing import Optional
import socket
import json

from open_notebook.domain.anki import AnkiCard, AudioMetadata
from open_notebook.config import UPLOADS_FOLDER


class AudioService:
    """Service for audio generation, transcription, and phonetic analysis."""
    
    # Service URLs from environment or defaults
    # Prefer localhost defaults so services running on host are reachable
    WHISPER_URL = os.getenv("WHISPER_API_URL", "http://127.0.0.1:9000")
    PIPER_URL = os.getenv("PIPER_API_URL", "http://127.0.0.1:10200")
    
    # Audio settings
    AUDIO_FORMAT = "mp3"
    AUDIO_BITRATE = "128k"
    AUDIO_EXPIRY_DAYS = 30
    
    def __init__(self):
        """Initialize audio service."""
        logger.info("Initializing Audio service")
        self.audio_dir = Path(UPLOADS_FOLDER) / "anki_data" / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize phonemizer backend
        self.phonemizer_backend = EspeakBackend(
            language="nl",  # Dutch
            with_stress=True,
            preserve_punctuation=False,
        )
    
    async def generate_reference_audio(
        self,
        text: str,
        card_id: str,
        language: str = "nl",
        voice: str = "nl_NL-rdh-medium"
    ) -> AudioMetadata:
        """Generate reference audio using Piper TTS.
        
        Args:
            text: Text to synthesize
            card_id: ID of the card this audio is for
            language: Language code (default: Dutch)
            voice: Piper voice model to use
            
        Returns:
            AudioMetadata with reference audio path and IPA transcription
        """
        logger.info(f"Generating reference audio for card {card_id}")
        
        # Generate IPA transcription
        ipa = self._transcribe_to_ipa(text, language)
        
        # Generate audio file using Piper
        audio_path = await self._generate_piper_audio(text, card_id, voice)
        
        # Create audio metadata
        metadata = AudioMetadata(
            reference_mp3=str(audio_path),
            audio_expires_at=datetime.utcnow() + timedelta(days=self.AUDIO_EXPIRY_DAYS),
            ipa_transcriptions=[ipa],
            user_recordings=[],
            phonetic_scores=[]
        )
        
        logger.info(f"Reference audio generated: {audio_path}")
        return metadata
    
    async def _generate_piper_audio(
        self,
        text: str,
        card_id: str,
        voice: str
    ) -> Path:
        """Generate audio using Piper TTS service.
        
        Args:
            text: Text to synthesize
            card_id: Card ID for filename
            voice: Piper voice model
            
        Returns:
            Path to generated audio file
        """
        # Create filename based on card ID and content hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filename = f"{card_id}_{text_hash}.mp3"
        output_path = self.audio_dir / filename
        
        # If file already exists and is recent, return it
        if output_path.exists():
            logger.debug(f"Using cached audio: {output_path}")
            return output_path
        
        # First try HTTP-based TTS if Piper exposes an HTTP API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.PIPER_URL}/api/tts",
                    json={"text": text, "voice": voice, "output_format": "mp3"},
                )
                if response.status_code == 200 and response.content:
                    output_path.write_bytes(response.content)
                    logger.debug(f"Generated audio via Piper HTTP: {output_path}")
                    return output_path
                else:
                    logger.debug(f"Piper HTTP returned status {response.status_code}, falling back to Wyoming TCP")
        except Exception as e:
            logger.debug(f"Piper HTTP probe failed: {e}; will try Wyoming TCP fallback")

        # Fallback: use Wyoming protocol over TCP to request synthesis
        try:
            wyoming_bytes = await self._synthesize_via_wyoming(text=text, voice=voice)
            if wyoming_bytes:
                output_path.write_bytes(wyoming_bytes)
                logger.debug(f"Generated audio via Piper WYOMING TCP: {output_path}")
                return output_path
            else:
                raise RuntimeError("Wyoming synth produced no audio bytes")
        except Exception as e:
            logger.error(f"Piper TTS failed (HTTP + WYOMING): {e}")
            raise RuntimeError(f"Failed to generate audio: {e}")
        
        return output_path

    async def _synthesize_via_wyoming(self, text: str, voice: str) -> bytes:
        """Use the Wyoming JSONL/TCP protocol to request TTS from Piper.

        This opens a TCP socket to the host/port in `PIPER_URL`, sends a
        single-line JSON header with type 'synthesize' and waits for
        audio-start/audio-chunk/audio-stop events, concatenating payloads.
        Returns raw audio bytes as received from the service.
        """
        # Parse host and port from PIPER_URL (expect http://host:port or host:port)
        try:
            url = self.PIPER_URL
            if url.startswith("http://"):
                url = url[len("http://") :]
            host, port_s = url.split(":")[:2]
            port = int(port_s)
        except Exception:
            # default to localhost:10200
            host, port = "127.0.0.1", 10200

        logger.debug(f"Connecting to Wyoming Piper at {host}:{port}")

        # Connect with a short timeout. Try the parsed port first, then fall
        # back to the common Wyoming port 10200 if that fails (compose often
        # exposes HTTP on 5000 while Wyoming listens on 10200).
        def _try_connect(h: str, p: int):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(6)
            try:
                s.connect((h, p))
                return s
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass
                return None

        sock = _try_connect(host, port)
        if sock is None and port != 10200:
            sock = _try_connect(host, 10200)
        if sock is None:
            raise RuntimeError(f"Failed to connect to piper wyoming socket on {host}:{port} and {host}:10200")

        try:
            # Build header
            header = {"type": "synthesize", "data": {"text": text, "voice": voice}}
            header_line = json.dumps(header, ensure_ascii=False) + "\n"
            sock.sendall(header_line.encode("utf-8"))

            collected = bytearray()

            # Helper to read exactly n bytes
            def _read_n(n: int) -> bytes:
                buf = bytearray()
                while len(buf) < n:
                    chunk = sock.recv(n - len(buf))
                    if not chunk:
                        break
                    buf.extend(chunk)
                return bytes(buf)

            # Read loop: headers are JSON lines ending with '\n'
            while True:
                # Read header line until newline
                header_bytes = bytearray()
                while True:
                    ch = sock.recv(1)
                    if not ch:
                        break
                    if ch == b"\n":
                        break
                    header_bytes.extend(ch)
                if not header_bytes:
                    break
                try:
                    hdr = json.loads(header_bytes.decode("utf-8"))
                except Exception:
                    # malformed header; stop
                    break

                typ = hdr.get("type")
                # If there is extra JSON data following the header, read it
                data_len = int(hdr.get("data_length", 0) or 0)
                if data_len:
                    _ = _read_n(data_len)  # currently ignore extra data

                payload_len = int(hdr.get("payload_length", 0) or 0)
                if payload_len:
                    payload = _read_n(payload_len)
                    collected.extend(payload)

                if typ == "audio-stop":
                    break

            return bytes(collected)
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            sock.close()
    
    async def transcribe_user_recording(
        self,
        audio_file: Path,
        card_id: str,
        reference_text: str
    ) -> tuple[str, str, float]:
        """Transcribe user recording and calculate phonetic score.
        
        Args:
            audio_file: Path to user's audio recording
            card_id: Card ID for saving
            reference_text: Expected text for comparison
            
        Returns:
            Tuple of (transcribed_text, ipa_transcription, phonetic_score)
        """
        logger.info(f"Transcribing user recording for card {card_id}")
        
        # Transcribe using Whisper
        transcribed_text = await self._whisper_transcribe(audio_file)
        
        # Generate IPA for user's transcription
        user_ipa = self._transcribe_to_ipa(transcribed_text)
        
        # Generate IPA for reference text
        reference_ipa = self._transcribe_to_ipa(reference_text)
        
        # Calculate phonetic distance (similarity score)
        score = self._calculate_phonetic_score(user_ipa, reference_ipa)
        
        logger.info(f"Transcription: '{transcribed_text}' | Score: {score:.2f}")
        return transcribed_text, user_ipa, score
    
    async def _whisper_transcribe(self, audio_file: Path, language: Optional[str] = None) -> str:
        """Transcribe audio using Whisper service.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Transcribed text
        """
        # If language isn't provided, attempt autodetect via the Whisper detect-language endpoint
        detected_lang = None
        try:
            if language is None:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        with open(audio_file, "rb") as f:
                            files = {"audio_file": (audio_file.name, f, "audio/mpeg")}
                            resp = await client.post(f"{self.WHISPER_URL}/detect-language", files=files)
                            resp.raise_for_status()
                            j = resp.json()
                            detected_lang = j.get("language_code") or j.get("detected_language")
                            confidence = j.get("confidence")
                            logger.debug(f"Whisper detect-language returned: {detected_lang} (confidence={confidence})")
                            # Normalize common language names to short codes
                            if detected_lang and len(detected_lang) > 2:
                                name = str(detected_lang).lower()
                                mapping = {"english": "en", "dutch": "nl", "nederlands": "nl"}
                                detected_lang = mapping.get(name, detected_lang)
                            language = detected_lang or "nl"
                except Exception as e:
                    logger.debug(f"Language autodetect failed: {e}; defaulting to Dutch")
                    language = "nl"

            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_file, "rb") as f:
                    files = {"audio_file": (audio_file.name, f, "audio/mpeg")}
                    response = await client.post(
                        f"{self.WHISPER_URL}/asr",
                        files=files,
                        data={"language": language}
                    )
                    response.raise_for_status()
                    result = response.json()
                    text = result.get("text", "").strip()
                    logger.debug(f"Whisper transcribed text (lang={language}): {text[:120]}")
                    return text

        except httpx.HTTPError as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")
    
    def _transcribe_to_ipa(self, text: str, language: str = "nl") -> str:
        """Convert text to IPA phonetic transcription.
        
        Args:
            text: Text to transcribe
            language: Language code (default: Dutch)
            
        Returns:
            IPA transcription string
        """
        try:
            # Use phonemizer to convert text to IPA
            ipa = phonemize(
                text,
                language=language,
                backend="espeak",
                strip=True,
                preserve_punctuation=False,
                with_stress=True
            )
            return ipa.strip()
            
        except Exception as e:
            logger.error(f"IPA transcription failed: {e}")
            # Return original text as fallback
            return text
    
    def _calculate_phonetic_score(
        self,
        user_ipa: str,
        reference_ipa: str
    ) -> float:
        """Calculate phonetic similarity score using Levenshtein distance.
        
        Args:
            user_ipa: User's IPA transcription
            reference_ipa: Reference IPA transcription
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not user_ipa or not reference_ipa:
            return 0.0
        
        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(user_ipa, reference_ipa)
        
        # Convert to similarity score (0.0 to 1.0)
        max_len = max(len(user_ipa), len(reference_ipa))
        if max_len == 0:
            return 1.0
        
        similarity = 1.0 - (distance / max_len)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return AudioService._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    async def regenerate_expired_audio(
        self,
        deck_id: Optional[str] = None,
        all_decks: bool = False
    ) -> int:
        """Regenerate expired audio for cards in a deck or all decks.
        
        Args:
            deck_id: Specific deck ID to regenerate audio for
            all_decks: If True, regenerate for all decks
            
        Returns:
            Number of audio files regenerated
        """
        logger.info(f"Regenerating expired audio (deck_id={deck_id}, all_decks={all_decks})")
        
        anki_service = AnkiService()
        
        if all_decks:
            # Get all decks
            decks = await anki_service.get_all_decks()
            cards = []
            for deck in decks:
                deck_cards = await anki_service.get_expired_audio_cards(deck.id)
                cards.extend(deck_cards)
        elif deck_id:
            # Get cards from specific deck
            cards = await anki_service.get_expired_audio_cards(deck_id)
        else:
            logger.warning("No deck specified for audio regeneration")
            return 0
        
        # Regenerate audio for each card
        regenerated_count = 0
        for card in cards:
            try:
                # Generate new audio
                audio_metadata = await self.generate_reference_audio(
                    text=card.front,  # Use front of card as audio text
                    card_id=card.id
                )
                
                # Update card with new audio
                await anki_service.set_card_audio(card.id, audio_metadata)
                regenerated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to regenerate audio for card {card.id}: {e}")
                continue
        
        logger.info(f"Regenerated {regenerated_count} audio files")
        return regenerated_count
    
    async def cleanup_expired_audio(self) -> int:
        """Delete expired audio files from disk.
        
        Returns:
            Number of files deleted
        """
        logger.info("Cleaning up expired audio files")
        
        deleted_count = 0
        expiry_threshold = datetime.utcnow()
        
        # Iterate through all audio files
        for audio_file in self.audio_dir.glob("*.mp3"):
            # Check if file is old enough to be expired (older than expiry days)
            file_age = datetime.utcnow() - datetime.fromtimestamp(audio_file.stat().st_mtime)
            
            if file_age > timedelta(days=self.AUDIO_EXPIRY_DAYS):
                try:
                    audio_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted expired audio: {audio_file}")
                except Exception as e:
                    logger.error(f"Failed to delete {audio_file}: {e}")
        
        logger.info(f"Deleted {deleted_count} expired audio files")
        return deleted_count
