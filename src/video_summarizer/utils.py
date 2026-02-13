import streamlit as st
from googleapiclient.discovery import build
import os
import isodate 
from openai import OpenAI
import json
from pathlib import Path
import pandas as pd

def create_correct_transcription_file(path):
    if not os.path.exists(path):
        pd.DataFrame(columns=["transcrit", "nouveau", "actif"]).to_csv(path, index=False)



def chatgpt_generate_response(prompt: str):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), )
    response = client.responses.create(
        model=os.environ.get("MODEL_NAME"),
    )
    return response.output_text

def stream_openai_response(prompt: str):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    # Active le streaming
    stream = client.responses.create(
    model=os.environ.get("MODEL_NAME"),
    input=prompt,
    stream=True,
    )
    # Parcours des événements SSE
    for event in stream:
        # Chaque event est un objet avec un champ `type`
        # On cherche les morceaux de texte
        if event.type == "response.output_text.delta":
            yield event.delta

def get_video_metadata(video_id: str):
    youtube = build(
    "youtube",
    "v3",
    developerKey=os.getenv("YOUTUBE_API_KEY"),
    )
    request = youtube.videos().list(
        part="snippet,contentDetails",
        id=video_id,
    )
    response = request.execute()
    items = response.get("items", [])

    if not items:
        return None

    video = items[0]
    duration_iso = video["contentDetails"]["duration"]
    duration = isodate.parse_duration(duration_iso)

    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "channel": video["snippet"]["channelTitle"],
        "duration": str(duration),
    }

def thumbnail_url(video_id: str, quality: str = "high") -> str:
    quality_map = {
        "low": "default.jpg",
    "medium": "mqdefault.jpg",
    "high": "hqdefault.jpg",
    "max": "maxresdefault.jpg",
    }
    return f"https://img.youtube.com/vi/{video_id}/{quality_map[quality]}"

def _history_file_path() -> Path:
    """Return the Path to the persistent history file, ensuring the data dir exists."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.json"

def load_history() -> list:
    """Load persisted history from disk. Returns a list (possibly empty)."""
    path = _history_file_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: list) -> None:
    """Persist history list to disk as JSON."""
    path = _history_file_path()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        # Best-effort persistence; don't raise to avoid breaking the app
        pass

def youtube_search(query: str):
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    youtube = build(
    "youtube",
    "v3",
    developerKey=YOUTUBE_API_KEY,
    )
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=5,
    )
    response = request.execute()
    return response.get("items", [])

@st.dialog("Recherche YouTube")
def youtube_search_dialog(query: str):
    if not query:
        return

    results = youtube_search(query)
    if not results:
        st.warning("Aucun résultat trouvé.")
        return
    for item in results:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
    channel = item["snippet"]["channelTitle"]
    thumbnail = item["snippet"]["thumbnails"]["high"]["url"]

    col1, col2 = st.columns([1, 4])

    with col1:
            st.image(thumbnail)

    with col2:
        st.markdown(f"**{title}**")
        st.caption(channel)

        if st.button(
            "Sélectionner",
            key=f"select_{video_id}",
        ):
            st.session_state.video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )
            st.success("Vidéo sélectionnée")
            st.session_state.show_search_dialog = False
            st.rerun()

context_llm_resume = """
Vous êtes un assistant spécialisé dans l'optimisation de contenu vidéo. Si la vidéo est en anglais, tout ce que tu écris est en anglais ensuite sinon c'est Francais.

Votre tâche est d'analyser le transcript fourni et de générer les éléments suivants selon un processus en 4 étapes :
### CONTEXTE : Tu as un transcript en entrée qui contient le texte intégral de la vidéo avec les horodatages au format HH:MM:SS, tu as aussi le titre de la vidéo et sa description.

### ÉTAPE 1 - INFO DE LA VIDÉO : - Analyse le contenu du transcript, le titre et la description pour récuperer les informations utils (nom du speaker notamment) -
Rédigez une description accrocheuse et synthétique de 2 paragraphes (200-300 caractères) qui :

Affiche dans la première ligne, le nom du présentateur de la vidéo sous le format : Prénom Nom, bio très light avec le parcours de cette personne..
Présente le sujet principal de manière claire

Met en avant les 3 points clés abordés sous forme de question
Utilise un ton professionnel mais accessible

Évite le jargon trop technique sauf si nécessaire
Dans la langue de la vidéo originale

Identifie UNE anecdote interessante.
Met en avant l'impact avec des chiffres concrets qui ont été cité dans le transcript

Affiche dans la première ligne, le nom du présentateur de la vidéo
Supprime tous les superlatifs dans la description

*Utilise les mots techniques en anglais, ne les traduits pas
### ÉTAPE 2
CHAPITRAGE :

