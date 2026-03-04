import pytest
from unittest.mock import patch, AsyncMock
from apps.rag.extractor import IntentExtractor

@pytest.mark.asyncio
async def test_extractor_bible_intent():
    extractor = IntentExtractor()
    
    mock_response = {
        "intent": "BIBLE",
        "domains": ["BIBLE"],
        "entities": {
            "topic": "miséricorde",
            "date": None,
            "time_after": None,
            "city": None,
            "service": None
        }
    }
    
    with patch("apps.rag.llm_client.AsyncGeminiClient.generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await extractor.extract("Je cherche un verset sur la miséricorde")
        
        assert result["intent"] == "BIBLE"
        assert "BIBLE" in result["domains"]
        assert result["entities"]["topic"] == "miséricorde"
        mock_gen.assert_called_once()

@pytest.mark.asyncio
async def test_extractor_mixed_intent():
    extractor = IntentExtractor()
    
    mock_response = {
        "intent": "MIXED",
        "domains": ["BIBLE", "AVAILABILITY"],
        "entities": {
            "topic": "miséricorde",
            "date": "2026-03-02",
            "time_after": "16:00",
            "city": "Mbour",
            "service": "confession"
        }
    }
    
    with patch("apps.rag.llm_client.AsyncGeminiClient.generate_structured", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        result = await extractor.extract("Je veux un verset sur la miséricorde et demain à Mbour vers 16h pour confession")
        
        assert result["intent"] == "MIXED"
        assert "BIBLE" in result["domains"]
        assert "AVAILABILITY" in result["domains"]
        assert result["entities"]["city"] == "Mbour"
