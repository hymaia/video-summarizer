import streamlit as st
 
from video_summarizer.transcriptor import transcription
from video_summarizer import utils
import time
import uuid
from datetime import datetime
from st_copy import copy_button
# Render copy to clipboard button

if "history" not in st.session_state:
    st.session_state.history = utils.load_history()

# Persistant UI state
if "video_url" not in st.session_state:
    st.session_state.video_url = None
if "metadata" not in st.session_state:
    st.session_state.metadata = None
if "current_transcription" not in st.session_state:
    st.session_state.current_transcription = None
if "current_summary" not in st.session_state:
    st.session_state.current_summary = None

st.title("🎬 Video Summarizer")
options = ["URL", "Titre"]

section_1, section_2 = st.columns([1, 1])

with section_1:
    st.subheader("🔍 Recherche")
    with st.container(height=270):
        non_repertoriee = st.toggle('Description pour vidéo non répertoriée', value=False)
        methode_recherche = st.pills("Méthode de recherche", options, selection_mode="single", default="URL")

        if "video_url" not in st.session_state:
            st.session_state.video_url = None  
        if "show_search_dialog" not in st.session_state:
            st.session_state.show_search_dialog = False


        if methode_recherche == "URL":
            st.write("Colle une URL YouTube pour générer la transcription et le résumé.")
            url = st.text_input(
                "URL YouTube",
                placeholder="https://www.youtube.com/watch?v=3g7y-mG4QBc",
            )
            if url and st.session_state.video_url != url:
                if st.session_state.video_url:
                    st.write("⚠️ URL changé. Cliquez sur 'Transcrire & résumer'")
                st.session_state.video_url = url


        if methode_recherche == "Titre":
            query = st.text_input(
                "Titre de la vidéo",
                placeholder="LLMs in Production Gone Wrong: A Story of Prompts and Observability - Simone Civetta - Hymaïa",
            )
            
            st.session_state.search_query = query
            if st.button("Rechercher"):
                st.session_state.show_search_dialog = True

            if st.session_state.get("show_search_dialog"):
                utils.youtube_search_dialog(st.session_state.search_query)

with section_2:
    if st.session_state.video_url:
        video_id = transcription.extract_video_id(st.session_state.video_url)
        metadata = utils.get_video_metadata(video_id)
        st.session_state.metadata = metadata
        st.subheader("📸 Vidéo")
        with st.container(height=270):
            st.image(
            utils.thumbnail_url(video_id), width=150)
            if metadata:
                st.markdown(f"**🎬 Titre**  \n{metadata['title']}")
                st.markdown(f"⏱️ {metadata['duration']}")


if st.session_state.video_url:
    if methode_recherche == "Titre":
        st.write(f"URL Vidéo sélectionnée : {st.session_state.video_url}")

    if st.button("🚀 Transcrire & résumer"):
        if "youtube.com" not in st.session_state.video_url: 
            st.warning("Veuillez entrer une URL YouTube valide.")
            st.stop()
        
        col_left, col_right = st.columns([1.5, 2.5], gap="large")

        # Transcription
        with col_left:
            try:
                transcript = transcription.read_transcript(
                    st.session_state.video_url
                )
            except Exception as e:
                st.error(f"Erreur lors de la transcription : {e}")    
                st.stop()

            # save to session_state so it persists across interactions
            st.session_state.current_transcription = transcript

            st.subheader("✍ Transcription")
            with st.container(height=500):
                st.markdown(
                    f"""
                    <div style="white-space: pre-wrap;">{st.session_state.current_transcription}</div>
                    """,
                    unsafe_allow_html=True,
                )
            copy_button(st.session_state.current_transcription,
            tooltip="Copier la transcription",
            copied_label="Copié!",
            icon="st",
            key=str(uuid.uuid4()))

        # Résumé (stream into session_state.current_summary)
        with col_right:
            st.subheader("📰 Résumé généré")
            # ensure metadata available
            metadata = st.session_state.metadata or utils.get_video_metadata(transcription.extract_video_id(st.session_state.video_url))
            
            if non_repertoriee:
                prompt = utils.context_llm_description + f"\n\n ### TRANSCRIPT :\n{st.session_state.current_transcription}\n\n"

            else: 
                prompt = utils.context_llm_resume +  f"### METADATA :\nTitle: {metadata['title']}\n ### Description: {metadata['description']}\n\n" + f"\n\n ### TRANSCRIPT :\n{st.session_state.current_transcription}\n\n"

            start_time = time.perf_counter()
            with st.spinner("Génération du résumé..."):
                output_container = st.container(height=500)
                placeholder = output_container.empty()
                full_text = ""
                for chunk in utils.stream_openai_response(prompt):
                    full_text += chunk
                    # update session state continuously
                    st.session_state.current_summary = full_text
                    placeholder.markdown(full_text + " ▌")

            duration = time.perf_counter() - start_time
            st.toast(f"Résumé généré en {duration:.2f} secondes")
            copy_button(st.session_state.current_summary,
                tooltip="Copier le résumé",
                copied_label="Copié!",
                icon="st",
                key=str(uuid.uuid4())) 

            # persist into history
            if st.session_state.video_url not in [item["video_url"] for item in st.session_state.history]:
                st.session_state.history.append({
                    "video_url": st.session_state.video_url,
                    "metadata": metadata,
                    "transcript": st.session_state.current_transcription,
                    "summary": st.session_state.current_summary,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                try:
                    utils.save_history(st.session_state.history)
                except Exception:
                    pass

        
    else:
        # If user didn't click generate but session has previous results, show them persistently
        if st.session_state.current_transcription or st.session_state.current_summary:
            col_left, col_right = st.columns([1.5, 2.5], gap="large")
            with col_left:
                st.subheader("✍ Transcription")
                with st.container(height=500):
                    st.markdown(
                        f"""
                        <div style="white-space: pre-wrap;">{st.session_state.current_transcription or ''}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                copy_button(st.session_state.current_transcription,
                            tooltip="Copier la transcription",
                            copied_label="Copié!",
                            icon="st",
                            key=str(uuid.uuid4()))

            with col_right:
                st.subheader("📰 Résumé généré")
                with st.container(height=500):
                    st.markdown(
                        f"""
                        <div style="white-space: pre-wrap;">{st.session_state.current_summary or ''}</div>
                        """,
                        unsafe_allow_html=True,
                    )

                copy_button(st.session_state.current_summary,
                            tooltip="Copier le résumé",
                            copied_label="Copié!",
                            icon="st",
                            key=str(uuid.uuid4()))  