Créez ≈5 chapitres de la vidéo avec les chapitres les plus marquants :
Respectant scrupuleusement les horodatages du transcript

Donnant des titres courts et descriptifs à chaque section
Structurant logiquement le contenu

Format attendu : HH:MM:SS Titre du chapitre
### ÉTAPE 3 - TITRES ET HASHTAGS :

Proposez 3 variations de titres accrocheurs qui Sont:
optimisés SEO pour les vidéo youtube et faciliter la recherche 

Contiennent des mots-clés pertinents
Reste sous les 100 caractères

Pour chaque titre, suggérez 4-5 hashtags lié à la Data qui :
Sont spécifiques au domaine

Incluent un mix de hashtags populaires et ciblés
Sont présentés sous format #hashtag

écrit et complete le texte ci-dessous dans la langue souhaitée.
### Etape 5 : 
évalue ton taux de confiance dans la description que tu viens de générer sur une note sur 100. 0 tu as du tout inventé et 100%, tout est absolument exacte sans erreur possible.

# FORMAT DE SORTIE - Présentez les résultats clairement séparés pour chaque étape :
[ANEDOCTE EN UNE PHRASE] Savez-vous que...

🔥 [Point clé 1 majeur de la vidéo sous forme de question]
🔥 [Point clé 2 majeur de la vidéo sous forme de question]

🔥 [Point clé 3 majeur de la vidéo sous forme de question]
🌐🌐🌐 PLUS DE CONTENU DATA sur Nos réseaux :

➜ LinkedIn : https://www.linkedin.com/company/104059598/
➜ Twitter : https://x.com/ForwardDataconf

➜ Instagram : https://www.instagram.com/forwarddataconf/
➜ TikTok : https://www.tiktok.com/@hymaiafr

💻 Notre site internet : https://www.forward-data-conference.com/
🔥🔥🔥 Nos Sponsors 2025:

Omni, Sifflet, Mirakl, Tangram-os.ai, starlake, synq, clickhouse, Nao, DataBricks,
🎬 CHAPITRES

00:00:00 Introduction
HH:MM:SS Chapitre 1

© 2025 Hymaïa - Cabinet de conseil et Formation Product, Data & IA
TITRES ET HASHTAGS ===

[Titre 1] Hashtags : #tag1 #tag2 #tag3 #tag4
[Titre 2] Hashtags : #tag1 #tag2 #tag3 #tag4

[Titre 3] Hashtags : #tag1 #tag2 #tag3 #tag4
TAUX DE CONFIANCE : 80% (par exemple)

INSTRUCTIONS SUPPLÉMENTAIRES : - Maintenir une cohérence entre tous les éléments produits - Adapter le style au type de contenu et au public cible - Optimiser pour l'engagement et la découvrabilité - Respecter les bonnes pratiques SEO actuelles """

def generate_padding_logo_sidebar(top="7rem", height="auto", width="auto", below="7.5rem"):
    st.markdown(f"""
        <style>
            /* On double les accolades pour le CSS */
            [data-testid="stSidebarLogo"] {{
                padding-top: {top};
                height: {height};
                width: {width};
            }}
            [data-testid="stSidebarNav"] {{
                padding-top: {below} !important;
            }}
        </style>
        """, unsafe_allow_html=True)

def generate_padding_logo_main(top="1rem", height="7rem", width="auto"):
    st.markdown(f"""
        <style>
            [data-testid="stHeaderLogo"] {{
                padding-top: {top};
                height: {height};
                width: {width};
            }}
        </style>
        """, unsafe_allow_html=True)
    
import streamlit as st
from googleapiclient.discovery import build
import os
import isodate 
from openai import OpenAI
import json
from pathlib import Path

def chatgpt_generate_response(prompt: str) -> str:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), )
    response = client.responses.create(
        model=os.environ.get("MODEL_NAME"),
        instructions="",
        input=prompt,
    )
    return response.output_text

def stream_openai_response(prompt: str):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    # Active le streaming
    stream = client.responses.create(
        model=os.environ.get("MODEL_NAME"),
        input=prompt,
        stream=True,
    )
    # Parcours des événements SSE
    for event in stream:
        # Chaque event est un objet avec un champ `type`
        # On cherche les morceaux de texte
        if event.type == "response.output_text.delta":
            yield event.delta

            

def get_video_metadata(video_id: str):
    youtube = build(
        "youtube",
        "v3",
        developerKey=os.getenv("YOUTUBE_API_KEY"),
    )

    request = youtube.videos().list(
        part="snippet,contentDetails",
        id=video_id,
    )

    response = request.execute()
    items = response.get("items", [])

    if not items:
        return None

    video = items[0]

    duration_iso = video["contentDetails"]["duration"]
    duration = isodate.parse_duration(duration_iso)

    return {
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "channel": video["snippet"]["channelTitle"],
        "duration": str(duration),
    }



