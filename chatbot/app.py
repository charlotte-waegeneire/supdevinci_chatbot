import streamlit as st

from chatbot.pages.chatbot import show_chatbot
from chatbot.pages.home import show_home


def main():
    """Main application function using st.Page and st.navigation."""
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

    home_page = st.Page(show_home, title="Accueil", icon="🏠", default=True)

    chatbot_page = st.Page(show_chatbot, title="Chatbot", icon="🤖")

    pg = st.navigation([home_page, chatbot_page])

    with st.sidebar:
        st.title("🎓 Sup de Vinci")
        st.markdown("**École d'informatique**")
        st.markdown("---")
        st.markdown("### 📍 Navigation")

        if st.button("🏠 Accueil", use_container_width=True):
            st.switch_page(home_page)
        if st.button("🤖 Chatbot", use_container_width=True):
            st.switch_page(chatbot_page)

    pg.run()


if __name__ == "__main__":
    main()
