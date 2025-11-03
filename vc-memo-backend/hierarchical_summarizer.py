import asyncio
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import tiktoken
from smart_chunker import DocumentChunk
from summary_cache import SummaryCache
from text_preprocessor import TextPreprocessor
from rate_limiter import RateLimiter
import json


@dataclass
class SummaryResult:
    """Result from summarization"""
    content: str
    token_count: int
    cost: float
    source: str
    metadata: Dict[str, Any]
    level: int  # 1, 2, or 3


class HierarchicalSummarizer:
    """Three-layer hierarchical summarization system"""
    
    def __init__(self, cache_dir: str = "cache"):
        # Initialize models - use gpt-4o-mini for L1/L2, gpt-4o for L3
        self.l1_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=200)
        self.l2_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_tokens=400)
        self.l3_model = ChatOpenAI(model="gpt-4o", temperature=0.3, max_tokens=1000)
        
        # Initialize components
        self.cache = SummaryCache(cache_dir)
        self.preprocessor = TextPreprocessor()
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )
        
        # Concurrent request limits
        self.max_concurrent_l1 = 4  # Limit concurrent L1 requests
        self.max_concurrent_l2 = 3  # Limit concurrent L2 requests
        
        # Define prompts for each layer
        self.l1_prompt = ChatPromptTemplate.from_template(
            """Summarize this section in under 120 words focusing on facts, metrics, and insights. Avoid adjectives or filler.

CRITICAL: Extract and preserve ALL:
- Numbers, percentages, dollar amounts
- Dates and timeframes  
- Company/product names
- Key metrics (ARR, MRR, CAC, LTV, etc.)
- Technical specifications

Section metadata: {metadata}

Content:
{content}

Summary (facts only, under 120 words):"""
        )
        
        self.l2_prompt = ChatPromptTemplate.from_template(
            """Synthesize these chunk summaries into a cohesive document summary. Focus on key information.

Document: {source_file}
Document type: {doc_type}

Chunk summaries:
{chunk_summaries}

Create a structured summary (under 400 words) covering:
1. Main points and key data
2. All financial metrics and numbers
3. Critical dates and milestones
4. Important names and entities

Document summary:"""
        )
        
        self.l3_extraction_prompt = ChatPromptTemplate.from_template(
            """Extract {data_type} information from these document summaries for an investment memo.

CRITICAL: You MUST extract ALL specific numbers, metrics, and data points. Never omit quantitative information.

Document summaries:
{summaries}

Extract the following for {data_type}:
{extraction_requirements}

Output valid JSON with all found information. Return null for missing fields but include ALL data that exists:"""
        )
        
    async def summarize_documents(self, 
                                chunks: List[DocumentChunk],
                                extraction_types: List[str]) -> Dict[str, Any]:
        """Execute 3-layer hierarchical summarization"""
        
        print("Starting hierarchical summarization...")
        
        # Layer 1: Chunk-level summaries
        l1_summaries = await self._layer1_chunk_summaries(chunks)
        print(f"✓ Layer 1: Generated {len(l1_summaries)} chunk summaries")
        
        # Layer 2: Document-level summaries
        l2_summaries = await self._layer2_document_summaries(l1_summaries)
        print(f"✓ Layer 2: Generated {len(l2_summaries)} document summaries")
        
        # Layer 3: Structured extraction and synthesis
        extracted_data = await self._layer3_synthesis(l2_summaries, extraction_types)
        print(f"✓ Layer 3: Extracted data for {len(extraction_types)} categories")
        
        # Calculate total cost
        total_cost = (
            sum(s.cost for s in l1_summaries) +
            sum(s.cost for s in l2_summaries) +
            sum(d.get('_cost', 0) for d in extracted_data.values() if isinstance(d, dict))
        )
        
        return {
            'extracted_data': extracted_data,
            'total_cost': round(total_cost, 4),
            'summary_stats': {
                'l1_summaries': len(l1_summaries),
                'l2_summaries': len(l2_summaries),
                'total_chunks': len(chunks),
                'cache_hits': sum(1 for s in l1_summaries if s.metadata.get('cached', False))
            }
        }
    
    async def _layer1_chunk_summaries(self, chunks: List[DocumentChunk]) -> List[SummaryResult]:
        """Layer 1: Summarize individual chunks"""
        summaries = []
        
        # Process chunks in batches to respect rate limits
        semaphore = asyncio.Semaphore(self.max_concurrent_l1)
        
        async def summarize_chunk(chunk: DocumentChunk) -> Optional[SummaryResult]:
            async with semaphore:
                try:
                    # Check cache first
                    cached = await self.cache.get_summary(
                        chunk.content,
                        prompt_type="l1_chunk",
                        model="gpt-4o-mini"
                    )
                    
                    if cached:
                        return SummaryResult(
                            content=cached['summary'],
                            token_count=cached['token_count'],
                            cost=0,  # No cost for cached result
                            source=chunk.source_file,
                            metadata={
                                **chunk.metadata,
                                'cached': True,
                                'chunk_id': chunk.chunk_id
                            },
                            level=1
                        )
                    
                    # Skip very small chunks
                    if chunk.token_count < 50:
                        return None
                    
                    # Compress text before summarization
                    compressed = self.preprocessor.compress_text(chunk.content)
                    
                    # Generate summary with rate limiting
                    prompt_messages = self.l1_prompt.format_messages(
                        content=compressed[:3000],  # Limit input size
                        metadata=json.dumps(chunk.metadata)
                    )
                    
                    response = await self.rate_limiter.execute(
                        self.l1_model.ainvoke,
                        prompt_messages
                    )
                    
                    summary = response.content
                    
                    # Calculate tokens and cost
                    input_tokens = self._count_tokens(str(prompt_messages))
                    output_tokens = self._count_tokens(summary)
                    cost = self.cache.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")
                    
                    # Cache the result
                    await self.cache.store_summary(
                        text=chunk.content,
                        summary=summary,
                        prompt_type="l1_chunk",
                        model="gpt-4o-mini",
                        metadata=chunk.metadata,
                        token_count=output_tokens,
                        cost_estimate=cost
                    )
                    
                    return SummaryResult(
                        content=summary,
                        token_count=output_tokens,
                        cost=cost,
                        source=chunk.source_file,
                        metadata={
                            **chunk.metadata,
                            'cached': False,
                            'chunk_id': chunk.chunk_id
                        },
                        level=1
                    )
                    
                except Exception as e:
                    print(f"Error summarizing chunk {chunk.chunk_id}: {e}")
                    return None
        
        # Process all chunks
        tasks = [summarize_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        summaries = [r for r in results if r is not None]
        
        # Add small delay between batches to avoid rate limits
        await asyncio.sleep(0.5)
        
        return summaries
    
    async def _layer2_document_summaries(self, l1_summaries: List[SummaryResult]) -> List[SummaryResult]:
        """Layer 2: Combine chunk summaries by source document"""
        # Group summaries by source file
        summaries_by_source = {}
        for summary in l1_summaries:
            source = summary.source
            if source not in summaries_by_source:
                summaries_by_source[source] = []
            summaries_by_source[source].append(summary)
        
        l2_summaries = []
        semaphore = asyncio.Semaphore(self.max_concurrent_l2)
        
        async def summarize_document(source: str, chunk_summaries: List[SummaryResult]) -> Optional[SummaryResult]:
            async with semaphore:
                try:
                    # Combine chunk summaries
                    combined_text = "\n\n".join([
                        f"[Chunk {i+1} - {s.metadata.get('section', 'content')}]:\n{s.content}"
                        for i, s in enumerate(chunk_summaries)
                    ])
                    
                    # Check cache
                    cached = await self.cache.get_summary(
                        combined_text,
                        prompt_type="l2_document",
                        model="gpt-4o-mini"
                    )
                    
                    if cached:
                        return SummaryResult(
                            content=cached['summary'],
                            token_count=cached['token_count'],
                            cost=0,
                            source=source,
                            metadata={
                                'cached': True,
                                'chunk_count': len(chunk_summaries),
                                'doc_type': chunk_summaries[0].metadata.get('type', 'unknown')
                            },
                            level=2
                        )
                    
                    # Generate document summary
                    prompt_messages = self.l2_prompt.format_messages(
                        source_file=source,
                        doc_type=chunk_summaries[0].metadata.get('type', 'document'),
                        chunk_summaries=combined_text[:4000]  # Limit input
                    )
                    
                    response = await self.rate_limiter.execute(
                        self.l2_model.ainvoke,
                        prompt_messages
                    )
                    
                    summary = response.content
                    
                    # Calculate cost
                    input_tokens = self._count_tokens(str(prompt_messages))
                    output_tokens = self._count_tokens(summary)
                    cost = self.cache.estimate_cost(input_tokens, output_tokens, "gpt-4o-mini")
                    
                    # Cache result
                    await self.cache.store_summary(
                        text=combined_text,
                        summary=summary,
                        prompt_type="l2_document",
                        model="gpt-4o-mini",
                        metadata={'source': source, 'chunks': len(chunk_summaries)},
                        token_count=output_tokens,
                        cost_estimate=cost
                    )
                    
                    return SummaryResult(
                        content=summary,
                        token_count=output_tokens,
                        cost=cost,
                        source=source,
                        metadata={
                            'cached': False,
                            'chunk_count': len(chunk_summaries),
                            'doc_type': chunk_summaries[0].metadata.get('type', 'unknown')
                        },
                        level=2
                    )
                    
                except Exception as e:
                    print(f"Error summarizing document {source}: {e}")
                    return None
        
        # Process all documents
        tasks = [
            summarize_document(source, summaries)
            for source, summaries in summaries_by_source.items()
        ]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        l2_summaries = [r for r in results if r is not None]
        
        # Add delay to avoid rate limits
        await asyncio.sleep(0.5)
        
        return l2_summaries
    
    async def _layer3_synthesis(self, 
                              l2_summaries: List[SummaryResult],
                              extraction_types: List[str]) -> Dict[str, Any]:
        """Layer 3: Extract structured data for investment memo"""
        
        # Combine all L2 summaries
        combined_summaries = "\n\n".join([
            f"[Document: {s.source}]\n{s.content}"
            for s in l2_summaries
        ])
        
        extraction_requirements = {
            "progress": """
- ARR/MRR with exact amounts and time periods
- Burn rate and runway  
- Growth rates (MoM/YoY) with percentages
- Customer metrics and churn
- CAC/LTV with amounts
- Any financial metrics with dates""",
            
            "financial": """
- Investment ask/current round size (CRITICAL)
- Use of funds breakdown (CRITICAL)
- Funding stage and round details
- Previous rounds with amounts and dates
- Valuations (pre/post-money)
- Cap table and ownership""",
            
            "market": """
- TAM/SAM/SOM with dollar amounts
- Market growth rates
- Target customer segments
- Competitors and positioning
- Market trends and timing""",
            
            "company": """
- Company name and mission
- Business model and revenue streams
- Products/services offered
- Value proposition
- Go-to-market strategy
- Current funding stage""",
            
            "team": """
- Founders with backgrounds
- Key employees and roles
- Advisors and board members
- Previous exits or successes
- Relevant experience"""
        }
        
        extracted_data = {}
        
        # Process each extraction type
        for extract_type in extraction_types:
            if extract_type not in extraction_requirements:
                continue
                
            try:
                # Use gpt-4o for final synthesis
                prompt_messages = self.l3_extraction_prompt.format_messages(
                    data_type=extract_type,
                    summaries=combined_summaries[:6000],  # Limit input
                    extraction_requirements=extraction_requirements[extract_type]
                )
                
                response = await self.rate_limiter.execute(
                    self.l3_model.ainvoke,
                    prompt_messages
                )
                
                # Parse JSON response
                result = json.loads(response.content)
                
                # Calculate cost
                input_tokens = self._count_tokens(str(prompt_messages))
                output_tokens = self._count_tokens(response.content)
                cost = self.cache.estimate_cost(input_tokens, output_tokens, "gpt-4o")
                
                result['_cost'] = cost
                result['confidence'] = self._calculate_extraction_confidence(result)
                
                extracted_data[extract_type] = result
                
            except Exception as e:
                print(f"Error extracting {extract_type}: {e}")
                extracted_data[extract_type] = {
                    'error': str(e),
                    'confidence': 0.0,
                    '_cost': 0
                }
        
        return extracted_data
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(str(text)))
    
    def _calculate_extraction_confidence(self, data: Dict) -> float:
        """Calculate confidence based on data completeness"""
        if not data:
            return 0.0
            
        # Count non-null fields
        total_fields = 0
        filled_fields = 0
        
        for key, value in data.items():
            if key.startswith('_'):  # Skip metadata fields
                continue
                
            total_fields += 1
            if value is not None and value != "" and value != []:
                filled_fields += 1
                
        if total_fields == 0:
            return 0.5
            
        return min(filled_fields / total_fields, 0.95)