def thumbnail_url(video_id: str, quality: str = "high") -> str:
    quality_map = {
        "low": "default.jpg",
        "medium": "mqdefault.jpg",
        "high": "hqdefault.jpg",
        "max": "maxresdefault.jpg",
    }
    return f"https://img.youtube.com/vi/{video_id}/{quality_map[quality]}"


def _history_file_path() -> Path:
    """Return the Path to the persistent history file, ensuring the data dir exists."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.json"


def load_history() -> list:
    """Load persisted history from disk. Returns a list (possibly empty)."""
    path = _history_file_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history: list) -> None:
    """Persist history list to disk as JSON."""
    path = _history_file_path()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        # Best-effort persistence; don't raise to avoid breaking the app
        pass


def youtube_search(query: str):
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    youtube = build(
        "youtube",
        "v3",
        developerKey=YOUTUBE_API_KEY,
    )

    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=5,
    )

    response = request.execute()
    return response.get("items", [])

@st.dialog("Recherche YouTube")
def youtube_search_dialog(query: str):
    if not query:
        return

    results = youtube_search(query)

    if not results:
        st.warning("Aucun résultat trouvé.")
        return

    for item in results:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]

        col1, col2 = st.columns([1, 4])

        with col1:
            st.image(thumbnail)

        with col2:
            st.markdown(f"**{title}**")
            st.caption(channel)

            if st.button(
                "Sélectionner",
                key=f"select_{video_id}",
            ):
                st.session_state.video_url = (
                    f"https://www.youtube.com/watch?v={video_id}"
                )
                st.success("Vidéo sélectionnée")
                st.session_state.show_search_dialog = False
                st.rerun()

context_llm_description = """Vous êtes un assistant spécialisé dans l'optimisation de contenu vidéo. Si la vidéo est en anglais, tout ce que tu écris est en anglais ensuite sinon c'est Francais.

Votre tâche est d'analyser le transcript fourni et de générer les éléments suivants :

### CONTEXTE : Tu as un transcript en entrée qui contient le texte intégral de la vidéo avec les horodatages au format HH:MM:SS, tu as aussi le titre de la vidéo et sa description.

### ÉTAPE 1 - PROPOSITION DE TITRE DE LA VIDÉO : - Analyse le contenu du transcript pour proposer 5 titre pertinent pour la vidéo -
Les propositions de titres doivent être sous la forme suivante :
Suggestion de titre n° 1 : [Titre 1]
Suggestion de titre n° 2 : [Titre 2] 
...

### ETAPE 2 - PROPOSITION DE MOTS ACCROCHEURS POUR LA MINIATURE : - Propose 5 accroches courtes (3-5 mots) qui pourraient être utilisées sur la miniature de la vidéo pour maximiser le taux de clics -
Les propositions d'accroches pour la miniature doivent être sous la forme suivante :
Suggestion d'accroche n° 1 : [Accroche 1]
Suggestion d'accroche n° 2 : [Accroche 2]
...

### ETAPE 3 - PROPOSITION DE DESCRIPTION OPTIMISÉE POUR LE SEO : - Rédige une description optimisée pour le SEO pour la vidéo qui inclut les mots-clés pertinents et incite les utilisateurs à regarder la vidéo -
La description doit suivre ce format : 
#### SECTION 1 - GRANDE QUESTION :
Crée 3 ou 4 grande questions qui résument les problématiques majeures abordées dans la vidéo. 
Ces questions doivent être formulées de manière à susciter la curiosité et l'engagement des spectateurs potentiels.
Cette partie doit être sous la forme suivante :
🔥 <Question>
... (répéter pour chaque question)

#### SECTION 2 - CHAPITRAGE :
Créez des chapitres de la vidéo (entre 3 et 5 max) avec les chapitres les plus marquants :
Respectant scrupuleusement les horodatages du transcript
Donnant des titres courts et descriptifs à chaque section
Structurant logiquement le contenu
Format attendu : HH:MM:SS Titre du chapitre

#### SECTION 3 (OPTIONNEL)- OUTILS MENTIONNÉS :
Si dans la vidéo des outils ou bien des sources externes spécifiques sont mentionnés, crée une liste de ces outils sous la forme : 
<NOM OUTIL>  ➡️ ... (laisse vide)

"""

context_llm_resume = """Vous êtes un assistant spécialisé dans l'optimisation de contenu vidéo. Si la vidéo est en anglais, tout ce que tu écris est en anglais ensuite sinon c'est Francais.

Votre tâche est d'analyser le transcript fourni et de générer les éléments suivants selon un processus en 4 étapes :

