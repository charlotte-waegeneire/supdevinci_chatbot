from datetime import datetime
import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.form import CollectionState, InformationCollectorAgent


def initialize_session_state():
    if "chatbot_agent" not in st.session_state:
        st.session_state.chatbot_agent = InformationCollectorAgent(
            "../data/sup_de_vinci_students.json"
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = st.session_state.chatbot_agent.process_user_input("start")
        st.session_state.messages.append(
            {"role": "assistant", "content": welcome_msg, "timestamp": datetime.now()}
        )

    if "input_disabled" not in st.session_state:
        st.session_state.input_disabled = False


def display_message(message, is_user=False):
    if is_user:
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(message["content"])


def display_progress_indicator():
    agent = st.session_state.chatbot_agent
    current_state = agent.current_state

    steps = [
        ("Accueil", CollectionState.GREETING),
        ("Nom", CollectionState.COLLECTING_NAME),
        ("Prénom", CollectionState.COLLECTING_FIRSTNAME),
        ("Téléphone", CollectionState.COLLECTING_PHONE),
        ("Email", CollectionState.COLLECTING_EMAIL),
        ("Terminé", CollectionState.COMPLETED),
    ]

    current_step = 0
    for i, (_, state) in enumerate(steps):
        if current_state == state:
            current_step = i
            break

    progress = current_step / (len(steps) - 1)

    st.sidebar.markdown("### 📋 Progression de l'inscription")
    st.sidebar.progress(progress)

    for i, (step_name, _) in enumerate(steps):
        if i < current_step:
            st.sidebar.markdown(f"✅ {step_name}")
        elif i == current_step:
            st.sidebar.markdown(f"🔄 **{step_name}** (en cours)")
        else:
            st.sidebar.markdown(f"⏳ {step_name}")


def display_collected_info():
    pass


def handle_completion():
    st.balloons()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🆕 Nouvelle inscription", type="primary", use_container_width=True
        ):
            st.session_state.chatbot_agent.reset_session()
            st.session_state.messages = []
            welcome_msg = st.session_state.chatbot_agent.process_user_input("start")
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now(),
                }
            )
            st.session_state.input_disabled = False
            st.rerun()


def show_statistics():
    try:
        stats = st.session_state.chatbot_agent.get_statistics()
        st.sidebar.markdown("### 📊 Statistiques")
        st.sidebar.metric("Inscriptions aujourd'hui", stats["today"])
        st.sidebar.metric("Total inscriptions", stats["total"])
    except Exception as e:
        st.sidebar.error(f"Erreur lors du chargement des statistiques: {e}")


def inject_custom_css():
    st.markdown(
        """
    <style>
    .stChatMessage {
        margin-bottom: 1rem;
    }

    .stProgress > div > div {
        background-color: #1f77b4;
    }

    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }

    .chat-container {
        max-height: 500px;
        overflow-y: auto;
    }

    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }

    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #f8f9fa;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def show_chatbot():
    inject_custom_css()
    initialize_session_state()

    st.title("🤖 Chatbot - Sup de Vinci")
    st.markdown("## 💬 Conversation")

    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            display_message(message, message["role"] == "user")

    if not st.session_state.input_disabled:
        user_input = st.chat_input(
            placeholder="Tapez votre message ici...",
            disabled=st.session_state.chatbot_agent.is_collection_complete(),
        )

        if user_input:
            st.session_state.messages.append(
                {"role": "user", "content": user_input, "timestamp": datetime.now()}
            )

            try:
                bot_response = st.session_state.chatbot_agent.process_user_input(
                    user_input
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": bot_response,
                        "timestamp": datetime.now(),
                    }
                )

                if st.session_state.chatbot_agent.is_collection_complete():
                    st.session_state.input_disabled = True

            except Exception as e:
                st.error(f"Erreur lors du traitement: {e}")

            st.rerun()

    if st.session_state.chatbot_agent.is_collection_complete():
        st.markdown("---")
        st.success("🎉 Inscription terminée avec succès!")
        handle_completion()

    with st.expander("📌️ Informations sur le chatbot"):
        st.markdown("""
        **Chatbot d'inscription Sup de Vinci**

        Ce chatbot vous aide à compléter votre inscription en collectant vos informations personnelles :
        - Nom et prénom
        - Numéro de téléphone
        - Adresse email

        Toutes les informations sont automatiquement sauvegardées de manière sécurisée.

        💡 **Conseils d'utilisation :**
        - Répondez aux questions une par une
        - Utilisez un format valide pour le téléphone (ex: 06.00.00.00.00)
        - Vérifiez votre adresse email avant validation
        """)

        if st.button("📞 Besoin d'aide ?"):
            st.info(
                "Pour toute assistance, contactez notre équipe pédagogique au 01.23.45.67.89"
            )


if __name__ == "__main__":
    show_chatbot()
