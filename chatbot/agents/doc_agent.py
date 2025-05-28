# -*- coding: utf-8 -*-
"""
chatbot/agents/doc_agent.py

Agent Documentation (RAG) pour "vChatbot SupdeVinci".
Ce module utilise LangChain Community + Chroma via langchain-chroma pour répondre
à partir d'une base documentaire (PDFs, règlements, brochures),
avec optimisation des appels LLM pour limiter les coûts.

Ajout d'un système de prompt pour structurer et clarifier les réponses du chatbot.
"""
import os
from dotenv import load_dotenv

# Mise à jour des imports vers langchain-community
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class DocAgent:
    def __init__(
        self,
        docs_path: str = "chatbot/data/documents",
        persist_directory: str = "chatbot/data/vectorstore/supdevinci_docs",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "gpt-3.5-turbo",
        retrieval_k: int = 4,
        max_response_tokens: int = 512,
        # Template de prompt pour la question initiale
        question_prompt_template: str = (
            """Tu es un assistant intelligent spécialisé dans les formations de Sup de Vinci, une école d'informatique. Réponds comme si tu faisais partie de l'équipe pédagogique de Sup de Vinci.
Ta mission est de fournir des réponses précises et structurées à partir des documents ci-dessous, même si les informations sont dispersées.

Si la question concerne les formations, réponds de manière concise et précise en te basant sur les documents fournis.
Ne réponds jamais de sorte à dire que tu n'as pas d'informations, mais mets en lien les mots clés de la question avec les documents et formule une réponse.

Ne te contente pas de retranscrire les documents, mais reformule les réponses de manière claire et concise en récupérant les informations pertinentes.
Ne garde pas en mémoire les réponses que tu as donné précédemment pour ne pas t'embrouiller.
Réponds à chaque demande comme si c'était à lui que tu parles.
Analyse les documents ou se trouvent les mots clés de la question et utilise-les pour construire une réponse complète si tu n'a pas d'informations completes.
Si les questions sont trop spécifiques comme par exemple que la question concerne un cas très précis ou une personne en particulier, réponds que tu n'as pas d'informations à ce sujet et oriente vers le service concerné.

Si la question reste dans le cadre de sup de vinci (à savoir formations d'école, de diplômes, informatique, ...) qui n'est pas présent dans les documents, réponds en t'adaptant à la question.
Si la question n'a rien à voir avec Sup De Vinci, réponds poliment que tu n'es pas apte à répondre à cette question.
Si ce sont des affirmations ou questions de politesse, réponds poliment et de manière appropriée.

10 lignes maximum (et pas 10 lignes en général).

Réponds concrétement et sois direct sans ajouter des mots pour embellir tes réponses. Parle factuellement et pas en suposition.\n
            Question : {question}"""
        ),
        # Template de prompt pour l'étape de raffinage
        refine_prompt_template: str = (
            "La réponse actuelle est :\n{existing_answer}\n"  
            "Nouvelles informations extraites :\n{new_content}\n"  
            "Veuillez améliorer la réponse pour qu'elle soit complète, claire et directe, en prenant bien en compte la question : {question}"
        ),
    ):
        """
        Initialise le DocAgent.
        - Charge/crée le vectorstore Chroma via langchain-chroma
        - Configure le modèle d'embedding HuggingFace
        - Prépare le chain RetrievalQA en mode refine avec prompts personnalisés
        - Supporte Azure OpenAI si les variables d'env sont fournies.
        """
        self.llm_model_name = llm_model_name
        self.docs_path = docs_path
        self.persist_directory = persist_directory
        self.retrieval_k = retrieval_k
        self.max_response_tokens = max_response_tokens

        # Création des PromptTemplates
        self.question_prompt = PromptTemplate(
            input_variables=["question"],
            template=question_prompt_template,
        )
        self.refine_prompt = PromptTemplate(
            input_variables=["existing_answer", "new_content", "question"],
            template=refine_prompt_template,
        )

        # Modèle d'embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        # Charger ou créer le vectorstore Chroma
        if os.path.exists(os.path.join(self.persist_directory, "index.sqlite3")):
            print(f"Chargement du vectorstore existant depuis {self.persist_directory}")
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding=self.embeddings,
                collection_name="supdevinci_docs",
            )
        else:
            self.db = self._build_vectorstore()

        # Chargement des variables Azure/OpenAI
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        deployment = os.getenv("AZURE_DEPLOYMENT_NAME")
        if not all([api_key, api_base, api_version, deployment]):
            raise ValueError(
                "Veuillez définir AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_API_VERSION et AZURE_DEPLOYMENT_NAME dans le .env."
            )

        # Chat LLM pour Azure OpenAI (mode refined)
        self.llm = AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=api_base,
            api_version=api_version,
            openai_api_key=api_key,
            temperature=0,
            max_tokens=self.max_response_tokens,
            model=self.llm_model_name,
        )

        # ——————————————————————————————————————————————————————————————————
        # Chaîne de retrieval  QA en mode map_reduce (contournement du refine bug)
        # 1) Prompt "map" : sur chaque chunk, répondre à la question à partir du contexte
        self.map_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "Vous êtes un assistant expert. En vous basant uniquement sur le contexte fourni, "
                "répondez de manière claire, concise et précise à la question.\n\n"
                "Contexte :\n{context}\n\n"
                "Question : {question}"
            ),
        )

        # 2) Prompt "combine" : fusionner les réponses partielles en une seule réponse cohérente
        self.combine_prompt = PromptTemplate(
            input_variables=["summaries", "question"],
            template=(
                "Vous êtes un assistant expert. Voici plusieurs réponses partielles extraites de différents "
                "extraits du document :\n{summaries}\n\n"
                "Veuillez combiner ces réponses en une réponse unique, claire, concise et précise "
                "à la question : {question}"
            ),
        )

        # 3) Instanciation du chain en map_reduce
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="map_reduce",
            retriever=self.db.as_retriever(search_kwargs={"k": self.retrieval_k}),
            return_source_documents=True,
            chain_type_kwargs={
                "question_prompt": self.map_prompt,
                "combine_prompt": self.combine_prompt,
            },
        )



    def _build_vectorstore(self) -> Chroma:
        """
        Ingeste les PDFs, segmente les textes, crée le vectorstore Chroma.
        """
        print(f"Chargement des documents PDF depuis {self.docs_path}...")
        loader = PyPDFDirectoryLoader(self.docs_path)
        docs = loader.load()
        if not docs:
            raise FileNotFoundError(f"Aucun PDF trouvé dans {self.docs_path}.")
        print(f"Documents chargés : {len(docs)}")

        # Découpage en chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
        )
        texts = splitter.split_documents(docs)
        print(f"Chunks créés : {len(texts)}")

        # Création du vectorstore
        print("Construction du vectorstore Chroma...")
        vectordb = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="supdevinci_docs",
        )
        print("Vectorstore prêt dans :", self.persist_directory)
        return vectordb

    def query(self, question: str) -> str:
        """
        Exécute la chaîne RAG pour répondre à la question.
        Affiche les sources utilisées et renvoie la réponse.
        """
        result = self.qa_chain({"query": question})
        # Logging des sources
        sources = [doc.metadata.get("source", "[source inconnue]") for doc in result["source_documents"]]
        print("Sources utilisées :", sources)
        return result["result"]

if __name__ == "__main__":
    # Démarrage interactif en terminal
    agent = DocAgent()
    print("""
Bienvenue dans le Chatbot SupdeVinci ! (tapez 'exit' pour quitter)
""")
    while True:
        try:
            question = input("Vous : ")
        except (KeyboardInterrupt, EOFError):
            print("""
Au revoir !""")
            break
        question = question.strip()
        if not question:
            continue
        if question.lower() in ['exit', 'quit', 'q']:
            print("Au revoir !")
            break
        # Envoi de la question à l'agent et affichage de la réponse
        reponse = agent.query(question)
        print("""
SupdeVinci :
""", reponse, """
""")
