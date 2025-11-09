"""
Tests for fact-checking logic in memo generator
"""
import pytest
from app.services.generation.memo_generator import MemoGenerator
from app.core.models import FinancialData, CompanyData, ProgressData


class TestFactChecking:
    """Test fact-checking functionality"""

    @pytest.fixture
    def memo_generator(self):
        """Create MemoGenerator instance"""
        return MemoGenerator()

    def test_fact_check_funding_stage_mismatch(self, memo_generator):
        """Test detection of funding stage mismatch between financial and company data"""
        data = {
            "financial": FinancialData(funding_stage="Series A"),
            "company": CompanyData(funding_stage="Series B")
        }
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        assert len(result["inconsistencies"]) > 0
        assert any("funding stage" in inc.lower() for inc in result["inconsistencies"])

    def test_fact_check_investment_ask_mismatch(self, memo_generator):
        """Test detection of investment ask mismatch"""
        data = {
            "financial": FinancialData(
                investment_ask="$10M",
                current_round_size="$15M"
            )
        }
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        assert len(result["inconsistencies"]) > 0
        assert any("investment ask" in inc.lower() or "round size" in inc.lower() 
                  for inc in result["inconsistencies"])

    def test_fact_check_missing_investment_ask(self, memo_generator):
        """Test detection of missing investment ask in exec summary"""
        data = {
            "financial": FinancialData(
                total_funding_raised="$5M",
                # Missing investment_ask and current_round_size
            )
        }
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        assert len(result["inconsistencies"]) > 0
        assert any("investment ask" in inc.lower() or "round size" in inc.lower()
                  for inc in result["inconsistencies"])

    def test_fact_check_no_inconsistencies(self, memo_generator):
        """Test that no inconsistencies are detected when data is consistent"""
        data = {
            "financial": FinancialData(
                funding_stage="Series A",
                investment_ask="$10M",
                current_round_size="$10M"
            ),
            "company": CompanyData(
                funding_stage="Series A"
            )
        }
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        assert len(result["inconsistencies"]) == 0

    def test_fact_check_with_dict_data(self, memo_generator):
        """Test fact-checking with dict data (not Pydantic models)"""
        data = {
            "financial": {
                "funding_stage": "Series A",
                "investment_ask": "$10M"
            },
            "company": {
                "funding_stage": "Series B"
            }
        }
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        assert len(result["inconsistencies"]) > 0

    def test_fact_check_empty_data(self, memo_generator):
        """Test fact-checking with empty data"""
        data = {}
        
        result = memo_generator._fact_check_data(data, "exec_summary")
        
        assert result["checked"] is True
        # Should not crash, may or may not have inconsistencies

