import streamlit as st
import pandas as pd
import subprocess
import os
import plotly.express as px
import shlex

st.set_page_config(layout="wide")

# Custom CSS for messages
st.markdown("""
    <style>
    .st-alert {
        padding: 15px;
        background-color: #f44336; /* Red */
        color: white;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    .st-success {
        padding: 15px;
        background-color: #4CAF50; /* Green */
        color: white;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

def run_tests(file_path, test_type, devices):
    try:
        devices_str = " ".join([f'"{device}"' for device in devices]) if devices else ""
        if os.name == 'nt':
            venv_activate = os.path.join(os.getcwd(), 'venv', 'Scripts', 'activate.bat')
            command = f"{venv_activate} & python .\\run_tests.py {shlex.quote(file_path)} --test_type {shlex.quote(test_type)} --devices {devices_str}"
        else:
            venv_activate = os.path.join(os.getcwd(), 'venv', 'bin', 'activate')
            command = f"source {venv_activate} && python ./run_tests.py {shlex.quote(file_path)} --test_type {shlex.quote(test_type)} --devices {devices_str}"

        if not os.path.exists(venv_activate):
            command = f"python run_tests.py {shlex.quote(file_path)} --test_type {shlex.quote(test_type)} --devices {devices_str}"

        # st.write(command)
        result = subprocess.run(command, shell=True, capture_output=True, text=True, env=os.environ)
        # st.write(f"STDOUT:\n{result.stdout}")
        # st.write(f"STDERR:\n{result.stderr}")

        if result.returncode == 0:
            st.session_state.message = ("success", "Tests completed successfully.")
        else:
            st.session_state.message = ("alert", "Error running the tests.")
        return result
    except Exception as e:
        st.session_state.message = ("alert", f"Error running tests: {e}")

def save_data(data, file_path):
    try:
        data['Port'] = data['Port'].fillna(22).astype(int)  # Ensure Port is always int
        data.to_csv(file_path, index=False)
        st.session_state.message = ("success", "Data saved successfully.")
    except Exception as e:
        st.session_state.message = ("alert", f"Error saving data: {e}")

def classify_connectivity(row):
    if not row['Ping']:
        return 'No Ping'
    if row['Ping'] and not row['SSH']:
        return 'Ping Only'
    if row['Ping'] and row['SSH'] and not row['Access']:
        return 'Ping + SSH'
    if row['Ping'] and row['SSH'] and row['Access']:
        return 'Full Access'
    return 'Unknown'

# Path to the CSV file
file_path = 'devices.csv'  # Change this to your CSV file path

# App title
st.title('Connectivity Test Results')

# Create columns for the buttons
button_col1, button_col2, button_col3 = st.columns(3)

# Sidebar for controls and messages
with st.sidebar:
    st.header("Test Configuration")
    test_type = st.selectbox("Select Test Type", options=["all", "ping", "ssh"], index=0)
    devices = st.multiselect("Select Devices (optional)", options=load_data(file_path)["Name"])

    st.subheader("Add New Entry")
    with st.form(key='new_entry_form'):
        name = st.text_input("Name")
        ip = st.text_input("IP")
        port = st.text_input("Port")
        username = st.text_input("Username")
        password = st.text_input("Password")
        if st.form_submit_button("Add"):
            port = int(port) if port else 22  # Use default port 22 if not specified
            new_entry = pd.DataFrame([{"Name": name, "IP": ip, "Ping": False, "Port": port, "SSH": False, "Username": username, "Password": password, "Access": False}])
            data = load_data(file_path)
            data = pd.concat([data, new_entry], ignore_index=True)
            save_data(data, file_path)
            st.success("New entry added.")
            st.cache_data.clear()  # To reload the data after adding a new entry
            st.rerun()  # Reload the app to show the changes

    st.subheader("Delete Entries")
    data = load_data(file_path)
    selected_devices = st.multiselect("Select Devices to Delete", data["Name"])
    if st.button("Delete Selected"):
        data = data[~data["Name"].isin(selected_devices)]
        save_data(data, file_path)
        st.success("Selected entries deleted.")
        st.cache_data.clear()  # To reload the data after deleting entries
        st.rerun()  # Reload the app to show the changes

# Load the data from the CSV
data = load_data(file_path)

# Display the data table
st.subheader("Results Table")
edited_data = st.data_editor(data, use_container_width=True, key='data_editor')

# Button to save changes
with button_col3:
    if st.button('Save Changes', key='save_changes', help='Save changes to the CSV file'):
        save_data(edited_data, file_path)
        st.rerun()

# Button to run the tests
with button_col1:
    if st.button('Run Tests Again', key='run_tests'):
        with st.spinner('Running tests...'):
            run_tests(file_path, test_type, devices)
            st.cache_data.clear()
            st.rerun()

# Button to reload data
with button_col2:
    if st.button('Reload Data', key='reload_data'):
        st.cache_data.clear()
        st.rerun()

# Classify connectivity
edited_data['Connectivity'] = edited_data.apply(classify_connectivity, axis=1)

# Summary of connectivity
connectivity_summary = edited_data['Connectivity'].value_counts().rename_axis('Connectivity').reset_index(name='Counts')

# Create pie chart
fig_pie = px.pie(connectivity_summary, names='Connectivity', values='Counts', title="Connectivity Summary")

# Display pie chart
st.subheader("Connectivity Summary")
st.plotly_chart(fig_pie, use_container_width=True)

# Display messages in the sidebar
with st.sidebar:
    st.write("### Status")
    message_type, message_text = st.session_state.get('message', ('', ''))
    if message_type == "success":
        st.write(f'<div class="st-success">{message_text}</div>', unsafe_allow_html=True)
    elif message_type == "alert":
        st.write(f'<div class="st-alert">{message_text}</div>', unsafe_allow_html=True)