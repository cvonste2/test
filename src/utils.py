"""
Utility functions for the Fireflies downloader.
"""

import re
from datetime import datetime
from typing import List


def sanitize_filename(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for use in filenames.

    - Replaces spaces with underscores
    - Removes special characters (keeps only alphanumeric and underscores)
    - Truncates to max_length

    Args:
        text: The text to sanitize
        max_length: Maximum length for the result

    Returns:
        Sanitized string safe for use in filenames
    """
    # Replace spaces with underscores
    text = text.replace(' ', '_')

    # Remove any character that's not alphanumeric or underscore
    text = re.sub(r'[^\w]', '', text)

    # Remove multiple consecutive underscores
    text = re.sub(r'_+', '_', text)

    # Remove leading/trailing underscores
    text = text.strip('_')

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rstrip('_')

    return text


def generate_transcript_filename(
    date: datetime,
    title: str,
    participants: List[str],
    max_participants: int = 5,
    max_length: int = 200
) -> str:
    """
    Generate standardized filename for transcript.

    Format: yyyyMMdd_meeting_title_participant1_participant2_..._fireflies_transcript.txt

    Args:
        date: Meeting date
        title: Meeting title
        participants: List of participant names
        max_participants: Maximum number of participants to include
        max_length: Maximum total filename length

    Returns:
        Formatted filename
    """
    # Format date as yyyyMMdd
    date_str = date.strftime('%Y%m%d')

    # Sanitize title
    title_clean = sanitize_filename(title, max_length=100)

    # Sanitize and limit participants
    participants_clean = [
        sanitize_filename(p, max_length=50)
        for p in participants[:max_participants]
    ]

    # Build filename parts
    parts = [date_str, title_clean] + participants_clean + ['fireflies_transcript']

    # Join with underscores
    filename = '_'.join(parts) + '.txt'

    # Ensure total length doesn't exceed max_length
    if len(filename) > max_length:
        # Truncate title or participants to fit
        available_length = max_length - len(date_str) - len('_fireflies_transcript.txt') - 10
        title_clean = title_clean[:available_length // 2]
        participants_clean = participants_clean[:2]  # Keep only first 2 participants

        parts = [date_str, title_clean] + participants_clean + ['fireflies_transcript']
        filename = '_'.join(parts) + '.txt'

    return filename


def format_date_for_display(date: datetime) -> str:
    """Format date for user-friendly display."""
    return date.strftime('%Y-%m-%d %H:%M')


def get_year_from_date(date: datetime) -> str:
    """Extract year as string from datetime."""
    return str(date.year)
