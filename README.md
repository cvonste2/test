# Fireflies Transcript Downloader

A Python tool to download meeting transcripts from Fireflies.ai and save them to Google Drive with an enhanced CLI interface.

## Overview

This project helps you automate the process of downloading transcripts from your Fireflies.ai meetings and organizing them in your Google Drive. It features an interactive CLI with transcript selection, duplicate detection, and automatic folder organization by year.

## Features

- **Interactive CLI** - Beautiful terminal interface with transcript selection
- **Smart Duplicate Detection** - Tracks what's already downloaded
- **Auto Organization** - Organizes transcripts by year in Google Drive
- **OAuth Authentication** - One-time setup for both Fireflies and Google Drive
- **Standardized Filenames** - Format: `yyyyMMdd_meeting_title_participants_fireflies_transcript.txt`
- **Error Handling** - User-friendly error messages with retry options
- **Progress Tracking** - Visual progress indicators and download summaries

## Prerequisites

- **Python 3.8+**
- **Fireflies.ai account** with API access
- **Google Cloud Project** with Drive API enabled
- **Google Drive** account

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/cvonste2/test.git
cd test
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

### Step 1: Get Fireflies API Key

1. Log in to [Fireflies.ai](https://app.fireflies.ai)
2. Go to **Settings** → **Integrations**
3. Find **Custom Integrations** or **API Access**
4. Generate a new API key
5. Copy the API key for later use

### Step 2: Set up Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Drive API**:
   - Go to **APIs & Services** → **Library**
   - Search for "Google Drive API"
   - Click **Enable**
4. Create credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Choose **Desktop app** as application type
   - Download the credentials JSON file
   - Save it as `credentials.json` in the project root

### Step 3: Configure the application

1. Copy the example configuration:
   ```bash
   cp config.example.ini config.ini
   ```

2. Edit `config.ini` and fill in your credentials:
   ```ini
   [fireflies]
   api_key = YOUR_FIREFLIES_API_KEY_HERE

   [google_drive]
   credentials_file = credentials.json
   destination_folder_name = Fireflies Transcripts
   ```

## Usage

### Basic Usage

Simply run the application:

```bash
python fireflies_downloader.py
```

### First Run

On first run, you'll need to:

1. **Authenticate with Google Drive** - A browser window will open asking you to authorize the app
2. **Grant permissions** - Allow the app to access your Google Drive
3. The app will save a `token.json` file for future runs (no re-authentication needed)

### Workflow

1. **Connection** - App connects to Fireflies and Google Drive
2. **Fetch Transcripts** - Displays all available transcripts in a table
3. **Select** - Use Space to select transcripts, Enter to confirm
4. **Download** - App downloads and uploads selected transcripts
5. **Summary** - View success/skip/error counts

### Example Output

```
┌─────────────────────────────────────────────────────┐
│   Fireflies Transcript Downloader                   │
│   Download meeting transcripts to Google Drive      │
└─────────────────────────────────────────────────────┘

✓ Connected to Fireflies API
✓ Connected to Google Drive
✓ Loaded download history

                  Available Transcripts (23 found)
#    Date              Title                Participants        Status
1    2025-01-15 14:00  Team Standup         John, Sarah, Mike   Downloaded ✓
2    2025-01-16 10:30  Client Review        Alice, Bob          Not downloaded
3    2025-01-17 15:00  Sprint Planning      Team members        Not downloaded

Select transcripts to download (use Space to select, Enter to confirm):
> [ ] 2025-01-16 Client Review
  [ ] 2025-01-17 Sprint Planning
```

### Advanced Options

```bash
# Verbose logging
python fireflies_downloader.py --verbose

# Custom config file
python fireflies_downloader.py --config /path/to/config.ini
```

## File Organization

Transcripts are automatically organized in Google Drive:

```
Fireflies Transcripts/
├── 2025/
│   ├── 20250115_Team_Standup_John_Smith_Sarah_Jones_fireflies_transcript.txt
│   ├── 20250116_Client_Review_Alice_Brown_Bob_Chen_fireflies_transcript.txt
│   └── 20250117_Sprint_Planning_fireflies_transcript.txt
└── 2024/
    └── 20241220_Year_End_Review_fireflies_transcript.txt
```

### Filename Format

`yyyyMMdd_meeting_title_participant1_participant2_..._fireflies_transcript.txt`

- Date in `yyyyMMdd` format
- Meeting title (sanitized, underscores only)
- Up to 5 participants (configurable)
- Maximum 200 characters (configurable)
- Special characters removed

## Configuration Reference

### config.ini Sections

**[fireflies]**
- `api_key` - Your Fireflies API key
- `api_base_url` - API endpoint (default: https://api.fireflies.ai/graphql)

**[google_drive]**
- `credentials_file` - Path to Google credentials JSON
- `destination_folder_name` - Root folder name in Drive
- `token_file` - OAuth token storage (auto-created)

**[download]**
- `max_participants_in_filename` - Max participants in filename (default: 5)
- `max_filename_length` - Max filename length (default: 200)
- `metadata_file` - Local tracking file (default: .fireflies_metadata.json)

**[logging]**
- `log_level` - INFO, DEBUG, WARNING, ERROR
- `log_file` - Log file path (empty = console only)

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root
- Verify the path in `config.ini`

### "Failed to connect to Fireflies API"
- Check your API key in `config.ini`
- Verify you have an active Fireflies subscription
- Test your API key at https://app.fireflies.ai/integrations

### "Failed to authenticate with Google Drive"
- Delete `token.json` and re-authenticate
- Verify Google Drive API is enabled in Cloud Console
- Check that credentials.json is for a Desktop app

### "No transcripts found"
- Verify you have transcripts in your Fireflies account
- Check that your API key has the correct permissions

## Development

### Project Structure

```
fireflies-downloader/
├── fireflies_downloader.py    # Main CLI application
├── config.example.ini          # Configuration template
├── requirements.txt            # Python dependencies
├── src/
│   ├── __init__.py            # Package init
│   ├── fireflies_client.py    # Fireflies API client
│   ├── gdrive_uploader.py     # Google Drive uploader
│   ├── metadata_tracker.py    # Download tracking
│   └── utils.py               # Utility functions
└── README.md                  # This file
```

## Roadmap

### v1.0 (Current)
- ✅ Enhanced CLI with interactive selection
- ✅ OAuth authentication
- ✅ Duplicate detection
- ✅ Year-based folder organization
- ✅ Error handling with user prompts

### v1.5 (Planned)
- 🔄 Transcript processing with LLM
- 🔄 n8n workflow integration
- 🔄 Meeting minutes extraction
- 🔄 Action item detection
- 🔄 Key discussion points

### v2.0 (Future)
- 📅 Mac desktop app
- 📅 Scheduled runs
- 📅 Advanced filtering
- 📅 Team features

## License

Apache License 2.0 - See LICENSE file for details

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the configuration reference

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
