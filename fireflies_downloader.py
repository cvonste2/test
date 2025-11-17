#!/usr/bin/env python3
"""
Fireflies Transcript Downloader
Downloads transcripts from Fireflies.ai and uploads them to Google Drive.
"""

import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Download Fireflies transcripts to Google Drive'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.ini',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("Starting Fireflies Transcript Downloader")

    # TODO: Implement Fireflies API client
    # TODO: Implement Google Drive uploader
    # TODO: Implement main download loop

    logger.info("Process completed successfully")


if __name__ == '__main__':
    main()
