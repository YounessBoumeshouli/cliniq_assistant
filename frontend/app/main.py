import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://backend:8000"
AUTH_URL = f"{API_BASE}/auth"
QUERY_URL = f"{API_BASE}/query"
USERS_URL = f"{API_BASE}/users"

st.set_page_config(
    page_title="CliniQ | Medical Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM PROFESSIONAL THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #2D3748;
    }

    .main {
        background-color: #F8FAFC;
    }

    .main-header {
        font-size: 2rem;
        font-weight: 600;
        color: #1A365D;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }
    
    .sub-header {
        font-size: 0.9rem;
        color: #718096;
        margin-bottom: 2rem;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 1rem;
    }

    .answer-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #2D7D8E;
        padding: 1.5rem;
        border-radius: 4px;
        margin: 1rem 0;
    }

    [data-testid="stSidebar"] {
        background-color: #1A2B3C;
    }
    
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    .stButton>button {
        border-radius: 4px;
        font-weight: 600;
    }

    .query-log-card {
        background: white;
        padding: 1rem;
        border: 1px solid #E2E8F0;
        border-radius: 4px;
        margin-bottom: 1rem;
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
    try:
        data = res.json()
        return data.get("detail") or data.get("error") or str(data)
    except:
        return f"HTTP Error {res.status_code}"

# --- PAGE FUNCTIONS ---

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">CLINIQ</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Professional Medical Support Portal</div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    try:
                        res = requests.post(f"{AUTH_URL}/login", json={"email": email, "password": password})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token = data["access_token"]
                            user_res = requests.get(f"{AUTH_URL}/me", headers={"Authorization": f"Bearer {data['access_token']}"})
                            if user_res.status_code == 200:
                                st.session_state.user = user_res.json()
                                st.rerun()
                        else:
                            st.error(get_error_message(res))
                    except:
                        st.error("Server connection failed.")

        with tab2:
            with st.form("reg_form"):
                username = st.text_input("Name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pass")
                role = st.selectbox("System Role", ["medecin", "admin"])
                if st.form_submit_button("Register", use_container_width=True):
                    res = requests.post(f"{AUTH_URL}/register", json={"username": username, "email": email, "password": password, "role": role})
                    if res.status_code == 200:
                        st.success("Account created. Please log in.")

def assistant_page():
    st.markdown("### Clinical Assistant")
    
    # Custom CSS for a professional pulse animation
    st.markdown("""
    <style>
    @keyframes pulse-teal {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    .thinking-box {
        padding: 1.5rem;
        background-color: #F0F4F8;
        border-radius: 4px;
        border: 1px solid #D1D5DB;
        color: #2D7D8E;
        font-weight: 600;
        text-align: center;
        animation: pulse-teal 2s infinite ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)

    question = st.text_area("Question", placeholder="Describe the clinical case or protocol required...", height=120)
    col_eval, col_btn = st.columns([4, 1])
    
    with col_eval:
        evaluate = st.checkbox("Include RAG Metrics")
    
    # Placeholder for the button and the animation
    button_placeholder = col_btn.empty()
    
    if button_placeholder.button("Process", use_container_width=True, type="primary"):
        if not question:
            st.warning("Please enter a valid clinical inquiry.")
        else:
            # Replace button with animation
            button_placeholder.empty()
            with st.container():
                st.markdown('<div class="thinking-box">SYSTEM ANALYSIS IN PROGRESS...</div>', unsafe_allow_html=True)
                
                try:
                    endpoint = "/assistant/evaluate" if evaluate else "/assistant"
                    # Add timeout of 120 seconds
                    res = requests.post(
                        f"{QUERY_URL}{endpoint}", 
                        json={"query_text": question}, 
                        headers=get_headers(),
                        timeout=120
                    )
                    
                    # Clear the animation once the request finishes
                    st.rerun() if res.status_code != 200 else None # Force clear if error
                    
                    if res.status_code == 200:
                        # Success: The animation disappears because the script reruns 
                        # or we display the result below
                        data = res.json()
                        st.markdown("#### Clinical Response")
                        st.markdown(f'<div class="answer-box">{data["answer"]}</div>', unsafe_allow_html=True)
                        
                        if evaluate and "metrics" in data:
                            m = data["metrics"]
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Relevance", f"{m['answer_relevance']:.1%}")
                            c2.metric("Faithfulness", f"{m['faithfulness']:.1%}")
                            c3.metric("Precision", f"{m['precision_at_k']:.1%}")
                            c4.metric("Recall", f"{m['recall_at_k']:.1%}")
                    else:
                        st.error(f"Error {res.status_code}: {get_error_message(res)}")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timeout (>120s). The system is taking too long. Check backend logs.")
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Connection error. Backend service may be down.")
                except Exception as e:
                    st.error(f"❌ System error: {str(e)}")

def my_queries_page():
    st.markdown("### My History")
    user_id = st.session_state.user["id"]
    res = requests.get(f"{QUERY_URL}/queries/user/{user_id}", headers=get_headers())
    if res.status_code == 200:
        queries = res.json()
        for q in reversed(queries):
            with st.expander(f"Log: {q['query'][:60]}..."):
                st.write(f"**Query:** {q['query']}")
                st.divider()
                st.write(f"**Response:** {q['response']}")
                if st.button("Delete Record", key=f"del_{q['id']}"):
                    requests.delete(f"{QUERY_URL}/queries/{q['id']}", headers=get_headers())
                    st.rerun()

def admin_users_page():
    st.markdown("### User Management")
    res = requests.get(f"{USERS_URL}/", headers=get_headers())
    if res.status_code == 200:
        for user in res.json():
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            c1.write(user['username'])
            c2.write(user['email'])
            c3.write(user['role'].upper())
            with c4:
                if user['id'] != st.session_state.user['id'] and st.button("Remove", key=f"u_{user['id']}"):
                    requests.delete(f"{USERS_URL}/{user['id']}", headers=get_headers())
                    st.rerun()
            st.divider()

def admin_queries_page():
    st.markdown("### System Audit Logs")
    res = requests.get(f"{QUERY_URL}/queries", headers=get_headers())
    if res.status_code == 200:
        queries = res.json()
        search = st.text_input("Filter Logs", placeholder="Search keywords in queries or responses...")
        
        filtered = [q for q in queries if search.lower() in q['query'].lower() or search.lower() in q['response'].lower()] if search else queries
        
        st.caption(f"Showing {len(filtered)} total records")
        
        for q in reversed(filtered):
            with st.expander(f"UID {q['user_id']} | {q['query'][:50]}..."):
                st.markdown(f"**Clinical Query:** {q['query']}")
                st.divider()
                st.markdown(f"**System Response:** {q['response']}")
                st.divider()
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.caption(f"User Reference: {q['user_id']}")
                c2.caption(f"Timestamp: {q.get('created_at', 'N/A')}")
                with c3:
                    if st.button("Purge Log", key=f"adm_del_{q['id']}", use_container_width=True):
                        requests.delete(f"{QUERY_URL}/queries/{q['id']}", headers=get_headers())
                        st.rerun()

def main_app():
    with st.sidebar:
        st.markdown(f"**{st.session_state.user['username']}**")
        st.caption(st.session_state.user['email'])
        st.divider()
        
        pages = ["Assistant", "Personal History"]
        if st.session_state.user['role'] == 'admin':
            pages.extend(["User Directory", "System Audit"])
        
        choice = st.radio("Navigation", pages)
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    st.markdown('<div class="main-header">CLINIQ</div>', unsafe_allow_html=True)
    
    if choice == "Assistant": assistant_page()
    elif choice == "Personal History": my_queries_page()
    elif choice == "User Directory": admin_users_page()
    elif choice == "System Audit": admin_queries_page()

if st.session_state.token and st.session_state.user:
    main_app()
else:
    login_page()