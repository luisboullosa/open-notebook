#!/usr/bin/env python3
"""
Extended test for Anki card generation from actual sources.

Tests card generation workflow: create source → vectorize → generate cards
"""

import asyncio
import httpx
import os
from pathlib import Path

# Load test environment variables from .env.test
env_file = Path(__file__).parent / ".env.test"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key] = value.strip("'\"")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5055")
API_PASSWORD = os.getenv("API_PASSWORD", "test123")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_PASSWORD}",
    "Accept": "application/json"
}

TEST_SOURCE_CONTENT = """
Dutch Verbs for Language Learners

werken (to work) - Common verb used in professional and daily contexts. Example: Ik werk in Amsterdam. (I work in Amsterdam.)

spreken (to speak) - Essential for communication. Example: Ik spreek Nederlands. (I speak Dutch.)

lezen (to read) - Important for comprehension of written material. Example: Ik lees een boek. (I am reading a book.)

schrijven (to write) - Crucial for written expression. Example: Ik schrijf een email. (I am writing an email.)

eten (to eat) - Basic daily activity. Example: Ik eet brood. (I eat bread.)

drinken (to drink) - Another daily necessity. Example: Ik drink water. (I drink water.)

slapen (to sleep) - Essential life activity. Example: Ik slaap acht uur per nacht. (I sleep eight hours per night.)
"""


async def create_source_with_content(notebook_id: str) -> str:
    """Create a source with actual text content."""
    print("\n➤ Creating source with text content...")
    
    async with httpx.AsyncClient() as client:
        try:
            request_data = {
                "title": "Dutch Verbs for Learning",
                "content": TEST_SOURCE_CONTENT,
                "type": "text",
                "notebook_id": notebook_id,
                "async_processing": "true"
            }
            
            # Sources API expects multipart/form-data with Form fields
            form_headers = {k: v for k, v in HEADERS.items()}
            form_headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = await client.post(
                f"{API_BASE_URL}/api/sources",
                data=request_data,
                headers=form_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                source = response.json()
                source_id = source.get("id")
                print(f"  ✓ Created source ID: {source_id}")
                return source_id
            else:
                print(f"  ✗ Failed to create source: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return None


async def vectorize_source(source_id: str) -> bool:
    """Submit source for vectorization."""
    print(f"\n➤ Submitting source {source_id} for vectorization...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/sources/{source_id}/vectorize",
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code in (200, 202):
                result = response.json()
                command_id = result.get("command_id")
                print(f"  ✓ Vectorization submitted: {command_id}")
                
                # Wait a bit for vectorization to process
                await asyncio.sleep(3)
                return True
            else:
                print(f"  ✗ Failed: {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False


async def test_card_generation_from_source(deck_id: str, source_id: str) -> bool:
    """Test card generation with actual source."""
    print(f"\n➤ Generating cards from source {source_id}...")
    
    async with httpx.AsyncClient() as client:
        try:
            request_data = {
                "source_ids": [source_id],
                "user_prompt": "Generate Dutch vocabulary flashcards (A1-A2 level) from the provided content",
                "model_id": "qwen2.5:1.5b",
                "num_cards": 3
            }
            
            response = await client.post(
                f"{API_BASE_URL}/api/anki/decks/{deck_id}/generate-cards",
                json=request_data,
                headers=HEADERS,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                cards = result.get("cards", [])
                print(f"  ✓ Generated {len(cards)} cards")
                
                for i, card in enumerate(cards[:3], 1):
                    print(f"    Card {i}: {card.get('front', 'N/A')} → {card.get('back', 'N/A')}")
                
                return True
            else:
                print(f"  ✗ Failed: {response.status_code}")
                print(f"    Response: {response.text[:300]}")
                return False
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False


async def create_notebook() -> str:
    """Create a test notebook."""
    print("➤ Creating test notebook...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/notebooks",
                json={"name": "Test Notebook - Card Generation", "description": "Test"},
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                notebook = response.json()
                notebook_id = notebook.get("id")
                print(f"  ✓ Created notebook ID: {notebook_id}")
                return notebook_id
            else:
                print(f"  ✗ Failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return None


async def create_deck() -> str:
    """Create a test deck."""
    print("➤ Creating test deck...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/anki/decks",
                json={"name": "Test - Card Generation", "description": "Test"},
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                deck = response.json()
                deck_id = deck.get("id")
                print(f"  ✓ Created deck ID: {deck_id}")
                return deck_id
            else:
                print(f"  ✗ Failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return None


async def main():
    """Run extended card generation test."""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*8 + "ANKI CARD GENERATION WITH SOURCE TEST" + " "*12 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\nAPI: {API_BASE_URL}")
    print(f"Auth Token: {API_PASSWORD[:10]}...")
    
    # Setup
    print("\n" + "="*60)
    print("SETUP: Creating Test Entities")
    print("="*60)
    
    notebook_id = await create_notebook()
    if not notebook_id:
        print("\n✗ Failed to create notebook. Exiting.")
        return
    
    deck_id = await create_deck()
    if not deck_id:
        print("\n✗ Failed to create deck. Exiting.")
        return
    
    # Create and vectorize source
    print("\n" + "="*60)
    print("STEP 1: Create and Vectorize Source")
    print("="*60)
    
    source_id = await create_source_with_content(notebook_id)
    if not source_id:
        print("\n✗ Failed to create source. Exiting.")
        return
    
    vectorized = await vectorize_source(source_id)
    if not vectorized:
        print("\n✗ Vectorization failed. Continuing anyway...")
    
    # Test card generation
    print("\n" + "="*60)
    print("STEP 2: Generate Cards from Source")
    print("="*60)
    
    cards_generated = await test_card_generation_from_source(deck_id, source_id)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if cards_generated:
        print("\n✓ SUCCESS: Card generation from source works!")
        print(f"  - Created source with text content")
        print(f"  - Submitted for vectorization")
        print(f"  - Generated cards from source")
    else:
        print("\n✗ FAILED: Card generation from source did not work")
        print("  Check logs above for details")


if __name__ == "__main__":
    asyncio.run(main())
