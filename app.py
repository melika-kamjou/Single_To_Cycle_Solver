"""Main Streamlit application for the thermodynamic equipment system."""
#pylint: disable=broad-exception-caught
import importlib
import streamlit as st

# --Page Configuration---
st.set_page_config(
    page_title= "Thermodynamic & Equipment System",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---Custom CSS Styling ---
st.markdown(
    """
    <style>
          .main-title {
                font-size: 2.2rem;
                color: #1E3A8A;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
            .subtitle {
                font-size: 1.1rem;
                color: #34B556;
                margin-bottom: 2rem;
            }
     </style>
    """,
        unsafe_allow_html= True,
)
# ---Header Section ---
st.markdown(
    '<p class= "main-title">⚙️ Smart Process Equipment Calculation System</p',
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='subtitle'>Precise calculation of thermodynamic properties"
    "(enthalpy, entropy, etc.) in a molar and advanced way</p>'", 
    unsafe_allow_html=True,
)
st.markdown("---")

# ---Sidebar & Equipment List Management ---
st.sidebar.markdown("### 🗂️ Equipment Navigation Menu")

#Define equipment registry dictionary (Display Name: Module File Name)
EQUIPMENT_REGISTRY={
    "🚰 Pump": "pump",
    "🌀 Compressor": "compressor",
    "⚡ Turbine":"multi_stage_turbine",
    "🔀 Expansion / Control Valve": "valve",
    "❄️ Condenser": "condenser",
    "☀️ Evaporator": "evaporator",
    "🔥 Boiler": "boiler",
    "🪘 Flash Tank": "flashtank",
    "🔀 Mixing_Chamber": "mixer",
    "🔱 Splitter": "splitter",
    "♨️ Combustion_Chamber": "combustion_chamber",
    "🔁 Heat_Exchanger": "heat_exchanger",
    # Add any new equipment here by adding a single line!
}

selected_equipment_label = st.sidebar.selectbox(
    "Please select the equipment:",list(EQUIPMENT_REGISTRY.keys())
)

#Get the corresponding module name
eq_folder_name= EQUIPMENT_REGISTRY[selected_equipment_label]

#---Dynamic Module Loading---
try:
    #Dynamically import from the equipments folder
    eq_frontend= importlib.import_module(f"equipments.{eq_folder_name}.frontend")
    #Execute the render function of the selected equipment
    if hasattr(eq_frontend, "render"):
        eq_frontend.render()
    else:
        st.error(
            f"⚠️ Structural Error: The 'frontend.py' inside"
            f"'equipments/{eq_folder_name}/' does not have a render() function."
        )

except Exception as e:
    st.error(f"🚨 Unexpected error loading module: {e}")
# ---Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Guide:** To add new equipment, simply place " 
    "your calculation file inside the equipment folder."
)
