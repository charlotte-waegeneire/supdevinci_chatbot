from setuptools import find_packages, setup

setup(
    name="supdevinci-chatbot",
    version="0.1.0",
    description="A Streamlit-based chatbot application",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.45.1,<2.0",
    ],
    extras_require={
        "dev": [
            "ruff>=0.11.11",
            "pre-commit>=4.2.0",
        ],
    },
)
