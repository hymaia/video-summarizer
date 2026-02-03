#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="video_summarizer"
PYTHON_VERSION="3.14"
REQ_FILE="requirements.txt"

echo "Vérification de la présence de conda..."
if ! command -v conda >/dev/null 2>&1; then
  echo "conda introuvable. Installez Miniconda/Anaconda puis relancez le script."
  exit 1
fi

echo "Création de l'environnement conda '$ENV_NAME' avec Python $PYTHON_VERSION..."
conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y

# Permet d'utiliser 'conda activate' dans ce script
eval "$(conda shell.bash hook)"

echo "Activation de l'environnement '$ENV_NAME'..."
conda activate "$ENV_NAME"

if [ -f "$REQ_FILE" ]; then
  echo "Installation des dépendances via pip depuis $REQ_FILE..."
  pip install -r "$REQ_FILE"
else
  echo "Fichier $REQ_FILE introuvable — installation pip ignorée."
fi

# Demander les clés API à l'utilisateur
echo "\nConfiguration des clés API..."
read -p "Entrez votre YOUTUBE_API_KEY : " YOUTUBE_API_KEY
read -p "Entrez votre OPENAI_API_KEY : " OPENAI_API_KEY
read -p "Entrez le nom du modèle (MODEL_NAME) : " MODEL_NAME

# Écrire les clés dans le fichier .env
env_file=".env"
echo "YOUTUBE_API_KEY=$YOUTUBE_API_KEY" > "$env_file"
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$env_file"
echo "MODEL_NAME=$MODEL_NAME" >> "$env_file"

echo "Clés API enregistrées dans $env_file."

echo "Terminé. Pour activer plus tard : conda activate $ENV_NAME"
