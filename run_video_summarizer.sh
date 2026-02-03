#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
SCRIPT_PATH="src/video_summarizer/ui/main.py"

# Vérification de la présence du venv
echo "Vérification de la présence du venv..."
if [ ! -d "$VENV_DIR" ]; then
  echo "Venv introuvable dans '$VENV_DIR'. Lancez d'abord install_video_summarizer.sh."
  exit 1
fi

echo "Activation du venv..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Vérification du chemin du script
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "Fichier $SCRIPT_PATH introuvable. Assurez-vous que le chemin est correct."
  exit 1
fi

# Lancer Streamlit
echo "Lancement de Streamlit avec $SCRIPT_PATH..."
cd src/
python -m streamlit run video_summarizer/ui/main.py
