"""
API Router for Anki flashcard management.

Endpoints:
- Card CRUD operations
- Deck management
- Export sessions
- Audio generation and upload
- Image search and upload
- CEFR classification
"""

from pathlib import Path
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel, Field

from api.anki_service import AnkiService
from api.cefr_service import CEFRService
from api.image_service import ImageService
from api.audio_service import AudioService
from open_notebook.domain.anki import (
    AnkiCard,
    AnkiDeck,
    AnkiExportSession,
    CEFRVote,
    ImageMetadata,
    AudioMetadata,
)
from open_notebook.exceptions import InvalidInputError

router = APIRouter(prefix="/anki", tags=["anki"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CardCreateRequest(BaseModel):
    """Request to create a new card."""
    front: str
    back: str
    notes: Optional[str] = None
    deck_id: str
    tags: List[str] = []


class CardUpdateRequest(BaseModel):
    """Request to update an existing card."""
    front: Optional[str] = None
    back: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class DeckCreateRequest(BaseModel):
    """Request to create a new deck."""
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CEFRClassifyRequest(BaseModel):
    """Request to classify text CEFR level."""
    text: str


class CEFRClassifyResponse(BaseModel):
    """Response from CEFR classification."""
    level: str
    confidence: float
    votes: List[CEFRVote]


class ImageSearchRequest(BaseModel):
    """Request to search for an image."""
    query: str
    context: Optional[str] = None


class ExportSessionCreateRequest(BaseModel):
    """Request to create an export session."""
    deck_ids: List[str]
    export_format: str = "apkg"
    include_audio: bool = True
    include_images: bool = True


# ============================================================================
# Card Endpoints
# ============================================================================


@router.post("/cards", response_model=AnkiCard)
async def create_card(request: CardCreateRequest):
    """Create a new flashcard."""
    try:
        service = AnkiService()
        
        card = AnkiCard(
            front=request.front,
            back=request.back,
            notes=request.notes,
            deck_id=request.deck_id,
            tags=request.tags
        )
        
        created_card = await service.create_card(card)
        logger.info(f"Created card: {created_card.id}")
        
        return created_card
        
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards/{card_id}", response_model=AnkiCard)
async def get_card(card_id: str):
    """Get a card by ID."""
    try:
        service = AnkiService()
        card = await service.get_card_by_id(card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        return card
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cards/{card_id}", response_model=AnkiCard)
async def update_card(card_id: str, request: CardUpdateRequest):
    """Update an existing card."""
    try:
        service = AnkiService()
        
        # Get existing card
        card = await service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Update fields
        if request.front is not None:
            card.front = request.front
        if request.back is not None:
            card.back = request.back
        if request.notes is not None:
            card.notes = request.notes
        if request.tags is not None:
            card.tags = request.tags
        
        updated_card = await service.update_card(card)
        logger.info(f"Updated card: {card_id}")
        
        return updated_card
        
    except HTTPException:
        raise
    except InvalidInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cards/{card_id}")
async def delete_card(card_id: str):
    """Delete a card."""
    try:
        service = AnkiService()
        await service.delete_card(card_id)
        logger.info(f"Deleted card: {card_id}")
        
        return {"success": True, "message": "Card deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}/cards", response_model=List[AnkiCard])
async def get_deck_cards(
    deck_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all cards in a deck with pagination."""
    try:
        service = AnkiService()
        deck = await service.get_deck_by_id(deck_id)
        
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")
        
        cards = await deck.get_cards()
        
        # Simple pagination
        return cards[skip:skip + limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deck cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Deck Endpoints
# ============================================================================


@router.post("/decks", response_model=AnkiDeck)
async def create_deck(request: DeckCreateRequest):
    """Create a new deck."""
    try:
        logger.info(f"Received deck creation request: name={request.name}, tags={request.tags}")
        service = AnkiService()
        
        created_deck = await service.create_deck(
            name=request.name,
            description=request.description,
            tags=request.tags
        )
        logger.info(f"Created deck: {created_deck.id}")
        
        return created_deck
        
    except InvalidInputError as e:
        logger.error(f"Invalid input error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to create deck: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks", response_model=List[AnkiDeck])
async def get_all_decks():
    """Get all decks."""
    try:
        service = AnkiService()
        decks = await service.get_all_decks()
        
        return decks
        
    except Exception as e:
        logger.error(f"Failed to get decks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}", response_model=AnkiDeck)
async def get_deck(deck_id: str):
    """Get a deck by ID."""
    try:
        service = AnkiService()
        deck = await service.get_deck_by_id(deck_id)
        
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")
        
        return deck
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deck: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: str,
    delete_cards: bool = Query(False)
):
    """Delete a deck (optionally with all cards)."""
    try:
        service = AnkiService()
        await service.delete_deck(deck_id, delete_cards=delete_cards)
        logger.info(f"Deleted deck: {deck_id} (delete_cards={delete_cards})")
        
        return {"success": True, "message": "Deck deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete deck: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CEFR Classification Endpoints
# ============================================================================


@router.post("/cefr/classify", response_model=CEFRClassifyResponse)
async def classify_cefr(request: CEFRClassifyRequest):
    """Classify text CEFR level using multi-model voting."""
    try:
        service = CEFRService()
        
        level, confidence, votes = await service.classify_text(request.text)
        
        return CEFRClassifyResponse(
            level=level,
            confidence=confidence,
            votes=votes
        )
        
    except Exception as e:
        logger.error(f"CEFR classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/{card_id}/cefr")
async def set_card_cefr(card_id: str, request: CEFRClassifyRequest):
    """Classify and set CEFR level for a card."""
    try:
        anki_service = AnkiService()
        cefr_service = CEFRService()
        
        # Check card exists
        card = await anki_service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Classify
        level, confidence, votes = await cefr_service.classify_text(request.text)
        
        # Update card
        await anki_service.set_card_cefr(
            card_id=card_id,
            cefr_level=level,
            cefr_confidence=confidence,
            cefr_votes=votes
        )
        
        logger.info(f"Set CEFR level for card {card_id}: {level}")
        
        return {
            "success": True,
            "level": level,
            "confidence": confidence,
            "votes": votes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set CEFR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Image Endpoints
# ============================================================================


@router.post("/images/search", response_model=ImageMetadata)
async def search_image(request: ImageSearchRequest):
    """Search for an image using external APIs."""
    try:
        service = ImageService()
        
        image_meta = await service.search_image(
            query=request.query,
            context=request.context
        )
        
        return image_meta
        
    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/{card_id}/image/upload")
async def upload_card_image(
    card_id: str,
    file: UploadFile = File(...)
):
    """Upload a custom image for a card."""
    try:
        anki_service = AnkiService()
        image_service = ImageService()
        
        # Check card exists
        card = await anki_service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Save uploaded image
        image_meta = await image_service.save_uploaded_image(
            file=file,
            card_id=card_id
        )
        
        # Update card
        await anki_service.set_card_image(card_id, image_meta)
        
        logger.info(f"Uploaded image for card {card_id}")
        
        return {"success": True, "image_metadata": image_meta}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Audio Endpoints
# ============================================================================


@router.post("/cards/{card_id}/audio/generate")
async def generate_card_audio(
    card_id: str,
    text: str = Query(...),
    language: str = Query("nl")
):
    """Generate reference audio for a card."""
    try:
        anki_service = AnkiService()
        audio_service = AudioService()
        
        # Check card exists
        card = await anki_service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Generate audio
        audio_meta = await audio_service.generate_reference_audio(
            text=text,
            card_id=card_id,
            language=language
        )
        
        # Update card
        await anki_service.set_card_audio(card_id, audio_meta)
        
        logger.info(f"Generated audio for card {card_id}")
        
        return {"success": True, "audio_metadata": audio_meta}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cards/{card_id}/audio/transcribe")
async def transcribe_user_recording(
    card_id: str,
    file: UploadFile = File(...),
    reference_text: str = Query(...)
):
    """Transcribe user recording and score pronunciation."""
    try:
        anki_service = AnkiService()
        audio_service = AudioService()
        
        # Check card exists
        card = await anki_service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Transcribe and score
        transcribed_text, ipa, score = await audio_service.transcribe_user_recording(
            audio_file=temp_path,
            card_id=card_id,
            reference_text=reference_text
        )
        
        # Clean up temp file
        temp_path.unlink()
        
        return {
            "success": True,
            "transcribed_text": transcribed_text,
            "ipa_transcription": ipa,
            "phonetic_score": score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Session Endpoints
# ============================================================================


@router.post("/export-sessions", response_model=AnkiExportSession)
async def create_export_session(request: ExportSessionCreateRequest):
    """Create a new export session."""
    try:
        service = AnkiService()
        
        # Get deck names for session naming
        deck_names = []
        for deck_id in request.deck_ids:
            deck = await service.get_deck_by_id(deck_id)
            if deck:
                deck_names.append(deck.name)
        
        # Generate session name
        base_name = ", ".join(deck_names) if deck_names else "Export"
        session_name = AnkiExportSession.generate_timestamped_name(base_name)
        
        # Create session
        session = AnkiExportSession(
            name=session_name,
            export_format=request.export_format,
            include_audio=request.include_audio,
            include_images=request.include_images,
            status="draft"
        )
        
        created_session = await service.create_export_session(session)
        
        # TODO: Link cards to session and generate export file
        
        logger.info(f"Created export session: {created_session.id}")
        
        return created_session
        
    except Exception as e:
        logger.error(f"Failed to create export session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-sessions/{session_id}", response_model=AnkiExportSession)
async def get_export_session(session_id: str):
    """Get an export session by ID."""
    try:
        service = AnkiService()
        session = await service.get_export_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Export session not found")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
