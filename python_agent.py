import tkinter as tk
from tkinter import messagebox
import requests
import xml.etree.ElementTree as ET
import json
import os
import logging
import re

# ---------------- CONFIG ----------------

CONFIG_PATH = "config.json"
AUTH_TOKEN = None

# DEFAULT_CONFIG = {
#     "tally_url": "http://localhost:9000",
#     "django_api_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/ledgers/",
#     "django_url_vendors": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/vendors/",
#     "auth_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/generate_token/"  # Django token endpoint
# }

DEFAULT_CONFIG = {
    "tally_url": "http://localhost:9000",
    "django_api_url": "http://127.0.0.1:8000/api/users/ledgers/",
    "django_url_vendors": "http://127.0.0.1:8000/api/users/vendors/",
    "auth_url": "http://127.0.0.1:8000/api/generate_token/"  # Django token endpoint
}

# ---------------- LOGGING ----------------

logging.basicConfig(
    filename='sync_gui.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# ---------------- CONFIG LOADER ----------------

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    else:
        with open(CONFIG_PATH, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        return DEFAULT_CONFIG

config = load_config()
TALLY_URL = config["tally_url"]
# DJANGO_API_URL = config["django_api_url"]
AUTH_URL = config["auth_url"]
DJANGO_API_URL_CUSTOMERS =config["django_api_url"]
DJANGO_API_URL_VENDORS =config["django_url_vendors"]

# ---------------- TOKEN HANDLER ----------------

def get_token(username, password):
    global AUTH_TOKEN
    try:
        response = requests.post(AUTH_URL, data={"username": username, "password": password})
        response.raise_for_status()
        token_data = response.json()
        AUTH_TOKEN = token_data.get("token")
        return True if AUTH_TOKEN else False
    except requests.exceptions.RequestException as e:
        logging.error(f"Login failed: {e}")
        return False

# ---------------- TALLY REQUEST ----------------

TALLY_REQUEST_XML_CUSTOMERS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Customer Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Customer Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsSundryDebtor</FILTER>
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE</FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsSundryDebtor">
             $Parent = "Sundry Debtors"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_VENDORS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Vendor Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Vendor Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsSundryCreditor</FILTER>
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE</FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsSundryCreditor">
             $Parent = "Sundry Creditors"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_COA = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>All Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="All Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FETCH>NAME, PARENT</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

TALLY_REQUEST_XML_ITEMS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Stock Items</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Stock Items" ISMODIFY="No">
            <TYPE>StockItem</TYPE>
            <FETCH>NAME, RATE, DESCRIPTION, PARTNUMBER, PARENT</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

# TALLY_TO_ZOHO_ACCOUNT_TYPE = {
#     "Bank Accounts": "Bank",
#     "Bank OCC A/c": "Bank",
#     "Bank OD A/c": "Loan",
#     "Branch / Divisions": "Other Current Asset",
#     "Capital Account": "Equity",
#     "Cash-in-Hand": "Cash and Cash Equivalents",
#     "Current Assets": "Other Current Asset",
#     "Current Liabilities": "Current Liability",
#     "Deposits (Asset)": "Deposits",
#     "Direct Expenses": "Cost of Goods Sold (COGS)",
#     "Direct Incomes": "Revenue",
#     "Duties & Taxes": "Tax Payable",
#     "Expenses (Direct)": "Cost of Goods Sold (COGS)",
#     "Expenses (Indirect)": "Other Expense",
#     "Fixed Assets": "Fixed Asset",
#     "Income (Direct)": "Revenue",
#     "Income (Indirect)": "Other Income",
#     "Indirect Expenses": "Other Expense",
#     "Indirect Incomes": "Other Income",
#     "Investments": "Investments",
#     "Loans & Advances (Asset)": "Other Current Asset",
#     "Loans (Liability)": "Loan",
#     "Misc. Expenses (ASSET)": "Prepaid Expense",
#     "Provisions": "Other Current Liability",
#     "Purchase Accounts": "Cost of Goods Sold",
#     "Reserves & Surplus": "Equity",
#     "Retained Earnings": "Retained Earnings",
#     "Sales Accounts": "Revenue",
#     "Secured Loans": "Loan",
#     "Stock-in-Hand": "Inventory Asset",
#     "Sundry Creditors": "Accounts Payable",
#     "Sundry Debtors": "Accounts Receivable",
#     "Suspense A/c": "Suspense Account",
#     "Unsecured Loans": "Loan",
# }
TALLY_TO_ZOHO_ACCOUNT_TYPE = {
    "Bank Accounts": "bank", ##Bank
    "Bank OCC A/c": "bank",  ##Bank
    "Bank OD A/c": "bank",   ##N
    "Branch / Divisions": "other_liability",  
    "Capital Account": "equity",
    "Cash-in-Hand": "cash",
    "Current Assets": "other_current_asset", 
    "Current Liabilities": "other_current_liability",
    "Deposits (Asset)": "other_current_asset",
    "Direct Expenses": "expense",
    "Direct Incomes": "income",
    "Duties & Taxes": "other_current_asset",  #other current asset
    "Expenses (Direct)": "expense",
    "Expenses (Indirect)": "other_expense",
    "Fixed Assets": "fixed_asset",
    "Income (Direct)": "income",
    "Income (Indirect)": "other_income",
    "Indirect Expenses": "other_expense",
    "Indirect Incomes": "other_income",
    "Investments": "other_current_asset",  #other_current_asset
    "Loans & Advances (Asset)": "other_current_asset", ##Doubt
    "Loans (Liability)": "long_term_liability", ##doubt me
    "Misc. Expenses (ASSET)": "other_asset",
    "Provisions": "other_current_liability",
    "Purchase Accounts": "cost_of_goods_sold",
    "Reserves & Surplus": "equity",
    "Retained Earnings": "income", 
    "Sales Accounts": "income",
    "Secured Loans": "other_liability", 
    "Stock-in-Hand": "cost_of_goods_sold", # --
    "Sundry Creditors": "accounts_payable",
    "Sundry Debtors": "accounts_receivable",
    "Suspense A/c": "other_liability",
    "Unsecured Loans": "loans_and_borrowing", #--
}
# ---------------- XML PARSER ----------------

def clean_xml(xml_string):
    xml_string = re.sub(r'&#\d+;', '', xml_string)  # Remove numeric character references
    xml_string = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', xml_string)  # Remove control chars
    return xml_string


def parse_ledgers(xml_data, ledger_type="customer"):
    ledgers = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            name_elem = ledger.find(".//NAME")
            parent = ledger.findtext("PARENT", default="")
            email = ledger.findtext("EMAIL", default="")
            website = ledger.findtext("WEBSITE", default="")
            ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
            state_name = ledger.findtext("LEDSTATENAME", default="")
            country_name = ledger.findtext("COUNTRYNAME", default="")
            pincode = ledger.findtext("PINCODE", default="")

            address_elems = ledger.findall(".//ADDRESS")
            address_lines = [elem.text.strip() for elem in address_elems if elem.text]
            address = ", ".join(address_lines)

            if ledger_type == "customer" and parent.strip().lower() == "sundry debtors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent,
                    "email": email,
                    "address": address,
                    "ledger_mobile": ledger_mobile,
                    "website": website,
                    "state_name": state_name,
                    "country_name": country_name,
                    "pincode": pincode
                })
            elif ledger_type == "vendor" and parent.strip().lower() == "sundry creditors":
                ledgers.append({
                    "name": name_elem.text if name_elem is not None else "Unknown",
                    "parent": parent,
                    "email": email,
                    "address": address,
                    "ledger_mobile": ledger_mobile,
                    "website": website,
                    "state_name": state_name,
                    "country_name": country_name,
                    "pincode": pincode
                })

        return ledgers

    except ET.ParseError as e:
        logging.error(f"XML Parse Error: {e}")
        with open("last_raw_tally.xml", "w", encoding="utf-8") as file:
            file.write(xml_data)
        raise Exception("Failed to parse Tally XML response.")

