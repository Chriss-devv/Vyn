"""
VYN v1.0 - Memory Manager
Long-term memory using SQLite for conversation history and learned patterns.
"""

import logging
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages long-term memory storage for VYN using SQLite.
    Stores conversations, learned patterns, and user preferences.
    """
    
    DB_PATH = "/mnt/ollama_storage/vyn_brain.db"
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DB_PATH
        self._ensure_db_directory()
        self.connection = None
        self.initialize_database()
    
    def _ensure_db_directory(self):
        """Ensures database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize_database(self):
        """Creates database tables if they don't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    model_used TEXT,
                    context_type TEXT,
                    intent TEXT
                )
            ''')
            
            # Learned patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data JSON NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key TEXT UNIQUE NOT NULL,
                    preference_value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_learned_patterns_type 
                ON learned_patterns(pattern_type)
            ''')
            
            self.connection.commit()
            logger.info(f"[VYN] Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"[VYN] Database initialization failed: {e}")
    
    def log_conversation(
        self,
        user_input: str,
        assistant_response: str,
        model_used: str,
        context_type: str = "general",
        intent: str = "general"
    ):
        """
        Logs a conversation exchange.
        
        Args:
            user_input: User's input
            assistant_response: VYN's response
            model_used: Which model generated the response
            context_type: Type of conversation
            intent: Detected intent
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO conversations 
                (user_input, assistant_response, model_used, context_type, intent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_input, assistant_response, model_used, context_type, intent))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"[VYN] Failed to log conversation: {e}")
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """
        Retrieves recent conversation history.
        
        Args:
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversation dicts
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id, timestamp, user_input, assistant_response, 
                       model_used, context_type, intent
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'user_input': row[2],
                    'assistant_response': row[3],
                    'model_used': row[4],
                    'context_type': row[5],
                    'intent': row[6]
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"[VYN] Failed to retrieve conversations: {e}")
            return []
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Searches conversation history for relevant context.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching conversations
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id, timestamp, user_input, assistant_response, 
                       model_used, context_type, intent
                FROM conversations
                WHERE user_input LIKE ? OR assistant_response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'user_input': row[2],
                    'assistant_response': row[3],
                    'model_used': row[4],
                    'context_type': row[5],
                    'intent': row[6]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"[VYN] Conversation search failed: {e}")
            return []
    
    def learn_pattern(self, pattern_type: str, pattern_data: Dict):
        """
        Stores or updates a learned pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "common_query", "preferred_model")
            pattern_data: Pattern data as dict
        """
        try:
            cursor = self.connection.cursor()
            pattern_json = json.dumps(pattern_data)
            
            # Check if pattern exists
            cursor.execute('''
                SELECT id, frequency FROM learned_patterns
                WHERE pattern_type = ? AND pattern_data = ?
            ''', (pattern_type, pattern_json))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency and last_used
                cursor.execute('''
                    UPDATE learned_patterns
                    SET frequency = frequency + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (existing[0],))
            else:
                # Insert new pattern
                cursor.execute('''
                    INSERT INTO learned_patterns (pattern_type, pattern_data)
                    VALUES (?, ?)
                ''', (pattern_type, pattern_json))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"[VYN] Failed to learn pattern: {e}")
    
    def get_patterns(self, pattern_type: str, limit: int = 10) -> List[Dict]:
        """
        Retrieves learned patterns of a specific type.
        
        Args:
            pattern_type: Type of patterns to retrieve
            limit: Maximum number of patterns
            
        Returns:
            List of pattern dicts
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id, pattern_data, frequency, last_used
                FROM learned_patterns
                WHERE pattern_type = ?
                ORDER BY frequency DESC, last_used DESC
                LIMIT ?
            ''', (pattern_type, limit))
            
            rows = cursor.fetchall()
            
            patterns = []
            for row in rows:
                patterns.append({
                    'id': row[0],
                    'data': json.loads(row[1]),
                    'frequency': row[2],
                    'last_used': row[3]
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"[VYN] Failed to retrieve patterns: {e}")
            return []
    
    def set_preference(self, key: str, value: str):
        """
        Sets a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (preference_key, preference_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"[VYN] Failed to set preference: {e}")
    
    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Gets a user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT preference_value FROM user_preferences
                WHERE preference_key = ?
            ''', (key,))
            
            result = cursor.fetchone()
            return result[0] if result else default
            
        except Exception as e:
            logger.error(f"[VYN] Failed to get preference: {e}")
            return default
    
    def close(self):
        """Closes database connection"""
        if self.connection:
            self.connection.close()
            logger.info("[VYN] Database connection closed")
