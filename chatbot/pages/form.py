"""Module for the Sup de Vinci application form page."""

import streamlit as st


def _validate_form_data(form_data):
    """Validate form data and return list of errors."""
    errors = []

    required_personal_fields = ["last_name", "first_name", "email", "phone"]
    if not all(form_data.get(field) for field in required_personal_fields):
        errors.append(
            "Veuillez remplir tous les champs d'information personnelle obligatoires"
        )

    if form_data.get("candidate_type") == "Sélectionnez votre situation":
        errors.append("Veuillez sélectionner votre situation")

    if form_data.get("current_level") == "Sélectionnez votre niveau":
        errors.append("Veuillez sélectionner votre niveau d'études")

    if form_data.get("target_level") == "Sélectionnez le niveau":
        errors.append("Veuillez sélectionner le niveau de formation souhaité")

    if form_data.get("preferred_campus") == "Sélectionnez un campus":
        errors.append("Veuillez sélectionner un campus")

    if not form_data.get("supdevinci_reason"):
        errors.append("Veuillez expliquer pourquoi Sup de Vinci vous intéresse")

    if not form_data.get("gdpr_consent"):
        errors.append("Vous devez accepter le traitement de vos données personnelles")

    return errors


def _display_next_steps(target_level):
    """Display next steps based on target level."""
    st.markdown("### 🎯 Prochaines étapes :")

    steps_map = {
        "Cycle Préparatoire (1 an)": """
            **Pour le Cycle Préparatoire :**
            1. Examen de votre dossier sous 48h
            2. Tests et entretien de motivation
            3. Coaching pour votre recherche d'alternance (années 3-5)
        """,
        "Bachelor (BAC+3)": """
            **Pour le Bachelor :**
            1. Analyse de votre dossier par nos équipes
            2. Tests techniques selon votre spécialisation
            3. Entretien de motivation personnalisé
        """,
        "Mastère (BAC+5)": """
            **Pour le Mastère :**
            1. Examen approfondi de votre parcours
            2. Tests techniques spécialisés obligatoires
            3. Entretien projet professionnel
        """,
    }

    if target_level in steps_map:
        st.info(steps_map[target_level])


def _display_application_summary(form_data):
    """Display application summary."""
    with st.expander("📋 Résumé de votre candidature", expanded=False):
        st.write(
            f"**Candidat(e) :** {form_data['first_name']} {form_data['last_name']}"
        )
        st.write(f"**Email :** {form_data['email']}")
        st.write(f"**Formation souhaitée :** {form_data['target_level']}")
        st.write(f"**Campus :** {form_data['preferred_campus']}")

        if form_data.get("bachelor_specializations"):
            specializations = ", ".join(form_data["bachelor_specializations"])
            st.write(f"**Spécialisations Bachelor :** {specializations}")

        if form_data.get("master_specializations"):
            specializations = ", ".join(form_data["master_specializations"])
            st.write(f"**Spécialisations Mastère :** {specializations}")


def _render_personal_info_section():
    """Render personal information section and return collected data."""
    st.subheader("📋 Informations personnelles")

    col1, col2 = st.columns(2)
    with col1:
        last_name = st.text_input("Nom *", placeholder="Votre nom de famille")
        email = st.text_input("Email *", placeholder="votre.email@exemple.com")
        phone = st.text_input("Téléphone *", placeholder="+33 6 12 34 56 78")

    with col2:
        first_name = st.text_input("Prénom *", placeholder="Votre prénom")
        age = st.number_input("Âge", min_value=16, max_value=50, value=18)
        city = st.text_input("Ville de résidence", placeholder="Votre ville")

    return {
        "last_name": last_name,
        "first_name": first_name,
        "email": email,
        "phone": phone,
        "age": age,
        "city": city,
    }


def _render_profile_section():
    """Render profile section and return collected data."""
    st.subheader("👤 Votre profil")

    col3, col4 = st.columns(2)
    with col3:
        candidate_type = st.selectbox(
            "Vous êtes *",
            [
                "Sélectionnez votre situation",
                "Lycéen(ne) - Terminale",
                "Étudiant(e) - BAC+1",
                "Étudiant(e) - BAC+2",
                "Étudiant(e) - BAC+3",
                "Diplômé(e) BAC+3",
                "Professionnel en reconversion",
                "Demandeur d'emploi",
                "Autre",
            ],
        )

        current_level = st.selectbox(
            "Niveau d'études actuel *",
            [
                "Sélectionnez votre niveau",
                "Terminale",
                "BAC+1",
                "BAC+2",
                "BAC+3",
                "BAC+4",
                "BAC+5 et plus",
            ],
        )

    with col4:
        origin_education = st.text_input(
            "Formation d'origine",
            placeholder="Ex: Bac S, DUT Informatique, BTS SIO...",
        )

        it_experience = st.selectbox(
            "Expérience en informatique",
            [
                "Aucune expérience",
                "Notions de base",
                "Quelques projets personnels",
                "Stage(s) en informatique",
                "Expérience professionnelle",
                "Développeur amateur",
                "Certifications IT",
            ],
        )

    return {
        "candidate_type": candidate_type,
        "current_level": current_level,
        "origin_education": origin_education,
        "it_experience": it_experience,
    }


