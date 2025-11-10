"""
Scoring rubric for memo quality evaluation.
"""
import re
from typing import Dict, Any, List, Tuple


class Rubric:
    """Scoring rubric for memo evaluation"""
    
    # Default weights for composite score
    DEFAULT_WEIGHTS = {
        "coverage": 0.35,
        "consistency": 0.20,
        "numeric_sanity": 0.20,
        "citations": 0.15,
        "missing_info_penalty": -0.10,  # Penalty, not weight
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
    
    def score(
        self,
        memo_text: str,
        section_scores: Dict[str, float],
        required_fields: Dict[str, List[str]],
        citations_enabled: bool = True
    ) -> Tuple[Dict[str, float], float, Dict[str, Any]]:
        """
        Score a memo and return per-section scores, composite score, and flags.
        
        Args:
            memo_text: Full memo text
            section_scores: Dict of section_key -> confidence score
            required_fields: Dict of category -> list of required field names
            citations_enabled: Whether citations are expected
        
        Returns:
            Tuple of (section_scores_dict, composite_score, flags_list)
        """
        # Coverage: fraction of required fields mentioned
        coverage = self._compute_coverage(memo_text, required_fields)
        
        # Consistency: cross-section checks
        consistency = self._compute_consistency(memo_text, section_scores)
        
        # Numeric sanity: validate numbers are reasonable
        numeric_sanity = self._compute_numeric_sanity(memo_text)
        
        # Citations: presence of citations if enabled
        citations = self._compute_citations(memo_text) if citations_enabled else 1.0
        
        # Missing info penalty: based on low confidence sections
        missing_info_penalty = self._compute_missing_info_penalty(section_scores)
        
        # Contradictions penalty
        contradictions_penalty = self._compute_contradictions_penalty(memo_text)
        
        # Compute composite score
        composite = (
            self.weights["coverage"] * coverage +
            self.weights["consistency"] * consistency +
            self.weights["numeric_sanity"] * numeric_sanity +
            self.weights["citations"] * citations +
            self.weights["missing_info_penalty"] * missing_info_penalty +
            (-0.05) * contradictions_penalty  # Small penalty for contradictions
        )
        
        # Clamp to [0, 1]
        composite = max(0.0, min(1.0, composite))
        
        # Build flags
        flags = []
        if coverage < 0.7:
            flags.append("low_coverage")
        if consistency < 0.8:
            flags.append("inconsistency_detected")
        if numeric_sanity < 0.9:
            flags.append("numeric_anomaly")
        if citations_enabled and citations < 0.5:
            flags.append("missing_citations")
        if missing_info_penalty > 0.3:
            flags.append("missing_critical_info")
        if contradictions_penalty > 0.1:
            flags.append("contradictions_detected")
        
        # Enhanced section scores with rubric components
        enhanced_section_scores = {}
        for section, conf in section_scores.items():
            enhanced_section_scores[section] = {
                "confidence": conf,
                "coverage": self._section_coverage(memo_text, section, required_fields),
                "has_citations": self._section_has_citations(memo_text, section) if citations_enabled else True
            }
        
        return enhanced_section_scores, composite, flags
    
    def _compute_coverage(self, memo_text: str, required_fields: Dict[str, List[str]]) -> float:
        """Compute coverage: fraction of required fields mentioned"""
        if not required_fields:
            return 1.0
        
        total_required = sum(len(fields) for fields in required_fields.values())
        if total_required == 0:
            return 1.0
        
        found = 0
        memo_lower = memo_text.lower()
        
        for category, fields in required_fields.items():
            for field in fields:
                # Check for field name or common variations
                field_variations = [
                    field.replace("_", " "),
                    field.replace("_", ""),
                    field
                ]
                for variation in field_variations:
                    if variation.lower() in memo_lower:
                        found += 1
                        break
        
        return found / total_required if total_required > 0 else 1.0
    
    def _compute_consistency(self, memo_text: str, section_scores: Dict[str, float]) -> float:
        """Compute consistency: cross-section checks"""
        # Check for company name consistency
        company_names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', memo_text)
        if len(set(company_names)) > 3:  # Too many different capitalized phrases
            return 0.8
        
        # Check section score variance (lower variance = more consistent)
        if len(section_scores) < 2:
            return 1.0
        
        scores = list(section_scores.values())
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        
        # Lower variance = higher consistency
        consistency = 1.0 - min(1.0, variance * 2)  # Scale variance
        return max(0.5, consistency)  # Minimum 0.5
    
    def _compute_numeric_sanity(self, memo_text: str) -> float:
        """Compute numeric sanity: validate numbers are reasonable"""
        # Extract numbers (simplified)
        numbers = re.findall(r'\$?(\d+(?:\.\d+)?)\s*(?:M|million|K|thousand|B|billion)?', memo_text, re.IGNORECASE)
        
        if not numbers:
            return 1.0  # No numbers to validate
        
        issues = 0
        for num_str in numbers:
            try:
                num = float(num_str)
                # Check for obviously wrong values
                if num < 0:
                    issues += 1
                elif num > 1e12:  # > 1 trillion
                    issues += 1
            except:
                issues += 1
        
        sanity = 1.0 - (issues / len(numbers)) if numbers else 1.0
        return max(0.0, sanity)
    
    def _compute_citations(self, memo_text: str) -> float:
        """Compute citations score: presence of citations"""
        # Look for citation patterns
        citation_patterns = [
            r'\[.*?\]',  # [source]
            r'\(.*?\)',   # (source)
            r'Source:',   # Source: ...
            r'Footnote',  # Footnote references
        ]
        
        found = any(re.search(pattern, memo_text, re.IGNORECASE) for pattern in citation_patterns)
        return 1.0 if found else 0.3
    
    def _compute_missing_info_penalty(self, section_scores: Dict[str, float]) -> float:
        """Compute missing info penalty based on low confidence sections"""
        if not section_scores:
            return 1.0
        
        low_confidence_count = sum(1 for score in section_scores.values() if score < 0.7)
        penalty = low_confidence_count / len(section_scores) if section_scores else 0.0
        return penalty
    
    def _compute_contradictions_penalty(self, memo_text: str) -> float:
        """Compute contradictions penalty (simplified)"""
        # Look for contradictory phrases (simplified heuristic)
        contradictions = [
            (r'high growth', r'declining'),
            (r'profitable', r'losing money'),
            (r'strong', r'weak'),
        ]
        
        found = 0
        memo_lower = memo_text.lower()
        for pos, neg in contradictions:
            if re.search(pos, memo_lower) and re.search(neg, memo_lower):
                found += 1
        
        return min(1.0, found / len(contradictions)) if contradictions else 0.0
    
    def _section_coverage(self, memo_text: str, section_key: str, required_fields: Dict[str, List[str]]) -> float:
        """Compute coverage for a specific section"""
        # Simplified: assume section coverage matches overall if section exists
        # In a full implementation, would parse sections
        return 0.8  # Placeholder
    
    def _section_has_citations(self, memo_text: str, section_key: str) -> bool:
        """Check if section has citations"""
        # Simplified: check if citations exist in memo
        return bool(re.search(r'\[.*?\]|\(.*?\)', memo_text))
