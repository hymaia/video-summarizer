import streamlit as st
from video_summarizer.transcriptor import transcription
from video_summarizer import utils
import time


st.title("🎬 Video Summarizer")
options = ["URL", "Titre"]
methode_recherche = st.pills("Méthode de recherche", options, selection_mode="single", default="URL")

if "video_url" not in st.session_state:
    st.session_state.video_url = None  

if methode_recherche == "URL":
    st.write("Colle une URL YouTube pour générer la transcription et le résumé.")
    st.session_state.video_url = st.text_input(
        "URL YouTube",
        placeholder="https://www.youtube.com/watch?v=3g7y-mG4QBc",
    )

if methode_recherche == "Titre":
    query = st.text_input(
        "Titre de la vidéo",
        placeholder="Hymaïa LLM presentation",
    )
    if query:
        utils.youtube_search_dialog(query)


if st.session_state.video_url:
    if methode_recherche == "Titre":
        st.write(f"URL Vidéo sélectionnée : {st.session_state.video_url}")

    if st.button("Transcrire & résumer"):
        col_left, col_right = st.columns([1, 2.5], gap="large")

        with col_left:
            video_id = transcription.extract_video_id(st.session_state.video_url)

            metadata = utils.get_video_metadata(video_id)

            st.subheader("📸 Vidéo")

            st.image(
                utils.thumbnail_url(video_id),
                use_container_width=True, width=150
            )

            if metadata:
                st.markdown(f"**🎬 Titre**  \n{metadata['title']}")
                st.markdown(f"**⏱️ Durée**  \n{metadata['duration']}")

            st.caption(f"Video ID : {video_id}")


        with col_right:
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
            st.text_area(
                label="",
                value=transcript,
                height=450,
            )

        # Generation du rapport final
        st.subheader("Génération du résumé")
        prompt = utils.context_llm_resume +  f"### METADATA :\nTitle: {metadata['title']}\n ### Description: {metadata['description']}\n\n" + f"\n\n ### TRANSCRIPT :\n{transcript}\n\n"
        
        placeholder = st.empty()
        full_text = ""

        #with st.spinner("Génération du résumé..."):
        start_time = time.perf_counter()

        with st.spinner("Génération du résumé..."):
            for chunk in utils.stream_openai_response(prompt):
                full_text += chunk
                placeholder.markdown(full_text + " ▌")

        duration = time.perf_counter() - start_time


        st.success(f"Résumé généré en {duration:.2f} secondes")

