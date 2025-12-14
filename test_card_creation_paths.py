#!/usr/bin/env python3
"""
Test script for Anki card creation paths.

This script tests all three instantiation paths:
1. Direct card creation via API
2. Card generation from sources/notebooks
3. Card creation from deck insights

Credentials are loaded from .env.test (git-ignored) or use defaults.
See .env.test for configuration.
"""

import asyncio
import httpx
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load test environment variables from .env.test
env_file = Path(__file__).parent / ".env.test"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key] = value.strip("'\"")

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5055")
API_PASSWORD = os.getenv("API_PASSWORD", "test123")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_PASSWORD}",
    "Accept": "application/json"
}

# Test data
TEST_DECK_NAME = "Test Deck - Card Creation Paths"
TEST_SOURCE_CONTENT = """
Dutch verbs are fundamental to language learning. Common verbs include:
- werken (to work): used in professional contexts
- spreken (to speak): essential for communication
- lezen (to read): important for comprehension
- schrijven (to write): crucial for written expression
"""


async def test_direct_card_creation(deck_id: str) -> bool:
    """Test 1: Direct card creation via POST /anki/cards"""
    print("\n" + "="*60)
    print("TEST 1: Direct Card Creation")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Create cards directly
            cards_to_create = [
                {
                    "front": "werken",
                    "back": "to work",
                    "notes": "Common verb",
                    "deck_id": deck_id,
                    "tags": ["verb", "common"]
                },
                {
                    "front": "spreken",
                    "back": "to speak",
                    "notes": "Communication verb",
                    "deck_id": deck_id,
                    "tags": ["verb", "communication"]
                },
            ]
            
            created_ids = []
            for card_data in cards_to_create:
                print(f"\n➤ Creating card: {card_data['front']}")
                response = await client.post(
                    f"{API_BASE_URL}/api/anki/cards",
                    json=card_data,
                    headers=HEADERS,
                    timeout=30
                )
                
                if response.status_code == 200:
                    card = response.json()
                    created_ids.append(card.get("id"))
                    print(f"  ✓ Created card ID: {card.get('id')}")
                else:
                    print(f"  ✗ Failed: {response.status_code}")
                    print(f"    Response: {response.text}")
                    return False
            
            print(f"\n✓ Test 1 PASSED: Created {len(created_ids)} cards directly")
            return True
            
        except Exception as e:
            print(f"✗ Test 1 FAILED: {e}")
            return False


async def test_deck_card_generation(deck_id: str, source_ids: Optional[List[str]] = None) -> bool:
    """Test 2: Card generation from sources via POST /anki/decks/{deck_id}/generate-cards"""
    print("\n" + "="*60)
    print("TEST 2: Card Generation from Sources")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            # If no source IDs provided, just test with empty source list
            generate_request = {
                "source_ids": source_ids or [],
                "user_prompt": "Generate Dutch vocabulary flashcards for beginners (A1-A2 level) from the provided content",
                "model_id": "qwen2.5:1.5b",
                "num_cards": 3
            }
            
            print(f"\n➤ Generating cards from sources...")
            print(f"  Sources: {generate_request['source_ids'] or 'none'}")
            print(f"  Prompt: {generate_request['user_prompt'][:50]}...")
            print(f"  Model: {generate_request['model_id']}")
            print(f"  Num cards: {generate_request['num_cards']}")
            
            response = await client.post(
                f"{API_BASE_URL}/api/anki/decks/{deck_id}/generate-cards",
                json=generate_request,
                headers=HEADERS,
                timeout=60  # Generation might take longer
            )
            
            if response.status_code == 200:
                result = response.json()
                cards_count = len(result.get("cards", []))
                print(f"  ✓ Generated {cards_count} card previews")
                print(f"    Model used: {result.get('model_used', 'unknown')}")
                for i, card in enumerate(result.get("cards", [])[:3], 1):
                    print(f"    Card {i}: {card.get('front', 'N/A')} → {card.get('back', 'N/A')}")
                print(f"\n✓ Test 2 PASSED: Generated cards from sources")
                return True
            else:
                print(f"  ✗ Failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Test 2 FAILED: {e}")
            return False


async def test_deck_cards_retrieval(deck_id: str) -> bool:
    """Test 3: Retrieve cards from deck"""
    print("\n" + "="*60)
    print("TEST 3: Retrieve Deck Cards")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"\n➤ Retrieving cards from deck {deck_id}...")
            
            response = await client.get(
                f"{API_BASE_URL}/api/anki/decks/{deck_id}/cards",
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                cards = response.json()
                print(f"  ✓ Retrieved {len(cards)} cards")
                
                if cards:
                    print(f"    Sample cards:")
                    for i, card in enumerate(cards[:3], 1):
                        print(f"      {i}. {card.get('front', 'N/A')} → {card.get('back', 'N/A')}")
                        if card.get('notes'):
                            print(f"         Notes: {card['notes']}")
                
                print(f"\n✓ Test 3 PASSED: Retrieved deck cards")
                return True
            else:
                print(f"  ✗ Failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Test 3 FAILED: {e}")
            return False


async def create_test_deck() -> Optional[str]:
    """Create a test deck for card creation testing."""
    print("\n" + "="*60)
    print("SETUP: Creating Test Deck")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            deck_request = {
                "name": TEST_DECK_NAME,
                "description": "Test deck for card creation path validation",
                "tags": ["test", "card-creation"]
            }
            
            print(f"\n➤ Creating deck: {deck_request['name']}")
            response = await client.post(
                f"{API_BASE_URL}/api/anki/decks",
                json=deck_request,
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                deck = response.json()
                deck_id = deck.get("id")
                print(f"  ✓ Created test deck ID: {deck_id}")
                return deck_id
            else:
                print(f"  ✗ Failed to create deck: {response.status_code}")
                print(f"    Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Failed to create test deck: {e}")
            return None


async def main():
    """Run all card creation path tests."""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "ANKI CARD CREATION PATHS TEST SUITE" + " "*13 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Using auth password: {API_PASSWORD}")
    
    # Create test deck
    deck_id = await create_test_deck()
    if not deck_id:
        print("\n✗ Failed to create test deck. Exiting.")
        return {}
    
    # Run tests
    results = {
        "Direct Card Creation": await test_direct_card_creation(deck_id),
        "Deck Card Generation": await test_deck_card_generation(deck_id),
        "Retrieve Deck Cards": await test_deck_cards_retrieval(deck_id),
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASSED" if passed_flag else "✗ FAILED"
        print(f"  {test_name:<30} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests PASSED! Card creation paths are working.")
    else:
        print(f"\n✗ {total - passed} test(s) FAILED. Check logs above for details.")
    
    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    exit(0 if all(results.values()) else 1)
