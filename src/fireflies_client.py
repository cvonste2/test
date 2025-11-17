"""
Fireflies.ai API client for downloading transcripts.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FirefliesClient:
    """Client for interacting with Fireflies.ai API."""

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize Fireflies client.

        Args:
            api_key: Fireflies API key
            base_url: Base URL for Fireflies API
        """
        self.api_key = api_key
        self.base_url = base_url
        logger.info("Fireflies client initialized")

    def get_transcripts(self, days_back: int = 30) -> List[Dict]:
        """
        Retrieve transcripts from Fireflies.

        Args:
            days_back: Number of days to look back for transcripts

        Returns:
            List of transcript metadata
        """
        # TODO: Implement GraphQL query to fetch transcripts
        logger.info(f"Fetching transcripts from last {days_back} days")
        return []

    def download_transcript(self, transcript_id: str, format: str = 'txt') -> str:
        """
        Download a specific transcript.

        Args:
            transcript_id: ID of the transcript to download
            format: Output format (txt, pdf, json)

        Returns:
            Transcript content as string
        """
        # TODO: Implement transcript download
        logger.info(f"Downloading transcript {transcript_id} in {format} format")
        return ""
