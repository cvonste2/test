#!/usr/bin/env python3
"""
Fireflies Transcript Downloader
Downloads transcripts from Fireflies.ai and uploads them to Google Drive.
"""

import argparse
import configparser
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict

import inquirer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from src.fireflies_client import FirefliesClient
from src.gdrive_uploader import GDriveUploader
from src.metadata_tracker import MetadataTracker
from src.utils import generate_transcript_filename, format_date_for_display, get_year_from_date

console = Console()
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> configparser.ConfigParser:
    """Load configuration from file."""
    if not os.path.exists(config_path):
        console.print(f"[red]Error: Configuration file not found: {config_path}[/red]")
        console.print("[yellow]Please copy config.example.ini to config.ini and fill in your credentials.[/yellow]")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def display_header():
    """Display application header."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Fireflies Transcript Downloader[/bold cyan]\n"
        "Download meeting transcripts from Fireflies.ai to Google Drive",
        border_style="cyan"
    ))
    console.print()


def authenticate_services(config: configparser.ConfigParser) -> tuple:
    """
    Authenticate with Fireflies and Google Drive.

    Returns:
        Tuple of (fireflies_client, gdrive_uploader, metadata_tracker)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Initialize Fireflies client
        task1 = progress.add_task("Connecting to Fireflies API...", total=None)
        try:
            ff_client = FirefliesClient(
                api_key=config.get('fireflies', 'api_key'),
                base_url=config.get('fireflies', 'api_base_url')
            )
            if not ff_client.test_connection():
                raise Exception("Failed to connect to Fireflies API")
            progress.update(task1, completed=True)
            console.print("[green]✓[/green] Connected to Fireflies API")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to Fireflies: {e}[/red]")
            sys.exit(1)

        # Initialize Google Drive client
        task2 = progress.add_task("Connecting to Google Drive...", total=None)
        try:
            gdrive = GDriveUploader(
                credentials_file=config.get('google_drive', 'credentials_file'),
                token_file=config.get('google_drive', 'token_file'),
                root_folder_name=config.get('google_drive', 'destination_folder_name')
            )
            gdrive.authenticate()
            if not gdrive.test_connection():
                raise Exception("Failed to connect to Google Drive")
            progress.update(task2, completed=True)
            console.print("[green]✓[/green] Connected to Google Drive")
        except Exception as e:
            console.print(f"[red]✗ Failed to connect to Google Drive: {e}[/red]")
            sys.exit(1)

        # Initialize metadata tracker
        metadata = MetadataTracker(config.get('download', 'metadata_file'))
        console.print("[green]✓[/green] Loaded download history")

    return ff_client, gdrive, metadata