def _render_formation_project_section():
    """Render formation project section and return collected data."""
    st.subheader("🎯 Votre projet de formation")

    col5, col6 = st.columns(2)
    with col5:
        target_level = st.selectbox(
            "Niveau de formation souhaité *",
            [
                "Sélectionnez le niveau",
                "Bachelor (BAC+3)",
                "Mastère (BAC+5)",
            ],
        )
    with col6:
        preferred_campus = st.selectbox(
            "Campus souhaité *",
            [
                "Sélectionnez un campus",
                "Paris La Défense",
                "Rennes",
                "Bordeaux",
                "Nantes",
                "Indifférent",
            ],
        )

    return {"target_level": target_level, "preferred_campus": preferred_campus}


def _render_specializations_section():
    """Render specializations section and return collected data."""
    st.subheader("🔧 Spécialisation(s) qui vous intéresse(nt)")
    st.write("*Basé sur les formations de Sup de Vinci*")

    st.write("**Spécialisations Bachelor :**")
    bachelor_specializations = st.multiselect(
        "Choisissez jusqu'à 3 spécialisations Bachelor",
        [
            "Systèmes, Réseaux et Cloud",
            "Data",
            "Développement",
            "Je ne sais pas encore",
        ],
        max_selections=3,
        placeholder="Sélectionnez",
    )

    st.write("**Spécialisations Mastère :**")
    master_specializations = st.multiselect(
        "Choisissez jusqu'à 3 spécialisations Mastère",
        [
            "🖥️ Développement Full Stack",
            "🔧 DevOps, Infrastructure & Cloud",
            "🧠 Big Data & IA",
            "🛡️ Cybersécurité",
            "🎯 Chef de projet IT / Product Owner",
            "Je ne sais pas encore",
        ],
        max_selections=3,
        placeholder="Sélectionnez",
    )

    return {
        "bachelor_specializations": bachelor_specializations,
        "master_specializations": master_specializations,
    }


def _render_motivations_section():
    """Render motivations section and return collected data."""
    st.subheader("💭 Vos motivations")

    col7, col8 = st.columns(2)
    with col7:
        professional_objective = st.selectbox(
            "Votre objectif professionnel principal",
            [
                "Pas encore défini",
                "Trouver un premier emploi dans l'IT",
                "Évoluer dans mon poste actuel",
                "Changer de secteur d'activité",
                "Créer ma propre entreprise",
                "Travailler dans une grande entreprise",
                "Rejoindre une startup",
                "Devenir consultant indépendant",
            ],
        )

    with col8:
        interested_sectors = st.multiselect(
            "Secteurs d'activité qui vous intéressent",
            [
                "Banque/Finance",
                "E-commerce",
                "Santé/Médical",
                "Automobile",
                "Jeux vidéo",
                "Intelligence artificielle",
                "Cybersécurité",
                "Cloud/Infrastructure",
                "Startup/Innovation",
                "Consulting",
                "Secteur public",
                "Pas de préférence",
            ],
            placeholder="Sélectionnez",
        )

    supdevinci_reason = st.text_area(
        "Pourquoi Sup de Vinci vous intéresse-t-elle ? *",
        placeholder="Expliquez en quelques lignes ce qui vous attire dans notre école...",
        height=100,
    )

    school_discovery = st.selectbox(
        "Comment avez-vous connu Sup de Vinci ?",
        [
            "Site internet",
            "Salon étudiant",
            "Journée portes ouvertes",
            "Réseaux sociaux",
            "Bouche-à-oreille",
            "Ancien étudiant",
            "Moteur de recherche",
            "Publicité",
            "Conseiller d'orientation",
            "Autre",
        ],
        placeholder="Sélectionnez une option",
    )

    return {
        "professional_objective": professional_objective,
        "interested_sectors": interested_sectors,
        "supdevinci_reason": supdevinci_reason,
        "school_discovery": school_discovery,
    }


