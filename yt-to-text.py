import argparse
import os
import tempfile
from tqdm import tqdm
import yt_dlp
import whisper
import openai
from dotenv import load_dotenv


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

def download_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'progress_hooks': [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]

def read_prompt_file(prompt_file):
    try:
        with open(prompt_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    except IOError:
        raise IOError(f"Error reading prompt file: {prompt_file}")

def process_text(text, prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"{prompt}\n\nTranscribed text: {text}\n\nProcessed:",
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

def main():
    parser = argparse.ArgumentParser(description="Process YouTube audio with AI")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--prompt_file", help="Path to the Markdown file containing the prompt")
    parser.add_argument("--prompt", help="Text prompt for processing")
    args = parser.parse_args()

    if args.prompt_file and args.prompt:
        parser.error("Only one of --prompt_file or --prompt can be provided")

    load_dotenv()  # Load environment variables from .env file

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            print("Downloading audio...")
            base_audio_path = os.path.join(temp_dir, "yt-audio")
            download_audio(args.url, base_audio_path)
            audio_path = base_audio_path + ".mp3"  # Append .mp3 after download

            print("Transcribing audio at: ", audio_path)
            transcription = transcribe_audio(audio_path)

            prompt = None
            if args.prompt_file:
                print("Reading prompt from file...")
                prompt = read_prompt_file(args.prompt_file)
            elif args.prompt:
                prompt = args.prompt

            if prompt:
                print("Processing text...")
                result = process_text(transcription, prompt)
            else:
                print("No prompt provided. Skipping text processing.")
                result = transcription

            print("\nResult:")
            print(result)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
