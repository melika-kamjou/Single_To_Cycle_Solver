"""Frontend module for the industrial boiler equipment in Streamlit."""
#pylint: disable=broad-exception-caught
# pylint: disable=invalid-name, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, raise-missing-from. too-many-arguments
import sys
import os
import streamlit as st
from equipments.boiler.backend import Boiler
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """Render the Streamlit frontend interface for this equipment module."""

    st.subheader("🔥 Equipment Module: Boiler (Steam Generation)")
    st.markdown("Configure the inlet feedwater properties and operating parameters below.")

    control_mode= st.radio(
        "Pressure Drop Specification Mode",
        ["Specified Outlet Pressure (P_out)", "Specified Pressure Drop (Delta P)"]
    )

    with st.form(key="boiler_input_form"):
        # --- Section 1: Inlet Stream Properties ---
        st.markdown("###📥 1. Inlet Stream Specifications")
        col_in1, col_in2 = st.columns(2)

        with col_in1:
            fluid_name= st.text_input(
                "Fluid Name",
                value= "Water",
                help="Fluid name supported by CoolProp or stream model (e.g., Water, R134a)"
            )
            p_in= st.number_input("Inlet Pressure (Pa)", value=5000000.0,
                                  format="%.1f", help="Inlet pressure in Pascals")
        with col_in2:
            t_in= st.number_input("Inlet Temperature (°C)", value=100.0,
                                  format="%.2f", help="Inlet temperature in Celsius")
            m_dot= st.number_input("Mass Flow Rate (kg/s)", value=5.0,
                                   format="%.1f", help="Mass flow rate")

        st.markdown("---")
        # --- Section 2: Boiler Configuration ---
        st.markdown("#### 🔥 Boiler Operation Settings")
        col_v1, col_v2= st.columns(2)

        with col_v1:
            effectiveness = st.slider(
                "Component Effectiveness (epsilon)",
                min_value= 0.0,
                max_value= 1.0,
                value= 0.92,
                step= 0.01,
                help="Effectiveness must be within industrial limits [0.50, 1.0]"
            )

            target_superheat= st.number_input(
                "Target Superheat (°C)",
                value=50.0,
                format="%.1f",
                help="Degrees of subcooling below saturation temperature at outlet")

        with col_v2:

            p_out= None
            delta_p= None
            if control_mode == "Specified Outlet Pressure (P_out)":
                p_out= st.number_input("Target Outlet Pressure (Pa)",
                                       value=4900000.0, format="%.1f")
            else:
                delta_p= st.number_input("Pressure Drop Delta P (Pa)",
                                         value=100000.0, format="%.1f")
        submitted=st.form_submit_button("🚀 Run Boiler Thermodynamic Simulation")

    # ---Section 3: Calculation & Results ---
    if submitted:
        try:
            # 1. Create and update inlet stream from user inputs
            inlet_stream= Stream(name= "boiler_inlet", fluid=fluid_name)
            inlet_stream.update_by_PT(P=p_in, T= t_in + 273.15, m_dot= m_dot)

            # 2. Instantiate and run boiler backend
            boiler_system= Boiler(name="Process_Boiler", effectiveness=effectiveness)

            outlet_stream=boiler_system.run(
                inlet_stream= inlet_stream,
                P_out=p_out,
                delta_P=delta_p,
                target_superheat=target_superheat
            )

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
                st.metric(label="Pressure (P_in)", value=f"{inlet_stream.P/1e5:.1f} bar")
                st.metric(label="Enthalpy (h_in)", value=f"{inlet_stream.h / 1000.0 :.2f} kJ/kg")
                st.metric(label="Entropy (s_in)", value= f"{inlet_stream.s / 1000.0:.4f} kJ/kg.K")
                st.metric(label="Temperature (T_in)", value=f"{inlet_temp_c:.2f} °C")
            with res_col2:
                st.markdown("**Outlet Conditions:")
                st.metric(label="Pressure (P_out)", value=f"{outlet_stream.P/1e5:.1f} bar",
                          delta=f"{(outlet_stream.P - inlet_stream.P)/1e5:.2f} bar")
                st.metric(label="Enthalpy (h_out)", value=f"{outlet_stream.h / 1000.0 :.2f} kJ/kg",
                          delta=f"{(outlet_stream.h - inlet_stream.h)/1000.0:.2f} kJ/kg")
                st.metric(label="Entropy (s_out)", value= f"{outlet_stream.s / 1000.0:.4f} kJ/kg.K",
                          delta=f"{(outlet_stream.s - inlet_stream.s) / 1000.0:.3f} kJ/kg.K")
                st.metric(label="Temperature (T_out)", value=f"{outlet_stream_c:.2f} °C",
                          delta=f"{(outlet_stream_c - inlet_temp_c):.2f} °C")

            # Additional Thermal Performance Metrics
            st.markdown("---")
            st.markdown("### 🔬 Performance Metrics")
            perf_col1, perf_col2= st.columns(2)
            with perf_col1:
                st.metric(label="Heat Addition Rate (Q_dot)",
                          value=f"{boiler_system.Q_dot / 1000.0:.2f} kW")
            with perf_col2:
                st.metric(label="Thermal Efficiency ",
                          value=f"{boiler_system.effectiveness * 100.0:.1f} %")

            if outlet_stream.x is not None:
                st.info(f"💧 Vapor Quality ($x$) at Outlet: '{outlet_stream.x:.3f}'")
            else:
                st.info("💧 Outlet Stream State: **Superheated Liquid**")
            st.success("✅ Boiler simulation completed successfully!")
        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