def _render_support_section():
    """Render support section and return collected data."""
    st.subheader("📞 Accompagnement souhaité")

    col9, col10 = st.columns(2)
    with col9:
        info_needs = st.multiselect(
            "Informations souhaitées",
            [
                "Programme détaillé des formations",
                "Modalités d'admission",
                "Coût de la formation",
                "Aide au financement",
                "Vie étudiante",
                "Débouchés professionnels",
                "Partenariats entreprises",
                "Infrastructures et équipements",
            ],
            placeholder="Sélectionnez",
        )

        urgency = st.selectbox(
            "Urgence de votre demande",
            [
                "Pas d'urgence particulière",
                "J'aimerais être rappelé(e) rapidement",
                "C'est urgent, je dois me décider vite",
                "Je compare plusieurs écoles",
            ],
        )

    with col10:
        availability = st.multiselect(
            "Créneaux de disponibilité pour un appel",
            [
                "Matin (9h-12h)",
                "Après-midi (14h-17h)",
                "En soirée (18h-20h)",
                "Weekend",
                "Uniquement par email",
            ],
            placeholder="Sélectionnez",
        )

        specific_questions = st.text_area(
            "Questions spécifiques",
            placeholder="Y a-t-il des points particuliers que vous aimeriez aborder ?",
            height=80,
        )

    return {
        "info_needs": info_needs,
        "urgency": urgency,
        "availability": availability,
        "specific_questions": specific_questions,
    }


def _render_consents_section():
    """Render consents section and return collected data."""
    st.subheader("✅ Consentements")

    newsletter = st.checkbox("Je souhaite recevoir les actualités de Sup de Vinci")
    gdpr_consent = st.checkbox(
        "J'accepte que mes données soient utilisées pour le traitement de ma candidature *"
    )
    partner_contact = st.checkbox(
        "J'accepte d'être contacté(e) par des entreprises partenaires pour des opportunités"
    )

    return {
        "newsletter": newsletter,
        "gdpr_consent": gdpr_consent,
        "partner_contact": partner_contact,
    }


def _handle_form_submission(form_data):
    """Handle form submission logic."""
    errors = _validate_form_data(form_data)

    if errors:
        st.error("⚠️ Veuillez corriger les erreurs suivantes :")
        for error in errors:
            st.error(f"• {error}")
        return False

    st.success("✅ Votre candidature a été envoyée avec succès !")

    if "supdevinci_applications" not in st.session_state:
        st.session_state.supdevinci_applications = []

    st.session_state.supdevinci_applications.append(form_data)
    st.balloons()

    with st.container():
        _display_next_steps(form_data["target_level"])
        st.success(
            "📧 Vous recevrez un email de confirmation et nos équipes vous contacteront "
            "sous 7 jours maximum."
        )

    _display_application_summary(form_data)
    return True


def show_form():
    """Display the Sup de Vinci application form."""
    st.title("🎓 Formulaire de candidature - Sup de Vinci")
    st.write(
        "École d'informatique | Formations du BAC au BAC+5 | "
        "Paris La Défense, Rennes, Bordeaux, Nantes"
    )

    st.markdown("""
        ---
        **Vous êtes intéressé(e) par nos formations en informatique ?**
        Complétez ce formulaire pour que nos équipes puissent mieux vous accompagner
        dans votre projet.
        """)

    with st.form("supdevinci_candidature_form"):
        personal_data = _render_personal_info_section()
        profile_data = _render_profile_section()
        formation_data = _render_formation_project_section()
        specializations_data = _render_specializations_section()
        motivations_data = _render_motivations_section()
        support_data = _render_support_section()
        consents_data = _render_consents_section()

        st.divider()
        submitted = st.form_submit_button(
            "🚀 Envoyer ma candidature", type="primary", use_container_width=True
        )

        if submitted:
            form_data = {
                **personal_data,
                **profile_data,
                **formation_data,
                **specializations_data,
                **motivations_data,
                **support_data,
                **consents_data,
            }
            _handle_form_submission(form_data)

    st.divider()
    st.markdown("""
        ### 📌 Informations utiles

        **🏢 Sup de Vinci en quelques chiffres :**
        - Plus de 25 ans d'expérience
        - Formations du BAC au BAC+5 reconnues par l'État
        - 5 spécialisations métier en Mastère
        - Taux d'insertion : 88% à 100% selon les formations
        - Campus à Paris La Défense, Rennes, Bordeaux et Nantes

        **📞 Contact :**
        - Email : [email protected]
        - Téléphone : 01 41 16 71 83
        - Site web : [www.supdevinci.fr](https://www.supdevinci.fr)
        """)

    if (
        "supdevinci_applications" in st.session_state
        and st.session_state.supdevinci_applications
        and st.checkbox("🔧 Mode développement - Afficher les candidatures")
    ):
        st.subheader("📊 Candidatures reçues")
        for i, application in enumerate(st.session_state.supdevinci_applications):
            candidate_name = f"{application['first_name']} {application['last_name']}"
            with st.expander(
                f"Candidature {i + 1}: {candidate_name} - {application['target_level']}"
            ):
                st.json(application)
