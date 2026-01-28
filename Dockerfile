FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps from requirements.txt
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy package source (assumes package is under src/video_summarizer)
COPY . .

WORKDIR src/

EXPOSE 8501

# Default command: run the package module
CMD ["python", "-m", "streamlit", "run",  "video_summarizer/ui/main.py"]
