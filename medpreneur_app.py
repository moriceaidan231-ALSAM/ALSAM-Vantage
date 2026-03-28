"""
================================================================================
ALSAM VANTANCE - Multi-Tenant Business Platform (Complete & Updated)
================================================================================
A multi-venture business management system for tracking cash flows,
inventory, and personal assets.

REAL BUSINESS LOGIC APPLIED:
1. Restock = Asset Swap (Net Worth Neutral).
2. Expense = Wealth Destruction (Net Worth Down).
3. Sell Item = Profit Realization (Net Worth Up by Profit Margin).
4. Inventory supports "Pack vs. Unit" conversion (Buy Cartons, Sell Pieces).
5. Weighted Average Cost: Correctly values inventory when restocking at different prices.
================================================================================
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import uuid
import hashlib
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# ================================================================================
# 1. CORE CONFIGURATION
# ================================================================================
st.set_page_config(
    page_title="ALSAM Vantage",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "alsam_data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.csv")
RECOVERY_FILE = os.path.join(DATA_DIR, "recovery_tokens.csv")
DB_FILE = os.path.join(DATA_DIR, "ledger.csv")
STOCK_FILE = os.path.join(DATA_DIR, "stocks.csv")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.csv")

LOGO_FILE = os.path.join(BASE_DIR, "alsam_logo.png")

# Schema Definitions
USERS_COLS = ["UserID", "Username", "Email", "PINHash", "Role", 
              "SecurityQuestion", "SecurityAnswerHash", "RecoveryKey",
              "FullName", "CreatedDate", "LastLogin"]

RECOVERY_COLS = ["TokenID", "UserID", "Token", "CreatedAt", "ExpiresAt", "Used"]

DB_COLS = ["UID", "OrgID", "Date", "Venture", "Amount", "Type", "Category", "Note", "CreatedBy"]

# UPDATED SCHEMA: Includes Pack/Unit logic columns
STK_COLS = ["UID", "OrgID", "Date", "Venture", "Item", "Units", "UnitType", 
            "BuyingPrice", "CurrentPrice", "PackSize", "PackType", "CreatedBy"]

PORT_COLS = ["UID", "OrgID", "Date", "Asset", "Ticker", "Units", "BuyPrice", "CurrentPrice", "CreatedBy"]

DEV_USERNAME = "admin"
DEV_PIN_HASH = hashlib.sha256("0000".encode()).hexdigest()

# ================================================================================
# 2. CSS STYLING
# ================================================================================
HIDE_SIDEBAR_CSS = """
<style>
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>
"""

st.markdown("""
<style>
    :root {
        --vantage-primary: #013C7B;
        --vantage-accent: #00C853;
        --vantage-danger: #FF5252;
        --vantage-warning: #FFB300;
    }
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', sans-serif; }
    
    .logo-wrapper { text-align: center; padding: 40px 0 20px 0; }
    .alsam-tagline { font-size: 1.4rem; color: #666; margin-top: 10px; margin-bottom: 40px; text-align: center; }
    
    .vantage-card {
        background: white; padding: 2rem; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align: center;
        border: 1px solid #f0f0f0; transition: all 0.3s ease;
    }
    .vantage-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: var(--vantage-primary); }
    
    .empty-state {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 16px; padding: 3rem 2rem; text-align: center;
        border: 2px dashed #d0d5dd; margin: 1rem 0;
    }
    .empty-state-icon { font-size: 3.5rem; margin-bottom: 1rem; opacity: 0.7; }
    .empty-state-title { font-size: 1.3rem; font-weight: 600; color: var(--vantage-primary); margin-bottom: 0.5rem; }
    .empty-state-subtitle { font-size: 0.95rem; color: #78909C; }
    
    div.stButton > button[kind="primary"] {
        background-color: var(--vantage-accent) !important; color: white !important;
        border: none !important; border-radius: 12px !important;
        font-weight: 700 !important; height: 3.2rem;
        box-shadow: 0 4px 10px rgba(0, 200, 83, 0.3) !important;
    }
    div.stButton > button[kind="primary"]:hover { background-color: #00E676 !important; }
    
    div.stButton > button[kind="secondary"] {
        border-radius: 12px !important; font-weight: 600 !important; height: 3.2rem;
        color: var(--vantage-primary) !important; border: 2px solid var(--vantage-primary) !important;
        background: transparent !important;
    }
    div.stButton > button[kind="secondary"]:hover { background-color: var(--vantage-primary) !important; color: white !important; }
    
    div.stTextInput > div > div > input {
        border: none !important; border-bottom: 2px solid #e0e0e0 !important;
        border-radius: 0 !important; background: transparent !important;
    }
    div.stTextInput > div > div > input:focus { border-bottom-color: var(--vantage-primary) !important; box-shadow: none !important; }
    
    div[data-testid="stMetric"] {
        background: white; padding: 1rem; border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #f0f0f0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; color: var(--vantage-primary) !important; }
    
    .stSuccess { background: linear-gradient(90deg, #e8f5e9, #c8e6c9) !important; border-left: 4px solid var(--vantage-accent) !important; border-radius: 0 8px 8px 0 !important; }
    .stError { background: linear-gradient(90deg, #ffebee, #ffcdd2) !important; border-left: 4px solid var(--vantage-danger) !important; border-radius: 0 8px 8px 0 !important; }
    .stWarning { background: linear-gradient(90deg, #fff8e1, #ffecb3) !important; border-left: 4px solid var(--vantage-warning) !important; border-radius: 0 8px 8px 0 !important; }
    
    .safety-link { font-size: 0.85rem; color: #78909C; cursor: pointer; }
    .safety-link:hover { color: var(--vantage-primary); text-decoration: underline; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #013C7B 0%, #0159B3 100%); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 { color: white !important; }
    
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    
    .danger-zone { background: #fff5f5; border: 2px solid var(--vantage-danger); border-radius: 12px; padding: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ================================================================================
# 3. SECURITY MODULE
# ================================================================================
class SecurityManager:
    @staticmethod
    def hash_pin(pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()
    
    @staticmethod
    def verify_pin_hash(pin: str, pin_hash: str) -> bool:
        return SecurityManager.hash_pin(pin) == pin_hash
    
    @staticmethod
    def generate_recovery_key(length: int = 16) -> str:
        import secrets
        import string
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_token(length: int = 8) -> str:
        import secrets
        import string
        chars = string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))


# ================================================================================
# 4. DATA MANAGER
# ================================================================================
class DataManager:
    def __init__(self):
        self.files = {
            "users": {"path": USERS_FILE, "cols": USERS_COLS},
            "recovery": {"path": RECOVERY_FILE, "cols": RECOVERY_COLS},
            "ledger": {"path": DB_FILE, "cols": DB_COLS},
            "stocks": {"path": STOCK_FILE, "cols": STK_COLS},
            "portfolio": {"path": PORTFOLIO_FILE, "cols": PORT_COLS}
        }
    
    def verify_system_integrity(self) -> Dict[str, str]:
        status = {}
        for name, config in self.files.items():
            path, cols = config["path"], config["cols"]
            if not os.path.exists(path):
                pd.DataFrame(columns=cols).to_csv(path, index=False)
                status[name] = "CREATED"
            else:
                try:
                    df = pd.read_csv(path)
                    missing = [c for c in cols if c not in df.columns]
                    if missing:
                        for c in missing:
                            df[c] = None
                        df.to_csv(path, index=False)
                        status[name] = "REPAIRED"
                    else:
                        status[name] = "OK"
                except:
                    pd.DataFrame(columns=cols).to_csv(path, index=False)
                    status[name] = "RECOVERED"
        return status
    
    def load_data(self, file_path: str, columns: List[str]) -> pd.DataFrame:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                return df
            except:
                return pd.DataFrame(columns=columns)
        return pd.DataFrame(columns=columns)
    
    def save_data(self, df: pd.DataFrame, file_path: str) -> bool:
        try:
            df.to_csv(file_path, index=False)
            return True
        except Exception as e:
            st.error(f"Save Error: {e}")
            return False
    
    @staticmethod
    def generate_uid() -> str:
        return str(uuid.uuid4())[:8].upper()
    
    def get_user_by_username(self, username: str) -> Optional[pd.Series]:
        if username.lower() == DEV_USERNAME.lower():
            return pd.Series({
                "UserID": "DEV001",
                "Username": DEV_USERNAME,
                "Email": "developer@alsamvantage.com",
                "PINHash": DEV_PIN_HASH,
                "Role": "Owner",
                "SecurityQuestion": "Developer Access",
                "SecurityAnswerHash": SecurityManager.hash_pin("dev"),
                "RecoveryKey": "DEV-ACCESS-KEY",
                "FullName": "Developer",
                "CreatedDate": datetime.now().isoformat(),
                "LastLogin": datetime.now().isoformat()
            })
        
        df = self.load_data(USERS_FILE, USERS_COLS)
        if df.empty:
            return None
        matches = df[df["Username"].str.lower() == username.lower()]
        if len(matches) == 0:
            return None
        return matches.iloc[0]
    
    def get_user_by_email(self, email: str) -> Optional[pd.Series]:
        df = self.load_data(USERS_FILE, USERS_COLS)
        if df.empty:
            return None
        matches = df[df["Email"].str.lower() == email.lower()]
        if len(matches) == 0:
            return None
        return matches.iloc[0]
    
    def get_user_by_id(self, user_id: str) -> Optional[pd.Series]:
        if user_id == "DEV001":
            return self.get_user_by_username(DEV_USERNAME)
        
        df = self.load_data(USERS_FILE, USERS_COLS)
        if df.empty:
            return None
        matches = df[df["UserID"] == user_id]
        if len(matches) == 0:
            return None
        return matches.iloc[0]
    
    def create_user(self, user_data: Dict) -> Tuple[bool, str]:
        df = self.load_data(USERS_FILE, USERS_COLS)
        
        if not df.empty and len(df[df["Username"].str.lower() == user_data["Username"].lower()]) > 0:
            return False, "Username already exists"
        
        if not df.empty and len(df[df["Email"].str.lower() == user_data["Email"].lower()]) > 0:
            return False, "Email already registered"
        
        user_data["UserID"] = self.generate_uid()
        user_data["CreatedDate"] = datetime.now().isoformat()
        user_data["LastLogin"] = None
        
        new_row = pd.DataFrame([user_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        if self.save_data(df, USERS_FILE):
            return True, user_data["UserID"]
        return False, "Failed to create account"
    
    def update_user_login(self, user_id: str) -> bool:
        if user_id == "DEV001":
            return True
        df = self.load_data(USERS_FILE, USERS_COLS)
        if df.empty:
            return False
        idx = df[df["UserID"] == user_id].index
        if len(idx) == 0:
            return False
        df.at[idx[0], "LastLogin"] = datetime.now().isoformat()
        return self.save_data(df, USERS_FILE)
    
    def update_user_pin(self, user_id: str, new_pin_hash: str) -> bool:
        if user_id == "DEV001":
            return False
        df = self.load_data(USERS_FILE, USERS_COLS)
        if df.empty:
            return False
        idx = df[df["UserID"] == user_id].index
        if len(idx) == 0:
            return False
        df.at[idx[0], "PINHash"] = new_pin_hash
        return self.save_data(df, USERS_FILE)
    
    def get_user_ledger(self, user_id: str) -> pd.DataFrame:
        df = self.load_data(DB_FILE, DB_COLS)
        if df.empty:
            return pd.DataFrame(columns=DB_COLS)
        return df[df["OrgID"] == user_id].copy()
    
    def get_user_stocks(self, user_id: str) -> pd.DataFrame:
        df = self.load_data(STOCK_FILE, STK_COLS)
        if df.empty:
            return pd.DataFrame(columns=STK_COLS)
        return df[df["OrgID"] == user_id].copy()
    
    def get_user_portfolio(self, user_id: str) -> pd.DataFrame:
        df = self.load_data(PORTFOLIO_FILE, PORT_COLS)
        if df.empty:
            return pd.DataFrame(columns=PORT_COLS)
        return df[df["OrgID"] == user_id].copy()
    
    def add_ledger_entry(self, user_id: str, record: Dict) -> Tuple[pd.DataFrame, bool]:
        df = self.load_data(DB_FILE, DB_COLS)
        if "UID" not in record:
            record["UID"] = self.generate_uid()
        record["OrgID"] = user_id
        new_row = pd.DataFrame([record])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        return updated_df, self.save_data(updated_df, DB_FILE)
    
    def add_stock_entry(self, user_id: str, record: Dict) -> Tuple[pd.DataFrame, bool]:
        df = self.load_data(STOCK_FILE, STK_COLS)
        if "UID" not in record:
            record["UID"] = self.generate_uid()
        record["OrgID"] = user_id
        new_row = pd.DataFrame([record])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        return updated_df, self.save_data(updated_df, STOCK_FILE)
    
    def upsert_stock_entry(self, user_id: str, venture: str, item: str, total_units: int, unit_type: str, unit_buy_price: float, sell_price: float, pack_size: int, pack_type: str, created_by: str) -> bool:
        """
        Updates existing item or adds new one. 
        HANDLES WEIGHTED AVERAGE COST for accurate accounting.
        """
        df = self.load_data(STOCK_FILE, STK_COLS)
        
        # Find existing item
        mask = (df["OrgID"] == user_id) & (df["Venture"] == venture) & (df["Item"] == item)
        existing_indices = df[mask].index
        
        if len(existing_indices) > 0:
            idx = existing_indices[0]
            
            # --- WEIGHTED AVERAGE COST CALCULATION ---
            old_units = float(df.at[idx, "Units"])
            old_cost = float(df.at[idx, "BuyingPrice"])
            
            # New values coming in
            new_units = float(total_units)
            new_cost = float(unit_buy_price)
            
            # Calculate Total Value of old stock + new stock
            old_value = old_units * old_cost
            new_value = new_units * new_cost
            
            total_combined_units = old_units + new_units
            total_combined_value = old_value + new_value
            
            # Avoid division by zero
            weighted_avg_cost = (total_combined_value / total_combined_units) if total_combined_units > 0 else new_cost
            
            # Update Record
            df.at[idx, "Units"] = total_combined_units
            df.at[idx, "BuyingPrice"] = weighted_avg_cost # Update to Weighted Average
            
            # Update selling price/packaging to latest specs
            df.at[idx, "CurrentPrice"] = sell_price
            df.at[idx, "UnitType"] = unit_type
            df.at[idx, "PackSize"] = pack_size
            df.at[idx, "PackType"] = pack_type
            df.at[idx, "Date"] = str(datetime.now().date()) 
        else:
            # Create New Item
            new_row = pd.DataFrame([{
                "UID": self.generate_uid(),
                "OrgID": user_id,
                "Date": str(datetime.now().date()),
                "Venture": venture,
                "Item": item,
                "Units": total_units,
                "UnitType": unit_type,
                "BuyingPrice": unit_buy_price,
                "CurrentPrice": sell_price,
                "PackSize": pack_size,
                "PackType": pack_type,
                "CreatedBy": created_by
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        
        return self.save_data(df, STOCK_FILE)

    def reduce_stock_entry(self, user_id: str, venture: str, item: str, qty: int) -> Tuple[bool, float]:
        """Reduces stock quantity. Used for Selling. Returns True and the BuyingPrice of sold items."""
        df = self.load_data(STOCK_FILE, STK_COLS)
        
        mask = (df["OrgID"] == user_id) & (df["Venture"] == venture) & (df["Item"] == item)
        existing_indices = df[mask].index
        
        if len(existing_indices) == 0:
            return False, 0.0
        
        idx = existing_indices[0]
        current_units = float(df.at[idx, "Units"])
        
        if current_units < qty:
            return False, 0.0 # Not enough stock
        
        # Get the cost price for Profit calculation
        cost_price = float(df.at[idx, "BuyingPrice"])
        
        # Deduct stock
        df.at[idx, "Units"] = current_units - qty
        
        return self.save_data(df, STOCK_FILE), cost_price

    def add_portfolio_entry(self, user_id: str, record: Dict) -> Tuple[pd.DataFrame, bool]:
        df = self.load_data(PORTFOLIO_FILE, PORT_COLS)
        if "UID" not in record:
            record["UID"] = self.generate_uid()
        record["OrgID"] = user_id
        new_row = pd.DataFrame([record])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        return updated_df, self.save_data(updated_df, PORTFOLIO_FILE)
    
    def delete_by_uid(self, file_path: str, columns: List[str], uid: str) -> Tuple[pd.DataFrame, bool]:
        df = self.load_data(file_path, columns)
        updated_df = df[df["UID"] != uid].reset_index(drop=True)
        return updated_df, self.save_data(updated_df, file_path)
    
    def delete_venture_completely(self, user_id: str, venture_name: str) -> bool:
        df_ledger = self.load_data(DB_FILE, DB_COLS)
        df_ledger = df_ledger[~((df_ledger["OrgID"] == user_id) & (df_ledger["Venture"] == venture_name))]
        self.save_data(df_ledger.reset_index(drop=True), DB_FILE)
        
        df_stocks = self.load_data(STOCK_FILE, STK_COLS)
        df_stocks = df_stocks[~((df_stocks["OrgID"] == user_id) & (df_stocks["Venture"] == venture_name))]
        self.save_data(df_stocks.reset_index(drop=True), STOCK_FILE)
        return True
    
    def create_recovery_token(self, user_id: str) -> str:
        df = self.load_data(RECOVERY_FILE, RECOVERY_COLS)
        token = SecurityManager.generate_token()
        record = {
            "TokenID": self.generate_uid(),
            "UserID": user_id,
            "Token": token,
            "CreatedAt": datetime.now().isoformat(),
            "ExpiresAt": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "Used": False
        }
        new_row = pd.DataFrame([record])
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_data(df, RECOVERY_FILE)
        return token
    
    def verify_recovery_token(self, user_id: str, token: str) -> bool:
        df = self.load_data(RECOVERY_FILE, RECOVERY_COLS)
        if df.empty:
            return False
        now = datetime.now().isoformat()
        matches = df[
            (df["UserID"] == user_id) & 
            (df["Token"] == token) & 
            (df["Used"] == False) &
            (df["ExpiresAt"] > now)
        ]
        return len(matches) > 0
    
    def mark_token_used(self, user_id: str, token: str) -> bool:
        df = self.load_data(RECOVERY_FILE, RECOVERY_COLS)
        if df.empty:
            return False
        idx = df[(df["UserID"] == user_id) & (df["Token"] == token)].index
        if len(idx) == 0:
            return False
        df.at[idx[0], "Used"] = True
        return self.save_data(df, RECOVERY_FILE)


data_manager = DataManager()


# ================================================================================
# 5. SESSION STATE
# ================================================================================
def init_session_state():
    defaults = {
        'authenticated': False,
        'user_id': None,
        'username': None,
        'role': None,
        'lang': "English",
        'page': "landing",
        'system_verified': False,
        'recovery_step': 0,
        'recovery_user_id': None,
        'recovery_token': None,
        'menu_selection': "🏢 Main Dashboard"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ================================================================================
# 6. TRANSLATIONS
# ================================================================================
TEXTS = {
    "English": {
        "app_title": "ALSAM Vantage",
        "tagline": "Smarter business, brighter future.",
        "card1_h": "Track Every Shilling",
        "card1_p": "Real-time visibility into your cash flow.",
        "card2_h": "Watch Growth",
        "card2_p": "Analytics designed for multi-venture scaling.",
        "card3_h": "Professional Reports",
        "card3_p": "Full financial health in one tap.",
        "btn_signup": "Create New Account",
        "btn_login": "Sign In",
        "forgot": "Forgotten Password?",
        "help": "Help & Support",
        "lang_switch": "🌐 Kiswahili",
        "signup_title": "Create Your Account",
        "signup_subtitle": "Start managing your business ventures today.",
        "username": "Username",
        "username_placeholder": "Choose a unique username",
        "email": "Email Address",
        "email_placeholder": "your@email.com",
        "pin": "4-Digit PIN",
        "pin_placeholder": "••••",
        "pin_confirm": "Confirm PIN",
        "security_question": "Security Question",
        "security_answer": "Your Answer",
        "recovery_key": "Recovery Key (Save This!)",
        "full_name": "Full Name",
        "btn_register": "Create Account",
        "btn_back": "← Back to Home",
        "registration_success": "Account Created Successfully!",
        "username_exists": "Username already exists.",
        "email_exists": "Email already registered.",
        "secure_access": "Secure Access",
        "enter_pin": "Enter your PIN to access ALSAM Vantage.",
        "unlock": "Unlock Dashboard",
        "enter_pin_warning": "Please enter your PIN.",
        "access_denied": "Access Denied: Invalid PIN or username.",
        "return_home": "← Return to Homepage",
        "welcome_msg": "Welcome! Access granted as",
        "forgot_title": "Password Recovery",
        "forgot_subtitle": "Reset your PIN through multi-factor verification.",
        "step_identification": "Step 1: Identification",
        "step_security": "Step 2: Security Challenge",
        "step_token": "Step 3: Verification Token",
        "step_reset": "Step 4: PIN Reset",
        "enter_username_email": "Enter your username or email",
        "btn_verify_identity": "Verify Identity",
        "answer_security_question": "Answer your security question:",
        "btn_verify_answer": "Verify Answer",
        "enter_token": "Enter the 8-digit verification token",
        "btn_verify_token": "Verify Token",
        "new_pin": "New 4-Digit PIN",
        "confirm_new_pin": "Confirm New PIN",
        "btn_reset_pin": "Reset PIN",
        "pin_reset_success": "PIN has been reset successfully!",
        "identity_not_found": "User not found.",
        "security_answer_wrong": "Incorrect answer.",
        "token_invalid": "Invalid or expired token.",
        "pins_dont_match": "PINs do not match.",
        "back": "← Back",
        "help_title": "Help & Support",
        "help_subtitle": "Get assistance with ALSAM Vantage",
        "faq_title": "Frequently Asked Questions",
        "contact_support": "Contact Support",
        "subject": "Subject",
        "message": "Message",
        "priority": "Priority",
        "btn_submit_ticket": "Submit Ticket",
        "ticket_created": "Support request submitted!",
        "fill_required": "Please fill all required fields.",
        "nav_title": "Navigation",
        "sign_out": "🚪 Sign Out",
        "role_label": "👤",
        "menu_dashboard": "🏠 Main Dashboard",
        "menu_quicklog": "📝 Quick-Log",
        "menu_records": "📜 Recent Records",
        "menu_ventures": "📊 Business Ventures",
        "menu_portfolio": "💰 Portfolio Vault",
        "menu_settings": "⚙️ Settings",
        "executive_overview": "🏠 {}'s Executive Summary",
        "liquid_cash": "💵 Liquid Cash",
        "inventory_value": "📦 Inventory Value",
        "portfolio": "📈 Portfolio",
        "net_worth": "🏆 NET WORTH",
        "wealth_assessment": "📊 Wealth Assessment",
        "total_capital": "Total Capital Employed",
        "expected_roi": "Expected ROI",
        "liquidity_ratio": "Liquidity Ratio",
        "cross_venture": "📊 Cross-Venture Performance",
        "no_data": "No Transaction Data",
        "start_logging": "Start logging transactions to see analytics.",
        "income": "Income",
        "expense": "Expense",
        "net_profit": "Net Profit",
        "transactions": "Transactions",
        "margin": "Margin %",
        "potential": "Potential",
        "profit": "Profit",
        "quicklog_title": "📝 Quick-Log Entry",
        "quicklog_info": "Record transactions quickly for any venture.",
        "date": "Date",
        "venture": "Venture",
        "new_venture": "New Venture",
        "new_venture_name": "New Venture Name",
        "amount_tzs": "Amount (TZS)",
        "type": "Type",
        "note": "Note",
        "save": "✅ Save",
        "fill_venture_amount": "Fill in venture and amount.",
        "transaction_saved": "Transaction saved for",
        "recent_records": "📜 Recent Records",
        "no_records": "No Records Yet",
        "start_transactions": "Start logging transactions.",
        "edit_hint": "💡 **Click any cell to edit. Changes save when you click 'Save All Changes'.**",
        "save_all": "💾 Save All Changes",
        "refresh": "🔄 Refresh",
        "cancel": "❌ Cancel",
        "changes_saved": "✅ All changes saved!",
        "delete_single": "🗑️ Delete Single Record",
        "select_record": "Select Record:",
        "delete_selected": "🗑️ Delete Selected Record",
        "record_deleted": "Record deleted!",
        "ventures_title": "📊 Business Ventures",
        "register_venture": "➕ Register Venture",
        "venture_name": "Venture Name",
        "description": "Description",
        "register": "Register",
        "venture_registered": "registered!",
        "select_venture_label": "Select Venture:",
        "no_ventures": "No Ventures",
        "register_first": "Register a venture from sidebar.",
        "tab_inventory": "📦 Inventory",
        "tab_transactions": "💸 Transactions",
        "tab_analytics": "📈 Analytics",
        "tab_delete": "⚠️ Delete",
        "tab_restock": "♻️ Restock",
        "tab_sell": "🛒 Sell Item",
        "inventory_for": "📦 Inventory:",
        "item_name": "Item Name",
        "quantity": "Quantity",
        "buy_price": "Buy Price/Unit",
        "target_price": "Target Price/Unit",
        "add_inventory": "➕ Add to Inventory",
        "added_units": "Added",
        "units_of": "units of",
        "no_inventory": "No Inventory",
        "add_items": "Add items above.",
        "total_investment": "Total Investment",
        "expected_profit": "Expected Profit",
        "delete_item": "🗑️ Delete Inventory Item",
        "select_item": "Select Item:",
        "delete_item_btn": "Delete Item",
        "item_deleted": "Item deleted!",
        "log_trans_for": "💸 Log Transaction:",
        "log_trans": "📝 Log Transaction",
        "trans_logged": "✅ Transaction logged!",
        "analytics_for": "📈 Analytics:",
        "net": "💵 Net Profit",
        "profit_margin": "📊 Profit Margin",
        "roi": "📈 ROI",
        "inventory_analysis": "📦 Inventory Analysis",
        "capital_invested": "Capital Invested",
        "danger_zone": "⚠️ Danger Zone",
        "delete_warning": "⚠️ You are about to DELETE the entire venture:",
        "delete_permanently": "This will permanently delete:",
        "all_trans_for": "All transactions for",
        "all_inventory_for": "All inventory items for",
        "all_related": "All related data",
        "cannot_undo": "**This action CANNOT be undone!**",
        "type_confirm": "Type venture name to confirm deletion:",
        "delete_entire": "🗑️ DELETE ENTIRE VENTURE:",
        "venture_deleted": "✅ Venture has been completely deleted!",
        "delete_failed": "Failed to delete venture.",
        "deletion_cancelled": "Deletion cancelled.",
        "portfolio_title": "💰 Portfolio Vault",
        "portfolio_info": "Manage shares and assets.",
        "asset_name": "Asset Name",
        "ticker": "Ticker",
        "units": "Units",
        "buy_price_short": "Buy Price",
        "current_price": "Current Price",
        "add_vault": "➕ Add to Vault",
        "added_to_vault": "added!",
        "vault_empty": "Vault Empty",
        "add_assets": "Add assets above.",
        "invested": "Invested",
        "value": "Value",
        "pl": "P/L",
        "pl_percent": "P/L %",
        "total_invested": "Total Invested",
        "current_value": "Current Value",
        "total_pl": "Total P/L",
        "remove_asset": "🗑️ Remove Asset",
        "select_asset": "Select Asset:",
        "remove_btn": "Remove Asset",
        "asset_removed": "Asset removed!",
        "settings_title": "⚙️ Settings",
        "account_tab": "🔒 Account",
        "data_tab": "💾 Data",
        "profile": "Profile",
        "role": "Role",
        "switch_lang": "🌐 Switch to",
        "data_management": "Data Management",
        "ledger": "Ledger",
        "stocks": "Stocks",
        "download_backup": "📥 Download Ledger Backup",
        "factory_reset": "🔥 Factory Reset",
        "type_confirm_reset": "Type 'CONFIRM' to delete all data:",
        "delete_all": "DELETE ALL DATA",
        "all_deleted": "All data deleted.",
        "col_date": "Date (YYYY-MM-DD)",
        "col_venture": "Venture",
        "col_amount": "Amount (TZS)",
        "col_type": "Type",
        "col_note": "Note",
        "col_uid": "UID",
        "col_buy_price": "Buy Price",
        "col_sell_price": "Sell Price",
        "col_cost": "Cost",
        "total_asset_base": "Total Asset Base",
        "wealth_growth_title": "📈 Wealth Growth Tracker",
        "month": "Month",
        "cumulative_cash": "Cumulative Cash",
        "restock_title": "♻️ Restock & Reinvest",
        "restock_info": "Convert Liquid Cash into Inventory. This preserves Net Worth by moving value from Cash to Assets.",
        "restock_item_label": "Select Item to Restock",
        "restock_new_item_label": "Or Add New Item",
        "restock_qty": "Quantity to Add",
        "restock_buy_price": "Cost per Unit (Buying Price)",
        "restock_sell_price": "New Selling Price",
        "btn_restock": "🛒 Confirm Restock",
        "restock_success": "Successfully restocked {item}. Cash converted to Inventory.",
        "insufficient_funds": "⚠️ Insufficient Liquid Cash for this reinvestment.",
        "restock_item_created": "New item created and stocked.",
        "restock_item_updated": "Inventory updated.",
        "inv_capital_label": "Capital Locked (Cost)",
        "inv_potential_label": "Sales Potential (Revenue)",
        "realized_profit_label": "Realized Profit (Cash Flow)",
        "unit_type_label": "Selling Unit (e.g., Piece, Meter)",
        "unit_type_placeholder": "e.g., Pcs, Meters",
        "sell_title": "🛒 Sell Item (Point of Sale)",
        "sell_info": "Select an item from your stock to sell. This automatically deducts inventory and records profit.",
        "sell_select_item": "Select Item to Sell",
        "sell_qty": "Quantity to Sell",
        "sell_price": "Selling Price per Unit",
        "btn_sell": "💵 Confirm Sale",
        "sell_success": "Sale complete! Sold {qty} {unit} of {item}.",
        "sell_no_stock": "No items in stock to sell.",
        "sell_insufficient_stock": "Insufficient stock. Available: {stock} {unit}.",
        "sell_profit_log": "Profit: {profit:,.0f} TZS.",
        "unit_pcs": "Pieces (Pcs)",
        "unit_m": "Meters (m)",
        "unit_box": "Boxes",
        "unit_ctn": "Cartons",
        "unit_kg": "Kilograms (kg)",
        "unit_other": "Other",
        "pack_buying_unit": "Buying Unit (Pack)",
        "pack_buying_unit_ph": "e.g., Carton, Jora, Box",
        "pack_size_label": "Pack Size (Units per Pack)",
        "pack_cost_label": "Cost per Pack (TZS)",
        "calc_unit_cost": "Calculated Unit Cost",
        "calc_total_units": "Total Units Added",
        "add_new_inventory_header": "➕ Add New Inventory Item",
        "add_new_inventory_info": "Define item details below. If 'Initial Quantity' > 0, it will be added to stock.",
        "init_qty_label": "Initial Quantity (Packs)",
        "deduct_cash_check": "Deduct Total Cost from Liquid Cash?",
        "item_added_success": "Item '{item}' added successfully."
    },
    "Kiswahili": {
        "app_title": "ALSAM Vantage",
        "tagline": "Biashara mahiri, mustakabali angavu.",
        "card1_h": "Fuatilia Kila Shilingi",
        "card1_p": "Ufuatiliaji wa mzunguko wa pesa kwa wakati halisi.",
        "card2_h": "Ona Ukuaji",
        "card2_p": "Uchambuzi wa biashara zako zote kwa pamoja.",
        "card3_h": "Ripoti za Kitaalamu",
        "card3_p": "Afya ya pesa zako mahali pamoja.",
        "btn_signup": "Fungua Akaunti Mpya",
        "btn_login": "Ingia",
        "forgot": "Umesahau Nenosiri?",
        "help": "Msaada na Usaidizi",
        "lang_switch": "🌐 English",
        "signup_title": "Fungua Akaunti Yako",
        "signup_subtitle": "Anza kusimamia biashara zako leo.",
        "username": "Jina la Mtumiaji",
        "username_placeholder": "Chagua jina la kipekee",
        "email": "Barua Pepe",
        "email_placeholder": "barua@pepe.com",
        "pin": "PIN ya Tarakima 4",
        "pin_placeholder": "••••",
        "pin_confirm": "Thibitisha PIN",
        "security_question": "Swali la Usalama",
        "security_answer": "Jibu Lako",
        "recovery_key": "Ufunguo wa Kurejesha (Hifadhi Hii!)",
        "full_name": "Jina Kamili",
        "btn_register": "Fungua Akaunti",
        "btn_back": "← Rudi Nyumbani",
        "registration_success": "Akaunti Imeundwa kwa Mafanikio!",
        "username_exists": "Jina la mtumiaji lipo tayari.",
        "email_exists": "Barua pepe imesajiliwa tayari.",
        "secure_access": "Ufikiaji Salama",
        "enter_pin": "Weka PIN yako kufikia ALSAM Vantage.",
        "unlock": "Fungua Dashibodi",
        "enter_pin_warning": "Tafadhali weka PIN yako.",
        "access_denied": "Ufikiaji Umekataliwa: PIN au jina la mtumiaji sio sahihi.",
        "return_home": "← Rudi Ukurasa wa Nyumbani",
        "welcome_msg": "Karibu! Umeidhinishwa kama",
        "forgot_title": "Kurejesha Nenosiri",
        "forgot_subtitle": "Badilisha PIN yako kwa uthibitisho wa vyanzo mbalimbali.",
        "step_identification": "Hatua 1: Utambulisho",
        "step_security": "Hatua 2: Jaribio la Usalama",
        "step_token": "Hatua 3: Nambari ya Uthibitisho",
        "step_reset": "Hatua 4: Kubadilisha PIN",
        "enter_username_email": "Weka jina lako la mtumiaji au barua pepe",
        "btn_verify_identity": "Thibitisha Utambulisho",
        "answer_security_question": "Jibu swali lako la usalama:",
        "btn_verify_answer": "Thibitisha Jibu",
        "enter_token": "Weka nambari ya tarakima 8 ya uthibitisho",
        "btn_verify_token": "Thibitisha Nambari",
        "new_pin": "PIN MpyA ya Tarakima 4",
        "confirm_new_pin": "Thibitisha PIN MpyA",
        "btn_reset_pin": "Badilisha PIN",
        "pin_reset_success": "PIN imebadilishwa kwa mafanikio!",
        "identity_not_found": "Mtumiaji hajapatikana.",
        "security_answer_wrong": "Jibu sio sahihi.",
        "token_invalid": "Nambari si sahihi au imepitwa na wakati.",
        "pins_dont_match": "PIN hazilingani.",
        "back": "← Rudi",
        "help_title": "Msaada na Usaidizi",
        "help_subtitle": "Pata usaidizi na ALSAM Vantage",
        "faq_title": "Maswali Ya Kuulizwa Mara kwa Mara",
        "contact_support": "Wasiliana na Usaidizi",
        "subject": "Mada",
        "message": "Ujumbe",
        "priority": "Kipaumbele",
        "btn_submit_ticket": "Tuma Tiketi",
        "ticket_created": "Ombi la usaidizi limetumwa!",
        "fill_required": "Tafadhali jaza masharti yote yaliyo hitajika.",
        "nav_title": "Uabiri",
        "sign_out": "🚪 Toka",
        "role_label": "👤",
        "menu_dashboard": "🏠 Dashibodi Kuu",
        "menu_quicklog": "📝 Kumbusho la Haraka",
        "menu_records": "📜 Rekodi za Hivi Karibuni",
        "menu_ventures": "📊 Biashara",
        "menu_portfolio": "💰 Hazina ya Hisa",
        "menu_settings": "⚙️ Mipangilio",
        "executive_overview": "🏠 Muhtasari wa {}",
        "liquid_cash": "💵 Pesa Taslimu",
        "inventory_value": "📦 Thamani ya Hifadhi",
        "portfolio": "📈 Hisa",
        "net_worth": "🏆 Jumla ya Mali",
        "wealth_assessment": "📊 Tathmini ya Mali",
        "total_capital": "Jumla ya Mtaji",
        "expected_roi": "ROI Inayotarajiwa",
        "liquidity_ratio": "Uwiano wa Uwezekaji",
        "cross_venture": "📊 Utendaji wa Biashara",
        "no_data": "Hakuna Data ya Muamala",
        "start_logging": "Anza kurekodi mikakati ya pesa.",
        "income": "Mapato",
        "expense": "Matumizi",
        "net_profit": "Faida ya Mtandao",
        "transactions": "Miamala",
        "margin": "Ukingo %",
        "potential": "Uwezekaji",
        "profit": "Faida",
        "quicklog_title": "📝 Kumbusho la Haraka",
        "quicklog_info": "Rekodi mikakati ya pesa kwa haraka kwa biashara yoyote.",
        "date": "Tarehe",
        "venture": "Biashara",
        "new_venture": "Biashara Mpya",
        "new_venture_name": "Jina la Biashara Mpya",
        "amount_tzs": "Kiasi (TZS)",
        "type": "Aina",
        "note": "Maelezo",
        "save": "✅ Hifadhi",
        "fill_venture_amount": "Jaza jina la biashara na kiasi.",
        "transaction_saved": "Muamala umehifadhiwa kwa",
        "recent_records": "📜 Rekodi za Hivi Karibuni",
        "no_records": "Hakuna Rekodi Bado",
        "start_transactions": "Anza kurekodi mikakati ya pesa.",
        "edit_hint": "💡 **Bofya kitufe chochote kuhariri. Mabadiliko huhifadhiwa unapobofya 'Hifadhi Yote'.**",
        "save_all": "💾 Hifadhi Yote",
        "refresh": "🔄 Onyesha upya",
        "cancel": "❌ Ghairi",
        "changes_saved": "✅ Mabadiliko yote yamehifadhiwa!",
        "delete_single": "🗑️ Futa Rekodi Moja",
        "select_record": "Chagua Rekodi:",
        "delete_selected": "🗑️ Futa Rekodi Iliyochaguliwa",
        "record_deleted": "Rekodi imefutwa!",
        "ventures_title": "📊 Biashara",
        "register_venture": "➕ Sajili Biashara",
        "venture_name": "Jina la Biashara",
        "description": "Maelezo",
        "register": "Sajili",
        "venture_registered": "imesajiliwa!",
        "select_venture_label": "Chagua Biashara:",
        "no_ventures": "Hakuna Biashara",
        "register_first": "Sajili biashara kutoka upande wa skrini.",
        "tab_inventory": "📦 Hifadhi",
        "tab_transactions": "💸 Mikakati",
        "tab_analytics": "📈 Uchambuzi",
        "tab_delete": "⚠️ Futa",
        "tab_restock": "♻️ Jazia",
        "tab_sell": "🛒 Uza",
        "inventory_for": "📦 Hifadhi:",
        "item_name": "Jina la Bidhaa",
        "quantity": "Idadi",
        "buy_price": "Bei ya Kununua",
        "target_price": "Bei ya Kuuza",
        "add_inventory": "➕ Ongeza kwenye Hifadhi",
        "added_units": "Umeongeza",
        "units_of": "vipande vya",
        "no_inventory": "Hakuna Hifadhi",
        "add_items": "Ongeza vitu hapo juu.",
        "total_investment": "Jumla ya Uwekezaji",
        "expected_profit": "Faida Inayotarajiwa",
        "delete_item": "🗑️ Futa Bidhaa",
        "select_item": "Chagua Bidhaa:",
        "delete_item_btn": "Futa Bidhaa",
        "item_deleted": "Bidhaa imefutwa!",
        "log_trans_for": "💸 Rekodi Muamala:",
        "log_trans": "📝 Rekodi Muamala",
        "trans_logged": "✅ Muamala umerekodiwa!",
        "analytics_for": "📈 Uchambuzi:",
        "net": "💵 Faida ya Mtandao",
        "profit_margin": "📊 Ukingo wa Faida",
        "roi": "📈 ROI",
        "inventory_analysis": "📦 Uchambuzi wa Hifadhi",
        "capital_invested": "Mtaji Ulioingizwa",
        "danger_zone": "⚠️ Eneo la Hatari",
        "delete_warning": "⚠️ Unakaribia KUFUTA biashara nzima:",
        "delete_permanently": "Hii itafuta kabisa:",
        "all_trans_for": "Miamala yote ya",
        "all_inventory_for": "Vitu vyote vya hifadhi vya",
        "all_related": "Data yote inayohusiana",
        "cannot_undo": "**Kitendo hiki HAKIWEZI kurudishwa!**",
        "type_confirm": "Andika jina la biashara kuthibitisha kufuta:",
        "delete_entire": "🗑️ FUTA BIASHARA NZIMA:",
        "venture_deleted": "✅ Biashara imefutwa kabisa!",
        "delete_failed": "Imeshindwa kufuta biashara.",
        "deletion_cancelled": "Kufuta kumeghairiwa.",
        "portfolio_title": "💰 Hazina ya Hisa",
        "portfolio_info": "Dhibiti hisa na mali.",
        "asset_name": "Jina la Mali",
        "ticker": "Alama",
        "units": "Vipande",
        "buy_price_short": "Bei ya Kununua",
        "current_price": "Bei ya Sasa",
        "add_vault": "➕ Ongeza kwenye Hazina",
        "added_to_vault": "imeongezwa!",
        "vault_empty": "Hazina Tupu",
        "add_assets": "Ongeza mali hapo juu.",
        "invested": "Uliowekeza",
        "value": "Thamani",
        "pl": "P/L",
        "pl_percent": "P/L %",
        "total_invested": "Jumla Uliowekeza",
        "current_value": "Thamani ya Sasa",
        "total_pl": "Jumla P/L",
        "remove_asset": "🗑️ Ondoa Mali",
        "select_asset": "Chagua Mali:",
        "remove_btn": "Ondoa Mali",
        "asset_removed": "Mali imeondolewa!",
        "settings_title": "⚙️ Mipangilio",
        "account_tab": "🔒 Akaunti",
        "data_tab": "💾 Data",
        "profile": "Wasifu",
        "role": "Jukumu",
        "switch_lang": "🌐 Badilisha kuwa",
        "data_management": "Usimamizi wa Data",
        "ledger": "Ledger",
        "stocks": "Hifadhi",
        "download_backup": "📥 Pakua Nakala ya Ledger",
        "factory_reset": "🔥 Kurudisha Kiwanda",
        "type_confirm_reset": "Andika 'CONFIRM' kufuta data yote:",
        "delete_all": "FUTA DATA YOTE",
        "all_deleted": "Data yote imefutwa.",
        "col_date": "Tarehe (YYYY-MM-DD)",
        "col_venture": "Biashara",
        "col_amount": "Kiasi (TZS)",
        "col_type": "Aina",
        "col_note": "Maelezo",
        "col_uid": "UID",
        "col_buy_price": "Bei ya Kununua",
        "col_sell_price": "Bei ya Kuuza",
        "col_cost": "Gharama",
        "total_asset_base": "Msingi wa Mali Yote",
        "wealth_growth_title": "📈 Kufuatilia Ukuaji wa Mali",
        "month": "Mwezi",
        "cumulative_cash": "Pesa Iliyokusanyika",
        "restock_title": "♻️ Jazia na Wekeza Tena",
        "restock_info": "Geuza Pesa Taslimu kuwa Hifadhi. Hii inahifadhi Jumla ya Mali kwa kuhamisha thamani kutoka Pesa hadi Mali.",
        "restock_item_label": "Chagua Bidhaa ya Kujazia",
        "restock_new_item_label": "Au Ongeza Bidhaa Mpya",
        "restock_qty": "Idadi ya Kuongeza",
        "restock_buy_price": "Gharama kwa Kipande (Bei ya Kununua)",
        "restock_sell_price": "Bei Mpya ya Kuuza",
        "btn_restock": "🛒 Thibitisha Ununuzi",
        "restock_success": "Umefanikiwa kununua {item}. Pesa imegeuzwa kuwa Hifadhi.",
        "insufficient_funds": "⚠️ Pesa Taslimu haitoshi kwa uwekezaji huu.",
        "restock_item_created": "Bidhaa mpya imeundwa na kuhifadhiwa.",
        "restock_item_updated": "Hifadhi imesasishwa.",
        "inv_capital_label": "Mtaji Umefungika (Gharama)",
        "inv_potential_label": "Uwezo wa Uuzaji (Mapato)",
        "realized_profit_label": "Faida Iliyopatikana (Taslimu)",
        "unit_type_label": "Kipimo cha Kuuza (kwa vipande)",
        "unit_type_placeholder": "mf. Pcs, Mita",
        "sell_title": "🛒 Uza Bidhaa (Point of Sale)",
        "sell_info": "Chagua bidhaa kutoka hifadhi yako kuuza. Hii inapunguza moja kwa moja hesabu na kurekodi faida.",
        "sell_select_item": "Chagua Bidhaa ya Kuuza",
        "sell_qty": "Idadi ya Kuuza",
        "sell_price": "Bei ya Uuzaji kwa Kipande",
        "btn_sell": "💵 Thibitisha Uuzaji",
        "sell_success": "Uuzaji umekamilika! Umeuza {qty} {unit} ya {item}.",
        "sell_no_stock": "Hakuna bidhaa kwenye hifadhi za kuuza.",
        "sell_insufficient_stock": "Hifadhi haitoshi. Zinazopatikana: {stock} {unit}.",
        "sell_profit_log": "Faida: {profit:,.0f} TZS.",
        "unit_pcs": "Vipande (Pcs)",
        "unit_m": "Mita (m)",
        "unit_box": "Masanduku",
        "unit_ctn": "Kartoni",
        "unit_kg": "Kilogramu (kg)",
        "unit_other": "Nyingine",
        "pack_buying_unit": "Aina ya Pakiti (Ununuzi)",
        "pack_buying_unit_ph": "mf. Kartoni, Jora",
        "pack_size_label": "Ukubwa wa Pakiti (Vipande kwa Pakiti)",
        "pack_cost_label": "Gharama kwa Pakiti (TZS)",
        "calc_unit_cost": "Gharama ya Kipande (Hesabu)",
        "calc_total_units": "Jumla ya Vipande Vilivyoongezwa",
        "add_new_inventory_header": "➕ Ongeza Bidhaa Mpya ya Hifadhi",
        "add_new_inventory_info": "Fafanua maelezo ya bidhaa hapa chini. Ikiwa 'Idadi ya Awali' > 0, itaongezwa kwenye hifadhi.",
        "init_qty_label": "Idadi ya Awali (Pakiti)",
        "deduct_cash_check": "Kata Gharama Jumla kutoka Pesa Taslimu?",
        "item_added_success": "Bidhaa '{item}' imeongezwa kwa mafanikio."
    }
}


def t(key: str) -> str:
    return TEXTS.get(st.session_state.lang, TEXTS["English"]).get(key, key)


def switch_language():
    if st.session_state.lang == "English":
        st.session_state.lang = "Kiswahili"
    else:
        st.session_state.lang = "English"

def render_language_switcher(key_suffix: str = ""):
    key = f"lang_switch_{key_suffix}" if key_suffix else "lang_switch"
    st.button(t('lang_switch'), use_container_width=True, key=key, on_click=switch_language)

def render_empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
        <div class="empty-state">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-subtitle">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)


# ================================================================================
# 7. LANDING PAGE
# ================================================================================
def show_landing():
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    cols = st.columns([9, 1])
    with cols[1]:
        render_language_switcher("landing")

    st.markdown("<div class='logo-wrapper'>", unsafe_allow_html=True)
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=320)
    else:
        st.markdown(f"<h1 style='color: #013C7B; font-size: 3rem; font-weight: 900; text-align: center;'>{t('app_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='alsam-tagline'>{t('tagline')}</p></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='vantage-card'><h2>📊</h2><b>{t('card1_h')}</b><p style='color:#666; margin-top:10px;'>{t('card1_p')}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='vantage-card'><h2>📈</h2><b>{t('card2_h')}</b><p style='color:#666; margin-top:10px;'>{t('card2_p')}</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='vantage-card'><h2>📑</h2><b>{t('card3_h')}</b><p style='color:#666; margin-top:10px;'>{t('card3_p')}</p></div>", unsafe_allow_html=True)

    st.write("---")

    _, center_col, _ = st.columns([3, 4, 3])
    with center_col:
        if st.button(t('btn_signup'), type="primary", use_container_width=True, key="btn_signup"):
            st.session_state.page = "signup"
            st.rerun()

        if st.button(t('btn_login'), type="secondary", use_container_width=True, key="btn_login"):
            st.session_state.page = "login"
            st.rerun()

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            if st.button(f"🔑 {t('forgot')}", key="forgot_btn", use_container_width=True):
                st.session_state.page = "forgot"
                st.rerun()
        with r_col2:
            if st.button(f"💬 {t('help')}", key="help_btn", use_container_width=True):
                st.session_state.page = "help"
                st.rerun()


# ================================================================================
# 8. REGISTRATION PAGE
# ================================================================================
def show_registration():
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    
    cols = st.columns([9, 1])
    with cols[1]:
        render_language_switcher("signup")

    st.markdown(f"<h1 style='text-align: center; color: #013C7B;'>🚀 {t('signup_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>{t('signup_subtitle')}</p>", unsafe_allow_html=True)
    st.write("---")

    with st.container(border=True):
        with st.form("registration_form", clear_on_submit=False):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input(t('username'), placeholder=t('username_placeholder'), key="reg_username")
                email = st.text_input(t('email'), placeholder=t('email_placeholder'), key="reg_email")
                full_name = st.text_input(t('full_name'), key="reg_fullname")

            with col2:
                pin = st.text_input(t('pin'), type="password", max_chars=4, placeholder=t('pin_placeholder'), key="reg_pin")
                pin_confirm = st.text_input(t('pin_confirm'), type="password", max_chars=4, placeholder=t('pin_placeholder'), key="reg_pin_confirm")

            st.divider()

            security_questions = [
                "What city were you born in?",
                "What is your mother's maiden name?",
                "What was the name of your first pet?",
                "What high school did you attend?",
                "What is your favorite book?"
            ]
            security_q = st.selectbox(t('security_question'), security_questions, key="reg_sec_q")
            security_a = st.text_input(t('security_answer'), key="reg_sec_a")

            submitted = st.form_submit_button(t('btn_register'), type="primary", use_container_width=True)

            if submitted:
                if not all([username, email, pin, full_name, security_a]):
                    st.error(t('fill_required'))
                elif pin != pin_confirm:
                    st.error(t('pins_dont_match'))
                elif len(pin) != 4 or not pin.isdigit():
                    st.error("PIN must be exactly 4 digits.")
                else:
                    recovery_key = SecurityManager.generate_recovery_key()

                    user_data = {
                        "Username": username,
                        "Email": email,
                        "PINHash": SecurityManager.hash_pin(pin),
                        "Role": "Owner",
                        "SecurityQuestion": security_q,
                        "SecurityAnswerHash": SecurityManager.hash_pin(security_a.lower()),
                        "RecoveryKey": recovery_key,
                        "FullName": full_name
                    }

                    success, result = data_manager.create_user(user_data)

                    if success:
                        st.success(f"✅ {t('registration_success')}")
                        st.info(f"🔑 **{t('recovery_key')}:** `{recovery_key}`")
                        st.warning("⚠️ **Save this recovery key securely!**")

                        if st.button("Continue to Login", type="primary", key="cont_to_login"):
                            st.session_state.page = "login"
                            st.rerun()
                    else:
                        if "Username" in result:
                            st.error(t('username_exists'))
                        elif "Email" in result:
                            st.error(t('email_exists'))
                        else:
                            st.error(result)

    st.write("")
    if st.button(t('btn_back'), type="secondary", use_container_width=True, key="back_signup"):
        st.session_state.page = "landing"
        st.rerun()


# ================================================================================
# 9. LOGIN PAGE
# ================================================================================
def show_login():
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    cols = st.columns([9, 1])
    with cols[1]:
        render_language_switcher("login")

    st.markdown(f"<h1 style='text-align: center; color: #013C7B;'>🔒 {t('secure_access')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>{t('enter_pin')}</p>", unsafe_allow_html=True)
    st.write("---")

    with st.container(border=True):
        with st.form("login_form", border=False):
            username = st.text_input(t('username'), key="login_username", placeholder="Enter your username")
            pin = st.text_input("PIN", type="password", max_chars=4, placeholder=t('pin_placeholder'), label_visibility="collapsed", key="pin_input")
            st.write("#")

            submitted = st.form_submit_button(t('unlock'), type="primary", use_container_width=True)

            if submitted:
                if not username:
                    st.warning("Please enter your username.")
                elif not pin:
                    st.warning(t('enter_pin_warning'))
                else:
                    user = data_manager.get_user_by_username(username)
                    if user is not None and SecurityManager.verify_pin_hash(pin, user["PINHash"]):
                        st.session_state.authenticated = True
                        st.session_state.user_id = user["UserID"]
                        st.session_state.username = user["Username"]
                        st.session_state.role = user["Role"]
                        st.session_state.page = "dashboard"
                        data_manager.update_user_login(user["UserID"])
                        st.success(f"✅ {t('welcome_msg')} {user['Role']}.")
                        st.rerun()
                    else:
                        st.error(t('access_denied'))

    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🔑 {t('forgot')}", key="login_forgot", use_container_width=True):
            st.session_state.page = "forgot"
            st.rerun()
    with col2:
        if st.button(f"💬 {t('help')}", key="login_help", use_container_width=True):
            st.session_state.page = "help"
            st.rerun()

    st.write("")
    if st.button(t('return_home'), type="secondary", use_container_width=True, key="return_home"):
        st.session_state.page = "landing"
        st.rerun()


# ================================================================================
# 10. FORGOT PASSWORD PAGE
# ================================================================================
def show_forgot_password():
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    cols = st.columns([9, 1])
    with cols[1]:
        render_language_switcher("forgot")

    st.markdown(f"<h1 style='text-align: center; color: #013C7B;'>🔑 {t('forgot_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>{t('forgot_subtitle')}</p>", unsafe_allow_html=True)
    st.write("---")

    with st.container(border=True):
        current_step = st.session_state.recovery_step + 1
        step_names = [t('step_identification'), t('step_security'), t('step_token'), t('step_reset')]
        for i, name in enumerate(step_names):
            if i < current_step:
                st.success(f"✅ {name}")
            elif i == current_step - 1:
                st.info(f"🔵 {name}")
            else:
                st.caption(f"⚪ {name}")

        st.divider()

        if st.session_state.recovery_step == 0:
            identifier = st.text_input(t('enter_username_email'), key="forgot_identifier")

            if st.button(t('btn_verify_identity'), type="primary", use_container_width=True, key="btn_verify_id"):
                user = data_manager.get_user_by_username(identifier)
                if user is None:
                    user = data_manager.get_user_by_email(identifier)

                if user is not None:
                    st.session_state.recovery_user_id = user["UserID"]
                    st.session_state.recovery_step = 1
                    st.rerun()
                else:
                    st.error(t('identity_not_found'))

        elif st.session_state.recovery_step == 1:
            user = data_manager.get_user_by_id(st.session_state.recovery_user_id)
            if user is not None:
                st.info(f"**{user['SecurityQuestion']}**")
                answer = st.text_input(t('security_answer'), key="forgot_answer")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(t('back'), key="back_sec", use_container_width=True):
                        st.session_state.recovery_step = 0
                        st.rerun()
                with col2:
                    if st.button(t('btn_verify_answer'), type="primary", key="btn_verify_ans", use_container_width=True):
                        if SecurityManager.hash_pin(answer.lower()) == user["SecurityAnswerHash"]:
                            st.session_state.recovery_step = 2
                            token = data_manager.create_recovery_token(user["UserID"])
                            st.session_state.recovery_token = token
                            st.rerun()
                        else:
                            st.error(t('security_answer_wrong'))

        elif st.session_state.recovery_step == 2:
            user = data_manager.get_user_by_id(st.session_state.recovery_user_id)
            st.info(f"Token: **{st.session_state.get('recovery_token', 'N/A')}**")
            st.caption(f"*(Sent to {user['Email']})*")

            token_input = st.text_input(t('enter_token'), max_chars=8, key="forgot_token")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(t('back'), key="back_token", use_container_width=True):
                    st.session_state.recovery_step = 1
                    st.rerun()
            with col2:
                if st.button(t('btn_verify_token'), type="primary", key="btn_verify_tok", use_container_width=True):
                    if data_manager.verify_recovery_token(st.session_state.recovery_user_id, token_input):
                        st.session_state.recovery_step = 3
                        st.rerun()
                    else:
                        st.error(t('token_invalid'))

        elif st.session_state.recovery_step == 3:
            col1, col2 = st.columns(2)
            with col1:
                new_pin = st.text_input(t('new_pin'), type="password", max_chars=4, key="new_pin")
            with col2:
                confirm_pin = st.text_input(t('confirm_new_pin'), type="password", max_chars=4, key="confirm_pin")

            if st.button(t('btn_reset_pin'), type="primary", use_container_width=True, key="btn_reset_pin"):
                if new_pin != confirm_pin:
                    st.error(t('pins_dont_match'))
                elif len(new_pin) != 4 or not new_pin.isdigit():
                    st.error("PIN must be exactly 4 digits.")
                else:
                    if data_manager.update_user_pin(st.session_state.recovery_user_id, SecurityManager.hash_pin(new_pin)):
                        data_manager.mark_token_used(st.session_state.recovery_user_id, st.session_state.recovery_token)
                        st.success(f"✅ {t('pin_reset_success')}")
                        st.session_state.recovery_step = 0
                        st.session_state.recovery_user_id = None
                        st.session_state.recovery_token = None

                        if st.button("Go to Login", type="primary", key="go_login"):
                            st.session_state.page = "login"
                            st.rerun()

    st.write("")
    if st.button(t('btn_back'), type="secondary", use_container_width=True, key="back_forgot"):
        st.session_state.page = "landing"
        st.session_state.recovery_step = 0
        st.rerun()


# ================================================================================
# 11. HELP PAGE
# ================================================================================
def show_help_support():
    st.markdown(HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    cols = st.columns([9, 1])
    with cols[1]:
        render_language_switcher("help")

    st.markdown(f"<h1 style='text-align: center; color: #013C7B;'>💬 {t('help_title')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>{t('help_subtitle')}</p>", unsafe_allow_html=True)
    st.write("---")

    with st.expander(f"❓ {t('faq_title')}", expanded=True):
        faqs = [
            ("How do I add a new venture?", "Navigate to 'Business Ventures' and click 'Register Venture'."),
            ("How do I track inventory?", "Select a venture, then use the Inventory tab."),
            ("How do I reset my PIN?", "Click 'Forgot Password' and follow the verification process."),
            ("What is the Recovery Key?", "A 16-character code for account recovery. Keep it safe."),
        ]
        for q, a in faqs:
            st.markdown(f"**Q: {q}**")
            st.markdown(f"A: {a}")
            st.write("")

    with st.container(border=True):
        st.markdown(f"**{t('contact_support')}**")
        with st.form("support_form", clear_on_submit=True):
            subject = st.text_input(t('subject'), key="help_subject")
            message = st.text_area(t('message'), height=100, key="help_message")
            priority = st.selectbox(t('priority'), ["Low", "Normal", "High", "Urgent"], key="help_priority")

            if st.form_submit_button(t('btn_submit_ticket'), type="primary", use_container_width=True):
                if subject and message:
                    st.success(f"✅ {t('ticket_created')}")
                else:
                    st.warning(t('fill_required'))

    st.write("")
    if st.button(t('btn_back'), type="secondary", use_container_width=True, key="back_help"):
        st.session_state.page = "landing"
        st.rerun()


# ================================================================================
# 12. DASHBOARD
# ================================================================================
def show_dashboard():
    if not st.session_state.system_verified:
        status = data_manager.verify_system_integrity()
        st.session_state.system_verified = True

    user_id = st.session_state.user_id
    current_role = st.session_state.role
    current_user = st.session_state.username

    df_ledger = data_manager.get_user_ledger(user_id)
    df_stocks = data_manager.get_user_stocks(user_id)
    df_portfolio = data_manager.get_user_portfolio(user_id)

    venture_list = sorted(df_ledger["Venture"].dropna().unique().tolist()) if not df_ledger.empty else []
    venture_list = [v for v in venture_list if v and v != "System"]

    with st.sidebar:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=150)
        else:
            st.title("🏢 ALSAM")
        
        st.divider()
        menu = st.radio("Navigation:", [
            "🏢 Main Dashboard", 
            "📝 Quick-Log", 
            "📜 Recent Records", 
            "📊 Business Ventures", 
            "💰 Portfolio Vault", 
            "⚙️ Settings"
        ], key="menu_selection")

        st.divider()
        render_language_switcher("dashboard")

        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.page = "landing"
            if 'menu_selection' in st.session_state:
                del st.session_state['menu_selection']
            st.rerun()

    if menu == "🏢 Main Dashboard":
        show_main_dashboard(df_ledger, df_stocks, df_portfolio, current_user)
    elif menu == "📝 Quick-Log":
        show_quick_log(df_ledger, venture_list, current_user, user_id)
    elif menu == "📜 Recent Records":
        show_recent_records(user_id, current_role, current_user)
    elif menu == "📊 Business Ventures":
        show_business_ventures(user_id, current_user, current_role, venture_list)
    elif menu == "💰 Portfolio Vault":
        show_portfolio_vault(user_id, current_user)
    elif menu == "⚙️ Settings":
        show_settings(user_id, current_role)


# ================================================================================
# 13. DASHBOARD FUNCTIONS
# ================================================================================
def show_main_dashboard(df_ledger, df_stocks, df_portfolio, username):
    st.header(f"🏠 {username.upper()}'s Executive Summary")

    actual_df = df_ledger[df_ledger["Type"] != "System"].copy() if not df_ledger.empty else pd.DataFrame()
    
    # --- CORE CALCULATION ---
    
    # 1. Cash Flow Calculation (Real)
    # Income adds money. Expenses destroy money. Reinvestment moves money.
    total_income = actual_df[actual_df["Type"].str.contains("Income", na=False)]["Amount"].sum() if not actual_df.empty else 0
    total_expense = actual_df[actual_df["Type"] == "Expense"]["Amount"].sum() if not actual_df.empty else 0
    total_reinvestment = actual_df[actual_df["Type"] == "Reinvestment"]["Amount"].sum() if not actual_df.empty else 0
    
    liquid_cash = total_income - total_expense - total_reinvestment

    # 2. Inventory Value (Real - Cost Basis)
    # This is the money tied up in unsold goods. An Asset.
    inventory_value_capital = (df_stocks["Units"] * df_stocks["BuyingPrice"]).sum() if not df_stocks.empty else 0
    
    # 3. Inventory Potential (Projected)
    # What you expect to get if you sell everything.
    inventory_potential = (df_stocks["Units"] * df_stocks["CurrentPrice"]).sum() if not df_stocks.empty else 0

    # 4. Portfolio Value
    port_current = (df_portfolio["Units"] * df_portfolio["CurrentPrice"]).sum() if not df_portfolio.empty else 0

    # 5. Net Worth (Real)
    # Cash + Assets (at cost) + Investments
    net_worth = liquid_cash + inventory_value_capital + port_current

    # 6. Realized Profit (The Truth of Business Performance)
    # Cash generated from operations.
    realized_profit = total_income - total_expense

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Liquid Cash", f"{liquid_cash:,.0f} TZS")
    col2.metric("📦 Inventory Value (Cost)", f"{inventory_value_capital:,.0f} TZS")
    col3.metric("📈 Portfolio", f"{port_current:,.0f} TZS")
    col4.metric("🏆 NET WORTH", f"{net_worth:,.0f} TZS", delta=f"Potential: {inventory_potential:,.0f}")

    # NEW: Realized Profit Metric
    st.divider()
    st.metric(f"📉 {t('realized_profit_label')}", f"{realized_profit:,.0f} TZS", 
              delta="Profit from Sales minus Expenses", delta_color="normal")
    st.caption("*This reflects the actual cash profit generated. Restock (Asset purchase) does not reduce this value, but Expenses (Rent/Transport) do.*")

    st.divider()
    
    st.subheader(t('wealth_growth_title'))
    
    if not actual_df.empty:
        actual_df['Date'] = pd.to_datetime(actual_df['Date'], errors='coerce')
        actual_df = actual_df.dropna(subset=['Date'])
        actual_df['Month'] = actual_df['Date'].dt.to_period('M')
        
        monthly_data = actual_df.groupby('Month').apply(
            lambda x: pd.Series({
                'Income': x[x['Type'].str.contains('Income', na=False)]['Amount'].sum(),
                'Expense': x[x['Type'] == 'Expense']['Amount'].sum(),
                'Reinvestment': x[x['Type'] == 'Reinvestment']['Amount'].sum()
            })
        ).reset_index()
        
        # Real Net Flow: Cash Generated or Lost
        monthly_data['Net Flow'] = monthly_data['Income'] - monthly_data['Expense'] - monthly_data['Reinvestment']
        
        # Cumulative Cash: Running total of wealth generation
        monthly_data['Cumulative Cash'] = monthly_data['Net Flow'].cumsum()
        monthly_data['Month'] = monthly_data['Month'].astype(str)
        
        display_growth = monthly_data.copy()
        display_growth['Income'] = display_growth['Income'].apply(lambda x: f"{x:,.0f}")
        display_growth['Expense'] = display_growth['Expense'].apply(lambda x: f"{x:,.0f}")
        display_growth['Reinvestment'] = display_growth['Reinvestment'].apply(lambda x: f"{x:,.0f}")
        display_growth['Net Flow'] = display_growth['Net Flow'].apply(lambda x: f"{x:,.0f}")
        display_growth['Cumulative Cash'] = display_growth['Cumulative Cash'].apply(lambda x: f"{x:,.0f}")
        
        display_growth.columns = [t('month'), t('income'), t('expense'), "Reinvestment", t('net_profit'), t('cumulative_cash')]
        
        st.dataframe(display_growth, use_container_width=True, hide_index=True)
    else:
        st.info(t('no_data'))
        
    st.divider()
    
    st.subheader("📊 Net Cash Flow by Venture")

    if not actual_df.empty:
        summary = actual_df.groupby("Venture").apply(
            lambda x: pd.Series({
                "Income": x[x["Type"].str.contains("Income", na=False)]["Amount"].sum(),
                "Expense": x[x["Type"] == "Expense"]["Amount"].sum(),
                "Reinvestment": x[x["Type"] == "Reinvestment"]["Amount"].sum()
            })
        ).reset_index()
        summary["Net Cash"] = summary["Income"] - summary["Expense"] - summary["Reinvestment"]
        summary = summary.sort_values("Net Cash", ascending=False)
        summary.index = range(1, len(summary) + 1)
        st.dataframe(summary[["Venture", "Income", "Expense", "Reinvestment", "Net Cash"]], use_container_width=True)
    else:
        st.info("No transaction data available yet. Start logging to see analytics.")


def show_quick_log(df_ledger, venture_list, current_user, user_id):
    st.header("📝 Quick-Log Entry")
    st.info("Use this form to record current or past transactions.")

    with st.container(border=True):
        with st.form("quick_log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                f_date = st.date_input("Date", value=datetime.now(), key="qlog_date")
                f_venture = st.selectbox("Venture", options=venture_list if venture_list else ["New Venture"], key="qlog_venture")
                if f_venture == "New Venture" or not venture_list:
                    f_venture = st.text_input("New Venture Name", key="qlog_new_venture")
            with col2:
                f_amount = st.number_input("Amount (TZS)", min_value=0, step=1000, key="qlog_amount")
                f_type = st.selectbox("Type", ["Income", "Expense"], key="qlog_type")

            f_note = st.text_input("Note", key="qlog_note")

            if st.form_submit_button("✅ Save", type="primary", use_container_width=True):
                if f_venture and f_amount > 0:
                    record = {"Date": str(f_date), "Venture": f_venture, "Amount": f_amount, "Type": f_type, "Category": "Quick Log", "Note": f_note, "CreatedBy": current_user}
                    _, success = data_manager.add_ledger_entry(user_id, record)
                    if success:
                        st.success(f"✅ Transaction saved for {f_venture}!")
                        st.rerun()
                else:
                    st.warning("Fill in venture and amount.")


def show_recent_records(user_id, current_role, current_user):
    st.header("📜 Recent Records")
    df_ledger = data_manager.get_user_ledger(user_id)
    display_df = df_ledger[df_ledger["Type"] != "System"].copy() if not df_ledger.empty else pd.DataFrame()

    if display_df.empty:
        st.info("No records yet. Start logging transactions.")
        return

    display_df = display_df.sort_values(by="Date", ascending=False).reset_index(drop=True)
    st.write("💡 **Click any cell to edit. Changes save when you click 'Save All Changes'.**")

    edit_df = display_df[["Date", "Venture", "Amount", "Type", "Note", "UID"]].copy()
    edited_df = st.data_editor(edit_df, use_container_width=True, num_rows="dynamic", key="records_editor",
        column_config={
            "Date": st.column_config.TextColumn("Date (YYYY-MM-DD)", required=True),
            "Venture": st.column_config.TextColumn("Venture"),
            "Amount": st.column_config.NumberColumn("Amount (TZS)", format="%,.0f", min_value=0),
            "Type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense", "Reinvestment"]),
            "Note": st.column_config.TextColumn("Note"),
            "UID": st.column_config.TextColumn("UID", disabled=True)
        }, hide_index=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("💾 Save All Changes", type="primary", key="save_records"):
            df_full = data_manager.get_user_ledger(user_id)
            system_rows = df_full[df_full["Type"] == "System"].copy() if not df_full.empty else pd.DataFrame()
            edited_df["OrgID"] = user_id
            edited_df["CreatedBy"] = current_user
            edited_df["Category"] = "Edited"
            final_df = pd.concat([system_rows, edited_df], ignore_index=True)
            if data_manager.save_data(final_df, DB_FILE):
                st.success("✅ All changes saved!")
                st.rerun()
    with col2:
        if st.button("🔄 Refresh", key="refresh_records"):
            st.rerun()
    with col3:
        if st.button("❌ Cancel", key="cancel_edits"):
            st.rerun()

    st.divider()
    st.subheader("🗑️ Delete Single Record")
    with st.expander("Select Record:"):
        record_options = display_df["UID"].tolist()
        if record_options:
            record_to_delete = st.selectbox("Select Record:", options=record_options,
                format_func=lambda x: f"{display_df[display_df['UID']==x]['Date'].iloc[0]} | {display_df[display_df['UID']==x]['Venture'].iloc[0]} | {float(display_df[display_df['UID']==x]['Amount'].iloc[0]):,.0f} TZS", key="delete_select")
            if st.button("🗑️ Delete Selected Record", type="secondary", key="confirm_delete"):
                _, success = data_manager.delete_by_uid(DB_FILE, DB_COLS, record_to_delete)
                if success:
                    st.success("Record deleted!")
                    st.rerun()


def show_business_ventures(user_id, current_user, current_role, venture_list):
    st.header("📊 Business Ventures")

    with st.expander("➕ Register New Venture", expanded=len(venture_list) == 0):
        with st.form("new_venture_form", clear_on_submit=True):
            new_name = st.text_input("Venture Name", key="nv_name")
            new_desc = st.text_area("Description", key="nv_desc")
            if st.form_submit_button("Register", type="primary"):
                if new_name:
                    record = {"Date": str(datetime.now().date()), "Venture": new_name, "Amount": 0, "Type": "System", "Category": "Initialization", "Note": new_desc, "CreatedBy": current_user}
                    _, success = data_manager.add_ledger_entry(user_id, record)
                    if success:
                        st.success(f"✅ {new_name} registered!")
                        st.rerun()

    clean_list = [v for v in venture_list if v]
    selected = st.selectbox("Select Venture:", options=clean_list if clean_list else ["No Ventures"], key="venture_select")

    if not clean_list:
        st.info("No ventures registered. Register a venture above.")
        return

    st.divider()
    df_ledger = data_manager.get_user_ledger(user_id)
    df_stocks = data_manager.get_user_stocks(user_id)
    v_ledger = df_ledger[df_ledger["Venture"] == selected].copy() if not df_ledger.empty else pd.DataFrame()
    v_stocks = df_stocks[df_stocks["Venture"] == selected].copy() if not df_stocks.empty else pd.DataFrame()

    v_income = v_ledger[v_ledger["Type"].str.contains("Income", na=False)]["Amount"].sum() if not v_ledger.empty else 0
    v_expense = v_ledger[v_ledger["Type"] == "Expense"]["Amount"].sum() if not v_ledger.empty else 0
    v_reinvest = v_ledger[v_ledger["Type"] == "Reinvestment"]["Amount"].sum() if not v_ledger.empty else 0
    v_liquid = v_income - v_expense - v_reinvest
    
    # Real Logic: Separate Capital from Potential
    v_inv_capital = (v_stocks["Units"] * v_stocks["BuyingPrice"]).sum() if not v_stocks.empty else 0
    v_inv_potential = (v_stocks["Units"] * v_stocks["CurrentPrice"]).sum() if not v_stocks.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Income", f"{v_income:,.0f} TZS")
    col2.metric("💸 Expense", f"{v_expense:,.0f} TZS")
    col3.metric("📈 Liquid Cash", f"{v_liquid:,.0f} TZS")
    col4.metric("📦 Inventory (Capital)", f"{v_inv_capital:,.0f} TZS", delta=f"Potential: {v_inv_potential:,.0f}")

    st.divider()
    # UPDATED TABS: Added "Sell Item"
    tab_stock, tab_trans, tab_restock, tab_sell, tab_intel, tab_delete = st.tabs(["📦 Inventory", "💸 Transactions", "♻️ Restock", "🛒 Sell Item", "📈 Analytics", "⚠️ Delete"])

    # --- INVENTORY TAB (UPDATED) ---
    with tab_stock:
        st.subheader(f"📦 Inventory: {selected}")
        
        # NEW: Add Item directly in Inventory
        with st.expander(f"{t('add_new_inventory_header')}"):
            st.info(t('add_new_inventory_info'))
            
            # Use a consistent form helper
            with st.form("add_inventory_item_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    ai_item_name = st.text_input(t('item_name'), key="ai_name")
                    ai_unit_type = st.selectbox(t('unit_type_label'), 
                        options=[t('unit_pcs'), t('unit_m'), t('unit_box'), t('unit_ctn'), t('unit_kg'), t('unit_other')], key="ai_unit")
                    
                    # Normalize unit type
                    if "Pieces" in ai_unit_type: ai_unit_val = "Pcs"
                    elif "Meters" in ai_unit_type: ai_unit_val = "Meters"
                    elif "Boxes" in ai_unit_type: ai_unit_val = "Box"
                    elif "Cartons" in ai_unit_type: ai_unit_val = "Carton"
                    elif "Kilograms" in ai_unit_type: ai_unit_val = "Kg"
                    else: ai_unit_val = ai_unit_type
                    
                    ai_pack_type = st.text_input(t('pack_buying_unit'), placeholder=t('pack_buying_unit_ph'), key="ai_pack_type")
                
                with col_b:
                    ai_pack_size = st.number_input(t('pack_size_label'), min_value=1, value=1, step=1, key="ai_pack_size")
                    ai_cost_per_pack = st.number_input(t('pack_cost_label'), min_value=0.0, step=100.0, key="ai_cost_pack")
                    ai_sell_price = st.number_input(t('target_price'), min_value=0.0, step=100.0, key="ai_sell")
                
                st.divider()
                ai_init_packs = st.number_input(t('init_qty_label'), min_value=0, value=0, step=1, key="ai_init_qty")
                ai_deduct_cash = st.checkbox(t('deduct_cash_check'), value=True, key="ai_deduct")
                
                submitted = st.form_submit_button(t('add_inventory'), type="primary")
                
                if submitted:
                    if not ai_item_name:
                        st.error("Item Name is required.")
                    else:
                        # Calculations
                        total_units = ai_init_packs * ai_pack_size
                        unit_cost = ai_cost_per_pack / ai_pack_size if ai_pack_size > 0 else 0
                        total_cost = ai_init_packs * ai_cost_per_pack
                        
                        # Logic: Check if we are adding stock
                        if ai_init_packs > 0 and ai_deduct_cash:
                            # Financial Check
                            if total_cost > v_liquid:
                                st.error(f"{t('insufficient_funds')} (Need: {total_cost:,.0f}, Have: {v_liquid:,.0f})")
                            else:
                                # 1. Log Reinvestment
                                record = {
                                    "Date": str(datetime.now().date()), 
                                    "Venture": selected, 
                                    "Amount": total_cost, 
                                    "Type": "Reinvestment", 
                                    "Category": "Inventory Setup", 
                                    "Note": f"Initial Stock: {ai_init_packs} {ai_pack_type} of {ai_item_name}", 
                                    "CreatedBy": current_user
                                }
                                _, success = data_manager.add_ledger_entry(user_id, record)
                                
                                if success:
                                    # 2. Add Inventory
                                    data_manager.upsert_stock_entry(user_id, selected, ai_item_name, total_units, ai_unit_val, unit_cost, ai_sell_price, ai_pack_size, ai_pack_type, current_user)
                                    st.success(t('item_added_success').format(item=ai_item_name))
                                    st.rerun()
                        else:
                            # Just add item definition (0 stock or no deduction)
                            data_manager.upsert_stock_entry(user_id, selected, ai_item_name, total_units, ai_unit_val, unit_cost, ai_sell_price, ai_pack_size, ai_pack_type, current_user)
                            st.success(t('item_added_success').format(item=ai_item_name))
                            st.rerun()

        st.divider()

        # Display Logic
        if not v_stocks.empty:
            v_stocks["Total Cost"] = v_stocks["Units"] * v_stocks["BuyingPrice"]
            v_stocks["Potential"] = v_stocks["Units"] * v_stocks["CurrentPrice"]
            v_stocks["Expected Profit"] = v_stocks["Potential"] - v_stocks["Total Cost"]
            
            # Fill NaN in UnitType for display
            v_stocks["UnitType"] = v_stocks["UnitType"].fillna("Units")
            
            st.dataframe(v_stocks[["Item", "Units", "UnitType", "BuyingPrice", "CurrentPrice", "Total Cost", "Potential", "Expected Profit", "UID"]], use_container_width=True, hide_index=True)
            total_cost = v_stocks["Total Cost"].sum()
            total_pot = v_stocks["Potential"].sum()
            st.markdown(f"**Total Investment: {total_cost:,.0f} | Potential: {total_pot:,.0f} | Expected Profit: {total_pot - total_cost:,.0f}**")

            with st.expander("🗑️ Delete Inventory Item"):
                stock_to_delete = st.selectbox("Select Item:", options=v_stocks["UID"].tolist(), format_func=lambda x: f"{v_stocks[v_stocks['UID']==x]['Item'].iloc[0]}", key="del_stock_item")
                if st.button("Delete Item", type="secondary", key="confirm_del_stock"):
                    _, success = data_manager.delete_by_uid(STOCK_FILE, STK_COLS, stock_to_delete)
                    if success:
                        st.success("Item deleted!")
                        st.rerun()
        else:
            st.info("No inventory. Add items using the form above.")

    with tab_trans:
        st.subheader(f"💸 Log Transaction: {selected}")
        with st.form("vtrans_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date = st.date_input("Date", value=datetime.now(), key="vt_date")
                t_type = st.selectbox("Type", ["Income", "Expense"], key="vt_type")
            with col2:
                t_amount = st.number_input("Amount (TZS)", min_value=0, step=500, key="vt_amount")
            t_note = st.text_input("Note", key="vt_note")
            if st.form_submit_button("📝 Log Transaction", type="primary"):
                record = {"Date": str(t_date), "Venture": selected, "Amount": t_amount, "Type": t_type, "Category": "Venture Log", "Note": t_note, "CreatedBy": current_user}
                _, success = data_manager.add_ledger_entry(user_id, record)
                if success:
                    st.success("✅ Transaction logged!")
                    st.rerun()

        v_trans = v_ledger[v_ledger["Type"] != "System"].copy() if not v_ledger.empty else pd.DataFrame()
        if not v_trans.empty:
            v_trans = v_trans.sort_values("Date", ascending=False).head(15)
            st.dataframe(v_trans[["Date", "Type", "Amount", "Note"]], use_container_width=True, hide_index=True)

    # Restock Logic (UPDATED with Pack Logic)
    with tab_restock:
        st.subheader(f"♻️ Restock & Reinvest: {selected}")
        st.info(t('restock_info'))
        
        existing_items = sorted(v_stocks["Item"].dropna().unique().tolist()) if not v_stocks.empty else []
        
        item_options = existing_items + ["-- Add New Item --"]
        default_index = 0
        if "-- Add New Item --" in item_options:
            default_index = len(item_options) - 1
            
        selected_item = st.selectbox(t('restock_item_label'), options=item_options, index=default_index, key="restock_select_outside")
        
        with st.form("restock_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if selected_item == "-- Add New Item --":
                    r_item_name = st.text_input(t('restock_new_item_label'), key="restock_new_name")
                else:
                    r_item_name = selected_item 
                    st.markdown(f"**Item:** {r_item_name}")
                
                # Pack Type (e.g., Carton)
                r_pack_type = st.text_input(t('pack_buying_unit'), placeholder=t('pack_buying_unit_ph'), key="restock_pack_type")
                
                # Pack Size (e.g., 12 pieces)
                r_pack_size = st.number_input(t('pack_size_label'), min_value=1, value=1, step=1, key="restock_pack_size")
                
            with col2:
                # Number of Packs
                r_num_packs = st.number_input("Number of Packs", min_value=1, step=1, key="restock_num_packs")
                
                # Cost per Pack
                r_cost_per_pack = st.number_input(t('pack_cost_label'), min_value=0.0, step=100.0, key="restock_cost_pack")
                
                # Selling Unit Type
                unit_types = [t('unit_pcs'), t('unit_m'), t('unit_box'), t('unit_ctn'), t('unit_kg'), t('unit_other')]
                r_unit_display = st.selectbox(t('unit_type_label'), options=unit_types, key="restock_unit")
                if "Pieces" in r_unit_display: r_unit = "Pcs"
                elif "Meters" in r_unit_display: r_unit = "Meters"
                elif "Boxes" in r_unit_display: r_unit = "Box"
                elif "Cartons" in r_unit_display: r_unit = "Carton"
                elif "Kilograms" in r_unit_display: r_unit = "Kg"
                else: r_unit = r_unit_display

            st.divider()
            
            # Calculations Preview
            total_units_calc = r_num_packs * r_pack_size
            unit_cost_calc = r_cost_per_pack / r_pack_size if r_pack_size > 0 else 0
            total_cost_calc = r_num_packs * r_cost_per_pack
            
            st.markdown(f"**{t('calc_unit_cost')}:** {unit_cost_calc:,.2f} TZS")
            st.markdown(f"**{t('calc_total_units')}:** {total_units_calc} {r_unit}")
            
            r_sell_price = st.number_input(t('restock_sell_price'), min_value=0.0, step=100.0, key="restock_sell")

            submitted = st.form_submit_button(t('btn_restock'), type="primary", use_container_width=True)

            if submitted:
                if not r_item_name:
                    st.error("Item name cannot be empty.")
                elif total_units_calc <= 0:
                    st.error("Total units must be greater than zero.")
                else:
                    # Total Cost Deduction from Cash
                    current_liquid = v_liquid
                    
                    # Balance Check
                    if total_cost_calc > current_liquid:
                        st.error(f"{t('insufficient_funds')} (Need: {total_cost_calc:,.0f}, Have: {current_liquid:,.0f})")
                    else:
                        # Ledger Entry (Cash Outflow -> Asset Inflow)
                        ledger_record = {
                            "Date": str(datetime.now().date()), 
                            "Venture": selected, 
                            "Amount": total_cost_calc, 
                            "Type": "Reinvestment", 
                            "Category": "Inventory Restock", 
                            "Note": f"Restock: {r_num_packs} {r_pack_type} of {r_item_name}", 
                            "CreatedBy": current_user
                        }
                        _, ledger_success = data_manager.add_ledger_entry(user_id, ledger_record)
                        
                        # Inventory Upsert (Now with Pack Logic)
                        if ledger_success:
                            stock_success = data_manager.upsert_stock_entry(
                                user_id, selected, r_item_name, 
                                total_units=total_units_calc, 
                                unit_type=r_unit, 
                                unit_buy_price=unit_cost_calc, 
                                sell_price=r_sell_price, 
                                pack_size=r_pack_size, 
                                pack_type=r_pack_type,
                                created_by=current_user
                            )
                            
                            if stock_success:
                                st.success(t('restock_success').format(item=r_item_name))
                                st.rerun()
                            else:
                                st.error("Failed to update inventory. Please check logs.")
                        else:
                            st.error("Failed to log transaction. Restock cancelled.")

    # NEW TAB: SELL ITEM (AUTOMATED POS)
    with tab_sell:
        st.subheader(f"🛒 {t('sell_title')}")
        st.info(t('sell_info'))
        
        # Get items with stock > 0
        sellable_stock = v_stocks[v_stocks["Units"] > 0].copy() if not v_stocks.empty else pd.DataFrame()
        
        if sellable_stock.empty:
            st.warning(t('sell_no_stock'))
        else:
            # Display current stock nicely
            sellable_stock["Display"] = sellable_stock.apply(lambda x: f"{x['Item']} (Stock: {x['Units']} {x['UnitType']})", axis=1)
            
            with st.form("sell_form", clear_on_submit=True):
                sel_item_uid = st.selectbox(t('sell_select_item'), options=sellable_stock["UID"].tolist(), 
                                            format_func=lambda x: sellable_stock[sellable_stock['UID']==x]['Display'].iloc[0], key="sell_item_select")
                
                selected_row = sellable_stock[sellable_stock["UID"] == sel_item_uid].iloc[0]
                max_qty = int(selected_row["Units"])
                default_price = float(selected_row["CurrentPrice"])
                item_name = selected_row["Item"]
                item_unit = selected_row["UnitType"]
                buying_price = float(selected_row["BuyingPrice"])
                
                col1, col2 = st.columns(2)
                with col1:
                    s_qty = st.number_input(t('sell_qty'), min_value=1, max_value=max_qty, value=1, step=1, key="sell_qty")
                with col2:
                    s_price = st.number_input(t('sell_price'), value=default_price, min_value=0.0, step=100.0, key="sell_price")
                
                submitted = st.form_submit_button(t('btn_sell'), type="primary", use_container_width=True)
                
                if submitted:
                    if s_qty > max_qty:
                        st.error(t('sell_insufficient_stock').format(stock=max_qty, unit=item_unit))
                    else:
                        # CALCULATIONS
                        total_sale_value = s_qty * s_price
                        cost_of_goods = s_qty * buying_price
                        profit_on_sale = total_sale_value - cost_of_goods
                        
                        # 1. Reduce Stock
                        success, _ = data_manager.reduce_stock_entry(user_id, selected, item_name, s_qty)
                        
                        if success:
                            # 2. Log Income (Total Sale Value)
                            # Note: This increases Net Worth by `total_sale_value`
                            # But Inventory Capital decreases by `cost_of_goods`.
                            # Net Worth change = total_sale_value - cost_of_goods = profit_on_sale.
                            
                            ledger_record = {
                                "Date": str(datetime.now().date()),
                                "Venture": selected,
                                "Amount": total_sale_value,
                                "Type": "Income",
                                "Category": "Item Sale",
                                "Note": f"Sold {s_qty} {item_unit} of {item_name}",
                                "CreatedBy": current_user
                            }
                            _, ledger_success = data_manager.add_ledger_entry(user_id, ledger_record)
                            
                            if ledger_success:
                                st.success(t('sell_success').format(qty=s_qty, unit=item_unit, item=item_name))
                                st.metric("Realized Profit", f"{profit_on_sale:,.0f} TZS")
                                st.caption(f"Sale Value: {total_sale_value:,.0f} TZS | Cost: {cost_of_goods:,.0f} TZS")
                                st.rerun()
                            else:
                                st.error("Failed to log transaction.")
                        else:
                            st.error("Stock update failed.")

    with tab_intel:
        st.subheader(f"📈 Analytics: {selected}")
        
        # Real Business Logic Analytics
        profit_margin = (v_liquid / v_income * 100) if v_income > 0 else 0
        
        # ROI Logic
        total_invested_capital = v_inv_capital
        total_return = v_liquid + v_inv_potential
        roi = ((total_return - total_invested_capital) / total_invested_capital * 100) if total_invested_capital > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Net Cash", f"{v_liquid:,.0f} TZS")
        col2.metric("📊 Profit Margin", f"{profit_margin:.1f}%")
        col3.metric("📈 ROI", f"{roi:.1f}%")

    with tab_delete:
        st.subheader("⚠️ Danger Zone")
        st.markdown("<div class='danger-zone'>", unsafe_allow_html=True)
        st.warning(f"⚠️ You are about to DELETE the entire venture: **{selected}**")
        st.error("This will permanently delete:")
        st.markdown(f"- All transactions for **{selected}**\n- All inventory items for **{selected}**\n- All related data")
        st.markdown("**This action CANNOT be undone!**")
        confirm_text = st.text_input("Type venture name to confirm deletion:", key="del_venture_confirm")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🗑️ DELETE ENTIRE VENTURE: {selected}", type="primary", disabled=(confirm_text != selected), key="delete_venture_btn"):
                if data_manager.delete_venture_completely(user_id, selected):
                    st.success("✅ Venture has been completely deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete venture.")
        with col2:
            if st.button("❌ Cancel", type="secondary", key="cancel_delete_venture"):
                st.info("Deletion cancelled.")
        st.markdown("</div>", unsafe_allow_html=True)


def show_portfolio_vault(user_id, current_user):
    st.header("💰 Portfolio Vault")
    st.info("Manage shares and assets.")

    with st.form("portfolio_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            p_asset = st.text_input("Asset Name", key="p_asset")
            p_ticker = st.text_input("Ticker", key="p_ticker")
            p_units = st.number_input("Units", min_value=0.0, step=1.0, key="p_units")
        with col2:
            p_buy = st.number_input("Buy Price", min_value=0.0, step=100.0, key="p_buy")
            p_curr = st.number_input("Current Price", min_value=0.0, step=100.0, key="p_curr")
        if st.form_submit_button("➕ Add to Vault", type="primary", use_container_width=True):
            if p_asset and p_ticker and p_units > 0:
                record = {"Date": str(datetime.now().date()), "Asset": p_asset, "Ticker": p_ticker.upper(), "Units": p_units, "BuyPrice": p_buy, "CurrentPrice": p_curr, "CreatedBy": current_user}
                _, success = data_manager.add_portfolio_entry(user_id, record)
                if success:
                    st.success(f"✅ {p_ticker.upper()} added!")
                    st.rerun()

    st.divider()
    df_portfolio = data_manager.get_user_portfolio(user_id)
    if not df_portfolio.empty:
        df_portfolio["Invested"] = df_portfolio["Units"] * df_portfolio["BuyPrice"]
        df_portfolio["Value"] = df_portfolio["Units"] * df_portfolio["CurrentPrice"]
        df_portfolio["P/L"] = df_portfolio["Value"] - df_portfolio["Invested"]
        df_portfolio["P/L %"] = (df_portfolio["P/L"] / df_portfolio["Invested"] * 100).round(1)
        st.dataframe(df_portfolio[["Asset", "Ticker", "Units", "BuyPrice", "CurrentPrice", "Invested", "Value", "P/L", "P/L %", "UID"]], use_container_width=True, hide_index=True)
        total_inv = df_portfolio["Invested"].sum()
        total_val = df_portfolio["Value"].sum()
        total_pl = df_portfolio["P/L"].sum()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invested", f"{total_inv:,.0f} TZS")
        col2.metric("Current Value", f"{total_val:,.0f} TZS")
        col3.metric("Total P/L", f"{total_pl:,.0f} TZS", delta=f"{total_pl:,.0f}")

        with st.expander("🗑️ Remove Asset"):
            asset_to_delete = st.selectbox("Select Asset:", options=df_portfolio["UID"].tolist(), format_func=lambda x: f"{df_portfolio[df_portfolio['UID']==x]['Ticker'].iloc[0]} - {df_portfolio[df_portfolio['UID']==x]['Asset'].iloc[0]}", key="del_port_asset")
            if st.button("Remove Asset", type="secondary", key="confirm_del_port"):
                _, success = data_manager.delete_by_uid(PORTFOLIO_FILE, PORT_COLS, asset_to_delete)
                if success:
                    st.success("Asset removed!")
                    st.rerun()
    else:
        st.info("Vault Empty. Add assets above.")


def show_settings(user_id, current_role):
    st.header("⚙️ Settings")
    tab1, tab2 = st.tabs(["🔒 Account", "💾 Data"])

    with tab1:
        st.subheader("Profile")
        user = data_manager.get_user_by_id(user_id)
        if user is not None:
            st.info(f"**Username:** {user['Username']}")
            st.info(f"**Email:** {user['Email']}")
            st.info(f"**Role:** {user['Role']}")
        st.divider()
        st.write("Language Settings:")
        render_language_switcher("settings_page")

    with tab2:
        st.subheader("Data Management")
        df_ledger = data_manager.get_user_ledger(user_id)
        df_stocks = data_manager.get_user_stocks(user_id)
        df_portfolio = data_manager.get_user_portfolio(user_id)
        st.success(f"✔️ Ledger: {len(df_ledger)} records")
        st.success(f"✔️ Stocks: {len(df_stocks)} records")
        st.success(f"✔️ Portfolio: {len(df_portfolio)} records")

        st.divider()
        if not df_ledger.empty:
            csv = df_ledger.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Ledger Backup", data=csv, file_name="ledger_backup.csv", mime="text/csv", use_container_width=True)

        with st.expander("🔥 Factory Reset"):
            confirm = st.text_input("Type 'CONFIRM' to delete all data:", key="reset_confirm")
            if st.button("DELETE ALL DATA", type="primary", disabled=(confirm != "CONFIRM"), key="reset_btn"):
                df_ledger_full = data_manager.load_data(DB_FILE, DB_COLS)
                df_ledger_full = df_ledger_full[df_ledger_full["OrgID"] != user_id]
                data_manager.save_data(df_ledger_full.reset_index(drop=True), DB_FILE)
                df_stocks_full = data_manager.load_data(STOCK_FILE, STK_COLS)
                df_stocks_full = df_stocks_full[df_stocks_full["OrgID"] != user_id]
                data_manager.save_data(df_stocks_full.reset_index(drop=True), STOCK_FILE)
                df_portfolio_full = data_manager.load_data(PORTFOLIO_FILE, PORT_COLS)
                df_portfolio_full = df_portfolio_full[df_portfolio_full["OrgID"] != user_id]
                data_manager.save_data(df_portfolio_full.reset_index(drop=True), PORTFOLIO_FILE)
                st.success("All data deleted.")
                st.rerun()


# ================================================================================
# MAIN ROUTER
# ================================================================================
def main():
    if st.session_state.authenticated:
        show_dashboard()
    elif st.session_state.page == "signup":
        show_registration()
    elif st.session_state.page == "login":
        show_login()
    elif st.session_state.page == "forgot":
        show_forgot_password()
    elif st.session_state.page == "help":
        show_help_support()
    else:
        show_landing()


if __name__ == "__main__":
    main()