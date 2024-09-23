import argparse
import os
import tempfile
from tqdm import tqdm
import yt_dlp
import whisper
from openai import OpenAI
from dotenv import load_dotenv
import logging
import warnings
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

def transcribe_audio(audio_path, verbose=False):
    if not verbose:
        logging.basicConfig(level=logging.CRITICAL)
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

    model = whisper.load_model("base")
    result = model.transcribe(audio_path, verbose=False)
    
    # Extract segments with timestamps
    segments = result["segments"]
    
    # Format the output in 30-second chunks
    transcription = []
    current_chunk = []
    chunk_start = 0
    
    for segment in segments:
        current_chunk.append(segment)
        
        if segment['end'] - chunk_start >= 30:
            chunk_text = format_chunk(current_chunk, chunk_start)
            transcription.append(chunk_text)
            current_chunk = []
            chunk_start = segment['end']
    
    # Add any remaining segments
    if current_chunk:
        chunk_text = format_chunk(current_chunk, chunk_start)
        transcription.append(chunk_text)
    
    return "\n".join(transcription)

def format_chunk(chunk, start_time):
    formatted_start = format_timestamp(start_time)
    text = " ".join(segment['text'] for segment in chunk)
    return f"({formatted_start}){text}"

def format_timestamp(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def read_prompt_file(prompt_file):
    try:
        with open(prompt_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    except IOError:
        raise IOError(f"Error reading prompt file: {prompt_file}")

def process_text(text, prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not specified
    
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Transcribed text: {text}"}
        ],
        stream=True  # Enable streaming
    )
    
    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end='', flush=True)  # Print each token immediately
            full_response += content
    
    print()  # Print a newline at the end

def main():
    parser = argparse.ArgumentParser(description="Process YouTube audio with AI")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--prompt_file", help="Path to the Markdown file containing the prompt")
    parser.add_argument("--prompt", help="Text prompt for processing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    args = parser.parse_args()

    if args.prompt_file and args.prompt:
        parser.error("Only one of --prompt_file or --prompt can be provided")

    load_dotenv()  # Load environment variables from .env file

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            if args.verbose:
                print("Downloading audio...")
            base_audio_path = os.path.join(temp_dir, "yt-audio")
            download_audio(args.url, base_audio_path, args.verbose)
            audio_path = base_audio_path + ".mp3"  # Append .mp3 after download

            if args.verbose:
                print("Transcribing audio at: ", audio_path)

            transcription = transcribe_audio(audio_path, args.verbose)

            if args.verbose:
                print("\nTranscribed audio:")
                print(transcription)
                print("\n" + "-"*50 + "\n")  # Separator for better readability

            prompt = None
            if args.prompt_file:
                if args.verbose:
                    print("Reading prompt from file...")
                prompt = read_prompt_file(args.prompt_file)
            elif args.prompt:
                prompt = args.prompt

            if prompt:
                if args.verbose:
                    print("Processing text...")
                process_text(transcription, prompt)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()