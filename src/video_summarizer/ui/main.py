import streamlit as st
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
from video_summarizer import utils

# Configuration de la page
st.set_page_config(
    page_title="Video Summarizer",
    page_icon=":material/dashboard:",
    layout="wide",
)


# logo 
utils.generate_padding_logo_sidebar()
utils.generate_padding_logo_main()
st.logo("../static/logo_video_summarizer.png")

# Definition des pages avec navigation top
print("current wd : " ,os.getcwd())
pages = [
    st.Page(
        r"tab_1.py",
        title="Principal",
        icon=":material/home:",
        default=True
    ),
    st.Page(
        r"tab_2.py",
        title="Historique",
        icon=":material/dashboard:",
    ),

]

# Navigation en position top
page = st.navigation(pages, position="sidebar")


# Execution de la page
page.run()