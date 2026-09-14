"""Frontend user interface module for the industrial gas compressor equipment.
This module provides an interactive Streamlit-based graphcal user interface (UI)
to configure operating parameters, execute backend thermodynamic simulations,
and visualize performance metrics and outlet stream properties.
"""
import sys
import os
#pylint: disable= invalid-name, too-many-locals, broad-exception-caught, too-many-statements, wrong-import-position
import streamlit as st
from equipments.compressor.backend import Compressor
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """
    Renders the specialized equipment panel for the Compressor.
    Strictly separates user input parameters from thermodynamic calculation outputs.
    ALL UI texts, labels, and comments are in English.
    """
    st.subheader("🌀 Equipment Module: Gas Compressor")
    st.markdown("Please enter the required inlet stream specifications "
                "and operating parameters for the compressor.")

    #User Inputs(Provided via UI Form)
    with st.form(key="compressor_input_form"):
        st.markdown("###📥 User Inputs")
        col1, col2 = st.columns(2)

        with col1:
            # Unconstrained fluid name input (supports any fluid supported by CoolProp/Stream)
            fluid_name= st.text_input(
                "Fluid Name (e.g., Water, R134a, Air, CarbonDioxide)",
                value="Water",
                help="Type any valid fluid name supported by CoolPropor the Stream module"
            )
            p_in= st.number_input("Inlet Pressure (Pa)", value=100000.0,
                                  format="%.1f", help="Pressure in Pascals")
            t_in= st.number_input("Inlet Temperature (°C)", value=150.0,
                                  format="%.2f", help="Temperature in Celsius (must be vapor/gas)")
        with col2:
            p_out = st.number_input("Outlet Pressure (Pa)", value=500000.0,
                                    format="%.1f", help="Target outlet pressure in Pascals")
            m_dot = st.number_input("Mass Flow Rate (kg/s)", value=1.0,
                                    format="%.2f", help="Mass flow rate through the compressor")
            eta_s = st.slider("Isentropic Efficiency (eta_s)", min_value=0.01, max_value=1.0,
                              value=0.85, step=0.01, help="Compressor isentropic "
                              "efficiency (0 < eta <= 1)")

        submitted = st.form_submit_button("🚀 Run Compressor Thermodynamic Simulation")

#Program Calculation Outputs (Isolated from user inputs)
    if submitted:
        try:
            #1. Initialize and update the inlet stream using user_provided variables
            inlet_stream = Stream(name="compressor_inlet", fluid=fluid_name)
            inlet_stream.update_by_PT(p_in, t_in+273.15, m_dot= m_dot)

            #3. Instantiate the Compressor backend class and execute the run method
            compressor_obj = Compressor(name="Process_Compressor", eta_s=eta_s)

            outlet_stream = compressor_obj.run(
                inlet_stream=inlet_stream,
                P_out=p_out,
                eta_s=eta_s
            )

            if outlet_stream is None:
                st.error("⚠️ Thermodynamic calculation could not be completed."
                         "Please check inlet conditions, fluid name validity, or constraints.")
                return

            st.markdown("---")
            st.markdown("### 📤 Program Calculation Outputs")
            st.info("These metrics and properties are computed directly by"
                    " the thermodynamic backend model and exclude raw user inputs.")

            #Display calculation results using structured metric components
            out_col1, out_col2 = st.columns(2)
            inlet_temp_c= inlet_stream.T - 273.15 if inlet_stream.T  else 0.0
            outlet_stream_c= outlet_stream.T - 273.15 if outlet_stream.T else 0.0

            with out_col1:
                st.markdown("**Inlet Conditions:")
                st.metric(label="Pressure (P_in)",
                          value=f"{inlet_stream.P/1e5:.1f} bar")
                st.metric(label="Enthalpy (h_in)",
                          value=f"{inlet_stream.h / 1000.0 :.2f} kJ/kg")
                st.metric(label="Entropy (s_in)",
                          value= f"{inlet_stream.s / 1000.0:.4f} kJ/kg.K")
                st.metric(label="Temperature (T_in)",
                          value=f"{inlet_temp_c:.2f} °C")
            with out_col2:
                st.markdown("**Outlet Conditions:")
                st.metric(label="Pressure (P_out)",
                          value=f"{outlet_stream.P/1e5:.1f} bar",
                          delta=f"{(outlet_stream.P - inlet_stream.P)/1e5:.2f} bar")
                st.metric(label="Enthalpy (h_out)",
                          value=f"{outlet_stream.h / 1000.0 :.2f} kJ/kg",
                          delta=f"{(outlet_stream.h - inlet_stream.h)/1000.0:.2f} kJ/kg")
                st.metric(label="Entropy (s_out)",
                          value= f"{outlet_stream.s / 1000.0:.4f} kJ/kg.K",
                          delta=f"{(outlet_stream.s - inlet_stream.s) / 1000.0:.3f} kJ/kg.K")
                st.metric(label="Temperature (T_out)",
                          value=f"{outlet_stream_c:.2f} °C",
                          delta=f"{(outlet_stream_c - inlet_temp_c):.2f} °C")

            st.markdown("---")
            st.markdown("### 🔬 Performance Metrics")
            perf_col1, perf_col2= st.columns(2)
            with perf_col1:
                st.metric(label="Work Transfered (W_dot)",
                          value=f"{compressor_obj.W_dot / 1000.0:.2f} kW")

            with perf_col2:
                st.metric(label="Effective Compressor Efficieny",
                          value=f"{compressor_obj.eta_s * 100.0:.1f} %")

            if outlet_stream.x is not None:
                st.info(f"💧 Vapor Quality ($x$) at Outlet: '{outlet_stream.x:.3f}'")
            else:
                st.info("💧 Outlet Stream State: **Subcooled Liquid**")

            st.success("✅ Thermodynamic simulation completed"
                       "succesfully without constraint violations!")

        except Exception as e:
            st.error("🚨 Thermodynamic Error in Compressor Execution"
                    f" (Ensure the fluid name is recognized by CoolProp): {e}")
