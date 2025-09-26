import re
import html
from typing import Optional

class InputSanitizer:
    """Utility class for sanitizing user inputs"""
    
    # Common spam patterns
    SPAM_PATTERNS = [
        r'https?://[^\s]+',  # URLs
        r'www\.[^\s]+',      # www links
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
        r'\b\d{10,}\b',      # Phone numbers (10+ digits)
        r'[^\w\s.,!?\-]',    # Special characters except basic punctuation
    ]
    
    # Allowed characters for names (letters, spaces, hyphens, apostrophes)
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\'\.]+$')
    
    # Allowed characters for bio/description (letters, numbers, spaces, basic punctuation)
    BIO_PATTERN = re.compile(r'^[a-zA-Z0-9\s.,!?\-\(\)]+$')
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize user name input"""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Check if name contains only allowed characters
        if not InputSanitizer.NAME_PATTERN.match(name):
            # Remove invalid characters
            name = re.sub(r'[^a-zA-Z\s\-\'\.]', '', name)
        
        # Limit length
        name = name[:50]
        
        return name.strip()
    
    @staticmethod
    def sanitize_bio(bio: str) -> str:
        """Sanitize user bio/description input"""
        if not bio:
            return ""
        
        # Remove extra whitespace
        bio = ' '.join(bio.split())
        
        # Check for spam patterns
        for pattern in InputSanitizer.SPAM_PATTERNS:
            bio = re.sub(pattern, '[REDACTED]', bio, flags=re.IGNORECASE)
        
        # Check if bio contains only allowed characters
        if not InputSanitizer.BIO_PATTERN.match(bio):
            # Remove invalid characters but keep basic punctuation
            bio = re.sub(r'[^a-zA-Z0-9\s.,!?\-\(\)]', '', bio)
        
        # Limit length
        bio = bio[:500]
        
        return bio.strip()
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """General text sanitization"""
        if not text:
            return ""
        
        # HTML escape
        text = html.escape(text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Check for spam patterns
        for pattern in InputSanitizer.SPAM_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        # Limit length
        text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def is_spam(text: str) -> bool:
        """Check if text contains spam patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for common spam keywords
        spam_keywords = [
            'click here', 'buy now', 'free money', 'earn money',
            'work from home', 'make money', 'get rich', 'investment',
            'loan', 'credit', 'debt', 'insurance', 'casino', 'gambling'
        ]
        
        for keyword in spam_keywords:
            if keyword in text_lower:
                return True
        
        # Check for excessive repetition
        words = text.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word.lower()] = word_counts.get(word.lower(), 0) + 1
            
            # If any word appears more than 30% of the time, it's likely spam
            max_repetition = max(word_counts.values()) if word_counts else 0
            if max_repetition > len(words) * 0.3:
                return True
        
        return False
