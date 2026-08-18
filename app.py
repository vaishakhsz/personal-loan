import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import os

# ==========================================
# 1. SQLITE DATABASE CONNECTION & INIT
# ==========================================
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auraloan.db")

def get_connection():
    """Create a connection to SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they do not exist"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. parties table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            guardian_name TEXT,
            dob TEXT,
            mobile TEXT NOT NULL,
            whatsapp TEXT,
            address TEXT,
            pincode TEXT,
            pan_masked TEXT,
            occupation TEXT,
            qualification TEXT,
            kyc_status TEXT,
            created_at TEXT
        )
        """)
        
        # 2. loans table (Personal Loan specific attributes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_id INTEGER NOT NULL,
            party_name TEXT NOT NULL,
            principal REAL NOT NULL,
            interest_rate REAL NOT NULL,
            duration_months INTEGER NOT NULL,
            emi REAL NOT NULL,
            processing_fee REAL DEFAULT 0.0,
            admin_fee REAL DEFAULT 0.0,
            documentation_fee REAL DEFAULT 0.0,
            net_disbursed REAL,
            interest_amount REAL,
            total_payable REAL,
            status TEXT DEFAULT 'Active',
            disbursed_date TEXT,
            created_at TEXT,
            
            -- Personal Loan Attributes
            monthly_income REAL NOT NULL,
            employer_name TEXT,
            designation TEXT,
            guarantor_name TEXT,
            guarantor_mobile TEXT,
            bank_name TEXT,
            bank_account_no TEXT,
            bank_ifsc TEXT,
            FOREIGN KEY (party_id) REFERENCES parties(id)
        )
        """)
        
        # 3. ledger table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (loan_id) REFERENCES loans(id)
        )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")

# Initialize DB at startup
init_db()

def get_table_data(table_name):
    """Retrieve all rows from target SQLite table as pandas DataFrame"""
    try:
        conn = get_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error reading from {table_name}: {str(e)}")
        return pd.DataFrame()

def insert_record(table_name, record):
    """Insert a record dictionary into SQLite table. Returns row ID on success, None on failure."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        columns = ", ".join(record.keys())
        placeholders = ", ".join(["?" for _ in record])
        values = tuple(record.values())
        
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except Exception as e:
        st.error(f"Error inserting into {table_name}: {str(e)}")
        return None

def update_record(table_name, record_id, updates):
    """Update a record with update-dict in SQLite table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = tuple(updates.values()) + (record_id,)
        
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating {table_name}: {str(e)}")
        return False

def delete_record(table_name, record_id):
    """Delete a record from SQLite table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting from {table_name}: {str(e)}")
        return False

# ==========================================
# 2. STREAMLIT UI & STYLE CONFIGURATION
# ==========================================
st.set_page_config(page_title="AuraLoan | Personal Loan System", layout="wide", page_icon="💼")

# Custom Styles for Goldish/Champagne background and Premium Elements
st.markdown("""
    <style>
    /* Global App Background */
    .stApp {
        background-color: #FAF6EE !important;
    }
    
    /* Headers & Text colors */
    .gold-header { 
        color: #8B6508; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 25px; 
        font-family: 'Playfair Display', serif;
    }
    
    /* Metrics panel cards styling */
    div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #8B6508 !important;
    }
    .stMetric { 
        background-color: #FFFDF7 !important; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #E3C16F !important;
        box-shadow: 0px 4px 10px rgba(227, 193, 111, 0.08);
        transition: all 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0px 6px 12px rgba(227, 193, 111, 0.15);
    }
    
    /* Form Container styling */
    div[data-testid="stForm"] {
        background-color: #FFFDF9 !important;
        border: 1px solid #E3C16F !important;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.02);
    }
    
    /* Custom buttons */
    .stButton>button {
        background-color: #8B6508 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #A07817 !important;
        transform: translateY(-1px);
        box-shadow: 0px 3px 6px rgba(139, 101, 8, 0.2);
    }
    
    /* Document/Agreement Styling */
    .agreement-box { 
        border: 2px solid #b8860b; 
        padding: 35px; 
        background-color: #fcfcf4; 
        border-radius: 10px; 
        font-family: 'Inter', sans-serif; 
        color: #333; 
        line-height: 1.8; 
    }
    .agreement-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 20px; 
        margin-bottom: 20px; 
    }
    .agreement-table th, .agreement-table td { 
        border: 1px solid #b8860b; 
        padding: 12px; 
        text-align: left; 
    }
    .agreement-table th { 
        background-color: #f5f0db; 
        color: #b8860b; 
        font-weight: bold;
    }
    
    /* Printable Ledger/Receipt Box */
    .printable-ledger { 
        font-family: Arial, sans-serif; 
        padding: 30px; 
        border: 1px solid #ccc; 
        background-color: white; 
        color: black; 
        border-radius: 6px; 
    }
    .printable-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 15px; 
    }
    .printable-table th, .printable-table td { 
        border: 1px solid #000; 
        padding: 10px; 
        text-align: left; 
    }
    .printable-table th { 
        background-color: #f2f2f2; 
    }
    .receipt-box { 
        border: 2px dashed #8b6508; 
        padding: 25px; 
        margin-top: 20px; 
        background-color: #fffdf7; 
    }
    </style>
""", unsafe_allow_html=True)

# Fetch Live System Data
parties_df = get_table_data('parties')
loans_df = get_table_data('loans')
ledger_df = get_table_data('ledger')

count_parties = len(parties_df)
count_loans = len(loans_df)
count_active_loans = len(loans_df[loans_df['status'] == 'Active']) if not loans_df.empty else 0
count_tx = len(ledger_df)