def parse_coa_ledgers(xml_data):
    accounts = []
    try:
        xml_data = clean_xml(xml_data)
        print(xml_data)
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="Unknown")
            account_type = TALLY_TO_ZOHO_ACCOUNT_TYPE.get(parent)

            accounts.append({
                "account_name": name,
                "account_code": name,  # assuming Tally name is code for now
                "account_type": account_type,
            })

        return accounts

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (COA): {e}")
        raise Exception("Failed to parse COA XML from Tally.")
    
def parse_items(xml_data):
    items = []
    try:
        xml_data = clean_xml(xml_data)
        print("Cleaned XML:\n", xml_data)

        root = ET.fromstring(xml_data)
        print("Root tag:", root.tag)

        for item in root.findall(".//STOCKITEM"):
            name = item.findtext(".//NAME", default="Unknown")
            rate = item.findtext("RATE", default="0")
            description = item.findtext("DESCRIPTION", default="")
            sku = item.findtext("PARTNUMBER", default="")
            product_type = item.findtext("PARENT", default="General")

            items.append({
                "name": name,
                "rate": rate,
                "description": description,
                "sku": sku,
                "product_type": product_type,
                "account_id": None  # Link it later if applicable
            })

        return items

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (Items): {e}")
        raise Exception("Failed to parse item XML from Tally.")


