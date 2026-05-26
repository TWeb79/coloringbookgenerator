"""Content safety filter for child-appropriate content"""
import re
from typing import List, Optional


class ContentFilter:
    """Filter for validating child-appropriate content."""

    # Inappropriate content patterns (case-insensitive)
    BLOCKED_PATTERNS = [
        # Violence
        r'\b(weapon|gun|pistol|rifle|shotgun|knife|sword|axe|murder|killed?|death|dying|dead\b)',
        # Adult content
        r'\b(sex|nude|naked|adult|blood|gore|graphic|explicit)\b',
        # Drugs/alcohol
        r'\b(drug|cocaine|heroin|marijuana|alcohol|drunk|smoking|cigarette)\b',
        # Fear-inducing content
        r'\b(ghost|haunted|monster|scary|horror|terrify|nightmare)\b',
        # Inappropriate language
        r'\b(hate|stupid|idiot|dumb|ugly|loser)\b',
    ]

    # Patterns that should trigger re-generation (not just warning)
    CRITICAL_PATTERNS = [
        r'\b(weapon|gun|pistol|rifle|shotgun|knife|sword|axe)\b',
        r'\b(sex|nude|naked|adult)\b',
        r'\b(drug|cocaine|heroin|marijuana)\b',
        r'\b(murder|killed?|death|dying)\b',
    ]

    def __init__(self, custom_blocked_patterns: Optional[List[str]] = None,
                 custom_critical_patterns: Optional[List[str]] = None):
        """Initialize content filter with optional custom patterns."""
        self.blocked_patterns = [
            re.compile(p, re.IGNORECASE) for p in (custom_blocked_patterns or self.BLOCKED_PATTERNS)
        ]
        self.critical_patterns = [
            re.compile(p, re.IGNORECASE) for p in (custom_critical_patterns or self.CRITICAL_PATTERNS)
        ]

    def check_text(self, text: str) -> tuple[bool, List[str]]:
        """Check text for inappropriate content.

        Args:
            text: The text to check

        Returns:
            Tuple of (is_safe, list of matched patterns)
        """
        if not text:
            return True, []

        matched_patterns = []
        for pattern in self.blocked_patterns:
            if pattern.search(text):
                matched_patterns.append(pattern.pattern)

        return len(matched_patterns) == 0, matched_patterns

    def is_critical(self, text: str) -> bool:
        """Check if text contains critical inappropriate content.

        Args:
            text: The text to check

        Returns:
            True if critical content is found
        """
        if not text:
            return False

        for pattern in self.critical_patterns:
            if pattern.search(text):
                return True

        return False

    def sanitize_text(self, text: str) -> str:
        """Remove or replace inappropriate content markers.

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return text

        sanitized = text
        for pattern in self.blocked_patterns:
            sanitized = pattern.sub('[content removed]', sanitized)

        return sanitized


# Global instance for easy import
content_filter = ContentFilter()