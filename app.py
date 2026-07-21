import base64
import json
from huggingface_hub import InferenceClient
from PIL import Image
import streamlit as st

# MUST be the very first Streamlit command in the entire file
st.set_page_config(
    page_title="Add Payee via Check Scanner", page_layout="centered"
)

# App UI Header
st.title("🏦 Add Payee - Bank Check Scanner")
st.write(
    "Upload a clear image of a bank check to automatically extract details"
    " and fill out the payee form."
)

# Sidebar Configuration
st.sidebar.header("Configuration")
hf_api_key = st.sidebar.text_input(
    "Hugging Face API Key", type="password", help="Enter your HF API key here."
)

# Session State Initialization
if "payee_name" not in st.session_state:
  st.session_state.payee_name = ""
if "account_number" not in st.session_state:
  st.session_state.account_number = ""
if "ifsc" not in st.session_state:
  st.session_state.ifsc = ""
if "branch_code" not in st.session_state:
  st.session_state.branch_code = ""
if "branch_name" not in st.session_state:
  st.session_state.branch_name = ""
if "amount" not in st.session_state:
  st.session_state.amount = ""

# File uploader widget
uploaded_file = st.file_uploader(
    "Choose a bank check image...", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
  image = Image.open(uploaded_file)
  st.image(image, caption="Uploaded Bank Check", use_container_width=True)

  if st.button("✨ Scan Check with AI"):
    if not hf_api_key:
      st.error("Please enter your Hugging Face API key in the sidebar first.")
    else:
      with st.spinner("Analyzing check with Qwen Vision AI..."):
        try:
          bytes_data = uploaded_file.getvalue()
          b64_data = base64.b64encode(bytes_data).decode("utf-8")
          image_url = f"data:image/jpeg;base64,{b64_data}"

          client = InferenceClient(api_key=hf_api_key)

          prompt = (
              "Analyze this bank check image and extract the following details"
              " into a strict JSON format:\n- name (Beneficiary/Payee name)\n-"
              " bank_account_number (Recipient account number usually at the"
              " bottom)\n- ifsc (IFSC code, alphanumeric code usually near the"
              " MICR line)\n- branch_code (Branch code if specified, otherwise"
              " empty string)\n- branch_name (Name of the bank branch)\n-"
              " amount (Numerical amount written on the check)\n\nReturn ONLY"
              " valid JSON matching these keys. Do not include markdown code"
              " blocks or extra text."
          )

          response = client.chat.completions.create(
              model="Qwen/Qwen2.5-VL-3B-Instruct",
              messages=[{
                  "role":
                  "user",
                  "content": [
                      {
                          "type": "image_url",
                          "image_url": {
                              "url": image_url
                          }
                      },
                      {"type": "text", "text": prompt},
                  ],
              }],
              max_tokens=300,
          )

          raw_content = response.choices[0].message.content.strip()
          if raw_content.startswith("```json"):
            raw_content = raw_content[7:-3].strip()
          elif raw_content.startswith("```"):
            raw_content = raw_content[3:-3].strip()

          parsed_data = json.loads(raw_content)

          st.session_state.payee_name = parsed_data.get("name", "")
          st.session_state.account_number = parsed_data.get(
              "bank_account_number", ""
          )
          st.session_state.ifsc = parsed_data.get("ifsc", "")
          st.session_state.branch_code = parsed_data.get("branch_code", "")
          st.session_state.branch_name = parsed_data.get("branch_name", "")
          st.session_state.amount = parsed_data.get("amount", "")

          st.success("Check successfully scanned and parsed!")
        except Exception as e:
          st.error(
              f"Error scanning check: {e}. Please fill out the fields manually."
          )

# Payee Form
st.divider()
st.subheader("Add Payee Details")

with st.form("payee_form"):
  name_input = st.text_input(
      "Payee Name", value=st.session_state.payee_name
  )
  acc_input = st.text_input(
      "Bank Account Number", value=st.session_state.account_number
  )
  ifsc_input = st.text_input("IFSC Code", value=st.session_state.ifsc)
  branch_code_input = st.text_input(
      "Branch Code", value=st.session_state.branch_code
  )
  branch_name_input = st.text_input(
      "Branch Name", value=st.session_state.branch_name
  )
  amount_input = st.text_input("Amount", value=st.session_state.amount)

  submitted = st.form_submit_button("🚀 Send / Save Payee")
  if submitted:
    if not name_input or not acc_input or not ifsc_input:
      st.error(
          "Please make sure Name, Account Number, and IFSC are filled out."
      )
    else:
      st.success(
          f"Payee '{name_input}' added and transfer request of"
          f" '{amount_input}' sent successfully!"
      )