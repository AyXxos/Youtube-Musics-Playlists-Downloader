# Youtube Music Downloader 
import os
import re
import yt_dlp
from pathlib import Path
from yt_dlp.utils import DownloadError
from typing import Optional
from pydantic import BaseModel, Field
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, TIT2
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

    def _sanitize_filename(self, file_name: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', file_name).strip().rstrip('.')
        return sanitized[:180] if sanitized else "unknown"

    def _clean_track_title(self, track_title: str) -> str:
        cleaned_title = re.sub(r'\s*\([^)]*\)', '', track_title)
        cleaned_title = re.sub(r'\s*\[[^\]]*\]', '', cleaned_title)
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
        cleaned_title = re.sub(r'\s*[-–—|:]\s*$', '', cleaned_title)
        cleaned_title = cleaned_title.strip(' -_')
        return cleaned_title or track_title

    def _parse_artist_track_from_title(self, raw_title: str) -> tuple[Optional[str], str]:
        normalized_title = re.sub(r'\s+', ' ', raw_title).strip()
        separators = [' - ', ' – ', ' — ', ' | ', ': ']

        for separator in separators:
            if separator in normalized_title:
                left_part, right_part = normalized_title.split(separator, 1)
                if len(left_part.strip()) > 1 and len(right_part.strip()) > 1:
                    artist_name = re.sub(r'\s+(ft\.?|feat\.?|featuring)\s+.+$', '', left_part.strip(), flags=re.IGNORECASE)
                    track_title = self._clean_track_title(right_part.strip())
                    return artist_name.strip(), track_title

        by_match = re.match(r'^(?P<track>.+?)\s+by\s+(?P<artist>.+)$', normalized_title, flags=re.IGNORECASE)
        if by_match:
            track_title = self._clean_track_title(by_match.group('track').strip())
            artist_name = by_match.group('artist').strip()
            return artist_name, track_title

        return None, self._clean_track_title(normalized_title)

    def _validate_with_musicbrainz(self, artist_name: str, track_title: str) -> bool:
        if not artist_name or not track_title:
            return False

        try:
            query = f'recording:"{track_title}" AND artist:"{artist_name}"'
            response = requests.get(
                'https://musicbrainz.org/ws/2/recording/',
                params={'query': query, 'fmt': 'json', 'limit': 1},
                headers={'User-Agent': 'YoutubeMusicDownloader/1.0 (local-script)'},
                timeout=8,
            )
            if response.status_code != 200:
                return False

            recordings = response.json().get('recordings', [])
            if not recordings:
                return False

            score = int(recordings[0].get('score', 0))
            return score >= 70
        except Exception:
            return False

    def _resolve_artist_and_track(self, video_info: dict) -> tuple[Optional[str], str]:
        source_title = video_info.get('title', 'unknown')
        source_artist = video_info.get('artist')
        source_track = video_info.get('track')
        channel_name = video_info.get('channel') or video_info.get('uploader')

        if source_artist and source_track:
            return source_artist, self._clean_track_title(source_track)

        parsed_artist, parsed_track = self._parse_artist_track_from_title(source_title)

        if parsed_artist and parsed_track and self._validate_with_musicbrainz(parsed_artist, parsed_track):
            return parsed_artist, parsed_track

        if source_artist and parsed_track:
            return source_artist, parsed_track

        if parsed_artist and parsed_track:
            return parsed_artist, parsed_track

        fallback_track = self._clean_track_title(source_track or source_title)
        return channel_name, fallback_track

    def _embed_thumbnail(
        self,
        video_title: str,
        thumbnail_url: str,
        artist_name: Optional[str] = None,
        track_title: Optional[str] = None,
    ) -> bool:
        """Download and embed thumbnail plus artist/title metadata in the MP3 file."""
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

            if artist_name:
                audio.tags.delall('TPE1')
                audio.tags.add(TPE1(
                    encoding=3,
                    text=[artist_name]
                ))

            if track_title:
                audio.tags.delall('TIT2')
                audio.tags.add(TIT2(
                    encoding=3,
                    text=[track_title]
                ))
            
            audio.tags.save(str(mp3_file), v2_version=3)

            if track_title:
                target_file = mp3_file.with_name(f"{self._sanitize_filename(track_title)}.mp3")
                if target_file != mp3_file:
                    if target_file.exists():
                        print(f"Rename skipped: '{target_file.name}' already exists")
                    else:
                        mp3_file.rename(target_file)
                        mp3_file = target_file
                        print(f"Renamed file to '{mp3_file.name}'")

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

                if isinstance(info, dict) and info.get('entries'):
                    for video in info.get('entries', []):
                        if not video:
                            continue
                        title = video.get('title', 'unknown')
                        thumbnail = video.get('thumbnail')
                        artist_name, track_title = self._resolve_artist_and_track(video)
                        if thumbnail:
                            self._embed_thumbnail(title, thumbnail, artist_name, track_title)
                else:
                    title = info.get('title', 'unknown')
                    thumbnail = info.get('thumbnail')
                    artist_name, track_title = self._resolve_artist_and_track(info)
                    if thumbnail:
                        self._embed_thumbnail(title, thumbnail, artist_name, track_title)
            
            return "Download completed successfully."
        except DownloadError as e:
            return f"An error occurred during download: {e}"


if __name__ == "__main__":
    options = DownloadOptions(
        url= str(input("Enter YouTube URL: ")),
        output_dir="./downloads",
        audio_format="mp3",
        quality="320",
        playlist=str(input("Is it a playlist? (yes/no): ")).lower() == 'yes'
    )
    downloader = YoutubeMusicDownloader(options)
    result = downloader.download()
    print(result)