# Helper function to generate standardized agreement HTML string
def generate_agreement_html(loan_row, party_row):
    return f"""
    <div class="agreement-box">
        <h2 class="gold-header">വ്യക്തിഗത വായ്പാ കരാർ പത്രം (Personal Loan Agreement)</h2>
        <p><b>കരാർ നമ്പർ (Agreement No):</b> #{loan_row.get('id', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; <b>തീയതി (Date):</b> {loan_row.get('disbursed_date', 'N/A')}</p>
        <hr style="border-top: 1px solid #b8860b;">
        
        <h3>👤 1. പാർട്ടി വിവരങ്ങൾ (Party Details)</h3>
        <table class="agreement-table">
            <tr><td><b>പേര് (Name)</b></td><td>{party_row.get('name', 'N/A')}</td></tr>
            <tr><td><b>പിതാവ്/ഭർത്താവിന്റെ പേര് (Guardian Name)</b></td><td>{party_row.get('guardian_name', 'N/A')}</td></tr>
            <tr><td><b>വിലാസം (Address)</b></td><td>{party_row.get('address', 'N/A')}, {party_row.get('pincode', '')}</td></tr>
            <tr><td><b>മൊബൈൽ നമ്പർ (Mobile)</b></td><td>{party_row.get('mobile', 'N/A')}</td></tr>
            <tr><td><b>തൊഴിൽ (Occupation)</b></td><td>{party_row.get('occupation', 'N/A')}</td></tr>
        </table>

        <h3>💰 2. വായ്പയുടെ വിവരങ്ങൾ (Loan Details)</h3>
        <table class="agreement-table">
            <tr><th>വിവരണം (Description)</th><th>തുക / നിരക്ക് (Amount / Rate)</th></tr>
            <tr><td>അനുവദിച്ച വായ്പ തുക (Principal / Disbursement)</td><td><b>₹{float(loan_row.get('principal', 0)):,.2f}</b></td></tr>
            <tr><td>പ്രതിവർഷ പലിശ നിരക്ക് (Interest Rate)</td><td>{loan_row.get('interest_rate', 0)}%</td></tr>
            <tr><td>കാലാവധി (Tenure)</td><td>{loan_row.get('duration_months', 0)} മാസങ്ങൾ</td></tr>
            <tr><td>പ്രതിമാസ തവണ (EMI)</td><td><b>₹{float(loan_row.get('emi', 0)):,.2f}</b></td></tr>
            <tr style="font-weight:bold; background-color: #fff0f6;"><td>ആകെ പലിശ തുക (Interest Amount)</td><td>₹{float(loan_row.get('interest_amount', 0)):,.2f}</td></tr>
            <tr style="font-weight:bold; background-color: #f6ffed;"><td>ആകെ തിരിച്ചടയ്ക്കാനുള്ളത് (Total Payable)</td><td>₹{float(loan_row.get('total_payable', 0)):,.2f}</td></tr>
        </table>

        <h3>💼 3. ജോലി, വരുമാന വിവരങ്ങൾ (Employment & Income Details)</h3>
        <table class="agreement-table">
            <tr><td><b>തൊഴിലുടമയുടെ പേര് (Employer Name)</b></td><td>{loan_row.get('employer_name', 'N/A')}</td></tr>
            <tr><td><b>തസ്തിക (Designation)</b></td><td>{loan_row.get('designation', 'N/A')}</td></tr>
            <tr><td><b>പ്രതിമാസ വരുമാനം (Monthly Income)</b></td><td><b>₹{float(loan_row.get('monthly_income', 0)):,.2f}</b></td></tr>
        </table>
        
        <h3>👥 4. ജാമ്യക്കാരൻ വിവരങ്ങൾ (Guarantor Details)</h3>
        <table class="agreement-table">
            <tr><td><b>ജാമ്യക്കാരന്റെ പേര് (Guarantor Name)</b></td><td>{loan_row.get('guarantor_name', 'N/A')}</td></tr>
            <tr><td><b>മൊബൈൽ നമ്പർ (Guarantor Mobile)</b></td><td>{loan_row.get('guarantor_mobile', 'N/A')}</td></tr>
        </table>

        <h3>🏦 5. ബാങ്ക് വിവരങ്ങൾ (Bank Account Details)</h3>
        <table class="agreement-table">
            <tr><td><b>ബാങ്ക് പേര് (Bank Name)</b></td><td>{loan_row.get('bank_name', 'N/A')}</td></tr>
            <tr><td><b>അക്കൗണ്ട് നമ്പർ (Account No)</b></td><td>{loan_row.get('bank_account_no', 'N/A')}</td></tr>
            <tr><td><b>IFSC കോഡ് (IFSC Code)</b></td><td>{loan_row.get('bank_ifsc', 'N/A')}</td></tr>
        </table>
        
        <br>
        <table style="width:100%; margin-top:30px;">
            <tr>
                <td>___________________________<br><b>വായ്പക്കാരന്റെ ഒപ്പ്<br>(Borrower Signature)</b></td>
                <td>___________________________<br><b>ജാമ്യക്കാരന്റെ ഒപ്പ്<br>(Guarantor Signature)</b></td>
                <td style="text-align:right;">___________________________<br><b>അധികാരിയുടെ ഒപ്പ്<br>(Authorized Signature)</b></td>
            </tr>
        </table>
    </div>
    """

# Helper function to generate Add-on Charges Fee Receipt
def generate_fee_receipt_html(loan_row, party_row):
    total_fees = float(loan_row.get('processing_fee', 0)) + float(loan_row.get('admin_fee', 0)) + float(loan_row.get('documentation_fee', 0))
    return f"""
    <div class="printable-ledger receipt-box">
        <h2 style="text-align:center;margin-bottom:2px;color:#8B6508;">AURA LOAN MANAGEMENT SYSTEM</h2>
        <h4 style="text-align:center;margin-top:0px;color:#555;">📋 ഫീസ് അടച്ച വൗച്ചർ / FEES RECEIPT</h4>
        <hr style="border-top: 1px dashed #000;">
        <table style="width:100%; margin-bottom:15px; font-size:14px;">
            <tr><td><b>കസ്റ്റമർ പേര് (Name):</b> {party_row.get('name', 'N/A')}</td><td><b>രസീത് നമ്പർ (Receipt No):</b> #FEE-{loan_row.get('id', 'N/A')}</td></tr>
            <tr><td><b>ലോൺ ലിങ്ക് ഐഡി (Loan Ref ID):</b> #{loan_row.get('id', 'N/A')}</td><td><b>തീയതി (Date):</b> {loan_row.get('disbursed_date', 'N/A')}</td></tr>
            <tr><td><b>മൊബൈൽ (Mobile):</b> {party_row.get('mobile', 'N/A')}</td><td><b>സ്റ്റാറ്റസ് (Status):</b> <span style="color:green;font-weight:bold;">Paid</span></td></tr>
        </table>
        
        <table class="printable-table">
            <thead>
                <tr style="background-color: #f9f9f9;"><th>ക്രമ നമ്പർ (Sl No)</th><th>ഫീസ് വിവരണം (Fee Description)</th><th>ഈടാക്കിയ തുക (Amount Collected)</th></tr>
            </thead>
            <tbody>
                <tr><td style="text-align:center;">1</td><td>പ്രോസസ്സിംഗ് ഫീസ് (Processing Fee)</td><td>₹{float(loan_row.get('processing_fee', 0)):,.2f}</td></tr>
                <tr><td style="text-align:center;">2</td><td>അഡ്മിൻ ഫീസ് (Admin Fee)</td><td>₹{float(loan_row.get('admin_fee', 0)):,.2f}</td></tr>
                <tr><td style="text-align:center;">3</td><td>ഡോക്യുമെന്റേഷൻ ഫീസ് (Documentation Fee)</td><td>₹{float(loan_row.get('documentation_fee', 0)):,.2f}</td></tr>
                <tr style="font-weight:bold; background-color: #f5f5f5;"><td colspan="2" style="text-align:right;">ആകെ ഈടാക്കിയ ഫീസ് (Total Service Charges):</td><td>₹{total_fees:,.2f}</td></tr>
            </tbody>
        </table>
        <br>
        <p style="font-size:13px; font-weight:bold;">തുക അക്ഷരത്തിൽ: രൂപ {total_fees} മാത്രം.</p>
        <br>
        <table style="width:100%; margin-top:20px; font-size:14px; text-align:center;">
            <tr><td>____________________<br>ക്യാഷറുടെ ഒപ്പ് (Cashier)</td><td>____________________<br>കസ്റ്റമർ ഒപ്പ് (Customer Signature)</td></tr>
        </table>
    </div>
    """

