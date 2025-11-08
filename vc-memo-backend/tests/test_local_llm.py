"""
Tests for local LLM service (Ollama integration)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.local_llm import LocalLLMService, get_local_llm


class TestLocalLLMService:
    """Test LocalLLMService with Ollama"""

    @pytest.fixture
    def local_llm(self):
        """Create LocalLLMService instance"""
        return LocalLLMService(base_url="http://localhost:11434", model="llama3.2:3b")

    @pytest.mark.asyncio
    async def test_check_availability_success(self, local_llm):
        """Test checking Ollama availability when available"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "llama3.2:3b"}]
            }
            mock_get.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.get = mock_get
            
            result = await local_llm.check_availability()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_availability_not_available(self, local_llm):
        """Test checking Ollama availability when not available"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            local_llm.client = AsyncMock()
            local_llm.client.get = mock_get
            
            result = await local_llm.check_availability()
            assert result is False

    @pytest.mark.asyncio
    async def test_check_availability_model_not_installed(self, local_llm):
        """Test when Ollama is available but model is not installed"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "other-model"}]
            }
            mock_get.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.get = mock_get
            
            result = await local_llm.check_availability()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_success(self, local_llm):
        """Test successful text generation"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Generated text response"}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.generate("Test prompt")
            assert result == "Generated text response"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, local_llm):
        """Test generation with system prompt"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Response with system prompt"}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.generate(
                "User prompt",
                system_prompt="System prompt"
            )
            assert result == "Response with system prompt"
            
            # Verify system prompt was included in request
            call_args = mock_post.call_args
            assert "system" in str(call_args)

    @pytest.mark.asyncio
    async def test_extract_json_success(self, local_llm):
        """Test successful JSON extraction"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": '{"field1": "value1", "field2": null}'}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.extract_json(
                "Test text",
                "Extract {text}"
            )
            assert result == {"field1": "value1", "field2": None}

    @pytest.mark.asyncio
    async def test_extract_json_with_markdown(self, local_llm):
        """Test JSON extraction when response includes markdown code blocks"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": '```json\n{"field": "value"}\n```'}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.extract_json(
                "Test text",
                "Extract {text}"
            )
            assert result == {"field": "value"}

    @pytest.mark.asyncio
    async def test_extract_json_invalid_json(self, local_llm):
        """Test JSON extraction with invalid JSON (should return empty dict)"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Not valid JSON"}
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.extract_json(
                "Test text",
                "Extract {text}"
            )
            assert result == {}

    @pytest.mark.asyncio
    async def test_extract_json_error_handling(self, local_llm):
        """Test error handling in JSON extraction"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            local_llm.client = AsyncMock()
            local_llm.client.post = mock_post
            
            result = await local_llm.extract_json(
                "Test text",
                "Extract {text}"
            )
            assert result == {}

    @pytest.mark.asyncio
    async def test_close(self, local_llm):
        """Test closing the HTTP client"""
        local_llm.client = AsyncMock()
        local_llm.client.aclose = AsyncMock()
        
        await local_llm.close()
        local_llm.client.aclose.assert_called_once()


class TestGetLocalLLM:
    """Test get_local_llm function"""

    @pytest.mark.asyncio
    async def test_get_local_llm_creates_instance(self):
        """Test that get_local_llm creates a singleton instance"""
        # Reset the global instance
        import app.services.local_llm
        app.services.local_llm._local_llm = None
        
        instance1 = get_local_llm()
        instance2 = get_local_llm()
        
        # Should return the same instance (singleton)
        assert instance1 is instance2
        assert instance1 is not None

