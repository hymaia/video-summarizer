import streamlit as st
from video_summarizer.transcriptor import transcription
from video_summarizer import utils
import time
import uuid
from datetime import datetime


st.title("🎬 Video Summarizer")
options = ["URL", "Titre"]
methode_recherche = st.pills("Méthode de recherche", options, selection_mode="single", default="URL")

if "video_url" not in st.session_state:
    st.session_state.video_url = None  
if "show_search_dialog" not in st.session_state:
    st.session_state.show_search_dialog = False
if "history" not in st.session_state:
    st.session_state.history = []


if methode_recherche == "URL":
    st.write("Colle une URL YouTube pour générer la transcription et le résumé.")
    st.session_state.video_url = st.text_input(
        "URL YouTube",
        placeholder="https://www.youtube.com/watch?v=3g7y-mG4QBc",
    )

if methode_recherche == "Titre":
    query = st.text_input(
        "Titre de la vidéo",
        placeholder="ForwardDataConf MCP Hymaïa",
    )
    
    st.session_state.search_query = query
    if st.button("Rechercher"):
        st.session_state.show_search_dialog = True

    if st.session_state.get("show_search_dialog"):
        utils.youtube_search_dialog(st.session_state.search_query)

if st.session_state.video_url:
    
    if methode_recherche == "Titre":
        st.write(f"URL Vidéo sélectionnée : {st.session_state.video_url}")

    if st.button("Transcrire & résumer"):
        st.divider()
        if "youtube.com" not in st.session_state.video_url: 
            st.warning("Veuillez entrer une URL YouTube valide.")
            st.stop()

        col_left, col_right = st.columns([1.5, 2.5], gap="large")

        with col_left:
            video_id = transcription.extract_video_id(st.session_state.video_url)
            metadata = utils.get_video_metadata(video_id)
            st.subheader("📸 Vidéo")
            
            col1, col2 = st.columns([1.5, 2.5], gap="large")
            
            with col1 : 
                st.image(
                utils.thumbnail_url(video_id), width=100, use_container_width=True)

            with col2: 
                if metadata:
                    st.markdown(f"**🎬 Titre**  \n{metadata['title']}  - ⏱️ {metadata['duration']}")


            # Transcription
            with st.spinner("Récupération de la transcription..."):
                try:
                    transcript = transcription.read_transcript(
                        st.session_state.video_url
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la transcription : {e}")
                    st.stop()

            st.subheader("📄 Transcription")
            with st.container(height=500) :
                st.markdown(
                f"""
                <div style="white-space: pre-wrap;">
                    {transcript}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_right:
            # Generation du rapport final
            st.subheader("Génération du résumé")
            prompt = utils.context_llm_resume +  f"### METADATA :\nTitle: {metadata['title']}\n ### Description: {metadata['description']}\n\n" + f"\n\n ### TRANSCRIPT :\n{transcript}\n\n"
            
            output_container = st.container(height=500)
            placeholder = output_container.empty()
            full_text = ""

            #with st.spinner("Génération du résumé..."):
            start_time = time.perf_counter()

            with st.spinner("Génération du résumé..."):
                for chunk in utils.stream_openai_response(prompt):
                    full_text += chunk
                    placeholder.markdown(full_text + " ▌")

            duration = time.perf_counter() - start_time


            st.success(f"Résumé généré en {duration:.2f} secondes")

            st.session_state.history.append({
                "id": str(uuid.uuid4()),
                "video_url": st.session_state.video_url,
                "metadata": metadata,
                "transcript": transcript,
                "summary": full_text,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
