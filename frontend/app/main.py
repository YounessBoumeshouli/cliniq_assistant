import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://backend:8000"
AUTH_URL = f"{API_BASE}/auth"
QUERY_URL = f"{API_BASE}/query"
USERS_URL = f"{API_BASE}/users"

st.set_page_config(
    page_title="CliniQ - Assistant Médical",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .answer-box {
        background-color: #f0f7ff;
        border-left: 4px solid #1E88E5;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .query-card {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .stButton>button {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)


if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def get_error_message(res):
    """Extract error message from backend response (handles both formats)."""
    try:
        data = res.json()
        return data.get("detail") or data.get("error") or str(data)
    except Exception:
        return f"Erreur HTTP {res.status_code}"


def login_page():
    st.markdown('<div class="main-header">🏥 CliniQ</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Assistant Médical Intelligent</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Connectez-vous")
            email = st.text_input("Email", placeholder="docteur@hopital.com")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.warning("Veuillez remplir tous les champs")
                else:
                    try:
                        res = requests.post(f"{AUTH_URL}/login", json={"email": email, "password": password})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token = data["access_token"]
                            user_res = requests.get(f"{AUTH_URL}/me", headers={"Authorization": f"Bearer {data['access_token']}"})
                            if user_res.status_code == 200:
                                st.session_state.user = user_res.json()
                                st.success("Connexion réussie!")
                                st.rerun()
                            else:
                                st.session_state.token = None
                                st.error(f"Erreur récupération profil: {get_error_message(user_res)}")
                        else:
                            st.error(get_error_message(res))
                    except requests.exceptions.ConnectionError:
                        st.error("Impossible de se connecter au serveur backend")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Créer un compte")
            username = st.text_input("Nom d'utilisateur", placeholder="Dr. Dupont")
            email = st.text_input("Email", placeholder="docteur@hopital.com", key="reg_email")
            password = st.text_input("Mot de passe", type="password", key="reg_pass",
                                    help="Min 8 caractères, 1 majuscule, 1 minuscule, 1 chiffre")
            role = st.selectbox("Rôle", ["medecin", "admin"])
            submit = st.form_submit_button("S'inscrire", use_container_width=True)
            
            if submit:
                if not username or not email or not password:
                    st.warning("Veuillez remplir tous les champs")
                else:
                    try:
                        res = requests.post(f"{AUTH_URL}/register", json={
                            "username": username,
                            "email": email,
                            "password": password,
                            "role": role
                        })
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token = data["access_token"]
                            user_res = requests.get(f"{AUTH_URL}/me", headers={"Authorization": f"Bearer {data['access_token']}"})
                            if user_res.status_code == 200:
                                st.session_state.user = user_res.json()
                                st.success("Compte créé avec succès!")
                                st.rerun()
                            else:
                                st.session_state.token = None
                                st.error(f"Erreur récupération profil: {get_error_message(user_res)}")
                        else:
                            st.error(get_error_message(res))
                    except requests.exceptions.ConnectionError:
                        st.error("Impossible de se connecter au serveur backend")


def assistant_page():
    st.markdown("## 🤖 Assistant Médical")
    st.markdown("Posez vos questions médicales et obtenez des réponses basées sur les protocoles cliniques.")
    
    with st.form("query_form"):
        question = st.text_area("Votre question", placeholder="Ex: Quels sont les traitements recommandés pour le prurit ?", height=100)
        col1, col2 = st.columns([3, 1])
        with col1:
            evaluate = st.checkbox("Évaluer la réponse (avec métriques RAG)", value=False)
        with col2:
            submit = st.form_submit_button("🔍 Rechercher", use_container_width=True)
        
        if submit:
            if not question:
                st.warning("Veuillez poser une question")
            else:
                with st.spinner("Recherche en cours..."):
                    try:
                        endpoint = "/assistant/evaluate" if evaluate else "/assistant"
                        res = requests.post(
                            f"{QUERY_URL}{endpoint}",
                            json={"query_text": question},
                            headers=get_headers()
                        )
                        
                        if res.status_code == 200:
                            data = res.json()
                            st.markdown("### 💬 Réponse")
                            st.markdown(f'<div class="answer-box">{data["answer"]}</div>', unsafe_allow_html=True)
                            
                            if evaluate and "metrics" in data:
                                st.markdown("### 📊 Métriques d'évaluation RAG")
                                m = data["metrics"]
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Answer Relevance", f"{m['answer_relevance']:.2%}")
                                col2.metric("Faithfulness", f"{m['faithfulness']:.2%}")
                                col3.metric("Precision@K", f"{m['precision_at_k']:.2%}")
                                col4.metric("Recall@K", f"{m['recall_at_k']:.2%}")
                        else:
                            st.error(f"Erreur: {get_error_message(res)}")
                    except requests.exceptions.ConnectionError:
                        st.error("Impossible de se connecter au serveur backend")


def my_queries_page():
    st.markdown("## 📋 Mon Historique")
    
    user_id = st.session_state.user["id"]
    try:
        res = requests.get(f"{QUERY_URL}/queries/user/{user_id}", headers=get_headers())
    except requests.exceptions.ConnectionError:
        st.error("Impossible de se connecter au serveur backend")
        return
    
    if res.status_code == 200:
        queries = res.json()
        
        if not queries:
            st.info("Vous n'avez pas encore de requêtes. Utilisez l'assistant pour poser des questions!")
        else:
            st.markdown(f"**{len(queries)} requête(s) trouvée(s)**")
            
            for q in reversed(queries):
                with st.expander(f"📝 {q['query'][:60]}..." if len(q['query']) > 60 else f"📝 {q['query']}"):
                    st.markdown(f"**Question:** {q['query']}")
                    st.markdown("---")
                    st.markdown(f"**Réponse:** {q['response']}")
                    st.markdown("---")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if q.get('created_at'):
                            st.caption(f"📅 {q['created_at']}")
                    with col2:
                        if st.button("🗑️ Supprimer", key=f"del_{q['id']}"):
                            del_res = requests.delete(f"{QUERY_URL}/queries/{q['id']}", headers=get_headers())
                            if del_res.status_code == 200:
                                st.success("Requête supprimée!")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {get_error_message(del_res)}")
    else:
        st.error(f"Erreur: {get_error_message(res)}")


def admin_users_page():
    st.markdown("## 👥 Gestion des Utilisateurs")
    
    try:
        res = requests.get(f"{USERS_URL}/", headers=get_headers())
    except requests.exceptions.ConnectionError:
        st.error("Impossible de se connecter au serveur backend")
        return
    
    if res.status_code == 200:
        users = res.json()
        
        st.markdown(f"**{len(users)} utilisateur(s)**")
        
        for user in users:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
                col1.write(f"**{user['username']}**")
                col2.write(user['email'])
                col3.write(f"🏷️ {user['role']}")
                col4.write(f"📅 {str(user.get('created_at', ''))[:10]}")
                with col5:
                    if user['id'] != st.session_state.user['id']:
                        if st.button("🗑️", key=f"del_user_{user['id']}"):
                            del_res = requests.delete(f"{USERS_URL}/{user['id']}", headers=get_headers())
                            if del_res.status_code == 200:
                                st.success("Utilisateur supprimé!")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {get_error_message(del_res)}")
                st.divider()
    else:
        st.error(f"Erreur: {get_error_message(res)}")


def admin_queries_page():
    st.markdown("## 📊 Toutes les Requêtes")
    
    try:
        res = requests.get(f"{QUERY_URL}/queries", headers=get_headers())
    except requests.exceptions.ConnectionError:
        st.error("Impossible de se connecter au serveur backend")
        return
    
    if res.status_code == 200:
        queries = res.json()
        
        st.markdown(f"**{len(queries)} requête(s) au total**")
        
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("🔍 Rechercher", placeholder="Filtrer par mot-clé...")
        
        filtered = queries
        if search:
            filtered = [q for q in queries if search.lower() in q['query'].lower() or search.lower() in q['response'].lower()]
        
        for q in reversed(filtered):
            with st.expander(f"👤 User {q['user_id']} | {q['query'][:50]}..."):
                st.markdown(f"**Question:** {q['query']}")
                st.markdown("---")
                st.markdown(f"**Réponse:** {q['response']}")
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.caption(f"👤 User ID: {q['user_id']}")
                with col2:
                    if q.get('created_at'):
                        st.caption(f"📅 {q['created_at']}")
                with col3:
                    if st.button("🗑️ Supprimer", key=f"admin_del_{q['id']}"):
                        del_res = requests.delete(f"{QUERY_URL}/queries/{q['id']}", headers=get_headers())
                        if del_res.status_code == 200:
                            st.success("Requête supprimée!")
                            st.rerun()
                        else:
                            st.error(f"Erreur: {get_error_message(del_res)}")
    else:
        st.error(f"Erreur: {get_error_message(res)}")


def main_app():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['username']}")
        st.caption(f"📧 {st.session_state.user['email']}")
        st.caption(f"🏷️ Rôle: {st.session_state.user['role']}")
        st.divider()
        
        pages = ["🤖 Assistant", "📋 Mon Historique"]
        
        if st.session_state.user['role'] == 'admin':
            pages.extend(["👥 Utilisateurs", "📊 Toutes les Requêtes"])
        
        page = st.radio("Navigation", pages)
        
        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    st.markdown('<div class="main-header">🏥 CliniQ</div>', unsafe_allow_html=True)
    
    if page == "🤖 Assistant":
        assistant_page()
    elif page == "📋 Mon Historique":
        my_queries_page()
    elif page == "👥 Utilisateurs":
        admin_users_page()
    elif page == "📊 Toutes les Requêtes":
        admin_queries_page()


if st.session_state.token and st.session_state.user:
    main_app()
else:
    login_page()
