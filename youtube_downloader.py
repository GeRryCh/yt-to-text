import yt_dlp
import re
from tqdm import tqdm

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', '0%')
            percent = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', percent)  # Remove ANSI color codes
            percent = percent.replace('%', '').strip()
            percent_float = float(percent)
            
            progress = tqdm(total=100, desc="Downloading", bar_format="{l_bar}{bar}", leave=False)
            progress.update(percent_float)
            progress.close()
        except ValueError:
            print(f"Download progress: {d.get('_percent_str', 'unknown')}")
        except Exception as e:
            print(f"Error updating progress: {str(e)}")

def download_audio(url, output_path, verbose=False):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'progress_hooks': [progress_hook]
    }
    if not verbose:
        ydl_opts['quiet'] = True
        ydl_opts['noprogress'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])