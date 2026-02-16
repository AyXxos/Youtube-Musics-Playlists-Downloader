# Youtube Music Downloader 
import os
import yt_dlp
from pathlib import Path
from yt_dlp.utils import DownloadError
from typing import Optional
from pydantic import BaseModel, Field
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image
from io import BytesIO
import time

class DownloadOptions(BaseModel):
    url: str = Field(..., description="The URL of the YouTube video or playlist to download.")
    output_dir: str = Field("downloads", description="Directory to save downloaded music files.")
    audio_format: str = Field("mp3", description="Audio format for the downloaded files (e.g., mp3, m4a).")
    quality: str = Field("320", description="Audio quality for the downloaded files.")
    playlist: bool = Field(False, description="Whether to download a playlist or a single video.")

class YoutubeMusicDownloader:
    def __init__(self, options: DownloadOptions):
        self.options = options
        self.ydl_opts = self._build_ydl_options()

    def _build_ydl_options(self) -> dict:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.options.output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.options.audio_format,
                'preferredquality': self.options.quality,
            }],
            'quiet': True,
            'noplaylist': not self.options.playlist,
            'writethumbnail': True,
        }
        return ydl_opts

    def _embed_thumbnail(self, video_title: str, thumbnail_url: str) -> bool:
        """Download and embed thumbnail as album art in the MP3 file."""
        try:
            mp3_file = None
            output_dir = Path(self.options.output_dir)
            
            # Wait a moment for the MP3 file to be created
            time.sleep(1)
            
            # Find thumbnail files to clean up later
            thumbnail_files = list(output_dir.glob(f"{video_title}*.webp")) + \
                            list(output_dir.glob(f"{video_title}*.jpg")) + \
                            list(output_dir.glob(f"{video_title}*.png"))
            
            # Find the MP3 file with matching title
            for file in output_dir.glob(f"{video_title}*"):
                if file.suffix.lower() == '.mp3':
                    mp3_file = file
                    break
            
            # If not found with glob, try a more permissive search
            if not mp3_file:
                mp3_files = list(output_dir.glob("*.mp3"))
                if mp3_files:
                    # Get the most recently modified MP3 file
                    mp3_file = max(mp3_files, key=lambda p: p.stat().st_mtime)
            
            if not mp3_file or not mp3_file.exists():
                print(f"Warning: MP3 file not found for '{video_title}'")
                return False
            
            # Download thumbnail image
            thumbnail_response = requests.get(thumbnail_url)
            thumbnail_data = thumbnail_response.content
            
            # Convert thumbnail to JPEG if needed
            try:
                img = Image.open(BytesIO(thumbnail_data))
                # Convert to RGB if necessary (for PNG with alpha channel, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Save as JPEG
                jpeg_buffer = BytesIO()
                img.save(jpeg_buffer, format='JPEG', quality=95)
                thumbnail_data = jpeg_buffer.getvalue()
            except Exception as e:
                print(f"Note: Could not convert thumbnail to JPEG, using original: {e}")
            
            # Embed as album art
            audio = MP3(str(mp3_file), ID3=ID3)
            
            # Create ID3 tag if it doesn't exist
            if audio.tags is None:
                audio.add_tags()
            
            # Remove existing pictures to avoid duplicates
            audio.tags.delall('APIC')
            
            # Add thumbnail image
            audio.tags.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=thumbnail_data
            ))
            
            audio.tags.save(str(mp3_file), v2_version=3)
            print(f"Thumbnail embedded successfully in '{mp3_file.name}'")
            
            # Clean up thumbnail files
            for thumb_file in thumbnail_files:
                try:
                    if thumb_file.exists():
                        thumb_file.unlink()
                        print(f"Deleted thumbnail: {thumb_file.name}")
                except Exception as e:
                    print(f"Could not delete {thumb_file.name}: {e}")
            
            return True
        except Exception as e:
            print(f"Error embedding thumbnail: {e}")
            return False

    def download(self) -> Optional[str]:
        Path(self.options.output_dir).mkdir(parents=True, exist_ok=True)
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Get video info to extract thumbnail
                info = ydl.extract_info(self.options.url, download=True)
                
                # Handle playlist or single video
                if isinstance(info, list):
                    # Playlist
                    for video in info:
                        title = video.get('title', 'unknown')
                        thumbnail = video.get('thumbnail')
                        if thumbnail:
                            self._embed_thumbnail(title, thumbnail)
                else:
                    # Single video
                    title = info.get('title', 'unknown')
                    thumbnail = info.get('thumbnail')
                    if thumbnail:
                        self._embed_thumbnail(title, thumbnail)
            
            return "Download completed successfully."
        except DownloadError as e:
            return f"An error occurred during download: {e}"


if __name__ == "__main__":
    options = DownloadOptions(
        url= str(input("Enter YouTube URL: ")),
        output_dir="./YoutubeMusicDownloader/downloads",
        audio_format="mp3",
        quality="320",
        playlist=str(input("Is it a playlist? (yes/no): ")).lower() == 'yes'
    )
    downloader = YoutubeMusicDownloader(options)
    result = downloader.download()
    print(result)