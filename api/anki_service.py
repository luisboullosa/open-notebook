"""
Anki service layer for card management, CRUD operations, and lifecycle management.
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.config import UPLOADS_FOLDER
from open_notebook.domain.anki import (
    AnkiCard,
    AnkiCardEdit,
    AnkiDeck,
    AnkiExportSession,
    AudioMetadata,
    CEFRVote,
    ImageCache,
    ImageMetadata,
    SourceCitation,
)
from open_notebook.exceptions import DatabaseOperationError, InvalidInputError


class AnkiService:
    """Service layer for Anki card operations."""

    def __init__(self):
        logger.info("Initializing Anki service")
        self.anki_data_dir = Path(UPLOADS_FOLDER) / "anki_data"
        self.images_dir = self.anki_data_dir / "images"
        self.audio_dir = self.anki_data_dir / "audio"
        self.cache_dir = self.images_dir / "cache"
        self.uploads_dir = self.images_dir / "uploads"
        
        # Ensure directories exist
        for dir_path in [self.images_dir, self.audio_dir, self.cache_dir, self.uploads_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    # ===== Card CRUD Operations =====

    async def create_card(
        self,
        front: str,
        back: str,
        notes: Optional[str] = None,
        deck_id: Optional[str] = None,
        export_session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_citation: Optional[SourceCitation] = None,
        image_url: Optional[str] = None,
        generate_audio: bool = False,
    ) -> AnkiCard:
        """
        Create a new Anki card.
        
        Args:
            front: Front of the card
            back: Back of the card
            notes: Additional notes
            deck_id: Optional deck assignment
            export_session_id: Optional export session
            tags: Card tags
            source_citation: Citation if generated from source
            image_url: URL for image (will be fetched/cached)
            generate_audio: Whether to generate pronunciation audio
        """
        try:
            card = AnkiCard(
                front=front,
                back=back,
                notes=notes,
                deck_id=deck_id,
                export_session_id=export_session_id,
                tags=tags or [],
                source_citation=source_citation,
            )
            
            # Handle image if provided
            if image_url:
                # This will be handled by image_service in the router layer
                pass
            
            await card.save()
            logger.info(f"Created Anki card: {card.id}")
            return card
        except Exception as e:
            logger.error(f"Error creating Anki card: {str(e)}")
            raise DatabaseOperationError(e)

    async def get_card(self, card_id: str) -> Optional[AnkiCard]:
        """Get a card by ID."""
        try:
            return await AnkiCard.get(card_id)
        except Exception as e:
            logger.error(f"Error fetching card {card_id}: {str(e)}")
            return None

    async def update_card(
        self,
        card_id: str,
        front: Optional[str] = None,
        back: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> AnkiCard:
        """
        Update a card and record changes in edit history.
        """
        try:
            card = await AnkiCard.get(card_id)
            if not card:
                raise InvalidInputError(f"Card {card_id} not found")
            
            # Track changes for history
            changes = {}
            if front is not None and front != card.front:
                changes["front"] = {"old": card.front, "new": front}
                card.front = front
            if back is not None and back != card.back:
                changes["back"] = {"old": card.back, "new": back}
                card.back = back
            if notes is not None and notes != card.notes:
                changes["notes"] = {"old": card.notes, "new": notes}
                card.notes = notes
            if tags is not None:
                changes["tags"] = {"old": card.tags, "new": tags}
                card.tags = tags
            
            if changes:
                await card.add_edit_history(changes, user_id)
                await AnkiCardEdit.cleanup_old_history(card_id, keep_count=10)
            
            await card.save()
            logger.info(f"Updated card: {card_id}")
            return card
        except Exception as e:
            logger.error(f"Error updating card {card_id}: {str(e)}")
            raise DatabaseOperationError(e)

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card and its associated files."""
        try:
            card = await AnkiCard.get(card_id)
            if not card:
                return False
            
            # Cleanup associated files
            if card.audio_metadata and card.audio_metadata.reference_mp3:
                self._cleanup_file(card.audio_metadata.reference_mp3)
            
            if card.image_metadata and card.image_metadata.cached_path:
                self._cleanup_file(card.image_metadata.cached_path)
            
            await card.delete()
            logger.info(f"Deleted card: {card_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting card {card_id}: {str(e)}")
            return False

    async def get_cards_by_deck(self, deck_id: str) -> List[AnkiCard]:
        """Get all cards in a deck."""
        try:
            deck = await AnkiDeck.get(deck_id)
            if not deck:
                return []
            return await deck.get_cards()
        except Exception as e:
            logger.error(f"Error fetching cards for deck {deck_id}: {str(e)}")
            return []

    async def get_cards_by_session(self, session_id: str) -> List[AnkiCard]:
        """Get all cards in an export session."""
        try:
            session = await AnkiExportSession.get(session_id)
            if not session:
                return []
            return await session.get_cards()
        except Exception as e:
            logger.error(f"Error fetching cards for session {session_id}: {str(e)}")
            return []

    # ===== Deck Operations =====

    async def create_deck(self, name: str, description: Optional[str] = None, tags: Optional[List[str]] = None) -> AnkiDeck:
        """Create a new deck."""
        try:
            deck = AnkiDeck(name=name, description=description, tags=tags or [])
            await deck.save()
            logger.info(f"Created deck: {deck.id}")
            return deck
        except Exception as e:
            logger.error(f"Error creating deck: {str(e)}")
            raise DatabaseOperationError(e)

    async def get_deck(self, deck_id: str) -> Optional[AnkiDeck]:
        """Get a deck by ID."""
        try:
            return await AnkiDeck.get(deck_id)
        except Exception as e:
            logger.error(f"Error fetching deck {deck_id}: {str(e)}")
            return None

    async def get_all_decks(self) -> List[AnkiDeck]:
        """Get all decks."""
        try:
            return await AnkiDeck.get_all()
        except Exception as e:
            logger.error(f"Error fetching all decks: {str(e)}")
            return []

    async def delete_deck(self, deck_id: str, delete_cards: bool = False) -> bool:
        """
        Delete a deck.
        
        Args:
            deck_id: Deck to delete
            delete_cards: If True, also delete all cards in the deck
        """
        try:
            deck = await AnkiDeck.get(deck_id)
            if not deck:
                return False
            
            if delete_cards:
                cards = await deck.get_cards()
                for card in cards:
                    await self.delete_card(str(card.id))
            
            await deck.delete()
            logger.info(f"Deleted deck: {deck_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting deck {deck_id}: {str(e)}")
            return False

    # ===== Export Session Operations =====

    async def create_export_session(
        self,
        base_name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        export_format: str = "apkg",
        include_audio: bool = True,
        include_images: bool = True,
    ) -> AnkiExportSession:
        """Create a new export session with timestamped name."""
        try:
            timestamped_name = AnkiExportSession.generate_timestamped_name(base_name)
            session = AnkiExportSession(
                name=timestamped_name,
                description=description,
                tags=tags or [],
                export_format=export_format,
                include_audio=include_audio,
                include_images=include_images,
                status="draft",
            )
            await session.save()
            logger.info(f"Created export session: {session.id}")
            return session
        except Exception as e:
            logger.error(f"Error creating export session: {str(e)}")
            raise DatabaseOperationError(e)

    async def get_export_session(self, session_id: str) -> Optional[AnkiExportSession]:
        """Get an export session by ID."""
        try:
            return await AnkiExportSession.get(session_id)
        except Exception as e:
            logger.error(f"Error fetching export session {session_id}: {str(e)}")
            return None

    async def get_all_export_sessions(self) -> List[AnkiExportSession]:
        """Get all export sessions."""
        try:
            return await AnkiExportSession.get_all()
        except Exception as e:
            logger.error(f"Error fetching all export sessions: {str(e)}")
            return []

    # ===== Audio Management =====

    async def set_card_audio(
        self,
        card_id: str,
        reference_mp3_path: str,
        ipa_transcription: Optional[str] = None,
    ) -> AnkiCard:
        """Set audio metadata for a card."""
        try:
            card = await AnkiCard.get(card_id)
            if not card:
                raise InvalidInputError(f"Card {card_id} not found")
            
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            audio_metadata = AudioMetadata(
                reference_mp3=reference_mp3_path,
                audio_expires_at=expires_at,
                ipa_transcriptions=[ipa_transcription] if ipa_transcription else [],
            )
            
            card.audio_metadata = audio_metadata
            await card.save()
            
            logger.info(f"Set audio for card {card_id}: {reference_mp3_path}")
            return card
        except Exception as e:
            logger.error(f"Error setting audio for card {card_id}: {str(e)}")
            raise DatabaseOperationError(e)

    async def get_expired_audio_cards(self, deck_id: Optional[str] = None) -> List[AnkiCard]:
        """Get cards with expired audio."""
        try:
            if deck_id:
                deck = await AnkiDeck.get(deck_id)
                if deck:
                    return await deck.get_expired_audio_cards()
                return []
            else:
                # Get all cards with expired audio
                all_cards = await AnkiCard.get_all()
                return [card for card in all_cards if card.is_audio_expired()]
        except Exception as e:
            logger.error(f"Error fetching expired audio cards: {str(e)}")
            return []

    # ===== Image Management =====

    async def set_card_image(
        self,
        card_id: str,
        image_metadata: ImageMetadata,
    ) -> AnkiCard:
        """Set image metadata for a card."""
        try:
            card = await AnkiCard.get(card_id)
            if not card:
                raise InvalidInputError(f"Card {card_id} not found")
            
            card.image_metadata = image_metadata
            await card.save()
            
            logger.info(f"Set image for card {card_id}")
            return card
        except Exception as e:
            logger.error(f"Error setting image for card {card_id}: {str(e)}")
            raise DatabaseOperationError(e)

    # ===== CEFR Classification =====

    async def set_card_cefr(
        self,
        card_id: str,
        cefr_level: str,
        confidence: float,
        votes: List[CEFRVote],
    ) -> AnkiCard:
        """Set CEFR classification for a card."""
        try:
            card = await AnkiCard.get(card_id)
            if not card:
                raise InvalidInputError(f"Card {card_id} not found")
            
            card.cefr_level = cefr_level
            card.cefr_confidence = confidence
            card.cefr_votes = votes
            
            # Add CEFR level to tags
            if cefr_level and cefr_level not in card.tags:
                card.tags.append(cefr_level)
            
            await card.save()
            logger.info(f"Set CEFR {cefr_level} for card {card_id}")
            return card
        except Exception as e:
            logger.error(f"Error setting CEFR for card {card_id}: {str(e)}")
            raise DatabaseOperationError(e)

    # ===== Utility Methods =====

    def _cleanup_file(self, file_path: str):
        """Delete a file if it exists."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Error deleting file {file_path}: {str(e)}")


# Global service instance
anki_service = AnkiService()
