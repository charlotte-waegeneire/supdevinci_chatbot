import os
from typing import List

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureChatOpenAI

from chatbot.utils import get_env_variable

_ROOT_DIR = get_env_variable("ROOT_DIR")


class WebAgent:
    def __init__(
        self,
        data_folder: str = os.path.join(_ROOT_DIR, "chatbot/data/website_pages/"),
        persist_directory: str = os.path.join(
            _ROOT_DIR, "chatbot/data/vectorstore/supdevinci_web/"
        ),
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.data_folder = data_folder
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

        self.prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
                Tu es un assistant intelligent spécialisé dans les formations de Sup de Vinci, une école d'informatique. Tu réponds comme si tu faisais partie de l'équipe pédagogique.

                Part du principe que tu t'adresses à un étudiant ou un futur étudiant de Sup de Vinci. Dans le cas où il te précise un autre profil (entreprise, demandeur d'emploi, etc.), adapte toi à ce profil.

                Ta mission est de fournir des réponses précises, structurées et concises à partir des documents ci-dessous, même si les informations sont dispersées.

                Si la question porte sur les formations, base-toi uniquement sur les documents, reformule les informations de façon claire et synthétique. Ne retranscris pas les documents mot à mot.

                Ne réponds jamais que tu n'as pas d'informations. Analyse les mots clés de la question, trouve les passages correspondants dans les documents et construis une réponse cohérente. Si les informations sont incomplètes, exploite ce qui est pertinent sans inventer.

                Ne garde aucune mémoire des échanges précédents. Réponds à chaque question comme si c'était la première.

                Si la question est trop spécifique (cas personnel ou individuel), indique que tu ne peux pas répondre et oriente vers le service concerné.

                Si la question est liée à Sup de Vinci (formations, diplômes, informatique…) mais absente des documents, adapte ta réponse en restant dans le cadre de l'école.

                Si elle n'a aucun lien avec Sup de Vinci, indique poliment que tu n'es pas en mesure de répondre.

                Pour les contacts , donne ceux génériques de Sup de Vinci.

                Réponds concrétement et sois direct sans ajouter des mots pour embellir tes réponses. Parle factuellement et pas en suposition.

                Si la question concerne les formations, utilise uniquement les documents pertinents. Si elle est trop vague, demande des précisions.
                Si la question concerne d'autres sujets, utilise les documents pertinents mais reste concis et factuel.

                Réponses limitées à 10 lignes maximum (et pas 10 lignes en général).

                Documents :
                {context}

                Question : {question}
            """.strip(),
        )

        if os.path.exists(persist_directory) and os.listdir(persist_directory):
            self.db = Chroma(
                persist_directory=persist_directory, embedding_function=self.embeddings
            )
        else:
            self.db = Chroma.from_documents(
                self._load_documents(),
                self.embeddings,
                persist_directory=persist_directory,
            )

        self._setup_llm()

    def _load_documents(self) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = []

        for filename in os.listdir(self.data_folder):
            if filename.endswith((".md", ".txt")):
                with open(
                    os.path.join(self.data_folder, filename), encoding="utf-8"
                ) as f:
                    chunks = splitter.split_text(f.read())
                    docs.extend(
                        [
                            Document(page_content=c, metadata={"source": filename})
                            for c in chunks
                        ]
                    )

        return docs

    def _setup_llm(self, temperature: float = 0.0) -> None:
        self.llm = AzureChatOpenAI(
            azure_endpoint=get_env_variable("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=get_env_variable("AZURE_DEPLOYMENT_NAME"),
            api_key=get_env_variable("AZURE_OPENAI_API_KEY"),
            api_version=get_env_variable("AZURE_OPENAI_API_VERSION"),
            temperature=temperature,
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.db.as_retriever(
                search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.6}
            ),
            chain_type_kwargs={"prompt": self.prompt},
        )

    def query(self, question: str) -> dict:
        result = self.qa_chain.invoke({"query": question})
        return {"question": question, "answer": result["result"]}


if __name__ == "__main__":
    agent = WebAgent()
    print(agent.query("Quelles sont les formations proposées par Sup de Vinci ?"))
