import streamlit as st
from video_summarizer import utils
from video_summarizer.transcriptor import transcription


if "history" not in st.session_state:
    st.session_state.history = []

if "current_item_id" not in st.session_state:
    st.session_state.current_item_id = None

with st.sidebar:
    st.subheader("🕘 Historique")

    if not st.session_state.history:
        st.caption("Aucun résumé généré")
    else:
        for item in reversed(st.session_state.history):
            label = f"🎬 {item['metadata']['title'][:40]}"
            if st.button(label, key=item["id"]):
                st.session_state.current_item_id = item["id"]

selected_item = None
if st.session_state.current_item_id:
    selected_item = next(
        (i for i in st.session_state.history if i["id"] == st.session_state.current_item_id),
        None
    )

if selected_item:
    st.divider()

    video_url = selected_item["video_url"]
    metadata = selected_item["metadata"]
    transcript = selected_item["transcript"]
    summary = selected_item["summary"]

    video_id = transcription.extract_video_id(video_url)

    col_left, col_right = st.columns([1.5, 2.5], gap="large")

    # ========= LEFT =========
    with col_left:
        st.subheader("📸 Vidéo")

        col1, col2 = st.columns([1.5, 2.5], gap="large")

        with col1:
            st.image(
                utils.thumbnail_url(video_id),
                use_container_width=True
            )

        with col2:
            st.markdown(
                f"**🎬 Titre**  \n{metadata['title']}  -  ⏱️ {metadata['duration']}"
            )

        st.subheader("📄 Transcription")
        st.text_area(
            label="",
            value=transcript,
            height=500,
        )

    # ========= RIGHT =========
    with col_right:
        st.subheader("Génération du résumé")
        st.markdown(
            summary,
            unsafe_allow_html=False 
        )
