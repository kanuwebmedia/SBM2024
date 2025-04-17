import streamlit as st
import mysql.connector
import hashlib
import io
from PIL import Image
import pandas as pd
from fpdf import FPDF
import base64

# -------- Database Connection --------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Kanu@9929",
        database="streamlit_app"
    )

# -------- Password Hashing --------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------- Auth Functions --------
def register_user(username, password, full_name):
    conn = connect_db()
    cursor = conn.cursor()
    hashed = hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)',
                       (username, hashed, full_name))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    hashed = hash_password(password)
    cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, hashed))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# -------- CRUD Functions --------
def create_entry(user_id, household_name, father_name, mobile_no, address, dustbin_number, image_bytes):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO entries (user_id, household_name, father_name, mobile_no, address, dustbin_number, image)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                   (user_id, household_name, father_name, mobile_no, address, dustbin_number, image_bytes))
    conn.commit()
    cursor.close()
    conn.close()

def get_entries(user_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM entries WHERE user_id=%s ORDER BY created_at DESC', (user_id,))
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return entries

def get_entry(entry_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM entries WHERE id=%s', (entry_id,))
    entry = cursor.fetchone()
    cursor.close()
    conn.close()
    return entry

def update_entry(entry_id, household_name, father_name, mobile_no, address, dustbin_number):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''UPDATE entries SET household_name=%s, father_name=%s, mobile_no=%s, address=%s, dustbin_number=%s WHERE id=%s''',
                   (household_name, father_name, mobile_no, address, dustbin_number, entry_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_entry(entry_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM entries WHERE id=%s', (entry_id,))
    conn.commit()
    cursor.close()
    conn.close()

# -------- PDF Export Function --------
def export_to_pdf(entries):
    pdf = FPDF()
    pdf.set_font("Arial", size=10)
    pdf.add_page()

    pdf.cell(200, 10, txt="My Entries Report", ln=True, align="C")
    pdf.ln(10)

    for idx, entry in enumerate(entries, 1):
        pdf.cell(0, 10, f"{idx}. Household: {entry['household_name']}, Father: {entry['father_name']}, Mobile: {entry['mobile_no']}", ln=True)
        pdf.cell(0, 10, f"Address: {entry['address']}, Dustbin No: {entry['dustbin_number']}", ln=True)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin1')

# -------- Streamlit App --------
def main():
    st.set_page_config(page_title="Swachh Bharat App", page_icon="🌿", layout="centered")

    if 'user' not in st.session_state:
        st.session_state.user = None

    if 'page' not in st.session_state:
        st.session_state.page = 'Home'

    if st.session_state.user:
        menu = ["Home", "My Entries", "Edit Entry", "Delete Entry", "Logout"]
    else:
        menu = ["Login", "Register"]

    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Register":
        page_register()
    elif choice == "Login":
        page_login()
    elif choice == "Home":
        if st.session_state.user:
            page_home()
        else:
            st.error("Please login first!")
    elif choice == "My Entries":
        if st.session_state.user:
            page_entries()
        else:
            st.error("Please login first!")
    elif choice == "Edit Entry":
        if st.session_state.user:
            page_edit()
        else:
            st.error("Please login first!")
    elif choice == "Delete Entry":
        if st.session_state.user:
            page_delete()
        else:
            st.error("Please login first!")
    elif choice == "Logout":
        st.session_state.user = None
        st.success("Logged out successfully!")
        st.rerun()

# -------- Pages --------
def page_register():
    st.title("📝 Register")
    username = st.text_input("Username")
    full_name = st.text_input("Full Name")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if register_user(username, password, full_name):
            st.success("Registration successful. Now login!")
        else:
            st.error("Username already exists.")

def page_login():
    st.title("🔑 Login")

    # >>> Yahan Green Color wali heading <<<
    st.markdown(
        """
        <h3 style='text-align: center; color: green;'>Nagar Nigam Greater Jaipur</h3>
        <h4 style='text-align: center; color: green;'>Murlipura Zone, Ward No. 25</h4>
        <h5 style='text-align: center; color: green;'>Swachh Bharat Mission</h5>
        """, unsafe_allow_html=True
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user = user
            st.success(f"Welcome, {user['full_name']}!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

def page_home():
    st.title("🏠 Create New Entry")
    household_name = st.text_input("Household Name")
    father_name = st.text_input("Father's Name")
    mobile_no = st.text_input("Mobile No.")
    address = st.text_area("Address")
    dustbin_number = st.number_input("Number of Dustbins", min_value=0, step=1)
    picture = st.camera_input("Take a Picture")

    if st.button("Save Entry"):
        image_bytes = picture.getvalue() if picture else None
        create_entry(st.session_state.user['id'], household_name, father_name, mobile_no, address, dustbin_number, image_bytes)
        st.success("Entry saved successfully!")
        st.rerun()

def page_entries():
    st.title("📋 My Entries")
    entries = get_entries(st.session_state.user['id'])

    if entries:
        table_data = []
        for idx, entry in enumerate(entries, 1):
            img = None
            if entry['image']:
                img_data = base64.b64encode(entry['image']).decode()
                img = f'<img src="data:image/jpeg;base64,{img_data}" width="50"/>'
            table_data.append([
                idx,
                entry['household_name'],
                entry['father_name'],
                entry['mobile_no'],
                entry['address'],
                entry['dustbin_number'],
                img
            ])

        df = pd.DataFrame(table_data, columns=["S.No", "Household Name", "Father Name", "Mobile No.", "Address", "Dustbin No", "Image"])

        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        if st.button("🔖 Download PDF"):
            pdf_data = export_to_pdf(entries)
            st.download_button("Download PDF", data=pdf_data, file_name="entries.pdf", mime="application/pdf")
    else:
        st.info("No entries found.")

def page_edit():
    st.title("🔵 Edit Entry")
    entries = get_entries(st.session_state.user['id'])
    entry_options = {f"{entry['household_name']} ({entry['created_at']})": entry['id'] for entry in entries}

    if not entry_options:
        st.info("No entries to edit.")
        return

    selected = st.selectbox("Select Entry to Edit", list(entry_options.keys()))
    entry_id = entry_options[selected]
    entry = get_entry(entry_id)

    household_name = st.text_input("Household Name", entry['household_name'])
    father_name = st.text_input("Father's Name", entry['father_name'])
    mobile_no = st.text_input("Mobile No.", entry['mobile_no'])
    address = st.text_area("Address", entry['address'])
    dustbin_number = st.number_input("Dustbin Number", min_value=0, step=1, value=entry['dustbin_number'])

    if st.button("Save Changes"):
        update_entry(entry_id, household_name, father_name, mobile_no, address, dustbin_number)
        st.success("Entry updated successfully!")
        st.rerun()

def page_delete():
    st.title("🗑️ Delete Entry")
    entries = get_entries(st.session_state.user['id'])
    entry_options = {f"{entry['household_name']} ({entry['created_at']})": entry['id'] for entry in entries}

    if not entry_options:
        st.info("No entries to delete.")
        return

    selected = st.selectbox("Select Entry to Delete", list(entry_options.keys()))
    entry_id = entry_options[selected]
    entry = get_entry(entry_id)

    st.warning(f"Are you sure you want to delete **{entry['household_name']}**?")

    if st.button("Yes, Delete"):
        delete_entry(entry_id)
        st.success("Entry deleted successfully!")
        st.rerun()

# ------------------------

if __name__ == "__main__":
    main()
