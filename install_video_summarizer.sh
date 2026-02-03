#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
REQ_FILE="requirements.txt"

echo "Vérification de la présence de Python 3..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 introuvable."
  if [ "$(uname -s)" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
      echo "Installation de Python 3 via Homebrew..."
      brew install python
    else
      echo "Homebrew introuvable. Installez Homebrew puis relancez le script."
      echo "Commande officielle : /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
      exit 1
    fi
  else
    echo "Système non supporté pour l'installation automatique de Python."
    exit 1
  fi
fi

echo "Vérification de pip..."
if ! command -v pip3 >/dev/null 2>&1; then
  echo "pip introuvable. Tentative d'installation via ensurepip..."
  python3 -m ensurepip --upgrade
fi

echo "Création du venv dans '$VENV_DIR'..."
python3 -m venv "$VENV_DIR"

echo "Activation du venv..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

if [ -f "$REQ_FILE" ]; then
  echo "Installation des dépendances via pip depuis $REQ_FILE..."
  pip install -r "$REQ_FILE"
else
  echo "Fichier $REQ_FILE introuvable — installation pip ignorée."
fi

# Demander les clés API à l'utilisateur
echo " "
echo "Configuration des clés API..."
echo " "
read -p "Entrez votre YOUTUBE_API_KEY : " YOUTUBE_API_KEY
read -p "Entrez votre OPENAI_API_KEY : " OPENAI_API_KEY
read -p "Entrez le nom du modèle (MODEL_NAME) : " MODEL_NAME

# Écrire les clés dans le fichier .env
env_file=".env"
echo "YOUTUBE_API_KEY=$YOUTUBE_API_KEY" > "$env_file"
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$env_file"
echo "MODEL_NAME=$MODEL_NAME" >> "$env_file"

echo "Clés API enregistrées dans $env_file."

echo "Terminé. Pour activer plus tard : source $VENV_DIR/bin/activate"
