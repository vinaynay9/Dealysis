"""
Semantic router for intelligently routing document chunks to relevant extractors.
Uses embeddings to match chunks with extractor intents, reducing unnecessary API calls.
"""

import os
import asyncio
import time
import tiktoken
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
        self.min_similarity_threshold = 0.55  # Minimum similarity to consider

        print(f"🧭 Semantic Router initialized with {self.embedding_model}")
        print(f"   Routing strategy: top-{self.top_k_per_chunk} extractors per chunk")
        print(f"   Minimum similarity threshold: {self.min_similarity_threshold}")

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
        print(f"\n🧭 Routing {len(documents)} chunks to extractors...")

        # Step 1: Ensure intent embeddings are computed
        if self._intent_embeddings is None:
            print("  Computing intent embeddings...")
            intent_start = time.time()
            self._intent_embeddings = await self._compute_intent_embeddings()
            intent_time = time.time() - intent_start
            print(f"  ✓ Intent embeddings computed in {intent_time:.2f}s")

        # Step 2: Compute embeddings for all chunks
        print(f"  Computing embeddings for {len(documents)} chunks...")
        embed_start = time.time()
        chunk_texts = [doc.page_content for doc in documents]
        chunk_embeddings = await self._embed_texts(chunk_texts)
        embed_time = time.time() - embed_start
        print(f"  ✓ Chunk embeddings computed in {embed_time:.2f}s")

        # Step 3: Route each chunk to relevant extractors
        print("  Calculating similarities and routing...")
        routed_chunks = defaultdict(list)
        routing_details = []

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
            for extractor_name, similarity in sorted_extractors[:self.top_k_per_chunk]:
                if similarity >= self.min_similarity_threshold:
                    routed_chunks[extractor_name].append(doc)
                    assigned.append(f"{extractor_name}({similarity:.2f})")
                    self._routing_stats[extractor_name] += 1

            # Log routing decision for first few chunks (for debugging)
            if idx < 3:
                source_file = doc.metadata.get("source_file", "unknown")
                preview = doc.page_content[:80].replace("\n", " ")
                routing_details.append(
                    f"    Chunk {idx+1} [{source_file}]: '{preview}...'\n"
                    f"       → Routed to: {', '.join(assigned) if assigned else 'none (below threshold)'}"
                )

        # Print sample routing decisions
        if routing_details:
            print("\n  Sample routing decisions:")
            for detail in routing_details:
                print(detail)

        # Print routing distribution
        total_assignments = sum(len(chunks) for chunks in routed_chunks.values())
        print(f"\n  📊 Routing Distribution:")
        for extractor_name in sorted(self.extractor_intents.keys()):
            chunk_count = len(routed_chunks[extractor_name])
            percentage = (chunk_count / len(documents) * 100) if documents else 0
            print(f"     {extractor_name:12} → {chunk_count:3} chunks ({percentage:.1f}%)")

        # Calculate efficiency metrics
        baseline_calls = len(documents) * len(self.extractor_intents)
        actual_calls = total_assignments
        reduction_pct = ((baseline_calls - actual_calls) / baseline_calls * 100) if baseline_calls > 0 else 0

        elapsed = time.time() - start_time

        print(f"\n  ✓ Routing complete in {elapsed:.2f}s")
        print(f"  📉 Efficiency: {actual_calls} assignments vs {baseline_calls} baseline")
        print(f"     ({reduction_pct:.1f}% reduction in API calls)")
        print(f"  💰 Routing cost: ~${self._embedding_cost:.4f}")
        print(f"     ({self._total_tokens:,} tokens embedded)")

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

        # Batch embed with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts,
                )

                embeddings = [item.embedding for item in response.data]
                return embeddings

            except Exception as e:
                if attempt < max_retries - 1:
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


