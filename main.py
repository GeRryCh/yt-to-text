import argparse
import os
import tempfile
from dotenv import load_dotenv
from youtube_downloader import download_audio
from audio_transcriber import transcribe_audio
from text_processor import process_text
from utils import read_prompt_file

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