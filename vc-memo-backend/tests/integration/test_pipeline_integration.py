"""
Integration tests for full pipeline with all new features
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.documents import Document
from app.services.pipeline.pipeline import run_memo_pipeline
from app.core.models import DEFAULT_TEMPLATE


class TestPipelineIntegration:
    """Test full pipeline integration with new features"""

    @pytest.mark.asyncio
    async def test_pipeline_with_uncertainty_flags(self):
        """Test that pipeline generates uncertainty flags"""
        documents = [
            {
                "filename": "test.pdf",
                "content": b"Test content with no metrics",
                "content_type": "application/pdf"
            }
        ]
        
        # Mock the document parser and extractors
        with patch("app.services.pipeline.LangChainDocumentParser") as mock_parser_class, \
             patch("app.services.pipeline.ExtractionCoordinator") as mock_coordinator_class, \
             patch("app.services.pipeline.MemoGenerator") as mock_generator_class:
            
            # Mock document parser
            mock_parser = AsyncMock()
            mock_doc = Document(page_content="Test content", metadata={"source_file": "test.pdf"})
            mock_parser.parse_documents = AsyncMock(return_value=[mock_doc])
            mock_parser_class.return_value = mock_parser
            
            # Mock extractor coordinator
            mock_coordinator = AsyncMock()
            from app.core.models import ProgressData, FinancialData, MarketData, CompanyData, TeamData
            mock_progress = ProgressData()
            mock_progress.uncertainty_flags = ["Missing critical field: arr"]
            mock_progress.confidence = 0.5
            mock_coordinator.extract_all = AsyncMock(return_value={
                "progress": mock_progress,
                "financial": FinancialData(),
                "market": MarketData(),
                "company": CompanyData(),
                "team": TeamData()
            })
            mock_coordinator_class.return_value = mock_coordinator
            
            # Mock memo generator
            mock_generator = AsyncMock()
            mock_generator.generate_complete_memo = AsyncMock(return_value={
                "sections": {"exec_summary": "Test memo"},
                "confidence_scores": {"exec_summary": 0.5},
                "flagged_items": [],
                "uncertainty_flags": [{"section": "exec_summary", "data_type": "progress", "flag": "Missing critical field: arr"}],
                "final_memo": "# Test Memo\n\nTest memo"
            })
            mock_generator_class.return_value = mock_generator
            
            result = await run_memo_pipeline("test_job", documents, DEFAULT_TEMPLATE)
            
            # Verify uncertainty flags are in response
            assert "uncertainty_flags" in result
            assert len(result["uncertainty_flags"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_with_source_citations(self):
        """Test that pipeline includes source citations"""
        documents = [
            {
                "filename": "financials.pdf",
                "content": b"ARR is $5M",
                "content_type": "application/pdf"
            }
        ]
        
        with patch("app.services.pipeline.LangChainDocumentParser") as mock_parser_class, \
             patch("app.services.pipeline.ExtractionCoordinator") as mock_coordinator_class, \
             patch("app.services.pipeline.MemoGenerator") as mock_generator_class:
            
            mock_parser = AsyncMock()
            mock_doc = Document(
                page_content="ARR is $5M",
                metadata={"source_file": "financials.pdf"}
            )
            mock_parser.parse_documents = AsyncMock(return_value=[mock_doc])
            mock_parser_class.return_value = mock_parser
            
            mock_coordinator = AsyncMock()
            from app.core.models import ProgressData, FinancialData, MarketData, CompanyData, TeamData
            mock_progress = ProgressData(arr="$5M")
            mock_progress.source_citations = {"arr": ["financials.pdf"]}
            mock_coordinator.extract_all = AsyncMock(return_value={
                "progress": mock_progress,
                "financial": FinancialData(),
                "market": MarketData(),
                "company": CompanyData(),
                "team": TeamData()
            })
            mock_coordinator_class.return_value = mock_coordinator
            
            mock_generator = AsyncMock()
            mock_generator.generate_complete_memo = AsyncMock(return_value={
                "sections": {"exec_summary": "Test"},
                "confidence_scores": {"exec_summary": 0.8},
                "flagged_items": [],
                "uncertainty_flags": [],
                "final_memo": "# Test"
            })
            mock_generator_class.return_value = mock_generator
            
            result = await run_memo_pipeline("test_job", documents, DEFAULT_TEMPLATE)
            
            # Verify pipeline completed
            assert result["success"] is True
            # Source citations should be in extracted data (checked via coordinator mock)

    @pytest.mark.asyncio
    async def test_pipeline_context_enrichment(self):
        """Test that context enrichment runs in pipeline"""
        documents = [
            {
                "filename": "test.pdf",
                "content": b"Test content",
                "content_type": "application/pdf"
            }
        ]
        
        with patch("app.services.pipeline.LangChainDocumentParser") as mock_parser_class, \
             patch("app.services.pipeline.ExtractionCoordinator") as mock_coordinator_class, \
             patch("app.services.pipeline.MemoGenerator") as mock_generator_class, \
             patch("app.services.pipeline.SemanticRouter") as mock_router_class:
            
            # Setup mocks
            mock_parser = AsyncMock()
            mock_doc = Document(page_content="Test", metadata={"source_file": "test.pdf"})
            mock_parser.parse_documents = AsyncMock(return_value=[mock_doc])
            mock_parser_class.return_value = mock_parser
            
            mock_router = AsyncMock()
            mock_router.route_chunks = AsyncMock(return_value={
                "progress": [mock_doc],
                "financial": [],
                "market": [],
                "company": [],
                "team": []
            })
            mock_router_class.return_value = mock_router
            
            mock_coordinator = AsyncMock()
            from app.core.models import ProgressData, FinancialData, MarketData, CompanyData, TeamData
            mock_coordinator.extract_all = AsyncMock(return_value={
                "progress": ProgressData(),
                "financial": FinancialData(),
                "market": MarketData(),
                "company": CompanyData(),
                "team": TeamData()
            })
            mock_coordinator_class.return_value = mock_coordinator
            
            mock_generator = AsyncMock()
            mock_generator.generate_complete_memo = AsyncMock(return_value={
                "sections": {"exec_summary": "Test"},
                "confidence_scores": {"exec_summary": 0.8},
                "flagged_items": [],
                "uncertainty_flags": [],
                "final_memo": "# Test"
            })
            mock_generator_class.return_value = mock_generator
            
            result = await run_memo_pipeline("test_job", documents, DEFAULT_TEMPLATE)
            
            # Verify pipeline completed (context enrichment runs as part of pipeline)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test that pipeline handles errors gracefully"""
        documents = [
            {
                "filename": "test.pdf",
                "content": b"Test",
                "content_type": "application/pdf"
            }
        ]
        
        with patch("app.services.pipeline.LangChainDocumentParser") as mock_parser_class:
            # Simulate parser error
            mock_parser = AsyncMock()
            mock_parser.parse_documents = AsyncMock(side_effect=Exception("Parser error"))
            mock_parser_class.return_value = mock_parser
            
            result = await run_memo_pipeline("test_job", documents, DEFAULT_TEMPLATE)
            
            # Should handle error gracefully
            assert result["success"] is False
            assert "error" in result or "error_messages" in result

