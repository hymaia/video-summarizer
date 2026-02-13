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
    page_icon="../static/VS_32x32.svg",
    layout="wide",
)


# logo 
#utils.generate_padding_logo_sidebar()
#utils.generate_padding_logo_main()
st.logo("../static/VS_logo.svg")

# Definition des pages avec navigation top
pages = [
    st.Page(
        r"tab_1.py",
        title="🏠 Principal",
        default=True
    ),
    st.Page(
        r"tab_2.py",
        title="🕒 Historique",
    ),
    st.Page(
        r"tab_3.py",
        title="⚙️ Paramètres",
    ),

]

# Navigation en position top
page = st.navigation(pages, position="sidebar")


# Execution de la page
page.run()