def fetch_and_display_transcripts(
    ff_client: FirefliesClient,
    metadata: MetadataTracker
) -> List[Dict]:
    """Fetch transcripts and display them in a table."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching available transcripts...", total=None)
        try:
            transcripts = ff_client.get_transcripts(limit=100)
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[red]✗ Failed to fetch transcripts: {e}[/red]")
            sys.exit(1)

    if not transcripts:
        console.print("[yellow]No transcripts found.[/yellow]")
        return []

    # Create table
    table = Table(title=f"Available Transcripts ({len(transcripts)} found)")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Participants", style="yellow")
    table.add_column("Status", style="blue")

    for idx, transcript in enumerate(transcripts, 1):
        status = "[green]Downloaded ✓[/green]" if metadata.is_downloaded(transcript['id']) else "[yellow]Not downloaded[/yellow]"
        participants_str = ", ".join(transcript['participants'][:3])
        if len(transcript['participants']) > 3:
            participants_str += f" +{len(transcript['participants']) - 3} more"

        table.add_row(
            str(idx),
            format_date_for_display(transcript['date']),
            transcript['title'][:50],
            participants_str[:40],
            status
        )

    console.print()
    console.print(table)
    console.print()

    return transcripts


def select_transcripts(transcripts: List[Dict], metadata: MetadataTracker) -> List[Dict]:
    """Let user select which transcripts to download."""
    # Create choices for inquirer
    choices = []
    for transcript in transcripts:
        status = "✓" if metadata.is_downloaded(transcript['id']) else " "
        label = f"[{status}] {format_date_for_display(transcript['date'])} - {transcript['title']}"
        choices.append((label, transcript))

    questions = [
        inquirer.Checkbox(
            'transcripts',
            message="Select transcripts to download (use Space to select, Enter to confirm)",
            choices=choices,
        ),
    ]

    answers = inquirer.prompt(questions)
    if not answers or not answers['transcripts']:
        console.print("[yellow]No transcripts selected.[/yellow]")
        return []

    return answers['transcripts']


def download_transcripts(
    selected: List[Dict],
    ff_client: FirefliesClient,
    gdrive: GDriveUploader,
    metadata: MetadataTracker,
    config: configparser.ConfigParser
):
    """Download and upload selected transcripts."""
    console.print(f"\n[bold]Downloading {len(selected)} transcript(s)...[/bold]\n")

    max_participants = config.getint('download', 'max_participants_in_filename', fallback=5)
    max_filename_length = config.getint('download', 'max_filename_length', fallback=200)

    success_count = 0
    skip_count = 0
    error_count = 0

    for idx, transcript in enumerate(selected, 1):
        console.print(f"[cyan]({idx}/{len(selected)})[/cyan] Processing: {transcript['title']}")

        try:
            # Generate filename
            filename = generate_transcript_filename(
                date=transcript['date'],
                title=transcript['title'],
                participants=transcript['participants'],
                max_participants=max_participants,
                max_length=max_filename_length
            )
            year = get_year_from_date(transcript['date'])

            # Check if already in Google Drive
            if gdrive.file_exists(filename, year):
                console.print(f"  [yellow]⊳ Skipped: Already exists in Google Drive[/yellow]")
                # Mark as downloaded in metadata if not already
                if not metadata.is_downloaded(transcript['id']):
                    metadata.mark_downloaded(
                        transcript_id=transcript['id'],
                        filename=filename,
                        title=transcript['title'],
                        date=transcript['date']
                    )
                skip_count += 1
                continue

            # Download transcript content
            console.print("  [blue]⊳ Downloading transcript content...[/blue]")
            content = ff_client.get_transcript_content(transcript['id'])

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write(f"Meeting: {transcript['title']}\n")
                tmp.write(f"Date: {format_date_for_display(transcript['date'])}\n")
                tmp.write(f"Participants: {', '.join(transcript['participants'])}\n")
                tmp.write(f"Duration: {transcript['duration']} minutes\n")
                tmp.write("=" * 80 + "\n\n")
                tmp.write(content)
                tmp_path = tmp.name

            # Upload to Google Drive
            console.print("  [blue]⊳ Uploading to Google Drive...[/blue]")
            drive_file_id = gdrive.upload_file(tmp_path, filename, year)

            # Clean up temp file
            os.unlink(tmp_path)

            if drive_file_id:
                # Mark as downloaded
                metadata.mark_downloaded(
                    transcript_id=transcript['id'],
                    filename=filename,
                    title=transcript['title'],
                    date=transcript['date'],
                    drive_file_id=drive_file_id
                )
                console.print(f"  [green]✓ Successfully uploaded: {filename}[/green]")
                success_count += 1
            else:
                console.print(f"  [red]✗ Upload failed[/red]")
                error_count += 1

        except KeyboardInterrupt:
            console.print("\n[yellow]Download interrupted by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")
            error_count += 1

            # Ask user what to do
            action = inquirer.prompt([
                inquirer.List('action',
                    message="What would you like to do?",
                    choices=['Continue', 'Retry this transcript', 'Abort'],
                )
            ])

            if action and action['action'] == 'Abort':
                console.print("[yellow]Aborted by user.[/yellow]")
                break
            elif action and action['action'] == 'Retry this transcript':
                # Retry logic would go here
                console.print("[yellow]Retry not yet implemented. Continuing...[/yellow]")

    # Display summary
    console.print()
    console.print(Panel.fit(
        f"[bold]Download Summary[/bold]\n\n"
        f"[green]✓ Successfully downloaded: {success_count}[/green]\n"
        f"[yellow]⊳ Skipped (already exists): {skip_count}[/yellow]\n"
        f"[red]✗ Errors: {error_count}[/red]",
        border_style="cyan"
    ))


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

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Display header
    display_header()

    # Load configuration
    config = load_config(args.config)

    # Authenticate
    ff_client, gdrive, metadata = authenticate_services(config)

    # Fetch and display transcripts
    transcripts = fetch_and_display_transcripts(ff_client, metadata)
    if not transcripts:
        return

    # Let user select transcripts
    selected = select_transcripts(transcripts, metadata)
    if not selected:
        return

    # Download selected transcripts
    download_transcripts(selected, ff_client, gdrive, metadata, config)

    console.print("\n[bold green]Done![/bold green]\n")


if __name__ == '__main__':
    main()
