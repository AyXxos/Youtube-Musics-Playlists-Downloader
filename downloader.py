# Youtube Music Downloader 
import os
import yt_dlp
from pathlib import Path
from yt_dlp.utils import DownloadError
from typing import Optional
from pydantic import BaseModel, Field

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
        }
        return ydl_opts

    def download(self) -> Optional[str]:
        Path(self.options.output_dir).mkdir(parents=True, exist_ok=True)
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.options.url])
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