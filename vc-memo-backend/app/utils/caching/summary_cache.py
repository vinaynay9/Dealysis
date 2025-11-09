import json
import hashlib
import sqlite3
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from pathlib import Path


class SummaryCache:
    """Caching layer for LLM summaries using SQLite"""
    
    def __init__(self, cache_dir: str = "runtime/cache", db_name: str = "summary_cache.db"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / db_name
        self._init_db()
        self._lock = asyncio.Lock()
        
    def _init_db(self):
        """Initialize SQLite database for caching"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create summaries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                hash TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                metadata TEXT,
                model TEXT NOT NULL,
                prompt_type TEXT NOT NULL,
                token_count INTEGER,
                cost_estimate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON summaries(created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prompt_type ON summaries(prompt_type)
        ''')
        
        conn.commit()
        conn.close()
        
    def _generate_cache_key(self, text: str, prompt_type: str, model: str) -> str:
        """Generate unique cache key from text content, prompt type, and model"""
        # Combine text, prompt type, and model for unique hash
        cache_input = f"{text}|{prompt_type}|{model}"
        return hashlib.sha256(cache_input.encode('utf-8')).hexdigest()
    
    async def get_summary(self, text: str, prompt_type: str, model: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached summary if it exists"""
        cache_key = self._generate_cache_key(text, prompt_type, model)
        
        async with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                # Get cached summary and update access stats
                cursor.execute('''
                    UPDATE summaries 
                    SET accessed_at = CURRENT_TIMESTAMP, 
                        access_count = access_count + 1
                    WHERE hash = ?
                    RETURNING summary, metadata, token_count, cost_estimate
                ''', (cache_key,))
                
                row = cursor.fetchone()
                
                if row:
                    conn.commit()
                    return {
                        'summary': row['summary'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'token_count': row['token_count'],
                        'cost_estimate': row['cost_estimate'],
                        'cached': True
                    }
                    
                return None
                
            finally:
                conn.close()
    
    async def store_summary(self, 
                          text: str, 
                          summary: str,
                          prompt_type: str,
                          model: str,
                          metadata: Optional[Dict] = None,
                          token_count: Optional[int] = None,
                          cost_estimate: Optional[float] = None):
        """Store summary in cache"""
        cache_key = self._generate_cache_key(text, prompt_type, model)
        
        async with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO summaries 
                    (hash, summary, metadata, model, prompt_type, token_count, cost_estimate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cache_key,
                    summary,
                    json.dumps(metadata) if metadata else None,
                    model,
                    prompt_type,
                    token_count,
                    cost_estimate
                ))
                
                conn.commit()
                
            finally:
                conn.close()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            try:
                # Total cache entries
                cursor.execute('SELECT COUNT(*) as total FROM summaries')
                total = cursor.fetchone()[0]
                
                # Cache hit rate (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) as recent_accesses 
                    FROM summaries 
                    WHERE accessed_at > datetime('now', '-1 day')
                    AND access_count > 1
                ''')
                recent_hits = cursor.fetchone()[0]
                
                # Total cost saved
                cursor.execute('''
                    SELECT SUM((access_count - 1) * cost_estimate) as cost_saved
                    FROM summaries
                    WHERE cost_estimate IS NOT NULL
                ''')
                cost_saved = cursor.fetchone()[0] or 0.0
                
                # Storage size
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
                
                # Model breakdown
                cursor.execute('''
                    SELECT model, COUNT(*) as count, SUM(cost_estimate) as total_cost
                    FROM summaries
                    GROUP BY model
                ''')
                model_stats = {row[0]: {'count': row[1], 'cost': row[2] or 0} 
                              for row in cursor.fetchall()}
                
                return {
                    'total_entries': total,
                    'recent_cache_hits': recent_hits,
                    'estimated_cost_saved': round(cost_saved, 2),
                    'cache_size_mb': round(db_size, 2),
                    'model_breakdown': model_stats
                }
                
            finally:
                conn.close()
    
    async def cleanup_old_entries(self, days: int = 30):
        """Remove cache entries older than specified days"""
        async with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    DELETE FROM summaries
                    WHERE accessed_at < datetime('now', '-' || ? || ' days')
                    AND access_count < 3
                ''', (days,))
                
                deleted = cursor.rowcount
                conn.commit()
                
                # Vacuum to reclaim space
                cursor.execute('VACUUM')
                
                return deleted
                
            finally:
                conn.close()
    
    async def export_cache(self, export_path: str):
        """Export cache to JSON for backup or analysis"""
        async with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    SELECT * FROM summaries
                    ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                
                export_data = []
                for row in rows:
                    export_data.append({
                        'hash': row['hash'],
                        'summary': row['summary'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else None,
                        'model': row['model'],
                        'prompt_type': row['prompt_type'],
                        'token_count': row['token_count'],
                        'cost_estimate': row['cost_estimate'],
                        'created_at': row['created_at'],
                        'accessed_at': row['accessed_at'],
                        'access_count': row['access_count']
                    })
                
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                return len(export_data)
                
            finally:
                conn.close()
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for a given model and token counts"""
        # Pricing as of 2024 (per 1K tokens)
        pricing = {
            'gpt-4': {'input': 0.01, 'output': 0.03},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
        }
        
        model_pricing = pricing.get(model, pricing['gpt-4o-mini'])
        
        input_cost = (input_tokens / 1000) * model_pricing['input']
        output_cost = (output_tokens / 1000) * model_pricing['output']
        
        return round(input_cost + output_cost, 6)
