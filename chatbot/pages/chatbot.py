from datetime import datetime
import json
import traceback

import streamlit as st

from chatbot.agents.form_agent import CollectionState
from chatbot.agents.main_agent import MainAgent


def initialize_session_state():
    """Initialize session state for the enhanced chatbot"""

    if "unified_agent" not in st.session_state:
        try:
            with st.spinner("🚀 Initialisation des agents intelligents..."):
                st.session_state.unified_agent = MainAgent()
                st.session_state.agent_initialized = True
                st.session_state.init_error = None
        except Exception as e:
            st.session_state.unified_agent = None
            st.session_state.agent_initialized = False
            st.session_state.init_error = str(e)

    if "messages" not in st.session_state:
        st.session_state.messages = []
        welcome_msg = get_welcome_message()
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": welcome_msg,
                "timestamp": datetime.now(),
                "agent_used": "main_agent",
                "intent": "greeting",
            }
        )

    if "conversation_mode" not in st.session_state:
        st.session_state.conversation_mode = "general"

    if "input_disabled" not in st.session_state:
        st.session_state.input_disabled = False

    if "error_count" not in st.session_state:
        st.session_state.error_count = 0

    if "chat_stats" not in st.session_state:
        st.session_state.chat_stats = {
            "total_messages": 0,
            "intents_detected": [],
            "agents_used": [],
            "successful_responses": 0,
            "failed_responses": 0,
        }


def get_welcome_message():
    """Get welcome message for the chatbot"""
    return """
🎓 **Bonjour et bienvenue chez Sup de Vinci !**

Je suis votre assistant virtuel intelligent. Je peux vous aider avec :

🌐 **Informations sur l'école** : formations, admissions, campus, programmes
📚 **Documentation** : règlements, brochures, guides détaillés
📝 **Contact et candidatures** : collecte d'informations pour votre inscription
💬 **Questions générales** : tout ce qui concerne Sup de Vinci

**Comment puis-je vous aider aujourd'hui ?**
    """.strip()


def display_message(message, is_user=False):
    """Display a chat message with enhanced styling"""
    if is_user:
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])
    else:
        agent_used = message.get("agent_used", "main_agent")

        agent_avatars = {
            "web_agent": "🌐",
            "doc_agent": "📚",
            "action_agent": "📝",
            "main_agent": "🤖",
        }

        avatar = agent_avatars.get(agent_used, "🤖")

        with st.chat_message("assistant", avatar=avatar):
            if agent_used != "main_agent":
                agent_names = {
                    "web_agent": "Agent Site Web",
                    "doc_agent": "Agent Documentation",
                    "action_agent": "Agent Contact",
                }
                st.caption(f"🏷️ {agent_names.get(agent_used, agent_used)}")

            st.markdown(message["content"])

            # Show error indicator if this was an error response
            if message.get("intent") == "error" and message.get("show_debug", False):
                with st.expander("🔧 Informations de débogage"):
                    st.code(
                        message.get(
                            "debug_info", "Aucune information de débogage disponible"
                        )
                    )


def display_progress_indicator():
    """Display progress indicator for information collection"""
    try:
        if (
            st.session_state.agent_initialized
            and hasattr(st.session_state.unified_agent, "information_collector")
            and st.session_state.unified_agent.information_collector
        ):
            collector = st.session_state.unified_agent.information_collector
            current_state = getattr(collector, "current_state", None)

            if current_state and current_state != CollectionState.GREETING:
                st.sidebar.markdown("### 📋 Progression")

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
                st.sidebar.progress(progress)

                for i, (step_name, _) in enumerate(steps):
                    if i < current_step:
                        st.sidebar.markdown(f"✅ {step_name}")
                    elif i == current_step:
                        st.sidebar.markdown(f"🔄 **{step_name}**")
                    else:
                        st.sidebar.markdown(f"⏳ {step_name}")

    except Exception as e:
        st.sidebar.error(f"Erreur progression: {e}")


def handle_completion():
    """Handle completion of information collection"""
    st.balloons()

    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "🆕 Nouvelle conversation", type="primary", use_container_width=True
        ):
            st.session_state.messages = []
            if st.session_state.agent_initialized:
                st.session_state.unified_agent.reset_conversation()

            welcome_msg = get_welcome_message()
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now(),
                    "agent_used": "main_agent",
                    "intent": "greeting",
                }
            )

            st.session_state.input_disabled = False
            st.session_state.conversation_mode = "general"
            st.session_state.error_count = 0
            st.rerun()


def inject_custom_css():
    """Inject custom CSS for better styling"""
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

    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }

    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #f8f9fa;
    }

    .agent-badge {
        background-color: #e3f2fd;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-left: 5px;
    }

    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def show_help_section():
    """Show help and information section"""
    with st.expander("📌 Guide d'utilisation du chatbot"):
        st.markdown("""
        **🤖 Chatbot Multi-Agents Sup de Vinci**

        Notre assistant intelligent utilise plusieurs agents spécialisés :

        🌐 **Agent Site Web** : Répond aux questions sur les formations, admissions, campus
        - Exemple: *"Quelles formations proposez-vous ?"*
        - Exemple: *"Existe-t-il d'autres spécialités ?"*

        📚 **Agent Documentation** : Consulte les règlements, brochures, guides
        - Exemple: *"Montrez-moi le règlement intérieur"*

        📝 **Agent Contact** : Collecte vos informations pour candidatures
        - Exemple: *"Je suis intéressé par une inscription"*

        🤖 **Assistant Principal** : Coordination et réponses générales

        **💡 Conseils d'utilisation :**
        - Posez des questions claires et précises
        - L'assistant détecte automatiquement le bon agent à utiliser
        - Pour les questions de suivi, utilisez des mots comme "autre", "également", "aussi"
        - Le chatbot maintient le contexte de la conversation
        - En cas d'erreur, le système propose des alternatives

        **🔧 En cas de problème :**
        - Le chatbot fonctionne en mode dégradé si certains agents sont indisponibles
        - Les erreurs sont automatiquement gérées avec des réponses de secours
        - Vous pouvez toujours nous contacter directement si nécessaire
        """)

        if st.button("📞 Besoin d'aide supplémentaire ?"):
            st.info(
                "Contactez notre équipe pédagogique au 01.23.45.67.89 ou par email à contact@supdevinci.fr"
            )


