import os
from typing import Optional

from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AzureOpenAI
from pydantic import Field

from chatbot.utils import get_env_variable


class AzureOpenAILLM(LLM):
    """Custom LangChain LLM wrapper for Azure OpenAI"""

    azure_endpoint: str = Field(...)
    api_key: str = Field(...)
    deployment: str = Field(...)
    api_version: str = Field(default="2024-12-01-preview")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=512)

    _client: Optional[AzureOpenAI] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
        )

    @property
    def _llm_type(self) -> str:
        return "azure_openai"

    def _call(
        self,
        prompt: str,
        stop: Optional[list[str]] = None,
    ) -> str:
        """Call Azure OpenAI API"""
        response = self._client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            model=self.deployment,
            stop=stop,
        )
        return response.choices[0].message.content


class DocAgent:
    def __init__(
        self,
        docs_path: str = "chatbot/data/documents",
        persist_directory: str = "chatbot/data/vectorstore",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_deployment: str = "gpt-4o-mini",
        retrieval_k: int = 3,
        max_response_tokens: int = 512,
    ):
        """
        Initialise le DocAgent avec Azure OpenAI.
        - Charge/crée le vectorstore Chroma via langchain-chroma
        - Configure le modèle d'embedding HuggingFace
        - Prépare le chain RetrievalQA avec Azure OpenAI
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

        azure_endpoint = get_env_variable("AZURE_OPENAI_ENDPOINT")
        api_key = get_env_variable("AZURE_OPENAI_API_KEY")
        api_version = get_env_variable("AZURE_OPENAI_API_VERSION")

        if not azure_endpoint or not api_key:
            raise ValueError(
                "Les variables d'environnement AZURE_OPENAI_ENDPOINT et AZURE_OPENAI_API_KEY doivent être définies."
            )

        print(f"Utilisation d'Azure OpenAI - Endpoint: {azure_endpoint}")

        # LLM Azure OpenAI personnalisé
        self.llm = AzureOpenAILLM(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            deployment=llm_deployment,
            api_version=api_version,
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
            raise FileNotFoundError(
                f"Aucun PDF trouvé dans {self.docs_path}. Vérifiez le chemin et les fichiers .pdf."
            )
        print(f"Documents chargés : {len(docs)}")

        # Découpage en chunks pour optimiser la recherche
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
        )
        texts = splitter.split_documents(docs)
        if not texts:
            raise ValueError(
                "Le découpage des documents a produit 0 chunks. Vérifiez le contenu des PDF."
            )
        print(f"Chunks créés : {len(texts)}")

        # Création du vectorstore via from_documents
        print(
            "Construction du vectorstore Chroma... (cela peut prendre quelques instants)"
        )
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
    agent = DocAgent(llm_deployment="gpt-4o-mini")
    print(
        agent.query(
            "Comment être admis à la formation Mastère Big Data de Sup de Vinci ?"
        )
    )
