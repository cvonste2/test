"""
Google Drive uploader for saving transcripts.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token file
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GDriveUploader:
    """Client for uploading files to Google Drive."""

    def __init__(self, credentials_file: str, token_file: str, root_folder_name: str):
        """
        Initialize Google Drive uploader.

        Args:
            credentials_file: Path to Google Drive credentials JSON
            token_file: Path to store OAuth token
            root_folder_name: Name of the root folder in Google Drive
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.root_folder_name = root_folder_name
        self.service = None
        self.root_folder_id = None
        self.year_folder_cache: Dict[str, str] = {}  # Cache for year folder IDs

    def authenticate(self) -> None:
        """Authenticate with Google Drive API using OAuth."""
        creds = None

        # Check if token file exists
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        f"Please download it from Google Cloud Console"
                    )

                logger.info("Starting OAuth flow for new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Saved credentials to {self.token_file}")

        # Build the Drive service
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Successfully authenticated with Google Drive")

        # Get or create root folder
        self._ensure_root_folder()

    def _ensure_root_folder(self) -> None:
        """Ensure the root folder exists, create if it doesn't."""
        try:
            # Search for existing folder
            query = f"name='{self.root_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if files:
                self.root_folder_id = files[0]['id']
                logger.info(f"Found existing root folder: {self.root_folder_name} (ID: {self.root_folder_id})")
            else:
                # Create root folder
                file_metadata = {
                    'name': self.root_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                self.root_folder_id = folder.get('id')
                logger.info(f"Created root folder: {self.root_folder_name} (ID: {self.root_folder_id})")

        except HttpError as error:
            logger.error(f"Failed to ensure root folder: {error}")
            raise

    def _get_or_create_year_folder(self, year: str) -> str:
        """
        Get or create a year folder within the root folder.

        Args:
            year: Year as string (e.g., "2025")

        Returns:
            Folder ID for the year folder
        """
        # Check cache first
        if year in self.year_folder_cache:
            return self.year_folder_cache[year]

        try:
            # Search for existing year folder
            query = (
                f"name='{year}' and "
                f"'{self.root_folder_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if files:
                folder_id = files[0]['id']
                logger.info(f"Found existing year folder: {year}")
            else:
                # Create year folder
                file_metadata = {
                    'name': year,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.root_folder_id]
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                folder_id = folder.get('id')
                logger.info(f"Created year folder: {year}")

            # Cache the folder ID
            self.year_folder_cache[year] = folder_id
            return folder_id

        except HttpError as error:
            logger.error(f"Failed to get/create year folder {year}: {error}")
            raise

    def file_exists(self, filename: str, year: str) -> bool:
        """
        Check if a file already exists in the year folder.

        Args:
            filename: Name of the file to check
            year: Year folder to check in

        Returns:
            True if file exists, False otherwise
        """
        try:
            year_folder_id = self._get_or_create_year_folder(year)

            query = (
                f"name='{filename}' and "
                f"'{year_folder_id}' in parents and "
                f"trashed=false"
            )
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            exists = len(files) > 0

            if exists:
                logger.debug(f"File exists in Drive: {filename}")
            return exists

        except HttpError as error:
            logger.error(f"Failed to check file existence: {error}")
            return False

    def upload_file(self, local_path: str, filename: str, year: str) -> Optional[str]:
        """
        Upload a file to Google Drive.

        Args:
            local_path: Local path to the file
            filename: Name for the file in Google Drive
            year: Year folder to upload to

        Returns:
            File ID in Google Drive, or None if upload failed
        """
        try:
            # Get or create year folder
            year_folder_id = self._get_or_create_year_folder(year)

            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [year_folder_id]
            }

            # Upload file
            media = MediaFileUpload(local_path, mimetype='text/plain', resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get('id')
            logger.info(f"Successfully uploaded {filename} to Google Drive (ID: {file_id})")
            return file_id

        except HttpError as error:
            logger.error(f"Failed to upload file {filename}: {error}")
            return None
        except Exception as error:
            logger.error(f"Unexpected error uploading file {filename}: {error}")
            return None

    def test_connection(self) -> bool:
        """
        Test the connection to Google Drive.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get info about the root folder
            about = self.service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            logger.info(f"Successfully connected to Google Drive as {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Drive: {e}")
            return False
