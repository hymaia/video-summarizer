from video_summarizer.transcriptor import transcription

url = "https://www.youtube.com/watch?v=3g7y-mG4QBc"

transcription = transcription.read_transcript(url)
print(transcription[:500], "\n...\n", transcription[-500:]) 


