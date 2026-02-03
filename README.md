# video-summarizer

## Objectif du projet
Ce projet permet de générer des transcriptions puis resumer des videos Youtube via une interface Streamlit.

## Cloner le projet
```bash
git clone https://github.com/hymaia/video-summarizer.git
cd video-summarizer
```

## Installation
Le script crée un environnement virtuel et installe les dependances.
```bash
bash install_video_summarizer.sh
```

## Lancer l'application
```bash
bash run_video_summarizer.sh
```

## Notes
- Le script d'installation vous demandera vos cles API et les écrira dans `.env`.
- Si Python 3 n'est pas present, le script tente de l'installer via Homebrew (macOS).
