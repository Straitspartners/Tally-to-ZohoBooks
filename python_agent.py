import tkinter as tk
from tkinter import messagebox
import requests
import xml.etree.ElementTree as ET
import json
import os
import logging
import re
from tkcalendar import DateEntry

# ---------------- CONFIG ----------------

CONFIG_PATH = "config.json"
AUTH_TOKEN = None

# DEFAULT_CONFIG = {
#     "tally_url": "http://localhost:9000",
#     "django_api_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/ledgers/",
#     "django_url_vendors": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/vendors/",
#     "auth_url": "https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/generate_token_agent/"  # Django token endpoint
# }

DEFAULT_CONFIG = {
    "tally_url": "http://localhost:9000",
    "django_api_url": "http://127.0.0.1:8000/api/users/ledgers/",
    "django_url_vendors": "http://127.0.0.1:8000/api/users/vendors/",
    "auth_url": "http://127.0.0.1:8000/api/generate_token_agent/"  # Django token endpoint
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
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE , GSTIN, GSTREGISTRATIONTYPE , OPENINGBALANCE</FETCH>
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
            <FETCH>NAME, PARENT, EMAIL ,ADDRESS , LEDGERMOBILE, WEBSITE , LEDSTATENAME ,COUNTRYNAME , PINCODE , OPENINGBALANCE </FETCH>
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
            <FETCH>NAME, PARENT , OPENINGBALANCE </FETCH>
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
            <FETCH>NAME, RATE, DESCRIPTION, PARTNUMBER, PARENT, GSTAPPLICABLE, GSTDETAILS.RATE, GSTDETAILS.HSN</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""

# TALLY_REQUEST_XML_SALES_VOUCHERS = """
# <ENVELOPE>
#   <HEADER>
#     <VERSION>1</VERSION>
#     <TALLYREQUEST>Export</TALLYREQUEST>
#     <TYPE>Collection</TYPE>
#     <ID>Sales Vouchers</ID>
#   </HEADER>
#   <BODY>
#     <DESC>
#       <STATICVARIABLES>
#         <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
#         <EXPLODEFLAG>Yes</EXPLODEFLAG>
#         <SVFROMDATE>20240101</SVFROMDATE>
#         <SVTODATE>20251231</SVTODATE>
#       </STATICVARIABLES>
#       <TDL>
#         <TDLMESSAGE>
#           <COLLECTION NAME="Sales Vouchers" ISMODIFY="No">
#             <TYPE>Voucher</TYPE>
#             <FILTER>IsSales</FILTER>
#             <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST</FETCH>
#           </COLLECTION>
#           <SYSTEM TYPE="Formulae" NAME="IsSales">
#             $VoucherTypeName = "Sales"
#           </SYSTEM>
#         </TDLMESSAGE>
#       </TDL>
#     </DESC>
#   </BODY>
# </ENVELOPE>
# """

# TALLY_REQUEST_XML_RECEIPTS = """
# <ENVELOPE>
#   <HEADER>
#     <VERSION>1</VERSION>
#     <TALLYREQUEST>Export</TALLYREQUEST>
#     <TYPE>Collection</TYPE>
#     <ID>Receipt Vouchers</ID>
#   </HEADER>
#   <BODY>
#     <DESC>
#       <STATICVARIABLES>
#         <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
#         <EXPLODEFLAG>Yes</EXPLODEFLAG>
#         <SVFROMDATE>20240101</SVFROMDATE>
#         <SVTODATE>20251231</SVTODATE>
#       </STATICVARIABLES>
#       <TDL>
#         <TDLMESSAGE>
#           <COLLECTION NAME="Receipt Vouchers" ISMODIFY="No">
#             <TYPE>Voucher</TYPE>
#             <FILTER>IsReceipt</FILTER>
#             <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
#           </COLLECTION>
#           <SYSTEM TYPE="Formulae" NAME="IsReceipt">
#             $VoucherTypeName = "Receipt"
#           </SYSTEM>
#         </TDLMESSAGE>
#       </TDL>
#     </DESC>
#   </BODY>
# </ENVELOPE>
# """

def get_sales_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Sales Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>20250401</SVFROMDATE>
            <SVTODATE>20260331</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Sales Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsSales</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsSales">
                $VoucherTypeName = "Sales "
              </SYSTEM>
              <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "20250401" AND $$Date <= DATE "20260331"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """

def get_receipt_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Receipt Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Receipt Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsReceipt</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsReceipt">
                $VoucherTypeName = "Receipt"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
def get_payment_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Payment Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Payment Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsPayment</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsPayment">
                $VoucherTypeName = "Payment"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
def parse_payments(xml_data):
    payments = []
    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)
    
    for voucher in root.findall(".//VOUCHER"):
        payment_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()
        try:
            payment_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            payment_date = date_str

        total_amount = 0.0
        vendor_name = "Unknown"
        payment_mode = "Unknown"
        cur_balance = None
        ref_name = None

        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            amt_str = ledger.findtext("AMOUNT", default="0.0").strip()

            try:
                amt = float(amt_str)
            except:
                amt = 0.0

            if "bank" in ledger_name.lower() or "cash" in ledger_name.lower():
                payment_mode = ledger_name
            else:
                vendor_name = ledger_name
                total_amount = abs(amt)  # Make positive

                balance_tags = ["CURRENTBALANCE", "LEDGERCLOSINGBALANCE"]
                for tag in balance_tags:
                    balance_str = ledger.findtext(tag)
                    if balance_str:
                        try:
                            cur_balance = float(balance_str)
                            break
                        except:
                            continue

                bill_alloc = ledger.find(".//BILLALLOCATIONS.LIST")
                if bill_alloc is not None:
                    ref_name = bill_alloc.findtext("NAME", default=None)

        payments.append({
            "payment_number": payment_number,
            "vendor_name": vendor_name,
            "payment_date": payment_date,
            "amount": f"{total_amount:.2f}",
            "payment_mode": payment_mode,
            "cur_balance": f"{cur_balance:.2f}" if cur_balance is not None else None,
            "agst_ref_name": ref_name
        })

    return payments

def send_payments_to_django(payments):
    try:
        valid_payments = []
        for payment in payments:
            if (
                payment.get("vendor_name") not in [None, "", "Unknown"]
                and payment.get("payment_number") not in [None, "", "Unknown"]
                and payment.get("payment_date")
            ):
                valid_payments.append(payment)
            else:
                print(f"⚠️ Skipping invalid payment: {payment}")

        if not valid_payments:
            raise Exception("No valid payments to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/payments/",
            json={"payments": valid_payments},
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending payments to Django: {e}")
        raise

def get_expenses_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Payment Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Payment Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsPayment</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.CURRENTBALANCE , LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsPayment">
                $VoucherTypeName = "Payment"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
def parse_expenses(xml_data):
    payments = []
    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)
    
    for voucher in root.findall(".//VOUCHER"):
        payment_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()
        try:
            payment_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            payment_date = date_str

        total_amount = 0.0
        vendor_name = "Unknown"
        payment_mode = "Unknown"
        cur_balance = None
        ref_name = None

        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            amt_str = ledger.findtext("AMOUNT", default="0.0").strip()

            try:
                amt = float(amt_str)
            except:
                amt = 0.0

            if "bank" in ledger_name.lower() or "cash" in ledger_name.lower():
                payment_mode = ledger_name
            else:
                vendor_name = ledger_name
                total_amount = abs(amt)  # Make positive

                balance_tags = ["CURRENTBALANCE", "LEDGERCLOSINGBALANCE"]
                for tag in balance_tags:
                    balance_str = ledger.findtext(tag)
                    if balance_str:
                        try:
                            cur_balance = float(balance_str)
                            break
                        except:
                            continue

                bill_alloc = ledger.find(".//BILLALLOCATIONS.LIST")
                if bill_alloc is not None:
                    ref_name = bill_alloc.findtext("NAME", default=None)

        payments.append({
            "payment_number": payment_number,
            "vendor_name": vendor_name,
            "payment_date": payment_date,
            "amount": f"{total_amount:.2f}",
            "payment_mode": payment_mode,
            "cur_balance": f"{cur_balance:.2f}" if cur_balance is not None else None,
            "agst_ref_name": ref_name
        })

    return payments

def send_expenses_to_django(payments):
    try:
        valid_payments = []
        for payment in payments:
            if (
                payment.get("vendor_name") not in [None, "", "Unknown"]
                and payment.get("payment_number") not in [None, "", "Unknown"]
                and payment.get("payment_date")
            ):
                valid_payments.append(payment)
            else:
                print(f"⚠️ Skipping invalid payment: {payment}")

        if not valid_payments:
            raise Exception("No valid payments to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/expenses/",
            json={"payments": valid_payments},
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending payments to Django: {e}")
        raise

def get_journal_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Journal Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Journal Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsJournal</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, NARRATION, LEDGERENTRIES.LIST, LEDGERENTRIES.LIST.AMOUNT, LEDGERENTRIES.LIST.LEDGERNAME, LEDGERENTRIES.LIST.ISDEEMEDPOSITIVE, LEDGERENTRIES.LIST.COSTCENTRENAME, LEDGERENTRIES.LIST.BILLALLOCATIONS.LIST.NAME</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsJournal">
                $VoucherTypeName = "Journal"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
def parse_journals(xml_data):
    journals = []
    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        voucher_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()
        narration = voucher.findtext("NARRATION", default="").strip()

        try:
            journal_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            journal_date = date_str

        ledger_entries = []
        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            amount_str = ledger.findtext("AMOUNT", default="0.0").strip()
            is_deemed_positive = ledger.findtext("ISDEEMEDPOSITIVE", default="Yes").strip()
            cost_centre = ledger.findtext("COSTCENTRENAME", default=None)
            ref_name = None

            try:
                amount = float(amount_str)
            except:
                amount = 0.0

            bill_alloc = ledger.find(".//BILLALLOCATIONS.LIST")
            if bill_alloc is not None:
                ref_name = bill_alloc.findtext("NAME", default=None)

            ledger_entries.append({
                "ledger_name": ledger_name,
                "amount": abs(amount),
                "type": "Credit" if is_deemed_positive == "Yes" else "Debit",
                "cost_centre": cost_centre,
                "ref_name": ref_name
            })

        journals.append({
            "voucher_number": voucher_number,
            "journal_date": journal_date,
            "narration": narration,
            "entries": ledger_entries
        })

    return journals
def send_journals_to_django(journals):
    try:
        valid_journals = [j for j in journals if j.get("voucher_number") and j.get("entries")]

        if not valid_journals:
            raise Exception("No valid journal vouchers to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/journals/",
            json={"journals": valid_journals},
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending journals to Django: {e}")
        raise

def get_credit_note_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Credit Notes</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Credit Notes" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsCreditNote</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST ,BILLALLOCATIONS.LIST</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsCreditNote">
                $VoucherTypeName = "Credit Note"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """

# def parse_credit_or_debit_vouchers(xml_data, voucher_type='credit'):
#     invoices = defaultdict(lambda: {
#         "customer_name": "",
#         "note_number": "",
#         "note_date": "",
#         "items": [],
#         "cgst": 0.0,
#         "sgst": 0.0,
#         "total_amount": 0.0,
#         "type": voucher_type
#     })

#     xml_data = clean_xml(xml_data)
#     print(xml_data)
#     root = ET.fromstring(xml_data)

#     for voucher in root.findall(".//VOUCHER"):
#         inv_no = voucher.findtext("VOUCHERNUMBER", default="Unknown")
#         ledger_entry = voucher.find(".//LEDGERENTRIES.LIST")
#         customer = ledger_entry.findtext(".//LEDGERNAME", default="Unknown") if ledger_entry is not None else "Unknown"
#         date_raw = voucher.findtext("DATE", default="")
#         date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw

#         key = (inv_no, customer, date)

#         invoice = invoices[key]
#         invoice["customer_name"] = customer
#         invoice["note_number"] = inv_no
#         invoice["note_date"] = date

#         for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
#             item_name = item.findtext("STOCKITEMNAME", default="")
#             qty = item.findtext("ACTUALQTY", default="")
#             amt = float(item.findtext("AMOUNT", default="0.0"))
#             amt_abs = abs(amt)

#             invoice["items"].append({
#                 "item_name": item_name,
#                 "quantity": qty.strip(),
#                 "amount": f"{amt_abs:.2f}"
#             })
#             invoice["total_amount"] += amt_abs

#         for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
#             ledger_name = ledger.findtext("LEDGERNAME", "").lower()
#             amt_abs = float(ledger.findtext("AMOUNT", default="0.0"))

#             if "cgst" in ledger_name:
#                 invoice["cgst"] += abs(amt_abs)
#             elif "sgst" in ledger_name:
#                 invoice["sgst"] += abs(amt_abs)

#             bill_allocation = ledger.find(".//BILLALLOCATIONS.LIST")
#             if bill_allocation is not None:
#                 against_ref = bill_allocation.findtext("NAME", default="")  # This is often the reference number
#             if against_ref:
#                 invoice["against_ref"] = against_ref
#     return [
#         {
#             **inv,
#             "cgst": f"{inv['cgst']:.2f}",
#             "sgst": f"{inv['sgst']:.2f}",
#             "total_amount": f"{(inv['total_amount'] + inv['cgst'] + inv['sgst']):.2f}",
#             "against_ref": inv.get("against_ref", "")
#         }
#         for inv in invoices.values()
#     ]
import xml.etree.ElementTree as ET
from collections import defaultdict

def clean_xml(xml_str):
    return xml_str.replace('&', '&amp;')  # minimal XML sanitizer

def parse_credit_or_debit_vouchers(xml_data, voucher_type='credit'):
    invoices = defaultdict(lambda: {
        "customer_name": "",
        "note_number": "",
        "note_date": "",
        "items": [],
        "cgst": 0.0,
        "sgst": 0.0,
        "total_amount": 0.0,
        "type": voucher_type,
        "ledger_type": "",
        "against_ref": ""
    })

    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        inv_no = voucher.findtext("VOUCHERNUMBER", default="Unknown")
        ledger_entry = voucher.find(".//LEDGERENTRIES.LIST")
        customer = ledger_entry.findtext(".//LEDGERNAME", default="Unknown") if ledger_entry is not None else "Unknown"
        date_raw = voucher.findtext("DATE", default="")
        date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw

        key = (inv_no, customer, date)

        invoice = invoices[key]
        invoice["customer_name"] = customer
        invoice["note_number"] = inv_no
        invoice["note_date"] = date

        # Get ledger type from ACCOUNTINGALLOCATIONS.LIST
        acc_alloc = voucher.find(".//ACCOUNTINGALLOCATIONS.LIST")
        if acc_alloc is not None:
            ledger_name = acc_alloc.findtext("LEDGERNAME", default="").strip()
            if ledger_name:
                invoice["ledger_type"] = ledger_name  # only one ledger_type as requested

        # Handle inventory entries
        for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
            item_name = item.findtext("STOCKITEMNAME", default="")
            qty = item.findtext("ACTUALQTY", default="")
            amt = float(item.findtext("AMOUNT", default="0.0"))
            amt_abs = abs(amt)

            invoice["items"].append({
                "item_name": item_name,
                "quantity": qty.strip(),
                "amount": f"{amt_abs:.2f}"
            })
            invoice["total_amount"] += amt_abs

        # Handle taxes and reference
        for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
            ledger_name_lower = ledger.findtext("LEDGERNAME", "").lower()
            amt = float(ledger.findtext("AMOUNT", default="0.0"))

            if "cgst" in ledger_name_lower:
                invoice["cgst"] += abs(amt)
            elif "sgst" in ledger_name_lower:
                invoice["sgst"] += abs(amt)

            bill_allocation = ledger.find(".//BILLALLOCATIONS.LIST")
            if bill_allocation is not None:
                against_ref = bill_allocation.findtext("NAME", default="")
                if against_ref:
                    invoice["against_ref"] = against_ref

    return [
        {
            **inv,
            "cgst": f"{inv['cgst']:.2f}",
            "sgst": f"{inv['sgst']:.2f}",
            "total_amount": f"{(inv['total_amount'] + inv['cgst'] + inv['sgst']):.2f}",
        }
        for inv in invoices.values()
    ]

def send_credit_notes_to_django(invoices):
    try:
        valid_notes = []
        for inv in invoices:
            if (
                inv.get("customer_name") not in [None, "", "Unknown"]
                and inv.get("note_number") not in [None, "", "Unknown"]
                and inv.get("note_date")
                and inv.get("items") and isinstance(inv.get("items"), list)
            ):
                valid_notes.append(inv)
            else:
                print(f"⚠️ Skipping invalid credit note: {inv}")

        if not valid_notes:
            raise Exception("No valid credit notes to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/credit-notes/",
            json={"credit_notes": valid_notes},
            headers=headers
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())
            raise Exception("Failed to send credit notes to server.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending credit notes to Django: {e}")
        raise Exception("Failed to send credit notes to server.")

def send_debit_notes_to_django(invoices):
    try:
        valid_notes = []
        for inv in invoices:
            if (
                inv.get("customer_name") not in [None, "", "Unknown"]
                and inv.get("note_number") not in [None, "", "Unknown"]
                and inv.get("note_date")
                and inv.get("items") and isinstance(inv.get("items"), list)
            ):
                valid_notes.append(inv)
            else:
                print(f"⚠️ Skipping invalid debit note: {inv}")

        if not valid_notes:
            raise Exception("No valid debit notes to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/debit-notes/",
            json={"debit_notes": valid_notes},
            headers=headers
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())
            raise Exception("Failed to send debit notes to server.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending debit notes to Django: {e}")
        raise Exception("Failed to send debit notes to server.")


def get_debit_note_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Debit Notes</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Debit Notes" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsDebitNote</FILTER>
                <FETCH>DATE, VOUCHERNUMBER, LEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsDebitNote">
                $VoucherTypeName = "Debit Note"
              </SYSTEM>
              <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """


TALLY_REQUEST_XML_BANK_ACCOUNTS = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>Bank Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="Bank Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
            <FILTER>IsBankAccount</FILTER>
            <FETCH>
              NAME, PARENT, EMAIL, ADDRESS, LEDGERMOBILE, WEBSITE, LEDSTATENAME, COUNTRYNAME, PINCODE,
              BANKALLOCATIONS.BANKNAME, BANKALLOCATIONS.BRANCHNAME, BANKALLOCATIONS.IFSCODE,
              BANKALLOCATIONS.ACCOUNTNUMBER, BANKALLOCATIONS.BSRCODE , OPENINGBALANCE
            </FETCH>
          </COLLECTION>
          <SYSTEM TYPE="Formulae" NAME="IsBankAccount">
            $Parent = "Bank Accounts"
          </SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""
def parse_bank_ledgers(xml_data):
    import xml.etree.ElementTree as ET
    import logging

    banks = []

    try:
        xml_data = clean_xml(xml_data)  # Make sure this is defined elsewhere
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="")
            email = ledger.findtext("EMAIL", default="")
            website = ledger.findtext("WEBSITE", default="")
            ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
            state_name = ledger.findtext("LEDSTATENAME", default="")
            country_name = ledger.findtext("COUNTRYNAME", default="")
            pincode = ledger.findtext("PINCODE", default="")
            opening_balance_raw = ledger.findtext("OPENINGBALANCE", default="0")
            try:
              opening_balance = str(abs(float(opening_balance_raw)))
            except ValueError:
              opening_balance = "0"
            # Address can have multiple lines
            address_elems = ledger.findall(".//ADDRESS")
            address_lines = [elem.text.strip() for elem in address_elems if elem.text]
            address = ", ".join(address_lines)


            # Handle BANKALLOCATIONS safely
            bank_alloc = ledger.find(".//BANKALLOCATIONS.LIST")
            if bank_alloc is not None:
                bank_name = bank_alloc.findtext("BANKNAME", default="")
                branch_name = bank_alloc.findtext("BRANCHNAME", default="")
                ifsc_code = bank_alloc.findtext("IFSCODE", default="")
                account_number = bank_alloc.findtext("ACCOUNTNUMBER", default="")
                bsr_code = bank_alloc.findtext("BSRCODE", default="")
            else:
                bank_name = branch_name = ifsc_code = account_number = bsr_code = ""

            banks.append({
                "name": name,
                "parent": parent,
                "email": email,
                "address": address,
                "ledger_mobile": ledger_mobile,
                "website": website,
                "state_name": state_name,
                "country_name": country_name,
                "pincode": pincode,
                "bank_name": bank_name,
                "branch_name": branch_name,
                "ifsc_code": ifsc_code,
                "account_number": account_number,
                "bsr_code": bsr_code,
                "opening_balance": opening_balance
            })

        return banks

    except ET.ParseError as e:
        logging.error(f"XML Parse Error in Bank Ledgers: {e}")
        with open("last_raw_bank_ledgers.xml", "w", encoding="utf-8") as file:
            file.write(xml_data)
        raise Exception("Failed to parse Tally Bank Ledger XML.")

# def parse_bank_ledgers(xml_data):
#     import xml.etree.ElementTree as ET
#     ledgers = []

#     try:
#         xml_data = clean_xml(xml_data)
#         print(xml_data)
#         root = ET.fromstring(xml_data)

#         for ledger in root.findall(".//LEDGER"):
#             name = ledger.findtext(".//NAME", default="Unknown")
#             parent = ledger.findtext("PARENT", default="")
#             email = ledger.findtext("EMAIL", default="")
#             website = ledger.findtext("WEBSITE", default="")
#             ledger_mobile = ledger.findtext("LEDGERMOBILE", default="")
#             state_name = ledger.findtext("LEDSTATENAME", default="")
#             country_name = ledger.findtext("COUNTRYNAME", default="")
#             pincode = ledger.findtext("PINCODE", default="")

#             address_elems = ledger.findall(".//ADDRESS")
#             address_lines = [elem.text.strip() for elem in address_elems if elem.text]
#             address = ", ".join(address_lines)

#             bank_name = ledger.findtext(".//BANKALLOCATIONS.BANKNAME", default="")
#             branch_name = ledger.findtext(".//BANKALLOCATIONS.BRANCHNAME", default="")
#             ifsc_code = ledger.findtext(".//BANKALLOCATIONS.IFSCODE", default="")
#             account_number = ledger.findtext(".//BANKALLOCATIONS.ACCOUNTNUMBER", default="")
#             bsr_code = ledger.findtext(".//BANKALLOCATIONS.BSRCODE", default="")

#             ledgers.append({
#                 "name": name,
#                 "parent": parent,
#                 "email": email,
#                 "address": address,
#                 "ledger_mobile": ledger_mobile,
#                 "website": website,
#                 "state_name": state_name,
#                 "country_name": country_name,
#                 "pincode": pincode,
#                 "bank_name": bank_name,
#                 "branch_name": branch_name,
#                 "ifsc_code": ifsc_code,
#                 "account_number": account_number,
#                 "bsr_code": bsr_code
#             })

#         return ledgers

#     except ET.ParseError as e:
#         logging.error(f"XML Parse Error in Bank Ledgers: {e}")
#         with open("last_raw_bank_ledgers.xml", "w", encoding="utf-8") as file:
#             file.write(xml_data)
#         raise Exception("Failed to parse Tally Bank Ledger XML.")

def send_banks_to_django(banks):
    try:
        valid_banks = []
        for bank in banks:
            if (
                bank.get("name") not in [None, "", "Unknown"] 
            ):
                valid_banks.append(bank)
            else:
                print(f"⚠️ Skipping invalid bank ledger: {bank}")

        if not valid_banks:
            raise Exception("No valid bank ledgers to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/bank-accounts/",
            json={"banks": valid_banks},
            headers=headers
        )
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending banks to Django: {e}")
        raise Exception("Failed to send bank ledger data to Django server.")


def get_purchase_voucher_xml(from_date, to_date):
    return f"""
    <ENVELOPE>
      <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>Purchase Vouchers</ID>
      </HEADER>
      <BODY>
        <DESC>
          <STATICVARIABLES>
            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            <EXPLODEFLAG>Yes</EXPLODEFLAG>
            <SVFROMDATE>{from_date}</SVFROMDATE>
            <SVTODATE>{to_date}</SVTODATE>
          </STATICVARIABLES>
          <TDL>
            <TDLMESSAGE>
              <COLLECTION NAME="Purchase Vouchers" ISMODIFY="No">
                <TYPE>Voucher</TYPE>
                <FILTER>IsPurchase</FILTER>
                  <FETCH>DATE, VOUCHERNUMBER, ALLLEDGERENTRIES.LIST, ALLINVENTORYENTRIES.LIST ,LEDGERENTRIES.LIST.LedgerName, LEDGERENTRIES.LIST.PARENT</FETCH>
              </COLLECTION>
              <SYSTEM TYPE="Formulae" NAME="IsPurchase">
                $VoucherTypeName = "Purchase"
              </SYSTEM>
                <SYSTEM TYPE="Formulae" NAME="DateFilter">
                $$Date >= DATE "{from_date}" AND $$Date <= DATE "{to_date}"
              </SYSTEM>
            </TDLMESSAGE>
          </TDL>
        </DESC>
      </BODY>
    </ENVELOPE>
    """
# def parse_purchase_vouchers(xml_data):
#     purchases = defaultdict(lambda: {
#         "vendor_name": "",
#         "purchase_number": "",
#         "purchase_date": "",
#         "purchase_ledger": "",
#         "items": [],
#         "cgst": 0.0,
#         "sgst": 0.0,
#         "total_amount": 0.0
#     })

#     xml_data = clean_xml(xml_data)
#     print(xml_data)
#     root = ET.fromstring(xml_data)

#     for voucher in root.findall(".//VOUCHER"):
#         purchase_no = voucher.findtext("VOUCHERNUMBER", default="Unknown")
#         ledger_entry = voucher.find(".//LEDGERENTRIES.LIST")
#         vendor = ledger_entry.findtext("LEDGERNAME", default="Unknown") if ledger_entry is not None else "Unknown"
#         date_raw = voucher.findtext("DATE", default="")
#         # date = f"{date_raw[6:8]}-{date_raw[4:6]}-{date_raw[0:4]}" if len(date_raw) == 8 else date_raw
#         date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}"


#         key = (purchase_no, vendor, date)

#         purchase = purchases[key]
#         purchase["vendor_name"] = vendor
#         purchase["purchase_number"] = purchase_no
#         purchase["purchase_date"] = date

#         for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
#             item_name = item.findtext("STOCKITEMNAME", default="")
#             qty = item.findtext("ACTUALQTY", default="")
#             amt = float(item.findtext("AMOUNT", default="0.0"))
#             amt = abs(amt)
            

#             purchase["items"].append({
#                 "item_name": item_name,
#                 "quantity": qty.strip(),
#                 "amount": f"{amt:.2f}"
#             })
#             purchase["total_amount"] += amt

#         for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
#             ledger_name = ledger.findtext("LEDGERNAME", "").lower()
#             amt = float(ledger.findtext("AMOUNT", default="0.0"))
#             if "cgst" in ledger_name:
#                 purchase["cgst"] += abs(amt)
#             elif "sgst" in ledger_name:
#                 purchase["sgst"] += abs(amt)

#     return [
#         {
#             **pur,
#             "cgst": f"{pur['cgst']:.2f}",
#             "sgst": f"{pur['sgst']:.2f}",
#             "total_amount": f"{(pur['total_amount'] + pur['cgst'] + pur['sgst']):.2f}"
#         }
#         for pur in purchases.values()
          
#     ]

from collections import defaultdict
import xml.etree.ElementTree as ET

def clean_xml(xml_data):
    return xml_data.strip()

def parse_purchase_vouchers(xml_data):
    purchases = defaultdict(lambda: {
        "vendor_name": "",
        "purchase_number": "",
        "purchase_date": "",
        "purchase_ledger": "",
        "items": [],
        "cgst": 0.0,
        "sgst": 0.0,
        "total_amount": 0.0
    })

    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        purchase_no = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_raw = voucher.findtext("DATE", default="").strip()
        date = f"{date_raw[0:4]}-{date_raw[4:6]}-{date_raw[6:8]}" if len(date_raw) == 8 else date_raw

        # Initialize variables to hold vendor and purchase ledger names
        vendor = "Unknown"
        purchase_ledger = ""

        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            is_party_ledger = ledger.findtext("ISPARTYLEDGER", default="").strip().lower()

            if is_party_ledger == "yes":
                vendor = ledger_name
            elif "purchase" in ledger_name.lower():
                purchase_ledger = ledger_name

        key = (purchase_no, vendor, date)
        purchase = purchases[key]
        purchase["vendor_name"] = vendor
        purchase["purchase_number"] = purchase_no
        purchase["purchase_date"] = date
        purchase["purchase_ledger"] = purchase_ledger

        for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
            item_name = item.findtext("STOCKITEMNAME", default="")
            qty = item.findtext("ACTUALQTY", default="")
            amt = float(item.findtext("AMOUNT", default="0.0"))
            amt = abs(amt)

            purchase["items"].append({
                "item_name": item_name,
                "quantity": qty.strip(),
                "amount": f"{amt:.2f}"
            })
            purchase["total_amount"] += amt

        for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", "").lower()
            amt = float(ledger.findtext("AMOUNT", default="0.0"))
            if "cgst" in ledger_name:
                purchase["cgst"] += abs(amt)
            elif "sgst" in ledger_name:
                purchase["sgst"] += abs(amt)

    return [
        {
            **pur,
            "cgst": f"{pur['cgst']:.2f}",
            "sgst": f"{pur['sgst']:.2f}",
            "total_amount": f"{(pur['total_amount'] + pur['cgst'] + pur['sgst']):.2f}"
        }
        for pur in purchases.values()
    ]


def send_purchases_to_django(purchases):
    print("▶️ send_purchases_to_django called with type:", type(purchases))

    try:
        valid_purchases = []
        for pur in purchases:
            if (
                pur.get("vendor_name") not in [None, "", "Unknown"]
                and pur.get("purchase_number") not in [None, "", "Unknown"]
                and pur.get("purchase_date")
                and pur.get("items") and isinstance(pur.get("items"), list) and len(pur.get("items")) > 0
            ):
                valid_purchases.append(pur)

            else:
                print(f"⚠️ Skipping invalid purchase: {pur}")

        if not valid_purchases:
            raise Exception("No valid purchases to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/purchases/",  # Update if your Django URL is different
            json={"purchases": valid_purchases},
            headers=headers
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())
            raise Exception("Failed to send purchases to server.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending purchases to Django: {e}")
        raise Exception("Failed to send purchases to server.")



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
    # "Sundry Creditors": "accounts_payable",
    # "Sundry Debtors": "accounts_receivable",
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
            gstin = ledger.findtext("GSTIN", default="")
            gst_reg_type = ledger.findtext("GSTREGISTRATIONTYPE", default="")
            opening_balance_raw = ledger.findtext("OPENINGBALANCE", default="0")
            try:
              opening_balance = str(abs(float(opening_balance_raw)))
            except ValueError:
              opening_balance = "0"



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
                    "pincode": pincode,
                    "gstin": gstin,
                    "gst_registration_type": gst_reg_type,
                    "opening_balance": opening_balance
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
                    "pincode": pincode,
                    "gstin": gstin,
                    "gst_registration_type": gst_reg_type,
                    "opening_balance": opening_balance
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
       
        root = ET.fromstring(xml_data)

        for ledger in root.findall(".//LEDGER"):
            opening_balance_raw = ledger.findtext("OPENINGBALANCE", default="0")
            try:
              opening_balance = str(abs(float(opening_balance_raw)))
            except ValueError:
              opening_balance = "0"
            name = ledger.findtext(".//NAME", default="Unknown")
            parent = ledger.findtext("PARENT", default="Unknown")
            account_type = TALLY_TO_ZOHO_ACCOUNT_TYPE.get(parent)

            accounts.append({
                "account_name": name,
                "account_code": name,  # assuming Tally name is code for now
                "account_type": account_type,
                "opening_balance": opening_balance
            })

        return accounts

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (COA): {e}")
        raise Exception("Failed to parse COA XML from Tally.")
    
import xml.etree.ElementTree as ET
import logging

def parse_items(xml_data):
    items = []
    try:
        xml_data = clean_xml(xml_data)
        root = ET.fromstring(xml_data)

        for item in root.findall(".//STOCKITEM"):
            name = item.findtext(".//NAME", default="Unknown")
            rate = item.findtext("RATE", default="0")
            description = item.findtext("DESCRIPTION", default="")
            sku = item.findtext("PARTNUMBER", default="")
            product_type = item.findtext("PARENT", default="General")
            gst_applicable = item.findtext("GSTAPPLICABLE", default="Not Applicable")

            # Initialize GST fields
            gst_rate = "0"
            hsn_code = ""

            # Extract GST details
            gst_details_list = item.findall("GSTDETAILS.LIST")
            if gst_details_list:
                first_gst_detail = gst_details_list[0]

                # Extract HSN
                hsn_text = first_gst_detail.findtext("HSN")
                if hsn_text:
                    hsn_code = hsn_text.strip()

                # Navigate to nested STATEWISEDETAILS
                statewise_details = first_gst_detail.find("STATEWISEDETAILS.LIST")
                if statewise_details is not None:
                    rate_details_list = statewise_details.findall("RATEDETAILS.LIST")

                    # Prefer IGST rate if available
                    igst_found = False
                    for rate_detail in rate_details_list:
                        duty_head = rate_detail.findtext("GSTRATEDUTYHEAD", "").strip()
                        rate_val = rate_detail.findtext("GSTRATE", "").strip()

                        if duty_head == "IGST" and rate_val:
                            gst_rate = rate_val
                            igst_found = True
                            break  # Found IGST, exit loop

                    # If IGST not found, sum CGST + SGST
                    if not igst_found:
                        total = 0
                        for rate_detail in rate_details_list:
                            duty_head = rate_detail.findtext("GSTRATEDUTYHEAD", "").strip()
                            rate_val = rate_detail.findtext("GSTRATE", "").strip()
                            if duty_head in ("CGST", "SGST/UTGST") and rate_val:
                                try:
                                    total += float(rate_val)
                                except ValueError:
                                    pass
                        if total > 0:
                            gst_rate = str(total)

            # Append parsed item
            items.append({
                "name": name,
                "rate": rate,
                "description": description,
                "sku": sku,
                "product_type": product_type,
                "gst_applicable": gst_applicable,
                "gst_rate": gst_rate,
                "hsn_code": hsn_code
            })

        return items

    except ET.ParseError as e:
        logging.error(f"XML Parse Error (Items): {e}")
        raise Exception("Failed to parse item XML from Tally.")



from collections import defaultdict

def parse_sales_vouchers(xml_data):
    invoices = defaultdict(lambda: {
        "customer_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "items": [],
        "cgst": 0.0,
        "sgst": 0.0,
        "total_amount": 0.0
    })

    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)

    for voucher in root.findall(".//VOUCHER"):
        inv_no = voucher.findtext("VOUCHERNUMBER", default="Unknown")
        ledger_entry = voucher.find(".//LEDGERENTRIES.LIST")
        customer = ledger_entry.findtext(".//LEDGERNAME", default="Unknown") if ledger_entry is not None else "Unknown"
        date_raw = voucher.findtext("DATE", default="")
        date = f"{date_raw[6:8]}-{date_raw[4:6]}-{date_raw[0:4]}" if len(date_raw) == 8 else date_raw

        key = (inv_no, customer, date)

        invoice = invoices[key]
        invoice["customer_name"] = customer
        invoice["invoice_number"] = inv_no
        invoice["invoice_date"] = date

        # Line items
        for item in voucher.findall(".//ALLINVENTORYENTRIES.LIST"):
            item_name = item.findtext("STOCKITEMNAME", default="")
            qty = item.findtext("ACTUALQTY", default="")
            amt = float(item.findtext("AMOUNT", default="0.0"))

            invoice["items"].append({
                "item_name": item_name,
                "quantity": qty.strip(),
                "amount": f"{amt:.2f}"
            })
            invoice["total_amount"] += amt

        # Taxes (CGST, SGST)
        for ledger in voucher.findall(".//LEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", "").lower()
            amt = float(ledger.findtext("AMOUNT", default="0.0"))

            if "cgst" in ledger_name:
                invoice["cgst"] += abs(amt)
            elif "sgst" in ledger_name:
                invoice["sgst"] += abs(amt)

    # Format totals as string with 2 decimals
    return [
        {
            **inv,
            "cgst": f"{inv['cgst']:.2f}",
            "sgst": f"{inv['sgst']:.2f}",
            "total_amount": f"{(inv['total_amount'] + inv['cgst'] + inv['sgst']):.2f}"
        }
        for inv in invoices.values()
    ]





def parse_receipts(xml_data):
    receipts = []

    # Clean and parse XML
    xml_data = clean_xml(xml_data)
    root = ET.fromstring(xml_data)
    for voucher in root.findall(".//VOUCHER"):
        receipt_number = voucher.findtext("VOUCHERNUMBER", default="Unknown").strip()
        date_str = voucher.findtext("DATE", default="").strip()

        try:
            receipt_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            receipt_date = date_str

        total_amount = 0.0
        customer_name = "Unknown"
        payment_mode = "Unknown"
        cur_balance = None
        ref_name = None

        for ledger in voucher.findall(".//ALLLEDGERENTRIES.LIST"):
            ledger_name = ledger.findtext("LEDGERNAME", default="").strip()
            amt_str = ledger.findtext("AMOUNT", default="0.0").strip()

            try:
                amt = float(amt_str)
            except:
                amt = 0.0

            # Payment mode: bank/cash
            if "bank" in ledger_name.lower() or "cash" in ledger_name.lower():
                payment_mode = ledger_name
            else:
                # Customer details
                customer_name = ledger_name
                total_amount = amt

                # Get current balance
                balance_tags = ["CURRENTBALANCE", "LEDGERCLOSINGBALANCE", "CLOSINGBALANCE", "OPENINGBALANCE", "BALANCE"]
                for tag in balance_tags:
                    balance_str = ledger.findtext(tag)
                    if balance_str:
                        try:
                            cur_balance = float(balance_str)
                            break
                        except:
                            continue

                # Get Agst Ref Name only from the customer ledger
                bill_alloc = ledger.find(".//BILLALLOCATIONS.LIST")
                if bill_alloc is not None:
                    ref_name = bill_alloc.findtext("NAME", default=None)

        receipts.append({
            "receipt_number": receipt_number,
            "customer_name": customer_name,
            "receipt_date": receipt_date,
            "amount": f"{abs(total_amount):.2f}",
            "payment_mode": payment_mode,
            "cur_balance": f"{cur_balance:.2f}" if cur_balance is not None else None,
            "agst_ref_name": ref_name
        })

    return receipts




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
        valid_items = []
        for item in items:
            # Corrected validation for the 'name' field
            if (
                item.get("name") not in [None, "", "Unknown"]
            ):
                valid_items.append(item)
            else:
                print(f"⚠️ Skipping invalid item: {item}")

        if not valid_items:
            raise Exception("No valid items to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/items/",
            json={"items": valid_items},
            headers=headers
        )
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending items to Django: {e}")
        raise Exception("Failed to send items to server.")

import logging

def send_invoices_to_django(invoices):
    try:
        valid_invoices = []
        for inv in invoices:
            if (
                inv.get("customer_name") not in [None, "", "Unknown"]
                and inv.get("invoice_number") not in [None, "", "Unknown"]
                and inv.get("invoice_date")
                and inv.get("items") and isinstance(inv.get("items"), list) and len(inv.get("items")) > 0
            ):
                valid_invoices.append(inv)
            else:
                print(f"⚠️ Skipping invalid invoice: {inv}")

        if not valid_invoices:
            raise Exception("No valid invoices to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/invoices/",
            json={"invoices": valid_invoices},
            headers=headers
        )

        if response.status_code != 201:
            print("🚫 Server responded with error:")
            print(response.status_code)
            print(response.json())  # <-- Show detailed validation error
            raise Exception("Failed to send invoices to server.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending invoices to Django: {e}")
        raise Exception("Failed to send invoices to server.")

def send_receipts_to_django(receipts):
    try:
        valid_receipts = []
        for receipt in receipts:
            if (
                receipt.get("customer_name") not in [None, "", "Unknown"]
                and receipt.get("receipt_number") not in [None, "", "Unknown"]
                and receipt.get("receipt_date")
            ):
                valid_receipts.append(receipt)
            else:
                print(f"⚠️ Skipping invalid receipt: {receipt}")

        if not valid_receipts:
            raise Exception("No valid receipts to send.")

        headers = {"Authorization": f"Token {AUTH_TOKEN}"}
        response = requests.post(
            "http://127.0.0.1:8000/api/users/receipts/",
            json={"receipts": valid_receipts},
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending receipts to Django: {e}")
        raise


# ---------------- GUI LOGIC ----------------

def sync_data(from_date, to_date):
    try:
        status_label.config(text="Connecting to Tally...", fg="blue")
        root.update()

        # Fetch customers
        xml_customers = get_tally_data(TALLY_REQUEST_XML_CUSTOMERS)
        customers = parse_ledgers(xml_customers, ledger_type="customer")
        for item in customers:
          print("\nFetched Customer:")
          print(json.dumps(item, indent=2))

        # Fetch and process bank accounts
        xml_banks = get_tally_data(TALLY_REQUEST_XML_BANK_ACCOUNTS)
        banks = parse_bank_ledgers(xml_banks)

        # Fetch vendors
        xml_vendors = get_tally_data(TALLY_REQUEST_XML_VENDORS)
        vendors = parse_ledgers(xml_vendors, ledger_type="vendor")
        for item in vendors:
          print("\nFetched Customer:")
          print(json.dumps(vendors, indent=2))
        # Chart of Accounts
        xml_coa = get_tally_data(TALLY_REQUEST_XML_COA)
        accounts = parse_coa_ledgers(xml_coa)

        # Items
        xml_items = get_tally_data(TALLY_REQUEST_XML_ITEMS)
        items = parse_items(xml_items)
        # for item in items:
        #   print("\nFetched Items:")
        
        #   print(json.dumps(item, indent=2))

        # from_date = from_date_picker.get_date().strftime("%Y%m%d")
        # to_date = to_date_picker.get_date().strftime("%Y%m%d")

        # Invoices
        xml_sales = get_tally_data(get_sales_voucher_xml(from_date, to_date))
        invoices = parse_sales_vouchers(xml_sales)
        from datetime import datetime
        for invoice in invoices:
          try:
            if invoice.get("invoice_date"):
              invoice["invoice_date"] = datetime.strptime(invoice["invoice_date"], "%d-%m-%Y").strftime("%Y-%m-%d")
          except Exception as e:
              # print(f"⚠️ Date formatting failed for invoice: {invoice.get('invoice_number')}, error: {e}")
              invoice["invoice_date"] = None
        
        print("\nFetched Invoices:")
        for invoice in invoices:
          print(json.dumps(invoice, indent=2))

        # if not customers and not vendors:
        #     messagebox.showwarning("No Data", "No customers or vendors found in Tally.")
        #     status_label.config(text="No ledgers found.", fg="orange")
        #     return

        xml_receipts=get_tally_data(get_receipt_voucher_xml(from_date, to_date))
        receipts=parse_receipts(xml_receipts)
        # print("\nFetched Receipts:")
        # for receipt in receipts:
        #   print(json.dumps(receipt, indent=2))

        if banks:
          print("\nFetched Bank Ledgers:")
          for bank in banks:
            print(json.dumps(bank, indent=2))
          send_banks_to_django(banks)

        # Purchase Vouchers
        xml_purchases = get_tally_data(get_purchase_voucher_xml(from_date, to_date))
        purchases = parse_purchase_vouchers(xml_purchases)
        print("Type of purchases:", type(purchases))
        print("Type of first purchase:", type(purchases[0]) if purchases else "No purchases")

        # print("\nFetched Purchases:")
        # for purchase in purchases:
        #   print(json.dumps(purchase, indent=2))

        # Fetch Payments
        xml_payments = get_tally_data(get_payment_voucher_xml(from_date, to_date))
        payments = parse_payments(xml_payments)

        print("\nFetched Payments:")
        for payment in payments:
          print(json.dumps(payment, indent=2))

        xml_creditnotes=get_tally_data(get_credit_note_xml(from_date,to_date))
        credit_notes=parse_credit_or_debit_vouchers(xml_creditnotes)
        print("\nFetched Credit Notes:")
        for credit in credit_notes:
          print(json.dumps(credit, indent=2))

        xml_debitnotes=get_tally_data(get_debit_note_xml(from_date,to_date))
        debit_notes=parse_credit_or_debit_vouchers(xml_debitnotes , voucher_type='debit')
        print("\nFetched debit Notes:")
        for debit in debit_notes:
          print(json.dumps(debit, indent=2))

        xml_expenses=get_tally_data(get_expenses_voucher_xml(from_date,to_date))
        expenses=parse_expenses(xml_expenses)

        xml_journals=get_tally_data(get_journal_voucher_xml(from_date,to_date))
        journals=parse_journals(xml_journals)
        print("\nFetched Journals:")
        for journal in journals:
          print(json.dumps(journal, indent=2))

        if customers:
            send_customers_to_django(customers)
        if vendors:
            send_vendors_to_django(vendors)
        if accounts:
            send_coa_to_django(accounts)
        if items:
            send_items_to_django(items)
        if invoices:
          send_invoices_to_django(invoices)
        if receipts:
          send_receipts_to_django(receipts)
        if purchases:
          send_purchases_to_django(purchases)
        if payments:
          send_payments_to_django(payments)
        if banks:
          send_banks_to_django(banks)
        if credit_notes:
          send_credit_notes_to_django(credit_notes)
        if debit_notes:
          send_debit_notes_to_django(debit_notes)
        if expenses:
          send_expenses_to_django(expenses)
        if journals:
          send_journals_to_django(journals)

        
        status_label.config(text="Syncing data to Django...", fg="blue")
        messagebox.showinfo("Success", "Customers and Vendors synced successfully!")
        status_label.config(text="✅ Sync complete!", fg="green")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text=f"❌ {str(e)}", fg="red")


# ---------------- GUI SETUP ----------------
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json

root = tk.Tk()
root.title("Tally Sync Agent")
root.geometry("380x350")
root.resizable(False, False)

title_label = tk.Label(root, text="Tally → Books Sync", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# Username input
tk.Label(root, text="Username").pack()
username_var = tk.StringVar()
tk.Entry(root, textvariable=username_var).pack()

# Password input
tk.Label(root, text="Password").pack()
password_var = tk.StringVar()
tk.Entry(root, textvariable=password_var, show="*").pack()

# Financial Year dropdown
financial_years = [f"April {year} to March {year+1}" for year in range(2015, 2027)]
fy_var = tk.StringVar()
fy_var.set(financial_years[-1])  # default to last FY option

tk.Label(root, text="Financial Year").pack()
fy_dropdown = ttk.Combobox(root, textvariable=fy_var, values=financial_years, state="readonly")
fy_dropdown.pack()

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack(pady=10)

footer = tk.Label(root, text="v1.0 - Developed by Your Straits Partners", font=("Arial", 8), fg="gray")
footer.pack(side="bottom", pady=5)

def login_and_sync():
    username = username_var.get()
    password = password_var.get()

    if not username or not password:
        messagebox.showwarning("Missing Fields", "Username and password are required.")
        return

    # Assume get_token is your login function; replace with actual implementation
    if not get_token(username, password):
        messagebox.showerror("Login Failed", "Invalid credentials or server error.")
        return

    # Parse financial year
    selected_fy = fy_var.get()  # e.g. "April 2024 to March 2025"
    parts = selected_fy.split()
    from_year = int(parts[1])
    to_year = int(parts[4])

    from_date = datetime.date(from_year, 4, 1).strftime('%Y%m%d')
    to_date = datetime.date(to_year, 3, 31).strftime('%Y%m%d')

    sync_data(from_date, to_date)

sync_btn = tk.Button(root, text="Login & Sync", command=login_and_sync, font=("Arial", 12), bg="green", fg="white")
sync_btn.pack(pady=20)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

root.mainloop()




# Installers :

# pip install requests
# pip install pyinstaller
# pyinstaller --onefile --windowed python_agent.py
# pip install tkcalendar
