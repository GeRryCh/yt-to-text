import whisper
import logging
import warnings
from utils import format_chunk, format_timestamp

def transcribe_audio(audio_path, verbose=False):
    if not verbose:
        logging.basicConfig(level=logging.CRITICAL)
        warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

    model = whisper.load_model("base")
    result = model.transcribe(audio_path, verbose=False)
    
    segments = result["segments"]
    
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
    
    if current_chunk:
        chunk_text = format_chunk(current_chunk, chunk_start)
        transcription.append(chunk_text)
    
    return "\n".join(transcription)