import streamlit as st

from chatbot.pages.chatbot import show_chatbot
from chatbot.pages.home import show_home


def main():
    """Main application function."""
    st.set_page_config(
        page_title="Sup de Vinci - Chatbot", page_icon="🎓", layout="wide"
    )

    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {display: none}

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 50px;
            margin: 5px 0;
            font-weight: bold;
        }

        .stButton > button:hover {
            background-color: #f0f2f6;
            border-color: #1f77b4;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("🎓 Sup de Vinci")
    st.sidebar.markdown("**École d'informatique**")
    st.sidebar.markdown("---")

    st.sidebar.markdown("### 📍 Navigation")

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    if st.sidebar.button("🏠 Accueil", use_container_width=True):
        st.session_state.current_page = "home"
    if st.sidebar.button("🤖 Chatbot", use_container_width=True):
        st.session_state.current_page = "chatbot"

    if st.session_state.current_page == "home":
        show_home()
    elif st.session_state.current_page == "chatbot":
        show_chatbot()


if __name__ == "__main__":
    main()
