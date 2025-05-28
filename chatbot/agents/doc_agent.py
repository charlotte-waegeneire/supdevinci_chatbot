import os
import warnings

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chatbot.utils import get_env_variable

warnings.filterwarnings("ignore", category=DeprecationWarning)


class DocAgent:
    def __init__(
        self,
        docs_path: str = "chatbot/data/documents",
        persist_directory: str = "chatbot/data/vectorstore/supdevinci_docs",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "gpt-3.5-turbo",
        retrieval_k: int = 4,
        max_response_tokens: int = 512,
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

        self.question_prompt = PromptTemplate(
            input_variables=["question"],
            template=question_prompt_template,
        )
        self.refine_prompt = PromptTemplate(
            input_variables=["existing_answer", "new_content", "question"],
            template=refine_prompt_template,
        )

        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        if os.path.exists(os.path.join(self.persist_directory, "index.sqlite3")):
            print(f"Chargement du vectorstore existant depuis {self.persist_directory}")
            self.db = Chroma(
                persist_directory=self.persist_directory,
                embedding=self.embeddings,
                collection_name="supdevinci_docs",
            )
        else:
            self.db = self._build_vectorstore()

        api_key = get_env_variable("AZURE_OPENAI_API_KEY")
        api_base = get_env_variable("AZURE_OPENAI_ENDPOINT")
        api_version = get_env_variable("AZURE_OPENAI_API_VERSION")
        deployment = get_env_variable("AZURE_DEPLOYMENT_NAME")
        if not all([api_key, api_base, api_version, deployment]):
            raise ValueError(
                "Veuillez définir AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_API_VERSION et AZURE_DEPLOYMENT_NAME dans le .env."
            )

        self.llm = AzureChatOpenAI(
            azure_deployment=deployment,
            azure_endpoint=api_base,
            api_version=api_version,
            openai_api_key=api_key,
            temperature=0,
            max_tokens=self.max_response_tokens,
            model=self.llm_model_name,
        )

        self.map_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "Vous êtes un assistant expert. En vous basant uniquement sur le contexte fourni, "
                "répondez de manière claire, concise et précise à la question.\n\n"
                "Contexte :\n{context}\n\n"
                "Question : {question}"
            ),
        )

        self.combine_prompt = PromptTemplate(
            input_variables=["summaries", "question"],
            template=(
                "Vous êtes un assistant expert. Voici plusieurs réponses partielles extraites de différents "
                "extraits du document :\n{summaries}\n\n"
                "Veuillez combiner ces réponses en une réponse unique, claire, concise et précise "
                "à la question : {question}"
            ),
        )

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

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
        )
        texts = splitter.split_documents(docs)
        print(f"Chunks créés : {len(texts)}")

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
        """
        result = self.qa_chain({"query": question})
        return result["result"]


if __name__ == "__main__":
    agent = DocAgent()
    question = "Parle moi de la formation en data science chez SupDevinci"
    print(agent.query(question))
