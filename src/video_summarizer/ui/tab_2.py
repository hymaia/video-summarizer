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
    st.session_state.video_url = selected_item["video_url"]

    col_left, col_right = st.columns([1.5, 2.5], gap="large")

    with col_left:
        st.subheader("📸 Vidéo")
        st.image(utils.thumbnail_url(
            transcription.extract_video_id(selected_item["video_url"])
        ), use_container_width=True)

        st.markdown(f"**🎬 Titre**  \n{selected_item['metadata']['title']}")
        st.markdown(f"**⏱️ Durée**  \n{selected_item['metadata']['duration']}")

    with col_right:
        st.subheader("📄 Transcription")
        st.text_area(
            "",
            selected_item["transcript"],
            height=450,
        )

    st.subheader("Génération du résumé")
    st.markdown(selected_item["summary"])