# ==========================================
# 3. SIDEBAR NAVIGATION MANAGEMENT
# ==========================================
st.sidebar.markdown("### 📋 Navigation")
main_menu = [
    "🏠 Dashboard",
    "👤 Party Master (Customer Reg)",
    "✏️ Edit/Delete Party Profile",
    "💰 Personal Loan Management",
    "📄 Loan Agreement (Malayalam)",
    "📅 EMI Schedule",
    "⚖️ Trial Balance",
    "💾 Backup, Restore & Upload"
]
choice = st.sidebar.selectbox("Select Module", main_menu)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Sub-Modules")
if choice == "💰 Personal Loan Management":
    sub_choice = st.sidebar.radio("Sub Navigation", ["💸 Loan Formulation", "📊 Party Ledger"])
else:
    st.sidebar.markdown("*No active sub-module*")
    sub_choice = None

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Stats")
st.sidebar.write(f"👤 Registered Parties: **{count_parties}**")
st.sidebar.write(f"💰 Total Loans: **{count_loans}**")
st.sidebar.write(f"🟢 Active Personal Loans: **{count_active_loans}**")
st.sidebar.write(f"📝 Ledger Entries: **{count_tx}**")

st.title("🏆 AuraLoan - Premium Personal Loan System")
st.markdown("---")

# ==========================================
# MODULE: DASHBOARD
# ==========================================
if choice == "🏠 Dashboard":
    st.header("📊 Executive Portfolio Dashboard")
    
    total_active = len(loans_df[loans_df['status'] == 'Active']) if not loans_df.empty else 0
    total_disbursed = loans_df['principal'].astype(float).sum() if not loans_df.empty and 'principal' in loans_df.columns else 0.0
    
    # Calculate total recovered and outstanding balance
    total_repaid = 0.0
    if not ledger_df.empty:
        total_repaid = ledger_df[ledger_df['transaction_type'].isin(['Repayment', 'Interest Settlement'])]['amount'].astype(float).sum()
    
    total_receivable = loans_df['total_payable'].astype(float).sum() if not loans_df.empty and 'total_payable' in loans_df.columns else 0.0
    total_outstanding = max(0.0, total_receivable - total_repaid)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Personal Loan Accounts", total_active)
    col2.metric("Total Disbursement Amount", f"₹{total_disbursed:,.2f}")
    col3.metric("Outstanding Balance (incl. Interest)", f"₹{total_outstanding:,.2f}")
    
    st.subheader("📈 Live Master Monitoring Stream")
    if not loans_df.empty and not parties_df.empty:
        # Merge loans with parties for better display
        dashboard_df = loans_df.merge(parties_df, left_on='party_id', right_on='id', how='left', suffixes=('', '_party'))
        dashboard_display = dashboard_df[['id', 'name', 'principal', 'interest_amount', 'total_payable', 'emi', 'status', 'disbursed_date']].copy()
        dashboard_display.columns = ['Loan ID', 'Customer Name', 'Principal Amount (₹)', 
                                    'Interest Amount (₹)', 'Total Payable (₹)', 'Monthly EMI (₹)', 'Status', 'Disbursement Date']
        for col in ['Principal Amount (₹)', 'Interest Amount (₹)', 'Total Payable (₹)', 'Monthly EMI (₹)']:
            if col in dashboard_display.columns:
                dashboard_display[col] = dashboard_display[col].astype(float).round(2)
        st.dataframe(dashboard_display, use_container_width=True)
    else:
        st.info("No active or past personal loans found.")

