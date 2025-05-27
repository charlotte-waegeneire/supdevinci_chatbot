# -*- coding: utf-8 -*-
"""
chatbot/agents/doc_agent.py

Agent Documentation (RAG) pour "vChatbot SupdeVinci".
Ce module utilise LangChain Community + Chroma via langchain-chroma pour répondre
à partir d'une base documentaire (PDFs, règlements, brochures),
avec optimisation des appels LLM pour limiter les coûts.
"""
import os
from dotenv import load_dotenv

# Mise à jour des imports vers langchain-community
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
# from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class DocAgent:
    def __init__(
        self,
        docs_path: str = "chatbot/data/documents",
        persist_directory: str = "chatbot/data/vectorstore",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "gpt-3.5-turbo",
        retrieval_k: int = 3,
        max_response_tokens: int = 512,
    ):
        """
        Initialise le DocAgent.
        - Charge/crée le vectorstore Chroma via langchain-chroma
        - Configure le modèle d'embedding HuggingFace
        - Prépare le chain RetrievalQA en limitant le nombre de chunks retournés
          et la longueur max de la réponse pour maîtriser la consommation de tokens.
        - Supporte Azure OpenAI si les variables d'env sont fournies.
        """
        self.docs_path = docs_path
        self.persist_directory = persist_directory
        self.retrieval_k = retrieval_k
        self.max_response_tokens = max_response_tokens

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
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_api_base = os.getenv("OPENAI_ENDPOINT")

        print(openai_api_base)

        if not openai_api_key or not openai_api_base:
            raise ValueError(
                "Les variables d'environnement OPENAI_API_KEY et OPENAI_ENDPOINT doivent être définies."
            )

                # LLM pour la génération de réponses, support Azure OpenAI
        # On utilise le nom de déploiement plutôt que model_name pour Azure
        self.llm = ChatOpenAI(
            openai_api_base=openai_api_base,
            openai_api_key=openai_api_key,
            temperature=0,
            max_tokens=self.max_response_tokens,
        )

        # Chaîne de retrieval + QA
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(search_kwargs={"k": self.retrieval_k}),
        )

    def _build_vectorstore(self) -> Chroma:
        """
        Ingeste les PDFs, segmente les textes, crée le vectorstore Chroma.
        """
        print(f"Chargement des documents PDF depuis {self.docs_path}...")
        loader = PyPDFDirectoryLoader(self.docs_path)
        docs = loader.load()
        if not docs:
            raise FileNotFoundError(f"Aucun PDF trouvé dans {self.docs_path}. Vérifiez le chemin et les fichiers .pdf.")
        print(f"Documents chargés : {len(docs)}")

        # Découpage en chunks pour optimiser la recherche
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
        )
        texts = splitter.split_documents(docs)
        if not texts:
            raise ValueError("Le découpage des documents a produit 0 chunks. Vérifiez le contenu des PDF.")
        print(f"Chunks créés : {len(texts)}")

        # Création du vectorstore via from_documents
        print("Construction du vectorstore Chroma... (cela peut prendre quelques instants)")
        vectordb = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="supdevinci_docs",
        )
        print("Vectorstore créé et persistant dans :", self.persist_directory)
        return vectordb

    def query(self, question: str) -> str:
        """
        Exécute la chaîne RAG pour répondre à la question.
        Renvoie la réponse texte générée par l'LLM.
        """
        # Utilisation de run bien que dépréciée, pour compatibilité immédiate
        return self.qa_chain.run(question)

if __name__ == "__main__":
    # Exemple d'utilisation
    agent = DocAgent()
    print(agent.query(
        "Comment être admis à la formation Mastère Big Data & IA de Sup de Vinci ?"
    ))
