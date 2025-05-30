from datetime import datetime
from enum import Enum
import os
import re
from typing import Dict, List

import pandas as pd

from chatbot.utils import get_env_variable

EXCEL_FILEPATH = os.path.join(
    get_env_variable("EXCEL_FILEPATH"), "sup_de_vinci_students.xlsx"
)


class CollectionState(Enum):
    GREETING = "greeting"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_FIRSTNAME = "collecting_firstname"
    COLLECTING_PHONE = "collecting_phone"
    COLLECTING_EMAIL = "collecting_email"
    COMPLETED = "completed"


class FormAgent:
    def __init__(self, output_file: str = EXCEL_FILEPATH):
        self.output_file = output_file
        self.reset_session()

        self.messages = {
            CollectionState.GREETING: [
                "Je vais vous aider à compléter votre inscription.",
                "Pour commencer, pouvez-vous me donner votre nom de famille ?",
            ],
            CollectionState.COLLECTING_NAME: [
                "Parfait ! Maintenant, quel est votre prénom ?",
                "Merci ! Et votre prénom, s'il vous plaît ?",
            ],
            CollectionState.COLLECTING_FIRSTNAME: [
                "Excellent ! J'ai besoin maintenant de votre numéro de téléphone.",
                "Parfait ! Pouvez-vous me communiquer votre numéro de téléphone ?",
            ],
            CollectionState.COLLECTING_PHONE: [
                "Merci ! Pour finir, j'aurais besoin de votre adresse email.",
                "Parfait ! Dernière information : votre adresse email, s'il vous plaît.",
            ],
            CollectionState.COMPLETED: [
                "Excellent ! J'ai bien enregistré toutes vos informations :",
                "Parfait ! Voici un récapitulatif de vos informations :",
            ],
        }

        self.error_messages = {
            "phone": "Le numéro de téléphone ne semble pas valide. Pouvez-vous le saisir à nouveau ? (Format attendu : 06.12.34.56.78 ou 0612345678)",
            "email": "L'adresse email ne semble pas valide. Pouvez-vous la saisir à nouveau ?",
            "name": "Le nom ne peut pas être vide. Pouvez-vous le saisir à nouveau ?",
            "firstname": "Le prénom ne peut pas être vide. Pouvez-vous le saisir à nouveau ?",
        }

    def reset_session(self):
        self.current_state = CollectionState.GREETING
        self.user_info = {
            "nom": "",
            "prenom": "",
            "telephone": "",
            "email": "",
            "timestamp": "",
        }
        self.conversation_history = []

    def validate_phone(self, phone: str) -> bool:
        clean_phone = re.sub(r"[\s\.\-]", "", phone)
        patterns = [
            r"^0[1-9](\d{8})$",
            r"^\+33[1-9](\d{8})$",
        ]
        return any(re.match(pattern, clean_phone) for pattern in patterns)

    def validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email.strip()) is not None

    def validate_name(self, name: str) -> bool:
        return (
            len(name.strip()) >= 2
            and name.strip().replace(" ", "").replace("-", "").isalpha()
        )

    def format_phone(self, phone: str) -> str:
        clean_phone = re.sub(r"[\s\.\-]", "", phone)
        if clean_phone.startswith("+33"):
            clean_phone = "0" + clean_phone[3:]

        if len(clean_phone) == 10:
            return f"{clean_phone[:2]}.{clean_phone[2:4]}.{clean_phone[4:6]}.{clean_phone[6:8]}.{clean_phone[8:]}"
        return clean_phone

    def process_user_input(self, user_input: str) -> str:
        user_input = user_input.strip()
        self.conversation_history.append(f"Utilisateur: {user_input}")

        response = ""

        if self.current_state == CollectionState.GREETING:
            response = self._handle_greeting()
        elif self.current_state == CollectionState.COLLECTING_NAME:
            response = self._handle_name_collection(user_input)
        elif self.current_state == CollectionState.COLLECTING_FIRSTNAME:
            response = self._handle_firstname_collection(user_input)
        elif self.current_state == CollectionState.COLLECTING_PHONE:
            response = self._handle_phone_collection(user_input)
        elif self.current_state == CollectionState.COLLECTING_EMAIL:
            response = self._handle_email_collection(user_input)
        elif self.current_state == CollectionState.COMPLETED:
            response = (
                "Merci ! Vos informations ont déjà été enregistrées. "
                "Y a-t-il autre chose pour laquelle je peux vous aider ?"
            )

        self.conversation_history.append(f"Agent: {response}")
        return response

    def _handle_greeting(self) -> str:
        self.current_state = CollectionState.COLLECTING_NAME
        return " ".join(self.messages[CollectionState.GREETING])

    def _handle_name_collection(self, user_input: str) -> str:
        if self.validate_name(user_input):
            self.user_info["nom"] = user_input.strip().title()
            self.current_state = CollectionState.COLLECTING_FIRSTNAME
            return self.messages[CollectionState.COLLECTING_NAME][0]
        return self.error_messages["name"]

    def _handle_firstname_collection(self, user_input: str) -> str:
        if self.validate_name(user_input):
            self.user_info["prenom"] = user_input.strip().title()
            self.current_state = CollectionState.COLLECTING_PHONE
            return self.messages[CollectionState.COLLECTING_FIRSTNAME][0]
        return self.error_messages["firstname"]

    def _handle_phone_collection(self, user_input: str) -> str:
        if self.validate_phone(user_input):
            self.user_info["telephone"] = self.format_phone(user_input)
            self.current_state = CollectionState.COLLECTING_EMAIL
            return self.messages[CollectionState.COLLECTING_PHONE][0]
        return self.error_messages["phone"]

    def _handle_email_collection(self, user_input: str) -> str:
        if self.validate_email(user_input):
            self.user_info["email"] = user_input.strip().lower()
            self.current_state = CollectionState.COMPLETED
            return self._complete_collection()
        return self.error_messages["email"]

    def _complete_collection(self) -> str:
        self.user_info["timestamp"] = datetime.now().isoformat()
        self.save_to_excel()

        return f"""
        {self.messages[CollectionState.COMPLETED][0]}
        \n\n• **Nom:** {self.user_info["nom"]}
        \n• **Prénom:** {self.user_info["prenom"]}
        \n• **Téléphone:** {self.user_info["telephone"]}
        \n• **Email:** {self.user_info["email"]}
        \n\n✅ Vos informations ont été enregistrées avec succès !
        \nUn conseiller vous contactera prochainement pour la suite de votre inscription à Sup de Vinci.
        \n\nMerci et à bientôt ! 🎓
        """.strip()

    def save_to_excel(self):
        """Save user information to Excel file"""
        try:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

            if not self.output_file.endswith(".xlsx"):
                self.output_file = self.output_file + ".xlsx"

            try:
                df_existing = pd.read_excel(self.output_file, engine="openpyxl")
            except FileNotFoundError:
                df_existing = pd.DataFrame(
                    columns=["nom", "prenom", "telephone", "email", "timestamp"]
                )
            except Exception as e:
                print(
                    f"Warning: Could not read existing file ({e}). Creating new file."
                )
                df_existing = pd.DataFrame(
                    columns=["nom", "prenom", "telephone", "email", "timestamp"]
                )

            new_row = pd.DataFrame([self.user_info])
            df_updated = pd.concat([df_existing, new_row], ignore_index=True)

            df_updated.to_excel(self.output_file, index=False, engine="openpyxl")

        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde: {e}") from e

    def get_conversation_history(self) -> List[str]:
        return self.conversation_history.copy()

    def is_collection_complete(self) -> bool:
        return self.current_state == CollectionState.COMPLETED

    def get_current_info(self) -> Dict:
        return self.user_info.copy()

    def get_statistics(self) -> Dict:
        """Get statistics from Excel file"""
        try:
            file_path = self.output_file
            if not file_path.endswith(".xlsx"):
                file_path = file_path + ".xlsx"

            df = pd.read_excel(file_path, engine="openpyxl")

            today = datetime.now().strftime("%Y-%m-%d")

            today_count = 0
            if "timestamp" in df.columns:
                today_count = len(df[df["timestamp"].astype(str).str.startswith(today)])

            return {"total": len(df), "today": today_count}

        except (FileNotFoundError, Exception):
            return {"total": 0, "today": 0}
