"""
Streamlit frontend interface module for Expansion, Control, and throttling Valves.
Handles user inputs for valve configuration and displays thermodynamic results.
"""
#pylint: disable= too-many-locals, broad-exception-caught, invalid-name, too-many-statements
import sys
import os
import streamlit as st
from equipments.valve.backend import Valve
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """
    Renders the specialized equipment panel for the 
    Expansion, Control, and Throttling Valves.
    Allows the user to specify BOTH inlet conditions and valve pressure drop parameters
    directly within the module for independent/standalone testing.
    """
    st.subheader("🔀 Equipment Module: Expansion / Throttling Valve")
    st.markdown("Configure the inlet stream properties and valve settings"
                " below to run the simulation.")

    control_mode= st.radio(
        "Pressure Drop Specification Mode",
        ["Specified Outlet Pressure (P_out)", "Specified Pressure Drop (Delta P)"]
    )

    with st.form(key="valve_input_form"):
        # --- Section 1: Inlet Stream Priperties ---
        st.markdown("###📥 1. Inlet Stream Specifications")
        col_in1, col_in2 = st.columns(2)

        with col_in1:
            fluid_name= st.text_input(
                "Fluid Name",
                value= "Water",
                help="Fluid name supported by CoolProp or stream modle (e.g., Water, R134a)"
            )
            p_in= st.number_input("Inlet Pressure (Pa)", value=2000000.0,
                                  format="%.1f", help="Inlet pressure in Pascals")

        with col_in2:
            t_in= st.number_input("Inlet Temperature (°C)", value=50.0,
                                 format="%.2f", help="Inlet temperature in Celsius")
            m_dot= st.number_input("Mass Flow Rate (kg/s)", value=1.0,
                                   format="%.1f", help="Mass flow rate")

        st.markdown("---")
        # --- Section 2: Valve Configuration ---
        st.markdown("#### 🔀 2. Valve Operation Settings")
        col_v1, col_v2= st.columns(2)

        with col_v1:
            valve_type = st.selectbox(
                "Valve_Type",
                ["Expansion Valve (Refrigeration / HVAC)",
                "Control Valve (Process Flow Control)",
                "Simple Throttling Valve",
                "Pressure Reducing Valve (PRV)"
                ],
                help="Select the operational category of the valve"
            )
        with col_v2:
            p_out= None
            delta_p= None

            if control_mode == "Specified Outlet Pressure (P_out)":
                p_out= st.number_input("Target Outlet Pressure (Pa)",
                                       value=500000.0, format="%.1f")
            else:
                delta_p= st.number_input("Pressure Drop Delta P (Pa)",
                                         value=1500000.0, format="%.1f")

        submitted=st.form_submit_button("🚀 Run Valve Thermodynamic Simulation")

    # ---Section 3: Calculation & Results ---
    if submitted:
        try:
            # 1. Create and update inlet stream from user inputs
            inlet_stream= Stream(name= "valve_inlet", fluid=fluid_name)
            inlet_stream.update_by_PT(P=p_in, T= t_in + 273.15, m_dot= m_dot)

            # 2. Instantiate and run valve backend
            valve_system= Valve(name="Process_Valve", valve_type=valve_type)

            if p_out is not None:
                outlet_stream= valve_system.run(inlet_stream=inlet_stream, P_out=p_out)
            else:
                outlet_stream= valve_system.run(inlet_stream=inlet_stream, delta_P=delta_p)

            if outlet_stream is None:
                st.error("⚠️ Simulation failed. Please check your inputs.")
                return

            # optional: Save to session state so next equipment can use it if needed
            st.session_state["current_stream"] = outlet_stream

            st.markdown("---")
            st.markdown("### 📤 Simulation Results Summary")

            res_col1, res_col2= st.columns(2)
            inlet_temp_c= inlet_stream.T - 273.15 if inlet_stream.T  else 0.0
            outlet_stream_c= outlet_stream.T - 273.15 if outlet_stream.T else 0.0

            with res_col1:
                st.markdown("**Inlet Conditions:")
                st.metric(label="Pressure (P_in)",
                          value=f"{inlet_stream.P/1e5:.1f} bar")
                st.metric(label="Enthalpy (h_in)",
                          value=f"{inlet_stream.h / 1000.0 :.2f} kJ/kg")
                st.metric(label="Entropy (s_in)",
                          value= f"{inlet_stream.s / 1000.0:.4f} kJ/kg.K")
                st.metric(label="Temperature (T_in)",
                          value=f"{inlet_temp_c:.2f} °C")
            with res_col2:
                st.markdown("**Outlet Conditions:")
                st.metric(label="Pressure (P_out)",
                          value=f"{outlet_stream.P/1e5:.1f} bar",
                          delta=f"{(outlet_stream.P - inlet_stream.P)/1e5:.2f} bar")
                st.metric(label="Enthalpy (h_out)",
                          value=f"{outlet_stream.h / 1000.0 :.2f} kJ/kg",
                          delta="0.00 (Isenthalpic)")
                st.metric(label="Entropy (s_out)",
                          value= f"{outlet_stream.s / 1000.0:.4f} kJ/kg.K",
                          delta=f"{(outlet_stream.s - inlet_stream.s) / 1000.0:.3f} kJ/kg.K")
                st.metric(label="Temperature (T_out)",
                          value=f"{outlet_stream_c:.2f} °C",
                          delta=f"{(outlet_stream_c - inlet_temp_c):.2f} °C")

            if outlet_stream.x is not None:
                st.info(f"💧 Vapor Quality ($x$) at Outlet: '{outlet_stream.x:.3f}'")

            st.success("✅ Valve simulation completed successfully!")

        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
