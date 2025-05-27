"""Home page module for Sup de Vinci chatbot."""

import streamlit as st


def show_home():
    """Display the home page of the Sup de Vinci chatbot."""
    st.title("🏠 Accueil - Sup de Vinci")

    st.markdown("""
    ## Bienvenue sur le portail Sup de Vinci ! 🎓

    **Sup de Vinci** est une école d'informatique qui forme les talents de demain
    dans les domaines du développement, de la cybersécurité, des données et du gaming.

    ### 🎯 Que pouvez-vous faire ici ?

    - **📝 Déposer une candidature** : Utilisez notre formulaire interactif
    - **💬 Poser vos questions** : Notre chatbot est là pour vous aider
    - **📚 Découvrir nos formations** : Bachelor et Mastère en informatique

    ### 🏢 Nos campus

    - **Paris La Défense** : Au cœur du quartier d'affaires
    - **Nanterre** : Campus moderne et connecté
    - **Bordeaux** : Dans l'écosystème tech bordelais
    - **Lyon** : Au centre de la French Tech lyonnaise

    ---

    👈 **Utilisez le menu à gauche pour naviguer**
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Étudiants", "3,000+")

    with col2:
        st.metric("Taux d'insertion", "85%")

    with col3:
        st.metric("Entreprises partenaires", "200+")
