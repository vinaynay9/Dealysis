"""
Semantic router for intelligently routing document chunks to relevant extractors.
Uses embeddings to match chunks with extractor intents, reducing unnecessary API calls.
"""

import os
import asyncio
import time
import tiktoken
import sys
from typing import List, Dict, Tuple
from openai import AsyncOpenAI
from langchain_core.documents import Document
import numpy as np
from collections import defaultdict


class SemanticRouter:
    """Routes document chunks to relevant extractors using semantic similarity"""

    def __init__(self):
        """Initialize semantic router with embedding model and extractor intents"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = AsyncOpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Rate limiting for Free tier (3 RPM = 20 seconds between requests)
        self._last_request_time = 0
        self._min_request_interval = 20.0  # 20 seconds for 3 RPM limit

        # Define semantic intents for each extractor type
        # These describe what kind of information each extractor looks for
        self.extractor_intents = {
            "progress": """
                ARR annual recurring revenue MRR monthly recurring revenue metrics 
                growth rate customer acquisition burn rate runway months churn rate 
                CAC customer acquisition cost LTV lifetime value unit economics 
                retention revenue performance KPIs key performance indicators
                monthly active users MAU daily active users DAU subscribers
                conversion rate sales pipeline bookings revenue streams
            """,
            "financial": """
                funding rounds seed series A B C D investment raise raising capital
                valuation pre-money post-money cap table capitalization table
                board of directors ownership percentages equity stake shares
                liquidation preference investors venture capital VC angels
                use of funds allocation budget term sheet convertible notes
                SAFE simple agreement future equity dilution vesting
            """,
            "market": """
                TAM total addressable market SAM serviceable addressable market
                SOM serviceable obtainable market market size opportunity
                competitors competition competitive landscape advantage moat
                differentiation target segments customer segments personas
                market growth rate industry trends sector analysis
                barriers to entry go-to-market strategy positioning
            """,
            "company": """
                company name mission statement vision business model
                products services offerings value proposition features
                technology platform architecture infrastructure solution
                go-to-market GTM sales strategy distribution channels
                partnerships integrations customers clients use cases
                problem solving pain points target audience
            """,
            "team": """
                founders CEO CTO CFO COO chief executive technology financial
                operating officer management team employees headcount
                advisors advisory board members directors backgrounds
                experience expertise previous companies exits acquisitions
                LinkedIn education degrees universities credentials
                domain knowledge industry veterans leadership
            """,
        }

        # Pre-compute intent embeddings (cached for efficiency)
        self._intent_embeddings = None
        self._embedding_cost = 0.0
        self._total_tokens = 0
        self._routing_stats = defaultdict(int)

        # Routing parameters
        self.top_k_per_chunk = 2  # Route each chunk to top 2 most relevant extractors
        self.min_similarity_threshold = 0.40  # Minimum similarity to consider (lowered from 0.55 for better recall)
        
        # Critical extractors that need minimum chunks for quality
        self.critical_extractors = ["financial", "progress"]
        self.min_chunks_per_critical = 2  # Ensure critical extractors get at least 2 chunks

        print(f"🧭 Semantic Router initialized with {self.embedding_model}", flush=True)
        print(f"   Routing strategy: top-{self.top_k_per_chunk} extractors per chunk", flush=True)
        print(f"   Minimum similarity threshold: {self.min_similarity_threshold}", flush=True)

    async def route_chunks(
        self, documents: List[Document]
    ) -> Dict[str, List[Document]]:
        """
        Route chunks to relevant extractors using semantic similarity.

        Args:
            documents: List of document chunks to route

        Returns:
            Dict mapping extractor names to their assigned chunks
        """
        if not documents:
            print("  ⚠ No documents to route")
            return {name: [] for name in self.extractor_intents.keys()}

        start_time = time.time()
        print(f"\n🧭 Routing {len(documents)} chunks to extractors...", flush=True)

        # Step 1: Ensure intent embeddings are computed
        if self._intent_embeddings is None:
            print("  Computing intent embeddings...", flush=True)
            intent_start = time.time()
            self._intent_embeddings = await self._compute_intent_embeddings()
            intent_time = time.time() - intent_start
            print(f"  ✓ Intent embeddings computed in {intent_time:.2f}s", flush=True)

        # Step 2: Compute embeddings for all chunks
        print(f"  Computing embeddings for {len(documents)} chunks...", flush=True)
        embed_start = time.time()
        chunk_texts = [doc.page_content for doc in documents]
        chunk_embeddings = await self._embed_texts(chunk_texts)
        embed_time = time.time() - embed_start
        print(f"  ✓ Chunk embeddings computed in {embed_time:.2f}s", flush=True)

        # Step 3: Route each chunk to relevant extractors
        print("  Calculating similarities and routing...", flush=True)
        routed_chunks = defaultdict(list)
        routing_details = []
        unmatched_chunks = []  # Track chunks that don't match any extractor above threshold

        for idx, (doc, chunk_emb) in enumerate(zip(documents, chunk_embeddings)):
            # Calculate similarity with each extractor intent
            similarities = {}
            for extractor_name, intent_emb in self._intent_embeddings.items():
                sim = self._cosine_similarity(chunk_emb, intent_emb)
                similarities[extractor_name] = sim

            # Route to top-k most similar extractors above threshold
            sorted_extractors = sorted(
                similarities.items(), key=lambda x: x[1], reverse=True
            )

            assigned = []
            chunk_matched = False
            for extractor_name, similarity in sorted_extractors[:self.top_k_per_chunk]:
                if similarity >= self.min_similarity_threshold:
                    routed_chunks[extractor_name].append(doc)
                    assigned.append(f"{extractor_name}({similarity:.2f})")
                    self._routing_stats[extractor_name] += 1
                    chunk_matched = True
            
            # Fallback: If chunk didn't match any extractor above threshold, route to top extractor anyway
            if not chunk_matched and sorted_extractors:
                top_extractor, top_similarity = sorted_extractors[0]
                routed_chunks[top_extractor].append(doc)
                assigned.append(f"{top_extractor}({top_similarity:.2f}, fallback)")
                self._routing_stats[top_extractor] += 1
                unmatched_chunks.append((idx, top_extractor, top_similarity))
                chunk_matched = True

            # Log routing decision for first few chunks (for debugging)
            if idx < 5:  # Show more chunks for better visibility
                source_file = doc.metadata.get("source_file", "unknown")
                preview = doc.page_content[:80].replace("\n", " ")
                all_similarities = ", ".join([f"{k}:{v:.2f}" for k, v in sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]])
                routing_details.append(
                    f"    Chunk {idx+1} [{source_file}]: '{preview}...'\n"
                    f"       → Similarities: {all_similarities}\n"
                    f"       → Routed to: {', '.join(assigned) if assigned else 'none (below threshold)'}"
                )

        # Print sample routing decisions
        if routing_details:
            print("\n  Sample routing decisions:", flush=True)
            for detail in routing_details:
                print(detail, flush=True)

        # Step 4: Ensure minimum chunks for critical extractors
        # This guarantees quality by ensuring critical extractors get enough content
        if len(documents) >= self.min_chunks_per_critical:
            for critical_extractor in self.critical_extractors:
                current_count = len(routed_chunks[critical_extractor])
                if current_count < self.min_chunks_per_critical:
                    # Find chunks not yet assigned to this extractor
                    all_assigned_chunks = set()
                    for chunks in routed_chunks.values():
                        all_assigned_chunks.update(chunks)
                    
                    unassigned_chunks = [doc for doc in documents if doc not in all_assigned_chunks]
                    if not unassigned_chunks:
                        # If all chunks are assigned, find chunks with reasonable similarity to critical extractor
                        # and reassign to critical extractor
                        for doc, chunk_emb in zip(documents, chunk_embeddings):
                            if doc not in routed_chunks[critical_extractor]:
                                # Calculate similarity to critical extractor
                                critical_sim = self._cosine_similarity(
                                    chunk_emb, 
                                    self._intent_embeddings[critical_extractor]
                                )
                                # Add if similarity is reasonable (even if below threshold)
                                if critical_sim >= 0.30:  # Lower threshold for guarantee
                                    routed_chunks[critical_extractor].append(doc)
                                    # Check if we've reached minimum
                                    if len(routed_chunks[critical_extractor]) >= self.min_chunks_per_critical:
                                        break
                    else:
                        # Use unassigned chunks first
                        needed = self.min_chunks_per_critical - current_count
                        for doc in unassigned_chunks[:needed]:
                            routed_chunks[critical_extractor].append(doc)
                    
                    added = len(routed_chunks[critical_extractor]) - current_count
                    if added > 0:
                        print(f"  ⚡ Guaranteed {added} additional chunk(s) for {critical_extractor} (minimum quality requirement)", flush=True)

        # Print routing distribution
        total_assignments = sum(len(chunks) for chunks in routed_chunks.values())
        print(f"\n  📊 Routing Distribution:", flush=True)
        for extractor_name in sorted(self.extractor_intents.keys()):
            chunk_count = len(routed_chunks[extractor_name])
            percentage = (chunk_count / len(documents) * 100) if documents else 0
            guarantee_marker = " ⚡" if extractor_name in self.critical_extractors and chunk_count >= self.min_chunks_per_critical else ""
            print(f"     {extractor_name:12} → {chunk_count:3} chunks ({percentage:.1f}%){guarantee_marker}", flush=True)

        # Log fallback routing stats
        if unmatched_chunks:
            print(f"  📋 Fallback routing: {len(unmatched_chunks)} chunks routed to best match (below threshold)", flush=True)

        # Calculate efficiency metrics
        baseline_calls = len(documents) * len(self.extractor_intents)
        actual_calls = total_assignments
        reduction_pct = ((baseline_calls - actual_calls) / baseline_calls * 100) if baseline_calls > 0 else 0

        elapsed = time.time() - start_time

        print(f"\n  ✓ Routing complete in {elapsed:.2f}s", flush=True)
        print(f"  📉 Efficiency: {actual_calls} assignments vs {baseline_calls} baseline", flush=True)
        print(f"     ({reduction_pct:.1f}% reduction in API calls)", flush=True)
        print(f"  💰 Routing cost: ~${self._embedding_cost:.4f}", flush=True)
        print(f"     ({self._total_tokens:,} tokens embedded)", flush=True)

        # Convert defaultdict to regular dict with all extractors
        result = {name: routed_chunks.get(name, []) for name in self.extractor_intents.keys()}

        return result

    async def _compute_intent_embeddings(self) -> Dict[str, List[float]]:
        """Pre-compute embeddings for extractor intents"""
        intent_texts = list(self.extractor_intents.values())
        embeddings = await self._embed_texts(intent_texts)

        return {
            name: emb
            for name, emb in zip(self.extractor_intents.keys(), embeddings)
        }

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed texts using OpenAI's embedding API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Count tokens for cost estimation
        total_tokens = sum(len(self.tokenizer.encode(text)) for text in texts)
        self._total_tokens += total_tokens

        # OpenAI pricing: $0.00002 per 1K tokens for text-embedding-3-small
        cost = (total_tokens / 1000) * 0.00002
        self._embedding_cost += cost

        # Rate limiting: respect 3 RPM limit (20 seconds between requests)
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            print(f"  ⏳ Rate limiting: waiting {wait_time:.1f}s to respect 3 RPM limit...")
            await asyncio.sleep(wait_time)
        
        # Batch embed with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._last_request_time = time.time()
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts,
                )

                embeddings = [item.embedding for item in response.data]
                return embeddings

            except Exception as e:
                error_str = str(e).lower()
                # For rate limit errors, wait longer (respect 3 RPM = 20s)
                if '429' in str(e) or 'rate' in error_str or 'quota' in error_str:
                    wait_time = 20.0 if attempt == 0 else (2 ** attempt) * 10
                    if attempt < max_retries - 1:
                        print(f"  ⚠ Rate limit hit (attempt {attempt + 1}/{max_retries}): {e}")
                        print(f"     Waiting {wait_time:.1f}s to respect 3 RPM limit...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"  ✗ Embedding API failed after {max_retries} attempts: {e}")
                        raise
                elif attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  ⚠ Embedding API error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"     Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"  ✗ Embedding API failed after {max_retries} attempts: {e}")
                    raise

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        # Convert to numpy arrays for efficient computation
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Cosine similarity = dot product / (magnitude1 * magnitude2)
        dot_product = np.dot(v1, v2)
        magnitude1 = np.linalg.norm(v1)
        magnitude2 = np.linalg.norm(v2)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return float(dot_product / (magnitude1 * magnitude2))

    def get_routing_stats(self) -> Dict[str, any]:
        """Get statistics about routing performance"""
        return {
            "total_tokens": self._total_tokens,
            "total_cost": self._embedding_cost,
            "assignments_per_extractor": dict(self._routing_stats),
        }


