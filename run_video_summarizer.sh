#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="video_summarizer"
SCRIPT_PATH="src/video_summarizer/ui/main.py"

# Vérification de la présence de conda
echo "Vérification de la présence de conda..."
if ! command -v conda >/dev/null 2>&1; then
  echo "conda introuvable. Installez Miniconda/Anaconda puis relancez le script."
  exit 1
fi

# Permet d'utiliser 'conda activate' dans ce script
eval "$(conda shell.bash hook)"

# Activation de l'environnement
echo "Activation de l'environnement '$ENV_NAME'..."
conda activate "$ENV_NAME"

# Vérification du chemin du script
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Fichier $SCRIPT_PATH introuvable. Assurez-vous que le chemin est correct."
  exit 1
fi

# Lancer Streamlit
echo "Lancement de Streamlit avec $SCRIPT_PATH..."
cd src/
python -m streamlit run video_summarizer/ui/main.py