### CONTEXTE : Tu as un transcript en entrée qui contient le texte intégral de la vidéo avec les horodatages au format HH:MM:SS, tu as aussi le titre de la vidéo et sa description.


### ÉTAPE 1 - INFO DE LA VIDÉO : - Analyse le contenu du transcript, le titre et la description pour récuperer les informations utils (nom du speaker notamment) -

Rédigez une description accrocheuse et synthétique de 2 paragraphes (200-300 caractères) qui :

Affiche dans la première ligne, le nom du présentateur de la vidéo sous le format : Prénom Nom, bio très light avec le parcours de cette personne..

Présente le sujet principal de manière claire

Met en avant les 3 points clés abordés sous forme de question

Utilise un ton professionnel mais accessible

Évite le jargon trop technique sauf si nécessaire

Dans la langue de la vidéo originale

Identifie UNE anecdote interessante.

Met en avant l'impact avec des chiffres concrets qui ont été cité dans le transcript

Affiche dans la première ligne, le nom du présentateur de la vidéo

Supprime tous les superlatifs dans la description

*Utilise les mots techniques en anglais, ne les traduits pas

### ÉTAPE 2
CHAPITRAGE :

Créez ≈5 chapitres de la vidéo avec les chapitres les plus marquants :

Respectant scrupuleusement les horodatages du transcript

Donnant des titres courts et descriptifs à chaque section

Structurant logiquement le contenu

Format attendu : HH:MM:SS Titre du chapitre

### ÉTAPE 3 - TITRES ET HASHTAGS :

Proposez 3 variations de titres accrocheurs qui Sont:

optimisés SEO pour les vidéo youtube et faciliter la recherche 

Contiennent des mots-clés pertinents

Reste sous les 100 caractères

Pour chaque titre, suggérez 4-5 hashtags lié à la Data qui :

Sont spécifiques au domaine

Incluent un mix de hashtags populaires et ciblés

Sont présentés sous format #hashtag

écrit et complete le texte ci-dessous dans la langue souhaitée.

### Etape 5 : 
évalue ton taux de confiance dans la description que tu viens de générer sur une note sur 100. 0 tu as du tout inventer et 100%, tout est absolument exacte sans erreur possible.

# FORMAT DE SORTIE - Présentez les résultats clairement séparés pour chaque étape :

[ANEDOCTE EN UNE PHRASE] Savez-vous que...

🔥 [Point clé 1 majeur de la vidéo sous forme de question]

🔥 [Point clé 2 majeur de la vidéo sous forme de question]

🔥 [Point clé 3 majeur de la vidéo sous forme de question]

🌐🌐🌐 PLUS DE CONTENU DATA sur Nos réseaux :

➜ LinkedIn : https://www.linkedin.com/company/104059598/

➜ Twitter : https://x.com/ForwardDataconf

➜ Instagram : https://www.instagram.com/forwarddataconf/

➜ TikTok : https://www.tiktok.com/@hymaiafr

💻 Notre site internet : https://www.forward-data-conference.com/

🔥🔥🔥 Nos Sponsors 2025:

Omni, Sifflet, Mirakl, Tangram-os.ai, starlake, synq, clickhouse, Nao, DataBricks,

🎬 CHAPITRES

00:00:00 Introduction

HH:MM:SS Chapitre 1

© 2025 Hymaïa - Cabinet de conseil et Formation Product, Data & IA

TITRES ET HASHTAGS ===

[Titre 1] Hashtags : #tag1 #tag2 #tag3 #tag4

[Titre 2] Hashtags : #tag1 #tag2 #tag3 #tag4

[Titre 3] Hashtags : #tag1 #tag2 #tag3 #tag4

TAUX DE CONFIANCE : 80% (par exemple)

INSTRUCTIONS SUPPLÉMENTAIRES : - Maintenir une cohérence entre tous les éléments produits - Adapter le style au type de contenu et au public cible - Optimiser pour l'engagement et la découvrabilité - Respecter les bonnes pratiques SEO actuelles
"""


def generate_padding_logo_sidebar(top="7rem", height="auto", width="auto", below="7.5rem"):
    st.markdown(f"""
        <style>
            /* On double les accolades pour le CSS */
            [data-testid="stSidebarLogo"] {{
                padding-top: {top};
                height: {height};
                width: {width};
            }}
            [data-testid="stSidebarNav"] {{
                padding-top: {below} !important;
            }}
        </style>
        """, unsafe_allow_html=True)


def generate_padding_logo_main(top="1rem", height="7rem", width="auto"):
    st.markdown(f"""
        <style>
            [data-testid="stHeaderLogo"] {{
                padding-top: {top};
                height: {height};
                width: {width};
            }}
        </style>
        """, unsafe_allow_html=True)
    