# ---------------- TALLY SYNC ----------------

def get_tally_data(tally_request_xml):
    try:
        response = requests.post(TALLY_URL, data=tally_request_xml)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Tally connection failed: {e}")
        raise Exception("Could not connect to Tally. Is it running and listening on port 9000?")

def send_customers_to_django(customers):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(DJANGO_API_URL_CUSTOMERS, json={"ledgers": customers}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending customers to Django: {e}")
        raise Exception("Failed to send customers data to server.")

def send_vendors_to_django(vendors):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(DJANGO_API_URL_VENDORS, json={"ledgers": vendors}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending vendors to Django: {e}")
        raise Exception("Failed to send vendors data to server.")

def send_coa_to_django(accounts):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post("http://127.0.0.1:8000/api/users/accounts/", json={"accounts": accounts}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending COA to Django: {e}")
        raise Exception("Failed to send COA data to server.")
    
def send_items_to_django(items):
    try:
        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post("http://127.0.0.1:8000/api/users/items/", json={"items": items}, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending items to Django: {e}")
        raise Exception("Failed to send items to server.")


# ---------------- GUI LOGIC ----------------

def sync_data():
    try:
        status_label.config(text="Connecting to Tally...", fg="blue")
        root.update()

        # Fetch customers
        xml_customers = get_tally_data(TALLY_REQUEST_XML_CUSTOMERS)
        customers = parse_ledgers(xml_customers, ledger_type="customer")

        # Fetch vendors
        xml_vendors = get_tally_data(TALLY_REQUEST_XML_VENDORS)
        vendors = parse_ledgers(xml_vendors, ledger_type="vendor")

        # Chart of Accounts
        xml_coa = get_tally_data(TALLY_REQUEST_XML_COA)
        accounts = parse_coa_ledgers(xml_coa)

        # Items
        xml_items = get_tally_data(TALLY_REQUEST_XML_ITEMS)
        items = parse_items(xml_items)

        if items:
            send_items_to_django(items)


        if not customers and not vendors:
            messagebox.showwarning("No Data", "No customers or vendors found in Tally.")
            status_label.config(text="No ledgers found.", fg="orange")
            return

        if customers:
            send_customers_to_django(customers)
        if vendors:
            send_vendors_to_django(vendors)
        if accounts:
            send_coa_to_django(accounts)
        if items:
            send_items_to_django(items)

        messagebox.showinfo("Success", "Customers and Vendors synced successfully!")
        status_label.config(text="✅ Sync complete!", fg="green")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text=f"❌ {str(e)}", fg="red")


# ---------------- GUI SETUP ----------------

root = tk.Tk()
root.title("Tally to Django Sync Agent")
root.geometry("400x260")
root.resizable(False, False)

title_label = tk.Label(root, text="Tally → Django Sync", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

username_var = tk.StringVar()
password_var = tk.StringVar()

tk.Label(root, text="Username").pack()
tk.Entry(root, textvariable=username_var).pack()

tk.Label(root, text="Password").pack()
tk.Entry(root, textvariable=password_var, show="*").pack()

def login_and_sync():
    username = username_var.get()
    password = password_var.get()

    if not username or not password:
        messagebox.showwarning("Missing Fields", "Username and password are required.")
        return

    if not get_token(username, password):
        messagebox.showerror("Login Failed", "Invalid credentials or server error.")
        return

    sync_data()

sync_btn = tk.Button(root, text="Login & Sync", command=login_and_sync, font=("Arial", 12), bg="green", fg="white")
sync_btn.pack(pady=20)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

footer = tk.Label(root, text="v1.0 - Developed by Your Company", font=("Arial", 8), fg="gray")
footer.pack(side="bottom", pady=5)

root.mainloop()




# Installers :

# pip install requests
# pip install pyinstaller
# pyinstaller --onefile --windowed python_agent.py
