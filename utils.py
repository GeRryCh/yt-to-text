def read_prompt_file(prompt_file):
    try:
        with open(prompt_file, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    except IOError:
        raise IOError(f"Error reading prompt file: {prompt_file}")

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