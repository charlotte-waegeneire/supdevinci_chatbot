from typing import Dict

from openai import AzureOpenAI

from chatbot.utils import get_env_variable


class MainAgent:
    def __init__(self):
        self.client = self._create_azure_client()
        self.conversation_history = []
        self.user_context = {}
        self.deployment_name = None

    def _create_azure_client(self):
        """Create an Azure OpenAI client instance"""
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

    def detect_intent(self, user_input: str) -> str:
        """Detect user intent from input"""
        intentions = {
            "web_info": [
                "admission",
                "formation",
                "campus",
                "programme",
                "école",
                "étudiant",
                "cours",
            ],
            "documentation": [
                "règlement",
                "brochure",
                "pdf",
                "document",
                "guide",
                "procédure",
            ],
            "contact": [
                "contact",
                "intéressé",
                "candidature",
                "postuler",
                "entreprise",
                "stage",
                "partenariat",
            ],
            "general": ["bonjour", "salut", "aide", "information", "question"],
        }

        user_lower = user_input.lower()

        for intent, keywords in intentions.items():
            if any(keyword in user_lower for keyword in keywords):
                return intent

        return "general"

    def _route_to_agent(self, intent: str) -> str:
        """Route to the appropriate agent based on intent"""
        routing_map = {
            "web_info": "web_agent",
            "documentation": "doc_agent",
            "contact": "action_agent",
            "general": "main_agent",
        }

        return routing_map.get(intent, "main_agent")

    def generate_response(self, user_input: str) -> Dict:
        """Generate a response and determine which agent to use"""

        intent = self.detect_intent(user_input)
        target_agent = self._route_to_agent(intent)

        self.conversation_history.append({"role": "user", "content": user_input})

        if target_agent == "main_agent":
            response = self._generate_general_response(user_input)
        else:
            response = f"Je vous oriente vers notre service spécialisé pour : {intent}"

        self.conversation_history.append({"role": "assistant", "content": response})

        return {
            "response": response,
            "intent": intent,
            "target_agent": target_agent,
            "needs_followup": target_agent != "main_agent",
        }

    def _generate_general_response(self, user_input: str) -> str:
        """Generate a general response using the LLM"""

        messages = [
            {
                "role": "system",
                "content": """Tu es un assistant virtuel de l'école SupdeVinci.
                Réponds de manière accueillante et professionnelle.""",
            }
        ]

        recent_history = (
            self.conversation_history[-6:]
            if len(self.conversation_history) > 6
            else self.conversation_history
        )
        messages.extend(recent_history)

        if not messages or messages[-1]["content"] != user_input:
            messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Désolé, une erreur s'est produite : {e!s}"

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def get_deployment_info(self):
        """Return deployment information"""
        return {
            "deployment_name": self.deployment_name,
            "endpoint": getattr(self.client, "_base_url", "Non disponible"),
        }


if __name__ == "__main__":
    agent = MainAgent()

    print("Informations du déploiement:", agent.get_deployment_info())

    response = agent.generate_response(
        "Bonjour, je suis intéressé par l'admission à l'école"
    )
    print("Réponse:", response["response"])
