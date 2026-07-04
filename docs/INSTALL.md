# Installation Guide

## Requirements

Before running UltraPeakPlayer, make sure you have:

- Windows 10 or Windows 11
- Python 3.10 or newer (64-bit recommended)
- VLC Media Player (64-bit)

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/UltraPeakPlayer.git
cd UltraPeakPlayer
```

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 3. Install VLC

Download and install the latest 64-bit version of VLC Media Player:

https://www.videolan.org/vlc/

The installer should place the files in:

```
C:\Program Files\VideoLAN\VLC
```

## 4. Add your media files (optional)

Place your default media inside the `assets` folder:

```
assets/
├── video_padrao.mp4
└── audio_padrao.mp3
```

Or create your own playlist inside:

```
playlist/
```

## 5. Run the application

```bash
python main.py
```

## Features

- Local video playback
- YouTube streaming
- Playlist support
- Retro terminal rendering
- HD fullscreen playback

## Troubleshooting

### VLC not found

Make sure the 64-bit version of VLC is installed.

### ModuleNotFoundError

Install all dependencies again:

```bash
pip install -r requirements.txt
```

### YouTube playback doesn't work

Update the required packages:

```bash
pip install -U yt-dlp streamlink
```
