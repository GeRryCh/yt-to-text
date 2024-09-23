
# yt-to-text

A simple script to transcribe YouTube videos and process the audio with OpenAI's API.

## Configuration

Create a `.env` file with the following:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini # or gpt-3.5-turbo
```

## Installation
Run: 

```bash
setup.sh
```

## Usage

```bash
python yt-to-text.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

