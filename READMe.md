# 🎵 YouTube Music Downloader

A simple and efficient tool to download music from YouTube in high quality MP3 format.

## 📋 Description

YouTube Music Downloader is a Python script that allows you to easily download audio from YouTube, whether it's a single video or a complete playlist. The program automatically converts videos to high-quality MP3 audio files (320 kbps).

## ✨ Features

- ✅ Download individual YouTube videos
- ✅ Download complete playlists
- ✅ Automatic MP3 conversion
- ✅ Maximum audio quality (320 kbps)
- ✅ Automatic organization of downloaded files
- ✅ Automatic album art embedding from YouTube thumbnail
- ✅ Simple command-line interface

## 🔧 Prerequisites

### Operating System
- Windows 10/11
- macOS 10.15+
- Linux (any recent distribution)

### Required Software
- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **FFmpeg**: Required for audio conversion

## 📥 Installation

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"

#### macOS
```bash
# With Homebrew
brew install python3
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

### Step 2: Install FFmpeg

#### Windows
**Option 1: With Chocolatey (recommended)**
```powershell
choco install ffmpeg
```

**Option 2: Manual installation**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the archive
3. Add the `bin` folder to system PATH

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Step 3: Install Python Dependencies

Open a terminal/command prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install yt-dlp pydantic requests mutagen pillow
```

## 🚀 Usage

### Launching the Program

1. Open a terminal/command prompt
2. Navigate to the project folder:
   ```bash
   cd path/to/YoutubeMusicDownloader
   ```
3. Run the script:
   ```bash
   python downloader.py
   ```

### How to Use

1. The program will ask for the YouTube URL:
   ```
   Enter YouTube URL: https://www.youtube.com/watch?v=xxxxx
   ```

2. Indicate if it's a playlist:
   ```
   Is it a playlist? (yes/no): no
   ```

3. The download starts automatically!

### Examples

**Download a single video:**
```
Enter YouTube URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Is it a playlist? (yes/no): no
```

**Download a playlist:**
```
Enter YouTube URL: https://www.youtube.com/playlist?list=PLxxxxxxxxxx
Is it a playlist? (yes/no): yes
```

## 📁 Project Structure

```
YoutubeMusicDownloader/
├── downloader.py          # Main script
├── downloads/             # Downloaded files folder
└── READMe.md             # This file
```

## ⚙️ Configuration

The script uses the following default settings:
- **Audio format**: MP3
- **Quality**: 320 kbps
- **Output folder**: `./YoutubeMusicDownloader/downloads`
- **Album art**: Automatically embedded from YouTube thumbnail

To modify these settings, edit the values in the `downloader.py` file:
```python
options = DownloadOptions(
    url= str(input("Enter YouTube URL: ")),
    output_dir="./YoutubeMusicDownloader/downloads",  # Change the path here
    audio_format="mp3",                                # or "m4a", "wav", etc.
    quality="320",                                     # 128, 192, 256, 320
    playlist=str(input("Is it a playlist? (yes/no): ")).lower() == 'yes'
)
```

## 🐛 Troubleshooting

### Error: "FFmpeg not found"
- Make sure FFmpeg is properly installed and in PATH
- Verify with: `ffmpeg -version`

### Error: "No module named 'yt_dlp'"
- Install dependencies: `pip install yt-dlp pydantic`

### Download error
- Check your Internet connection
- Make sure the URL is valid
- Some videos may have restrictions

### Program won't start
- Check that Python is installed: `python --version`
- Make sure you're in the correct folder

## 📜 License

This project is intended for personal and educational use. Respect copyright and YouTube's terms of service.

## ⚠️ Warning

Using this tool must comply with YouTube's terms of service and copyright laws in your country. Only download content that you have the right to use or that is under a free license.

## 🤝 Contributing

Suggestions and improvements are welcome! Feel free to open an issue or propose modifications.

## 📞 Support

If you encounter any issues:
1. Check that all dependencies are installed
2. Consult the "Troubleshooting" section
3. Make sure you're using the latest version of Python and dependencies

---

**Author**: AyXxos  
**Version**: 1.0.0  
**Last updated**: January 2026