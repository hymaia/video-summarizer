import streamlit as st
import pandas as pd
from video_summarizer import utils
import os


utils.inject_global_styles()

utils.create_correct_transcription_file("video_summarizer/data/correct_transcriptions.csv")

st.title("Mise à jour de l'application")
st.subheader("Mise à jour des erreurs de transcription")

df = pd.read_csv("video_summarizer/data/correct_transcriptions.csv")

edited_df = st.data_editor(df, num_rows="dynamic")

if st.button("Enregistrer les modifications"):
    edited_df.to_csv("video_summarizer/data/correct_transcriptions.csv", index=False)
    st.session_state.correct_transcription_file = pd.read_csv("video_summarizer/data/correct_transcriptions.csv")
    st.success("Modifications enregistrées avec succès !")
