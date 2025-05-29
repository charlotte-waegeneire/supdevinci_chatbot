import logging
import traceback
from typing import Dict

from openai import AzureOpenAI

from chatbot.agents.doc_agent import DocAgent
from chatbot.agents.form_agent import FormAgent
from chatbot.agents.web_agent import WebAgent
from chatbot.utils import get_env_variable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainAgent:
    def __init__(self):
        """Initialize the unified main agent with all specialized agents"""
        self.client = self._create_azure_client()
        self.conversation_history = []
        self.user_context = {}
        self.deployment_name = None

        self._initialize_agents()

        self.current_agent = None
        self.collection_in_progress = False
        self.last_intent = None
        self.conversation_context = {
            "topic": None,
            "user_type": None,
            "previous_questions": [],
        }

    def _create_azure_client(self):
        """Create an Azure OpenAI client instance"""
        try:
            api_key = get_env_variable("AZURE_OPENAI_API_KEY")
            endpoint = get_env_variable("AZURE_OPENAI_ENDPOINT")
            api_version = get_env_variable("AZURE_OPENAI_API_VERSION")
            deployment_name = get_env_variable("AZURE_DEPLOYMENT_NAME")

            self.deployment_name = deployment_name

            return AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=api_key,
            )
        except Exception as e:
            logger.error(f"Failed to create Azure OpenAI client: {e}")
            raise

    def _initialize_agents(self):
        """Initialize all specialized agents with better error handling"""
        self.web_agent = None
        self.doc_agent = None
        self.information_collector = None

        try:
            self.web_agent = WebAgent()
            logger.info("Web Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Web Agent: {e}")

        try:
            self.doc_agent = DocAgent()
            logger.info("Doc Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Doc Agent: {e}")

        try:
            self.information_collector = FormAgent()
            logger.info("Information Collector Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Information Collector Agent: {e}")

    def detect_intent(self, user_input: str) -> str:
        """Enhanced intent detection with conversation context"""
        user_lower = user_input.lower()

        if (
            self.collection_in_progress
            and self.information_collector
            and not self.information_collector.is_collection_complete()
        ):
            return "contact_collection"

        if self.last_intent and self._is_followup_question(user_input):
            return self.last_intent

        intentions = {
            "web_info": [
                "formation",
                "formations",
                "master",
                "mastère",
                "bachelor",
                "campus",
                "programme",
                "programmes",
                "école",
                "ecole",
                "étudiant",
                "etudiant",
                "cours",
                "cursus",
                "diplôme",
                "diplome",
                "informatique",
                "supdevinci",
                "sup de vinci",
                "admission",
                "admissions",
                "spécialité",
                "specialite",
                "spécialités",
                "specialites",
                "domaine",
                "filière",
                "filiere",
                "parcours",
                "option",
                "options",
            ],
            "documentation": [
                "règlement",
                "reglement",
                "brochure",
                "brochures",
                "pdf",
                "document",
                "documents",
                "guide",
                "guides",
                "procédure",
                "procedure",
                "manuel",
                "livret",
                "syllabus",
                "programme détaillé",
                "contenu",
            ],
            "contact": [
                "contact",
                "contacter",
                "intéressé",
                "interesse",
                "candidature",
                "postuler",
                "inscription",
                "inscrire",
                "candidat",
                "rdv",
                "rendez-vous",
                "information",
                "renseignement",
            ],
            "general": [
                "bonjour",
                "salut",
                "hello",
                "bonsoir",
                "aide",
                "aider",
                "merci",
                "question",
                "questions",
            ],
        }

        intent_scores = {}
        for intent, keywords in intentions.items():
            score = sum(1 for keyword in keywords if keyword in user_lower)
            if score > 0:
                intent_scores[intent] = score

        if intent_scores:
            detected_intent = max(intent_scores, key=intent_scores.get)
            self.last_intent = detected_intent
            return detected_intent

        return "general"

    def _is_followup_question(self, user_input: str) -> bool:
        """Check if the user input is a follow-up question"""
        followup_indicators = [
            "autre",
            "autres",
            "plus",
            "encore",
            "également",
            "aussi",
            "existe",
            "y a-t-il",
            "quoi d'autre",
            "d'autres",
            "sinon",
            "et",
            "ou",
            "comment",
            "pourquoi",
            "quand",
            "où",
        ]
        user_lower = user_input.lower()
        return any(indicator in user_lower for indicator in followup_indicators)

    def _route_to_agent(self, intent: str) -> str:
        """Route to the appropriate agent based on intent"""
        routing_map = {
            "web_info": "web_agent",
            "documentation": "doc_agent",
            "contact": "action_agent",
            "contact_collection": "action_agent",
            "general": "main_agent",
        }
        return routing_map.get(intent, "main_agent")

    def generate_response(self, user_input: str) -> Dict:
        """Generate a comprehensive response using the appropriate agent"""
        try:
            self.conversation_context["previous_questions"].append(user_input)
            if len(self.conversation_context["previous_questions"]) > 5:
                self.conversation_context["previous_questions"].pop(0)

            intent = self.detect_intent(user_input)
            target_agent = self._route_to_agent(intent)

            self.conversation_history.append({"role": "user", "content": user_input})

            response = ""
            agent_used = target_agent
            additional_info = {}

            if target_agent == "web_agent":
                response = self._handle_web_agent_safe(user_input)
                agent_used = "web_agent"

            elif target_agent == "doc_agent":
                response = self._handle_doc_agent_safe(user_input)
                agent_used = "doc_agent"

            elif target_agent == "action_agent":
                response, additional_info = self._handle_action_agent_safe(
                    user_input, intent
                )
                agent_used = "action_agent"

            else:
                response = self._generate_general_response_safe(user_input, intent)
                agent_used = "main_agent"

            self.conversation_history.append({"role": "assistant", "content": response})

            self._update_conversation_context(intent, user_input, response)

            return {
                "response": response,
                "intent": intent,
                "agent_used": agent_used,
                "needs_followup": target_agent != "main_agent",
                "collection_status": self._get_collection_status(),
                "success": True,
                **additional_info,
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            error_response = self._get_fallback_response(user_input)

            return {
                "response": error_response,
                "intent": "error",
                "agent_used": "main_agent",
                "needs_followup": False,
                "success": False,
                "error": str(e),
            }

    def _handle_web_agent_safe(self, user_input: str) -> str:
        """Handle web agent queries with error handling"""
        try:
            if not self.web_agent:
                return "L'agent Web n'est pas disponible pour le moment. Cependant, je peux vous dire que Sup de Vinci propose plusieurs formations en informatique. Pouvez-vous préciser quel type d'information vous recherchez ?"

            result = self.web_agent.query(user_input)
            return result.get(
                "answer",
                "Je n'ai pas pu trouver d'information spécifique. Pouvez-vous reformuler votre question ?",
            )
        except Exception as e:
            logger.error(f"Web agent error: {e}")
            return "Je rencontre des difficultés pour accéder aux informations du site. Cependant, je peux vous confirmer que Sup de Vinci propose des formations en informatique incluant des Mastères spécialisés. Souhaitez-vous que je vous mette en contact avec notre équipe pour plus de détails ?"

    def _handle_doc_agent_safe(self, user_input: str) -> str:
        """Handle documentation agent queries with error handling"""
        try:
            if not self.doc_agent:
                return "L'agent Documentation n'est pas disponible actuellement. Pour consulter nos documents officiels, je vous recommande de contacter directement notre équipe pédagogique."

            return self.doc_agent.query(user_input)
        except Exception as e:
            logger.error(f"Doc agent error: {e}")
            return "Je ne peux pas accéder à la documentation pour le moment. Pour obtenir des informations détaillées sur nos formations, puis-je recueillir vos coordonnées pour qu'un conseiller vous recontacte ?"

    def _handle_action_agent_safe(
        self, user_input: str, intent: str
    ) -> tuple[str, dict]:
        """Handle information collection agent with error handling"""
        try:
            if not self.information_collector:
                return (
                    "Le système de collecte d'informations n'est pas disponible. Vous pouvez nous contacter directement au 01.23.45.67.89 ou par email à contact@supdevinci.fr",
                    {},
                )

            if intent == "contact" and not self.collection_in_progress:
                self.collection_in_progress = True
                self.information_collector.reset_session()
                response = self.information_collector.process_user_input("")
            else:
                response = self.information_collector.process_user_input(user_input)

            additional_info = {}
            if self.information_collector.is_collection_complete():
                self.collection_in_progress = False
                stats = self.information_collector.get_statistics()
                additional_info = {
                    "collection_complete": True,
                    "collected_info": self.information_collector.get_current_info(),
                    "statistics": stats,
                }
            else:
                additional_info = {
                    "collection_complete": False,
                    "current_info": self.information_collector.get_current_info(),
                }

            return response, additional_info

        except Exception as e:
            logger.error(f"Action agent error: {e}")
            self.collection_in_progress = False
            return (
                "Une erreur s'est produite. Vous pouvez nous contacter directement au 01.23.45.67.89 pour toute demande d'information.",
                {},
            )

    def _generate_general_response_safe(self, user_input: str) -> str:
        """Generate a general response with error handling"""
        try:
            if not self.client:
                return self._get_fallback_response(user_input)

            system_prompt = f"""Tu es un assistant virtuel de l'école Sup de Vinci, une école d'informatique prestigieuse.

            Tu es accueillant, professionnel et serviable. Tu peux aider avec :
            - Des informations générales sur l'école (formations, admissions, campus)
            - Des questions sur la documentation (règlements, brochures)
            - La mise en contact pour les candidatures ou partenariats.

            Contexte de conversation actuel: {self.conversation_context}

            Si une question nécessite des informations spécifiques que tu n'as pas, propose des alternatives ou oriente vers le service approprié.
            Reste dans le contexte de Sup de Vinci et de l'enseignement informatique.

            Si l'utilisateur pose des questions de suivi, garde le contexte de la conversation précédente."""

            messages = [{"role": "system", "content": system_prompt}]

            recent_history = (
                self.conversation_history[-6:]
                if len(self.conversation_history) > 6
                else self.conversation_history
            )
            messages.extend(recent_history)

            if not messages or messages[-1]["content"] != user_input:
                messages.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM response error: {e}")
            return self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """Provide contextual fallback responses"""
        user_lower = user_input.lower()

        if any(
            word in user_lower
            for word in ["formation", "master", "mastère", "programme"]
        ):
            return """Sup de Vinci propose plusieurs formations en informatique :

            • **Mastères spécialisés** en développement, cybersécurité, data science
            • **Bachelors** en informatique avec différentes spécialisations
            • **Formations courtes** et certifications professionnelles

            Pour plus de détails spécifiques, puis-je recueillir vos coordonnées pour qu'un conseiller vous recontacte ?"""

        if any(
            word in user_lower for word in ["contact", "inscription", "candidature"]
        ):
            return """Je peux vous aider avec votre candidature !

            Pour commencer votre inscription chez Sup de Vinci, j'aurais besoin de quelques informations :
            - Vos coordonnées
            - Le type de formation qui vous intéresse
            - Votre niveau d'études actuel

            Souhaitez-vous commencer le processus maintenant ?"""

        return """Je suis là pour vous aider avec toutes vos questions sur Sup de Vinci !

            Je peux vous renseigner sur :
            🎓 Nos formations et programmes
            📋 Les modalités d'inscription
            🏢 Nos campus et équipements

            Que souhaitez-vous savoir ?"""

    def _update_conversation_context(self, intent: str, user_input: str):
        """Update conversation context for better follow-up handling"""
        if intent == "web_info":
            if "formation" in user_input.lower():
                self.conversation_context["topic"] = "formations"
            elif "campus" in user_input.lower():
                self.conversation_context["topic"] = "campus"

        if any(
            word in user_input.lower()
            for word in ["étudiant", "candidat", "inscription"]
        ):
            self.conversation_context["user_type"] = "student"
        elif any(
            word in user_input.lower() for word in ["entreprise", "recruteur", "stage"]
        ):
            self.conversation_context["user_type"] = "company"

    def _get_collection_status(self) -> dict:
        """Get current collection status"""
        if not self.information_collector:
            return {"active": False}

        return {
            "active": self.collection_in_progress,
            "complete": self.information_collector.is_collection_complete(),
            "current_state": self.information_collector.current_state.value
            if hasattr(self.information_collector, "current_state")
            else None,
        }

    def reset_conversation(self):
        """Reset conversation history and states"""
        self.conversation_history = []
        self.user_context = {}
        self.current_agent = None
        self.collection_in_progress = False
        self.last_intent = None
        self.conversation_context = {
            "topic": None,
            "user_type": None,
            "previous_questions": [],
        }

        if self.information_collector:
            self.information_collector.reset_session()

    def get_agent_status(self) -> dict:
        """Get status of all agents"""
        return {
            "web_agent": self.web_agent is not None,
            "doc_agent": self.doc_agent is not None,
            "information_collector": self.information_collector is not None,
            "azure_client": self.client is not None,
            "deployment_name": self.deployment_name,
        }

    def get_conversation_summary(self) -> dict:
        """Get conversation summary and statistics"""
        stats = {}
        if self.information_collector:
            try:
                stats = self.information_collector.get_statistics()
            except Exception:
                stats = {"total": 0, "today": 0}

        return {
            "message_count": len(self.conversation_history),
            "collection_in_progress": self.collection_in_progress,
            "current_agent": self.current_agent,
            "conversation_context": self.conversation_context,
            "statistics": stats,
        }
