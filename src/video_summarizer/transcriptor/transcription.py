from typing import Union
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> Union[str, None]:
    return url.split("v=")[1].split("&")[0]

def seconds_to_hhmmss(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def read_transcript(url: str) -> Union[str, None]:
    if "youtube" in url :
        video_id = extract_video_id(url)
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['en', 'fr'])
        transcript_text = ""
        for segment in transcript:
            timestamp = int(segment.start)
            timestamp = seconds_to_hhmmss(timestamp)
            transcript_text += f"[{timestamp}] {segment.text}\n"
        return transcript_text
    
    else:
        return None
     