def show_chatbot():
    """Main chatbot interface with multi-agent integration and improved error handling"""
    inject_custom_css()
    initialize_session_state()

    st.title("🤖 Assistant Virtuel Sup de Vinci")
    st.markdown("## 💬 Conversation Multi-Agents")

    if not st.session_state.agent_initialized:
        st.error(
            "⚠️ Erreur d'initialisation des agents. Vérifiez votre configuration Azure OpenAI."
        )
        with st.expander("Détails de l'erreur"):
            st.code(st.session_state.init_error)

        st.info(
            "💡 Le chatbot peut fonctionner en mode dégradé. Certaines fonctionnalités peuvent être limitées."
        )

        if st.button("🔄 Réessayer l'initialisation"):
            st.rerun()

        return

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_message(message, message["role"] == "user")

    if not st.session_state.input_disabled:
        user_input = st.chat_input(
            placeholder="Posez votre question sur Sup de Vinci...", disabled=False
        )

        if user_input:
            st.session_state.messages.append(
                {"role": "user", "content": user_input, "timestamp": datetime.now()}
            )

            st.session_state.chat_stats["total_messages"] += 1

            try:
                with st.spinner("🤔 L'assistant analyse votre demande..."):
                    response = st.session_state.unified_agent.generate_response(
                        user_input
                    )

                if response.get("success", True):
                    st.session_state.chat_stats["successful_responses"] += 1
                else:
                    st.session_state.chat_stats["failed_responses"] += 1
                    st.session_state.error_count += 1

                bot_message = {
                    "role": "assistant",
                    "content": response["response"],
                    "timestamp": datetime.now(),
                    "agent_used": response.get("agent_used", "main_agent"),
                    "intent": response.get("intent", "general"),
                }

                if response.get("intent") == "error" and st.session_state.get(
                    "debug_mode", False
                ):
                    bot_message["show_debug"] = True
                    bot_message["debug_info"] = response.get("error", "Erreur inconnue")

                st.session_state.messages.append(bot_message)

                st.session_state.chat_stats["intents_detected"].append(
                    response.get("intent", "unknown")
                )
                st.session_state.chat_stats["agents_used"].append(
                    response.get("agent_used", "unknown")
                )

                collection_status = response.get("collection_status", {})
                if collection_status.get("complete"):
                    st.session_state.input_disabled = True
                    st.session_state.conversation_mode = "completed"

                if response.get("intent") == "contact" and not collection_status.get(
                    "active"
                ):
                    st.success(
                        "✨ Processus de contact initié ! Suivez les instructions ci-dessus."
                    )

            except Exception as e:
                st.session_state.error_count += 1
                st.session_state.chat_stats["failed_responses"] += 1

                error_msg = "Une erreur inattendue s'est produite. Notre équipe technique a été notifiée."

                fallback_response = """Je rencontre une difficulté technique, mais je peux tout de même vous aider !

                🎓 **Pour les formations** : Sup de Vinci propose des Mastères en informatique avec plusieurs spécialisations
                📞 **Pour nous contacter** : 01.23.45.67.89 ou contact@supdevinci.fr
                📧 **Pour candidater** : Utilisez notre formulaire en ligne ou contactez-nous directement
                Que puis-je faire d'autre pour vous aider ?"""

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": fallback_response,
                        "timestamp": datetime.now(),
                        "agent_used": "main_agent",
                        "intent": "error",
                        "show_debug": st.session_state.get("debug_mode", False),
                        "debug_info": str(e) + "\n" + traceback.format_exc()
                        if st.session_state.get("debug_mode", False)
                        else None,
                    }
                )

                st.error(error_msg)

            st.rerun()

    if st.session_state.conversation_mode == "completed":
        st.markdown("---")
        st.success("🎉 Collecte d'informations terminée avec succès!")
        handle_completion()

    display_progress_indicator()

    st.sidebar.markdown("### 🎛️ Contrôles")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.agent_initialized:
                st.session_state.unified_agent.reset_conversation()

            welcome_msg = get_welcome_message()
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": welcome_msg,
                    "timestamp": datetime.now(),
                    "agent_used": "main_agent",
                    "intent": "greeting",
                }
            )
            st.session_state.error_count = 0
            st.rerun()

    with col2:
        if (
            st.button("💾 Export", use_container_width=True)
            and st.session_state.messages
        ):
            export_data = {
                "conversation": st.session_state.messages,
                "timestamp": datetime.now().isoformat(),
                "stats": st.session_state.chat_stats,
                "agent_status": st.session_state.unified_agent.get_agent_status()
                if st.session_state.agent_initialized
                else {},
            }
            st.sidebar.download_button(
                label="📥 Télécharger",
                data=json.dumps(export_data, ensure_ascii=False, indent=2, default=str),
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    st.sidebar.markdown("---")
    debug_mode = st.sidebar.checkbox(
        "🔧 Mode débogage", value=st.session_state.get("debug_mode", False)
    )
    st.session_state.debug_mode = debug_mode

    if debug_mode:
        st.sidebar.info(
            "Mode débogage activé - Les erreurs détaillées seront affichées"
        )

    # Help section
    show_help_section()


if __name__ == "__main__":
    show_chatbot()