# ==========================================
# MODULE: PARTY MASTER
# ==========================================
elif choice == "👤 Party Master (Customer Reg)":
    st.header("👤 Customer Registration (Party Master)")
    with st.form("party_master_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("പേര് (Name) *")
            guardian_name = st.text_input("പിതാവ്/ഭർത്താവിന്റെ പേര് (Father/Husband Name)")
            dob = st.date_input("തീയതി ജനനം (Date of Birth)", min_value=datetime(1900, 1, 1), max_value=datetime.now())
            mobile = st.text_input("മൊബൈൽ നമ്പർ (Mobile) *")
            whatsapp = st.text_input("WhatsApp Number")
        with col2:
            occupation = st.text_input("തൊഴിൽ (Occupation)")
            qualification = st.text_input("യോഗ്യത (Qualification)")
            address = st.text_area("വിലാസം (Address)")
            pincode = st.text_input("Pincode")
            pan = st.text_input("PAN Card Number")
            kyc_status = st.selectbox("KYC Status", ["Pending", "Verified", "Suspended"])
            
        if st.form_submit_button("Save Customer Profile"):
            if name and mobile:
                record = {
                    'name': name,
                    'guardian_name': guardian_name,
                    'dob': str(dob),
                    'mobile': mobile,
                    'whatsapp': whatsapp,
                    'address': address,
                    'pincode': pincode,
                    'pan_masked': pan,
                    'occupation': occupation,
                    'qualification': qualification,
                    'kyc_status': kyc_status,
                    'created_at': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
                if insert_record('parties', record):
                    st.success(f"Successfully registered customer: {name}")
                    st.rerun()
                else:
                    st.error("Failed to save customer profile.")
            else:
                st.error("Name and Mobile fields are required.")

# ==========================================
# MODULE: EDIT & DELETE PARTY DETAILS
# ==========================================
elif choice == "✏️ Edit/Delete Party Profile":
    st.header("✏️ Profile Management Core (Edit / Delete Customer Accounts)")
    
    if parties_df.empty:
        st.info("No customer profiles available.")
    else:
        party_to_edit = st.selectbox("Select Party Profile to Manage", parties_df['id'].tolist(), 
                                    format_func=lambda x: f"ID: {x} | {parties_df[parties_df['id']==x]['name'].values[0]} ({parties_df[parties_df['id']==x]['kyc_status'].values[0]})")
        selected_row = parties_df[parties_df['id'] == party_to_edit].iloc[0]
        
        tab_edit, tab_delete = st.tabs(["✏️ Edit Details", "❌ Delete Profile Permanently"])
        
        with tab_edit:
            with st.form("edit_party_form_main"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("പേര് (Name)", value=selected_row['name'])
                    edit_guardian = st.text_input("പിതാവ്/ഭർത്താവിന്റെ പേര്", value=selected_row['guardian_name'])
                    edit_mobile = st.text_input("മൊബൈൽ നമ്പർ (Mobile)", value=selected_row['mobile'])
                    edit_whatsapp = st.text_input("WhatsApp Number", value=selected_row['whatsapp'])
                with col2:
                    edit_occupation = st.text_input("തൊഴിൽ (Occupation)", value=selected_row['occupation'])
                    edit_qualification = st.text_input("യോഗ്യത (Qualification)", value=selected_row['qualification'])
                    edit_address = st.text_area("വിലാസം (Address)", value=selected_row['address'])
                    edit_pincode = st.text_input("Pincode", value=selected_row['pincode'])
                    edit_kyc = st.selectbox("KYC Status", ["Pending", "Verified", "Suspended"], 
                                           index=["Pending", "Verified", "Suspended"].index(selected_row['kyc_status']))
                
                if st.form_submit_button("Save All Updates"):
                    updates = {
                        'name': edit_name,
                        'guardian_name': edit_guardian,
                        'mobile': edit_mobile,
                        'whatsapp': edit_whatsapp,
                        'occupation': edit_occupation,
                        'qualification': edit_qualification,
                        'address': edit_address,
                        'pincode': edit_pincode,
                        'kyc_status': edit_kyc
                    }
                    if update_record('parties', party_to_edit, updates):
                        st.success("All updates saved successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update customer profile.")
                    
        with tab_delete:
            st.warning(f"⚠️ Warning: You are about to permanently delete the profile of **{selected_row['name']}**.")
            st.error("This will delete the customer profile. Make sure there are no open loans attached to this party.")
            
            # Check for active loans in sqlite
            has_active_loans = not loans_df.empty and len(loans_df[(loans_df['party_id'] == party_to_edit) & (loans_df['status'] == 'Active')]) > 0
            
            if has_active_loans:
                st.error("Cannot delete profile: This customer still has active personal loan files recorded.")
            else:
                confirm_delete_text = st.text_input("Type 'DELETE' to confirm account destruction:")
                if st.button("Confirm Account Destruction"):
                    if confirm_delete_text == "DELETE":
                        if delete_record('parties', party_to_edit):
                            st.success("Customer profile deleted from database successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to delete profile.")
                    else:
                        st.error("Confirmation string does not match.")

# ==========================================
# PARENT MODULE: PERSONAL LOAN MANAGEMENT
# ==========================================
elif choice == "💰 Personal Loan Management":
    
    # 💸 SUB-MODULE 1: LOAN FORMULATION & DISBURSEMENT
    if sub_choice == "💸 Loan Formulation":
        st.header("💸 Personal Loan Formulation (Disbursement Calculator)")
        
        verified_parties = parties_df[parties_df['kyc_status'] == 'Verified'] if not parties_df.empty else pd.DataFrame()
        
        if verified_parties.empty:
            st.warning("⚠️ No Verified Customers Available. Please verify a customer profile inside Party Management first.")
        else:
            party_options = {row['id']: row['name'] for _, row in verified_parties.iterrows()}
            
            with st.form("disbursement_calculator_form"):
                selected_party = st.selectbox("Select Verified Borrower Profile", list(party_options.keys()), format_func=lambda x: party_options[x])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 💼 1. തൊഴിൽ, ബാങ്ക് വിവരങ്ങൾ (Employment & Bank Details)")
                    monthly_income = st.number_input("പ്രതിമാസ വരുമാനം (Monthly Income - ₹) *", min_value=0.0, value=25000.0, step=1000.0)
                    employer_name = st.text_input("തൊഴിലുടമയുടെ പേര് (Employer Name)", placeholder="കമ്പനി / സ്ഥാപനത്തിന്റെ പേര്")
                    designation = st.text_input("തസ്തിക (Designation)", placeholder="ഉദ്യോഗം")
                    
                    st.markdown("---")
                    st.markdown("#### 👥 2. ജാമ്യക്കാരൻ വിവരങ്ങൾ (Guarantor Details)")
                    guarantor_name = st.text_input("ജാമ്യക്കാരന്റെ പേര് (Guarantor Name)")
                    guarantor_mobile = st.text_input("മൊബൈൽ നമ്പർ (Guarantor Mobile)")
                    
                    st.markdown("---")
                    st.markdown("#### 🏦 3. ബാങ്ക് അക്കൗണ്ട് വിവരങ്ങൾ (Disbursement Bank)")
                    bank_name = st.text_input("ബാങ്ക് പേര് (Bank Name)")
                    bank_account_no = st.text_input("അക്കൗണ്ട് നമ്പർ (Account No)")
                    bank_ifsc = st.text_input("IFSC കോഡ് (IFSC Code)")
                    
                with col2:
                    st.markdown("#### 📊 4. വായ്പയുടെ വ്യവസ്ഥകൾ (Calculation Terms)")
                    max_eligible = monthly_income * 10
                    st.info(f"💡 Recommended Personal Loan Cap (10x Salary): **₹{max_eligible:,.2f}**")
                    
                    principal = st.number_input("അനുവദിച്ച വായ്പ തുക (Principal/Disbursement) - ₹", min_value=0.0, value=100000.0, step=5000.0)
                    interest_rate = st.number_input("പ്രതിവർഷ പലിശ നിരക്ക് (Interest Rate % For Total Duration)", min_value=0.0, value=12.0, step=0.5)
                    duration = st.number_input("കാലാവധി (Tenure Duration - Months)", min_value=1, max_value=60, value=12, step=1)
                    
                    st.markdown("---")
                    st.markdown("#### 🏷️ ആഡ്ഓൺ ചാർജ്ജുകൾ (Service Fees)")
                    processing_fee = st.number_input("പ്രോസസ്സിംഗ് ഫീസ് (Processing Fee - ₹)", min_value=0.0, value=1000.0, step=100.0)
                    admin_fee = st.number_input("അഡ്മിൻ ഫീസ് (Admin Fee - ₹)", min_value=0.0, value=250.0, step=50.0)
                    doc_fee = st.number_input("ഡോക്യുമെന്റേഷൻ ഫീസ് (Documentation Fee - ₹)", min_value=0.0, value=500.0, step=100.0)
                    
                    # Mathematical terms logic
                    interest_amount = principal * (interest_rate / 100)
                    total_payable = principal + interest_amount
                    calculated_emi = total_payable / duration if duration > 0 else 0.0
                    
                    st.markdown("---")
                    st.write(f"**അസ്സൽ വായ്പ തുക (Principal):** ₹{principal:,.2f}")
                    st.write(f"**ആകെ പലിശ (Total Interest):** ₹{interest_amount:,.2f}")
                    st.write(f"**ആകെ തിരിച്ചടയ്ക്കാനുള്ളത് (Total Payable):** ₹{total_payable:,.2f}")
                    st.write(f"**പ്രതിമാസ തവണ (EMI):** ₹{calculated_emi:,.2f}")
                    
                    if principal > max_eligible:
                        st.warning("⚠️ Warning: Requested principal exceeds the recommended limit of 10 times monthly income.")
                    
                if st.form_submit_button("Finalize and Disburse Capital Allocation"):
                    if principal <= 0 or monthly_income <= 0:
                        st.error("Invalid entry constraints: Principal and Monthly Income must be greater than zero.")
                    else:
                        today_str = str(datetime.now().date())
                        created_at = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
                        party_name = verified_parties[verified_parties['id'] == selected_party]['name'].values[0]
                        
                        loan_record = {
                            'party_id': selected_party,
                            'party_name': party_name,
                            'principal': principal,
                            'interest_rate': interest_rate,
                            'duration_months': duration,
                            'emi': calculated_emi,
                            'processing_fee': processing_fee,
                            'admin_fee': admin_fee,
                            'documentation_fee': doc_fee,
                            'net_disbursed': principal,
                            'interest_amount': interest_amount,
                            'total_payable': total_payable,
                            'status': 'Active',
                            'disbursed_date': today_str,
                            'created_at': created_at,
                            # Personal specific
                            'monthly_income': monthly_income,
                            'employer_name': employer_name,
                            'designation': designation,
                            'guarantor_name': guarantor_name,
                            'guarantor_mobile': guarantor_mobile,
                            'bank_name': bank_name,
                            'bank_account_no': bank_account_no,
                            'bank_ifsc': bank_ifsc
                        }
                        
                        new_loan_id = insert_record('loans', loan_record)
                        if new_loan_id:
                            # Add initial disbursement to ledger
                            ledger_record = {
                                'loan_id': new_loan_id,
                                'transaction_type': 'Disbursement',
                                'amount': principal,
                                'transaction_date': today_str,
                                'created_at': created_at
                            }
                            insert_record('ledger', ledger_record)
                            
                            st.success(f"Personal Loan Account #{new_loan_id} successfully formulated and activated.")
                            st.session_state['active_contract_loan_id'] = new_loan_id
                            st.rerun()
                        else:
                            st.error("Failed to insert loan record to SQLite database.")

            if 'active_contract_loan_id' in st.session_state:
                l_id = st.session_state['active_contract_loan_id']
                loans_df = get_table_data('loans')
                parties_df = get_table_data('parties')
                
                loan_row = loans_df[loans_df['id'] == l_id].iloc[0] if not loans_df.empty else None
                if loan_row is not None:
                    party_row = parties_df[parties_df['id'] == loan_row['party_id']].iloc[0] if not parties_df.empty else None
                    
                    if party_row is not None:
                        tab_voucher, tab_fee_receipt = st.tabs(["📄 വ്യക്തിഗത വായ്പാ കരാർ ഫോം (Agreement Form)", "🖨️ ഫീസ് രസീത് (Fee Receipt)"])
                        
                        with tab_voucher:
                            instant_html = generate_agreement_html(loan_row.to_dict(), party_row.to_dict())
                            st.download_button(label="📥 ഡൗൺലോഡ് കരാർ പത്രം (Download Agreement)", data=instant_html, file_name=f"Personal_Agreement_Loan_{l_id}.html", mime="text/html")
                        
                        with tab_fee_receipt:
                            fee_html = generate_fee_receipt_html(loan_row.to_dict(), party_row.to_dict())
                            st.download_button(label="📥 പ്രിന്റ് ഫീസ് രസീത് (Download Fee Receipt)", data=fee_html, file_name=f"Fee_Receipt_Loan_{l_id}.html", mime="text/html")

    # 📊 SUB-MODULE 2: PARTY LEDGER ACCOUNTANT
    elif sub_choice == "📊 Party Ledger":
        st.header("📊 Customer Ledger Statements")
        
        active_loans = loans_df[loans_df['status'] == 'Active'] if not loans_df.empty else pd.DataFrame()
        
        if active_loans.empty:
            st.info("No active personal loan records found.")
        else:
            loan_options = {}
            for _, row in active_loans.iterrows():
                party_name = parties_df[parties_df['id'] == row['party_id']]['name'].values[0] if not parties_df.empty else 'Unknown'
                loan_options[row['id']] = f"Loan #{row['id']} - Holder: {party_name} (₹{float(row['principal']):,.2f})"
            
            selected_loan = st.selectbox("Select Target Portfolio File", list(loan_options.keys()), format_func=lambda x: loan_options[x])
            
            # Fetch liability balance details
            loan_row_data = active_loans[active_loans['id'] == selected_loan].iloc[0]
            total_liability = float(loan_row_data['total_payable'])
            principal = float(loan_row_data['principal'])
            
            loan_ledger = ledger_df[ledger_df['loan_id'] == selected_loan] if not ledger_df.empty else pd.DataFrame()
            total_repaid_credits = loan_ledger[loan_ledger['transaction_type'].isin(['Repayment', 'Interest Settlement'])]['amount'].astype(float).sum() if not loan_ledger.empty else 0.0
            live_outstanding_balance = max(0.0, total_liability - total_repaid_credits)
            
            tab_post, tab_view, tab_print = st.tabs(["💳 Collection Repayment Entry", "📑 View Balancing Ledger Statement", "🖨️ Generate Printable Sheet"])
            
            with tab_post:
                if live_outstanding_balance <= 0.0:
                    st.success("🎉 Already Repaid / Bill completely paid in full.")
                else:
                    # Calculate outstanding principal and interest
                    total_principal_repaid_so_far = loan_ledger[loan_ledger['transaction_type'] == 'Repayment']['amount'].astype(float).sum() if not loan_ledger.empty else 0.0
                    outstanding_principal = max(0.0, principal - total_principal_repaid_so_far)
                    
                    total_interest_charged = float(loan_row_data['interest_amount'])
                    total_interest_repaid_so_far = loan_ledger[loan_ledger['transaction_type'] == 'Interest Settlement']['amount'].astype(float).sum() if not loan_ledger.empty else 0.0
                    outstanding_interest = max(0.0, total_interest_charged - total_interest_repaid_so_far)
                    
                    # Separate inputs without st.form for live updates
                    principal_repay_input = st.number_input(f"Principal Repayment (Outstanding: ₹{outstanding_principal:,.2f})", min_value=0.0, max_value=outstanding_principal, value=0.0, step=100.0)
                    interest_settled_input = st.number_input(f"Interest Settlement (Outstanding: ₹{outstanding_interest:,.2f})", min_value=0.0, max_value=outstanding_interest, value=0.0, step=100.0)
                    repay_date = st.date_input("Settlement Date")
                    
                    total_collection = principal_repay_input + interest_settled_input
                    st.info(f"💵 Total Collection Amount to Post: **₹{total_collection:,.2f}**")
                    
                    if st.button("Post Ledger Entry"):
                        if total_collection <= 0:
                            st.error("Please enter an amount greater than zero.")
                        else:
                            success = False
                            created_at = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            
                            if principal_repay_input > 0:
                                ledger_record_p = {
                                    'loan_id': selected_loan,
                                    'transaction_type': 'Repayment',
                                    'amount': principal_repay_input,
                                    'transaction_date': str(repay_date),
                                    'created_at': created_at
                                }
                                success = insert_record('ledger', ledger_record_p) is not None
                                
                            if interest_settled_input > 0:
                                ledger_record_i = {
                                    'loan_id': selected_loan,
                                    'transaction_type': 'Interest Settlement',
                                    'amount': interest_settled_input,
                                    'transaction_date': str(repay_date),
                                    'created_at': created_at
                                }
                                success = insert_record('ledger', ledger_record_i) is not None or success
                                
                            if success:
                                # Re-fetch updated ledger data to check closed status
                                new_ledger = get_table_data('ledger')
                                updated_loan_ledger = new_ledger[new_ledger['loan_id'] == selected_loan] if not new_ledger.empty else pd.DataFrame()
                                total_repaid_credits = updated_loan_ledger[updated_loan_ledger['transaction_type'].isin(['Repayment', 'Interest Settlement'])]['amount'].astype(float).sum() if not updated_loan_ledger.empty else 0.0
                                
                                if total_repaid_credits >= total_liability:
                                    update_record('loans', selected_loan, {'status': 'Closed'})
                                
                                st.success("Ledger entry successfully posted inside local ledger.")
                                st.rerun()
                            
            with tab_view:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Disbursement / Principal Amount", f"₹{principal:,.2f}")
                col_m2.metric("Total Payable (with Interest)", f"₹{total_liability:,.2f}")
                
                if live_outstanding_balance <= 0.0:
                    col_m3.metric("Current Outstanding Balance", "Already Repaid")
                else:
                    col_m3.metric("Current Outstanding Balance", f"₹{live_outstanding_balance:,.2f}", delta_color="inverse")
                
                if not loan_ledger.empty:
                    display_df = loan_ledger[['transaction_type', 'amount', 'transaction_date']].copy()
                    display_df.columns = ['Activity Type', 'Value (₹)', 'Date']
                    display_df['Value (₹)'] = display_df['Value (₹)'].astype(float).round(2)
                    st.table(display_df)
                else:
                    st.info("No ledger entries recorded for this personal loan account.")
                
            with tab_print:
                st.markdown("### 🖨️ Printable Ledger Statement")
                party_name = parties_df[parties_df['id'] == loan_row_data['party_id']]['name'].values[0] if not parties_df.empty else 'Unknown'
                party_mobile = parties_df[parties_df['id'] == loan_row_data['party_id']]['mobile'].values[0] if not parties_df.empty else 'Unknown'
                party_address = parties_df[parties_df['id'] == loan_row_data['party_id']]['address'].values[0] if not parties_df.empty else 'Unknown'
                
                table_html_rows = ""
                if not loan_ledger.empty:
                    for _, tx in loan_ledger.iterrows():
                        display_type = "Loan Disbursement (Principal)" if tx['transaction_type'] == "Disbursement" else tx['transaction_type']
                        table_html_rows += f"<tr><td>{tx['transaction_date']}</td><td>{display_type}</td><td>₹{float(tx['amount']):,.2f}</td></tr>"
                
                total_repaid = loan_ledger[loan_ledger['transaction_type'].isin(['Repayment', 'Interest Settlement'])]['amount'].astype(float).sum() if not loan_ledger.empty else 0.0
                balance_left = total_liability - total_repaid
                
                if balance_left < 0.01:
                    balance_html_str = "<b style='color:green; font-size:18px;'>Already Repaid / Paid in Full</b>"
                else:
                    balance_html_str = f"<b>₹{balance_left:,.2f}</b>"
                
                printable_html = f"""
                <div class="printable-ledger">
                    <h2 style="text-align:center;margin-bottom:2px;">AURA LOAN MANAGEMENT SYSTEM</h2>
                    <h4 style="text-align:center;margin-top:0px;color:#555;">STATEMENT OF ACCOUNT / PARTY LEDGER</h4>
                    <hr>
                    <table style="width:100%; margin-bottom:20px; font-size:14px;">
                        <tr><td><b>കസ്റ്റമർ പേര് (Name):</b> {party_name}</td><td><b>ലോൺ നമ്പർ (Loan ID):</b> #{selected_loan}</td></tr>
                        <tr><td><b>ഫോൺ (Mobile):</b> {party_mobile}</td><td><b>തീയതി (Date Issued):</b> {loan_row_data['disbursed_date']}</td></tr>
                        <tr><td colspan="2"><b>മേൽവിലാസം (Address):</b> {party_address}</td></tr>
                    </table>
                    
                    <table class="printable-table">
                        <thead>
                            <tr><th>തീയതി (Date)</th><th>വിവരണം (Description)</th><th>തുക (Amount)</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>{loan_row_data['disbursed_date']}</td><td>Fixed Term Interest Charged</td><td>₹{float(loan_row_data['interest_amount']):,.2f}</td></tr>
                            {table_html_rows}
                        </tbody>
                    </table>
                    
                    <div style="margin-top:20px; text-align:right; font-size:16px;">
                        <p><b>അസ്സൽ തുക (Principal/Disbursed Amount):</b> ₹{principal:,.2f}</p>
                        <p><b>ആകെ പലിശ (Total Interest Charged):</b> ₹{float(loan_row_data['interest_amount']):,.2f}</p>
                        <hr style="border-top: 1px solid #000; width: 40%; margin-left: auto;">
                        <p><b>ആകെ അടയ്ക്കേണ്ടത് (Total Payable):</b> ₹{total_liability:,.2f}</p>
                        <p style="color:green;"><b>ഇതുവരെ അടച്ചത് (Total Repaid):</b> ₹{total_repaid:,.2f}</p>
                        <p style="color:red; font-size:18px;"><b>ബാക്കി കുടിശ്ശിക (Outstanding Balance):</b> {balance_html_str}</p>
                    </div>
                </div>
                """
                st.download_button(label="📥 ഡൗൺലോഡ് ലെഡ്ജർ (Download HTML Ledger)", data=printable_html, file_name=f"Ledger_Loan_{selected_loan}.html", mime="text/html")

# ==========================================
# MODULE: LOAN AGREEMENT MALAYALAM
# ==========================================
elif choice == "📄 Loan Agreement (Malayalam)":
    st.header("📄 Malayalam Legal Agreement Console")
    
    if loans_df.empty:
        st.info("No personal loan files found inside the database.")
    else:
        contract_options = {}
        for _, row in loans_df.iterrows():
            party_name = parties_df[parties_df['id'] == row['party_id']]['name'].values[0] if not parties_df.empty else 'Unknown'
            contract_options[row['id']] = f"Loan #{row['id']} Ledger Account - {party_name}"
        
        target_contract = st.selectbox("Select Target Active Portfolio File", list(contract_options.keys()), format_func=lambda x: contract_options[x])
        
        loan_row = loans_df[loans_df['id'] == target_contract].iloc[0] if not loans_df.empty else None
        if loan_row is not None:
            party_row = parties_df[parties_df['id'] == loan_row['party_id']].iloc[0] if not parties_df.empty else None
            
            if party_row is not None:
                tab_contract_view, tab_receipt_view = st.tabs(["📜 വൗച്ചർ ഡൗൺലോഡ് (Agreement Form)", "🧾 രസീത് ഡൗൺലോഡ് (Fee Receipt)"])
                
                with tab_contract_view:
                    agreement_html = generate_agreement_html(loan_row.to_dict(), party_row.to_dict())
                    st.download_button(label="📥 ഡൗൺലോഡ് കരാർ പത്രം (Download Agreement HTML)", data=agreement_html, file_name=f"Agreement_Loan_{loan_row['id']}.html", mime="text/html")
                    
                with tab_receipt_view:
                    fee_html = generate_fee_receipt_html(loan_row.to_dict(), party_row.to_dict())
                    st.download_button(label="📥 ഡൗൺലോഡ് ഫീസ് രസീത് (Download Fee Receipt HTML)", data=fee_html, file_name=f"Fee_Receipt_Loan_{loan_row['id']}.html", mime="text/html")

# ==========================================
# MODULE: EMI SCHEDULE MATRIX
# ==========================================
elif choice == "📅 EMI Schedule":
    st.header("📅 Monthly Recovery Projection Mapping (EMI Schedule)")
    
    active_loans = loans_df[loans_df['status'] == 'Active'] if not loans_df.empty else pd.DataFrame()
    
    if active_loans.empty:
        st.info("No active loan tracking matrices found.")
    else:
        loan_options = {}
        for _, row in active_loans.iterrows():
            party_name = parties_df[parties_df['id'] == row['party_id']]['name'].values[0] if not parties_df.empty else 'Unknown'
            loan_options[row['id']] = f"Loan #{row['id']} - Account: {party_name} (EMI: ₹{float(row['emi']):,.2f})"
        
        selected_sched = st.selectbox("Select Target Loan ID Schedule Map", list(loan_options.keys()), format_func=lambda x: loan_options[x])
        
        target_l = active_loans[active_loans['id'] == selected_sched].iloc[0]
        party_name = parties_df[parties_df['id'] == target_l['party_id']]['name'].values[0] if not parties_df.empty else 'Unknown'
        party_mobile = parties_df[parties_df['id'] == target_l['party_id']]['mobile'].values[0] if not parties_df.empty else 'Unknown'
        
        schedule_rows_html = ""
        remaining_reduction_pool = float(target_l['total_payable'])
        
        schedule_list = []
        for index in range(1, int(target_l['duration_months']) + 1):
            remaining_reduction_pool -= float(target_l['emi'])
            current_rem = max(0.0, remaining_reduction_pool)
            
            if current_rem < 0.01:
                display_rem = "Already Repaid"
            else:
                display_rem = f"₹{current_rem:,.2f}"
                
            schedule_rows_html += f"""
            <tr>
                <td style="border: 1px solid #000; padding: 8px; text-align: center;">Month {index}</td>
                <td style="border: 1px solid #000; padding: 8px;">₹{float(target_l['emi']):,.2f}</td>
                <td style="border: 1px solid #000; padding: 8px;">{display_rem}</td>
            </tr>
            """
            schedule_list.append({
                "Installment": f"Month No. {index}",
                "Payment Amount (₹)": f"₹{float(target_l['emi']):,.2f}",
                "Outstanding Balance": display_rem
            })
            
        st.table(pd.DataFrame(schedule_list))
        
        printable_schedule_html = f"""
        <div class="printable-ledger">
            <h2 style="text-align:center;margin-bottom:2px;">AURA LOAN MANAGEMENT SYSTEM</h2>
            <h4 style="text-align:center;margin-top:0px;color:#555;">📊 പ്രതിമാസ തവണ വിവരപ്പട്ടിക (EMI SCHEDULE PLAN)</h4>
            <hr>
            <table style="width:100%; margin-bottom:20px; font-size:14px;">
                <tr><td><b>കസ്റ്റമർ പേര് (Name):</b> {party_name}</td><td><b>ലോൺ നമ്പർ (Loan ID):</b> #{target_l['id']}</td></tr>
                <tr><td><b>ഫോൺ (Mobile):</b> {party_mobile}</td><td><b>അസ്സൽ വായ്പ (Principal/Disbursed):</b> ₹{float(target_l['principal']):,.2f}</td></tr>
                <tr><td><b>ആകെ അടയ്ക്കേണ്ടത് (Total Liability):</b> ₹{float(target_l['total_payable']):,.2f}</td></tr>
            </table>
            
            <table class="printable-table">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #000; padding: 8px; text-align: center;">തവണ നമ്പർ (Installment)</th>
                        <th style="border: 1px solid #000; padding: 8px;">അടയ്ക്കേണ്ട തുക (EMI Amount)</th>
                        <th style="border: 1px solid #000; padding: 8px;">ബാക്കി വരാവുന്ന തുക (Remaining Balance)</th>
                    </tr>
                </thead>
                <tbody>
                    {schedule_rows_html}
                </tbody>
            </table>
        </div>
        """
        
        st.download_button(label="📥 ഡൗൺലോഡ് & പ്രിന്റ് ഷെഡ്യൂൾ (Download Schedule Sheet)", data=printable_schedule_html, file_name=f"EMI_Schedule_Loan_{selected_sched}.html", mime="text/html")

# ==========================================
# MODULE: TRIAL BALANCE
# ==========================================
elif choice == "⚖️ Trial Balance":
    st.header("⚖️ Double-Entry System Trial Balance")
    st.markdown("This statement verifies that total debits match total credits in the database ledgers.")
    
    if loans_df.empty:
        st.info("No financial accounts exist to generate a Trial Balance.")
    else:
        # Fees
        total_proc_fees = loans_df['processing_fee'].astype(float).sum() if 'processing_fee' in loans_df.columns else 0.0
        total_admin_fees = loans_df['admin_fee'].astype(float).sum() if 'admin_fee' in loans_df.columns else 0.0
        total_doc_fees = loans_df['documentation_fee'].astype(float).sum() if 'documentation_fee' in loans_df.columns else 0.0
        total_fees = total_proc_fees + total_admin_fees + total_doc_fees
        
        # Disbursements & Repayments from ledger
        total_disbursed = 0.0
        total_principal_repaid = 0.0
        total_interest_repaid = 0.0
        
        if not ledger_df.empty:
            total_disbursed = ledger_df[ledger_df['transaction_type'] == 'Disbursement']['amount'].astype(float).sum()
            total_principal_repaid = ledger_df[ledger_df['transaction_type'] == 'Repayment']['amount'].astype(float).sum()
            total_interest_repaid = ledger_df[ledger_df['transaction_type'] == 'Interest Settlement']['amount'].astype(float).sum()
            
        # Interest Charged from loans
        total_interest_charged = loans_df['interest_amount'].astype(float).sum() if 'interest_amount' in loans_df.columns else 0.0
        total_principal_issued = loans_df['principal'].astype(float).sum() if 'principal' in loans_df.columns else 0.0
        
        # Calculations
        cash_inflows = total_principal_repaid + total_interest_repaid + total_fees
        cash_outflows = total_disbursed
        net_cash = cash_inflows - cash_outflows
        
        cash_dr = net_cash if net_cash >= 0 else 0.0
        cash_cr = abs(net_cash) if net_cash < 0 else 0.0
        
        net_receivables = total_principal_issued - total_principal_repaid
        receivables_dr = net_receivables if net_receivables >= 0 else 0.0
        receivables_cr = abs(net_receivables) if net_receivables < 0 else 0.0
        
        net_interest_receivables = total_interest_charged - total_interest_repaid
        int_receivables_dr = net_interest_receivables if net_interest_receivables >= 0 else 0.0
        int_receivables_cr = abs(net_interest_receivables) if net_interest_receivables < 0 else 0.0
        
        interest_income_cr = total_interest_charged
        fee_income_cr = total_fees
        
        # Build Table
        tb_data = []
        tb_data.append({
            "Code": "1001",
            "Account Name": "Cash & Bank Account",
            "Debit (DR)": f"₹{cash_dr:,.2f}" if cash_dr > 0 or cash_cr == 0 else "",
            "Credit (CR)": f"₹{cash_cr:,.2f}" if cash_cr > 0 else ""
        })
        tb_data.append({
            "Code": "1002",
            "Account Name": "Loan Principal Receivables (Asset)",
            "Debit (DR)": f"₹{receivables_dr:,.2f}" if receivables_dr > 0 or receivables_cr == 0 else "",
            "Credit (CR)": f"₹{receivables_cr:,.2f}" if receivables_cr > 0 else ""
        })
        tb_data.append({
            "Code": "1003",
            "Account Name": "Loan Interest Receivables (Asset)",
            "Debit (DR)": f"₹{int_receivables_dr:,.2f}" if int_receivables_dr > 0 or int_receivables_cr == 0 else "",
            "Credit (CR)": f"₹{int_receivables_cr:,.2f}" if int_receivables_cr > 0 else ""
        })
        tb_data.append({
            "Code": "3001",
            "Account Name": "Interest Revenue (Income)",
            "Debit (DR)": "",
            "Credit (CR)": f"₹{interest_income_cr:,.2f}"
        })
        tb_data.append({
            "Code": "3002",
            "Account Name": "Service Fees Collected (Income)",
            "Debit (DR)": "",
            "Credit (CR)": f"₹{fee_income_cr:,.2f}"
        })
        
        total_dr = cash_dr + receivables_dr + int_receivables_dr
        total_cr = cash_cr + receivables_cr + int_receivables_cr + interest_income_cr + fee_income_cr
        
        st.dataframe(pd.DataFrame(tb_data), use_container_width=True, hide_index=True)
        
        col_dr, col_cr = st.columns(2)
        col_dr.metric("Total Debits (DR)", f"₹{total_dr:,.2f}")
        col_cr.metric("Total Credits (CR)", f"₹{total_cr:,.2f}")
        
        if abs(total_dr - total_cr) < 0.01:
            st.success("🟢 **Trial Balance is in Balance.** Total Debits match Total Credits perfectly.")
        else:
            st.error(f"🔴 **Out of Balance Warning:** Difference is ₹{abs(total_dr - total_cr):,.2f}")

# ==========================================
# MODULE: BACKUP, RESTORE & DATA UPLOADER
# ==========================================
elif choice == "💾 Backup, Restore & Upload":
    st.header("💾 Storage Engine Maintenance & Data Integration Tools")
    
    st.subheader("📥 Upload Existing Datasets (CSV Imports)")
    target_upload_table = st.selectbox("Select Destination Database Table to Populate:", ["parties", "loans"])
    uploaded_csv = st.file_uploader(f"Choose a CSV file containing '{target_upload_table}' row records", type=["csv"])
    
    if uploaded_csv is not None:
        try:
            input_df = pd.read_csv(uploaded_csv)
            st.write("🔍 Preview of data to import:")
            st.dataframe(input_df.head(5))
            
            if st.button("Commit Data Feed to SQLite Database"):
                success_count = 0
                for _, row in input_df.iterrows():
                    record = row.to_dict()
                    # Remove id if present to let SQLite auto-generate
                    if 'id' in record:
                        del record['id']
                    if insert_record(target_upload_table, record):
                        success_count += 1
                
                st.success(f"Successfully integrated {success_count} rows into the `{target_upload_table}` database table.")
                st.rerun()
        except Exception as err:
            st.error(f"Failed parsing file formatting layout context. Internal error: {err}")
            
    st.markdown("---")
    
    st.subheader("📤 Local Backup Operations")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Party Registries Matrix")
        df_p = get_table_data('parties')
        if not df_p.empty:
            st.download_button("Download Customers CSV", data=df_p.to_csv(index=False).encode('utf-8'), file_name="parties_export.csv", mime="text/csv")
        else:
            st.write("No party data available")
        
    with col2:
        st.markdown("#### Active Portfolio Matrix")
        df_l = get_table_data('loans')
        if not df_l.empty:
            st.download_button("Download Loans CSV", data=df_l.to_csv(index=False).encode('utf-8'), file_name="loans_export.csv", mime="text/csv")
        else:
            st.write("No loan data available")
        
    st.markdown("---")
    
    st.subheader("📤 Download Ledger Data")
    df_ledger = get_table_data('ledger')
    if not df_ledger.empty:
        st.download_button("Download Ledger CSV", data=df_ledger.to_csv(index=False).encode('utf-8'), file_name="ledger_export.csv", mime="text/csv")
    else:
        st.write("No ledger data available")
    
    st.markdown("---")
    st.info("💡 Your data is stored locally in SQLite database file (auraloan.db). All updates persist across server restarts.")
