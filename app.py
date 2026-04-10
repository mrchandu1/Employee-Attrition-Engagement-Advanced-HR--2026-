import streamlit as st

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True

# Show title ONLY after login
if st.session_state.logged_in:
    st.markdown("<h1>🏢 Corporate Access Management System</h1>", unsafe_allow_html=True)
else:
    st.info(" Please log in to continue")

# ================= BACKGROUND SETUP =================
import streamlit as st

st.set_page_config(
    page_title="HR Attrition Analytics",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* ===== Background Image ===== */
    .stApp {
        background-image: url("https://static.vecteezy.com/system/resources/thumbnails/016/343/314/small/businessman-hand-selecting-job-candidates-recruitment-hiring-human-resources-management-concept-employment-head-hunting-and-select-job-applicantsto-working-of-the-hr-free-photo.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* ===== Overlay for Readability ===== */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(245, 247, 250, 0.85);
        z-index: -1;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ================= FULL APPLICATION CODE =================
import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
import json
import os

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Enterprise Workforce Hub",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SECURITY & AUTHENTICATION ---
USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    try:
        with open(USER_DB_FILE, "r") as f:
            content = f.read().strip()
            if not content: return {} 
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users):
    try:
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except IOError:
        st.error("System Error: Could not save user database.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hashlib.sha256(password.encode()).hexdigest()

def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None

def login_user(username, password):
    users = load_users()
    if username in users and verify_password(users[username], password):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        return True
    return False

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "User created successfully! Please log in."

def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.rerun()

# --- DATA PROCESSING ---
@st.cache_data(show_spinner=False)
def process_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

    if not df.empty:
        df.columns = df.columns.str.strip()
        
        # Standardize Status
        if 'Status' in df.columns:
            df['Status'] = df['Status'].replace({'Act': 'Active'})
            df['Is_Attrited'] = df['Status'].apply(lambda x: 0 if x == 'Active' else 1)
        
        # Dates
        if 'Hire_Date' in df.columns:
            df['Hire_Date'] = pd.to_datetime(df['Hire_Date'], errors='coerce')
            if 'Year' not in df.columns:
                df['Year'] = df['Hire_Date'].dt.year
        
        # Create a display name column for easier searching
        if 'Full_Name' in df.columns and 'Employee_ID' in df.columns:
            df['Display_Label'] = df['Full_Name'] + " (" + df['Employee_ID'] + ")"
        elif 'Employee_ID' in df.columns:
            df['Display_Label'] = df['Employee_ID']

    return df

# --- MAIN DASHBOARD LOGIC ---
def dashboard_ui():
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.title("📊 Enterprise Workforce Intelligence")
    with c2:
        st.write(f"User: *{st.session_state['username']}*")
        if st.button("Log Out", type="primary"):
            logout_user()
    st.markdown("---")

    # --- 1. DATA INGESTION ---
    with st.sidebar:
        st.header("🗂️ Data Input")
        uploaded_file = st.file_uploader("Upload CSV File", type="csv")
        st.info("Upload your dataset to begin analysis.")

    if uploaded_file is None:
        st.warning("⚠️ *Waiting for Data Upload...* Please use the sidebar.")
        st.stop()

    df = process_data(uploaded_file)
    if df is None or df.empty:
        st.error("File is empty or invalid.")
        st.stop()

    # --- 2. GLOBAL FILTERS (Sidebar) ---
    with st.sidebar:
        st.header("⚙️ Global Filters")
        
        # Categorical Filters
        dept_opts = ['All'] + sorted(df['Department'].dropna().unique().tolist()) if 'Department' in df.columns else ['All']
        sel_dept = st.selectbox("Department", dept_opts)

        country_opts = ['All'] + sorted(df['Country'].dropna().unique().tolist()) if 'Country' in df.columns else ['All']
        sel_country = st.selectbox("Country", country_opts)

        mode_opts = ['All'] + sorted(df['Work_Mode'].dropna().unique().tolist()) if 'Work_Mode' in df.columns else ['All']
        sel_mode = st.selectbox("Work Mode", mode_opts)
        
        st.markdown("---")
        st.subheader("📊 Range Filters")

        # 1. Year of Hiring Range
        if 'Year' in df.columns:
            min_yr, max_yr = int(df['Year'].min()), int(df['Year'].max())
            sel_years = st.slider("📅 Hiring Year", min_yr, max_yr, (min_yr, max_yr))
        else:
            sel_years = None

        # 2. Experience Years Range
        if 'Experience_Years' in df.columns:
            min_exp, max_exp = int(df['Experience_Years'].min()), int(df['Experience_Years'].max())
            sel_exp = st.slider("🎓 Experience (Years)", min_exp, max_exp, (min_exp, max_exp))
        else:
            sel_exp = None

        # 3. Salary Range
        if 'Salary_INR' in df.columns:
            min_sal, max_sal = int(df['Salary_INR'].min()), int(df['Salary_INR'].max())
            sel_sal = st.slider("💰 Salary Range (INR)", min_sal, max_sal, (min_sal, max_sal))
        else:
            sel_sal = None
            
        # 4. Performance Rating
        if 'Performance_Rating' in df.columns:
            perf_opts = sorted(df['Performance_Rating'].unique().tolist())
            sel_perf = st.multiselect("⭐ Performance Rating", perf_opts, default=perf_opts)
        else:
            sel_perf = None

    # --- APPLY FILTERS ---
    df_filtered = df.copy()
    
    # Standard Filters
    if sel_dept != 'All':
        df_filtered = df_filtered[df_filtered['Department'] == sel_dept]
    if sel_country != 'All':
        df_filtered = df_filtered[df_filtered['Country'] == sel_country]
    if sel_mode != 'All':
        df_filtered = df_filtered[df_filtered['Work_Mode'] == sel_mode]
    
    # Range Filters
    if sel_years:
        df_filtered = df_filtered[df_filtered['Year'].between(sel_years[0], sel_years[1])]
    if sel_exp:
        df_filtered = df_filtered[df_filtered['Experience_Years'].between(sel_exp[0], sel_exp[1])]
    if sel_sal:
        df_filtered = df_filtered[df_filtered['Salary_INR'].between(sel_sal[0], sel_sal[1])]
    if sel_perf is not None and len(sel_perf) > 0:
        df_filtered = df_filtered[df_filtered['Performance_Rating'].isin(sel_perf)]

    # --- TABS FOR FEATURES ---
    tab1, tab2, tab3 = st.tabs(["📊 Analytics Overview", "🔍 Employee Search", "⚖️ Compare Employees"])

    # === TAB 1: ANALYTICS ===
    with tab1:
        st.markdown(f"### 🏢 Organizational Overview (Filtered: {len(df_filtered)} Records)")
        
        # KPIs
        total = len(df_filtered)
        attrition = df_filtered['Is_Attrited'].sum() if 'Is_Attrited' in df_filtered else 0
        rate = (attrition/total*100) if total > 0 else 0
        salary = df_filtered['Salary_INR'].mean() if 'Salary_INR' in df_filtered else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Workforce", f"{total:,}")
        k2.metric("Attrition Rate", f"{rate:.2f}%", delta_color="inverse")
        k3.metric("Total Attrition", f"{attrition:,}", delta_color="inverse")
        k4.metric("Avg Salary", f"₹{salary:,.0f}")

        st.markdown("---")

        # Charts
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("Attrition by Department")
            if 'Department' in df_filtered and 'Is_Attrited' in df_filtered:
                d_grp = df_filtered.groupby('Department')['Is_Attrited'].mean().reset_index()
                d_grp['Rate'] = d_grp['Is_Attrited'] * 100
                fig = px.bar(d_grp.sort_values('Rate', ascending=False), x='Department', y='Rate', 
                             color='Rate', color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.subheader("Work Mode Distribution")
            if 'Work_Mode' in df_filtered:
                fig = px.pie(df_filtered, names='Work_Mode', hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig, use_container_width=True)

        # Deep Dive
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Salary vs. Status")
            if 'Salary_INR' in df_filtered and 'Status' in df_filtered:
                fig = px.box(df_filtered, x='Status', y='Salary_INR', color='Status')
                st.plotly_chart(fig, use_container_width=True)
        
        with c4:
            st.subheader("Performance Rating Distribution")
            if 'Performance_Rating' in df_filtered:
                perf_counts = df_filtered['Performance_Rating'].value_counts().sort_index().reset_index()
                perf_counts.columns = ['Rating', 'Count']
                fig = px.bar(perf_counts, x='Rating', y='Count', title="Employee Count by Rating", color_discrete_sequence=['#3366cc'])
                st.plotly_chart(fig, use_container_width=True)

    # === TAB 2: SEARCH ===
    with tab2:
        st.markdown("### 🔍 Individual Record Lookup")
        search_query = st.text_input("Search by Name or Employee ID", placeholder="Type here...", key="search_box")

        if search_query:
            mask = pd.Series(False, index=df.index)
            if 'Full_Name' in df.columns:
                mask |= df['Full_Name'].astype(str).str.contains(search_query, case=False, na=False)
            if 'Employee_ID' in df.columns:
                mask |= df['Employee_ID'].astype(str).str.contains(search_query, case=False, na=False)
            
            results = df[mask]
            if not results.empty:
                st.success(f"Found {len(results)} matches.")
                st.dataframe(results.drop(columns=['Display_Label'], errors='ignore'), use_container_width=True)
            else:
                st.warning("No matches found.")

    # === TAB 3: COMPARISON (UPDATED) ===
    with tab3:
        st.markdown("### ⚖️ Multi-Employee Comparison Tool")
        st.write("Compare Salary, Experience, Performance, and Hiring Year side-by-side.")

        if 'Display_Label' not in df.columns:
            st.error("Data missing required columns for comparison.")
        else:
            # Use filters to narrow down list if needed, or show all
            # Showing all employees from the filtered list to respect sidebar
            available_employees = df_filtered['Display_Label'].unique().tolist()
            
            selected_names = st.multiselect("Select Employees to Compare:", options=available_employees)

            if selected_names:
                comp_df = df[df['Display_Label'].isin(selected_names)]

                # --- VISUAL COMPARISON ---
                st.subheader("📈 Visual Metrics Comparison")
                
                # Row 1: Salary & Experience
                r1_c1, r1_c2 = st.columns(2)
                with r1_c1:
                    if 'Salary_INR' in comp_df.columns:
                        fig_sal = px.bar(comp_df, x='Full_Name', y='Salary_INR', color='Full_Name', 
                                         title="💰 Salary (INR)", text_auto='.2s')
                        st.plotly_chart(fig_sal, use_container_width=True)
                
                with r1_c2:
                     if 'Experience_Years' in comp_df.columns:
                        fig_exp = px.bar(comp_df, x='Full_Name', y='Experience_Years', color='Full_Name', 
                                         title="🎓 Experience (Years)", text_auto=True)
                        st.plotly_chart(fig_exp, use_container_width=True)

                # Row 2: Performance & Year
                r2_c1, r2_c2 = st.columns(2)
                with r2_c1:
                    if 'Performance_Rating' in comp_df.columns:
                        fig_perf = px.bar(comp_df, x='Full_Name', y='Performance_Rating', color='Full_Name', 
                                          title="⭐ Performance Rating (1-5)", text_auto=True)
                        # Fix y-axis to be 1-5 reasonable range
                        fig_perf.update_yaxes(range=[0, 6])
                        st.plotly_chart(fig_perf, use_container_width=True)
                
                with r2_c2:
                    if 'Year' in comp_df.columns:
                        # Use a scatter plot or bar for year to make it distinct
                        fig_year = px.scatter(comp_df, x='Full_Name', y='Year', color='Full_Name', 
                                              title="📅 Hiring Year", size_max=15)
                        fig_year.update_traces(marker=dict(size=20, symbol='diamond'))
                        fig_year.update_yaxes(dtick=1) # Show every year tick
                        st.plotly_chart(fig_year, use_container_width=True)

                # --- DATA TABLE ---
                st.subheader("📋 Detailed Attribute Table")
                cols_to_show = [c for c in comp_df.columns if c not in ['Display_Label', 'Is_Attrited']]
                display_df = comp_df[cols_to_show].set_index('Full_Name').T
                st.dataframe(display_df, use_container_width=True)

            else:
                st.info("Select employees from the dropdown above to generate comparisons.")

# --- AUTHENTICATION UI ---
def login_ui():
    st.markdown("<h3>🔑🛡️ Authorized access only</h3>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login","Register"])
    
    with t1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In"):
                if login_user(u, p): st.rerun()
                else: st.error("Invalid credentials")
    
    with t2:
        with st.form("signup"):
            u = st.text_input("New Username")
            p = st.text_input("New Password", type="password")
            cp = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Register"):
                if p!=cp: st.error("Passwords mismatch")
                elif len(p)<4: st.error("Password too short")
                elif not u: st.error("Username required")
                else: 
                    suc, msg = register_user(u, p)
                    if suc: st.success(msg)
                    else: st.error(msg)

if __name__ == "__main__":
    init_auth()
    if st.session_state["authenticated"]:
        dashboard_ui()
    else:
        login_ui()