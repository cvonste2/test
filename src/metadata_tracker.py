"""
Metadata tracker for managing downloaded transcripts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class MetadataTracker:
    """Tracks which transcripts have been downloaded."""

    def __init__(self, metadata_file: str):
        """
        Initialize metadata tracker.

        Args:
            metadata_file: Path to JSON file storing metadata
        """
        self.metadata_file = metadata_file
        self.data: Dict = {}
        self._load()

    def _load(self) -> None:
        """Load metadata from file."""
        if Path(self.metadata_file).exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded metadata from {self.metadata_file}")
            except Exception as e:
                logger.warning(f"Failed to load metadata file: {e}. Starting fresh.")
                self.data = {'downloads': {}, 'last_updated': None}
        else:
            logger.info("No existing metadata file found. Starting fresh.")
            self.data = {'downloads': {}, 'last_updated': None}

    def _save(self) -> None:
        """Save metadata to file."""
        try:
            self.data['last_updated'] = datetime.now().isoformat()
            with open(self.metadata_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.debug(f"Saved metadata to {self.metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def is_downloaded(self, transcript_id: str) -> bool:
        """
        Check if a transcript has been downloaded.

        Args:
            transcript_id: ID of the transcript

        Returns:
            True if already downloaded, False otherwise
        """
        return transcript_id in self.data.get('downloads', {})

    def mark_downloaded(
        self,
        transcript_id: str,
        filename: str,
        title: str,
        date: datetime,
        drive_file_id: Optional[str] = None
    ) -> None:
        """
        Mark a transcript as downloaded.

        Args:
            transcript_id: ID of the transcript
            filename: Filename used for the transcript
            title: Meeting title
            date: Meeting date
            drive_file_id: Google Drive file ID (if uploaded)
        """
        if 'downloads' not in self.data:
            self.data['downloads'] = {}

        self.data['downloads'][transcript_id] = {
            'filename': filename,
            'title': title,
            'date': date.isoformat(),
            'downloaded_at': datetime.now().isoformat(),
            'drive_file_id': drive_file_id
        }
        self._save()
        logger.info(f"Marked transcript {transcript_id} as downloaded")

    def get_downloaded_ids(self) -> Set[str]:
        """
        Get set of all downloaded transcript IDs.

        Returns:
            Set of transcript IDs
        """
        return set(self.data.get('downloads', {}).keys())

    def get_download_info(self, transcript_id: str) -> Optional[Dict]:
        """
        Get download information for a specific transcript.

        Args:
            transcript_id: ID of the transcript

        Returns:
            Dictionary with download info, or None if not found
        """
        return self.data.get('downloads', {}).get(transcript_id)

    def get_stats(self) -> Dict:
        """
        Get statistics about downloads.

        Returns:
            Dictionary with stats
        """
        downloads = self.data.get('downloads', {})
        return {
            'total_downloads': len(downloads),
            'last_updated': self.data.get('last_updated'),
            'oldest_download': min(
                (d['downloaded_at'] for d in downloads.values()),
                default=None
            ),
            'newest_download': max(
                (d['downloaded_at'] for d in downloads.values()),
                default=None
            )
        }
