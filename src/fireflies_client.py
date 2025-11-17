"""
Fireflies.ai API client for downloading transcripts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

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
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize GraphQL client with authentication."""
        try:
            transport = RequestsHTTPTransport(
                url=self.base_url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                verify=True,
                retries=3,
            )
            self.client = Client(transport=transport, fetch_schema_from_transport=False)
            logger.info("Fireflies client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Fireflies client: {e}")
            raise

    def get_transcripts(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve transcripts from Fireflies.

        Args:
            limit: Maximum number of transcripts to fetch

        Returns:
            List of transcript metadata dictionaries with keys:
                - id: Transcript ID
                - title: Meeting title
                - date: Meeting date (datetime)
                - participants: List of participant names
                - duration: Meeting duration in minutes
        """
        query = gql("""
            query GetTranscripts($limit: Int!) {
                transcripts(limit: $limit) {
                    id
                    title
                    date
                    participants {
                        name
                    }
                    duration
                    transcript_url
                }
            }
        """)

        try:
            logger.info(f"Fetching up to {limit} transcripts from Fireflies")
            result = self.client.execute(query, variable_values={'limit': limit})

            transcripts = []
            for item in result.get('transcripts', []):
                # Parse date
                date = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))

                # Extract participant names
                participants = [p['name'] for p in item.get('participants', [])]

                transcripts.append({
                    'id': item['id'],
                    'title': item.get('title', 'Untitled Meeting'),
                    'date': date,
                    'participants': participants,
                    'duration': item.get('duration', 0),
                    'transcript_url': item.get('transcript_url', '')
                })

            logger.info(f"Successfully fetched {len(transcripts)} transcripts")
            return transcripts

        except Exception as e:
            logger.error(f"Failed to fetch transcripts: {e}")
            raise

    def get_transcript_content(self, transcript_id: str) -> str:
        """
        Download the full transcript content.

        Args:
            transcript_id: ID of the transcript to download

        Returns:
            Transcript content as plain text
        """
        query = gql("""
            query GetTranscript($transcriptId: String!) {
                transcript(id: $transcriptId) {
                    id
                    title
                    sentences {
                        text
                        speaker_name
                        start_time
                    }
                }
            }
        """)

        try:
            logger.info(f"Downloading transcript content for {transcript_id}")
            result = self.client.execute(query, variable_values={'transcriptId': transcript_id})

            transcript = result.get('transcript', {})
            sentences = transcript.get('sentences', [])

            # Format transcript as speaker: text
            lines = []
            current_speaker = None

            for sentence in sentences:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', '')

                if speaker != current_speaker:
                    lines.append(f"\n{speaker}:")
                    current_speaker = speaker

                lines.append(f"  {text}")

            content = '\n'.join(lines)
            logger.info(f"Successfully downloaded transcript {transcript_id} ({len(content)} characters)")
            return content

        except Exception as e:
            logger.error(f"Failed to download transcript {transcript_id}: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test the connection to Fireflies API.

        Returns:
            True if connection is successful, False otherwise
        """
        query = gql("""
            query {
                user {
                    email
                }
            }
        """)

        try:
            result = self.client.execute(query)
            email = result.get('user', {}).get('email', 'Unknown')
            logger.info(f"Successfully connected to Fireflies API as {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Fireflies API: {e}")
            return False
