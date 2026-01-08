import streamlit as st
from googleapiclient.discovery import build
import os
import isodate 
from openai import OpenAI

def chatgpt_generate_response(prompt: str) -> str:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), )
    response = client.responses.create(
        model=os.environ.get("MODEL_NAME"),
        instructions="",
        input=prompt,
    )
    return response.output_text



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