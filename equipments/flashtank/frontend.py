"""Frontend user interface module for the industrial flash tank equipment.
This module provides an interactive Streamlit-based graphical user interface (UI)
to configure feed conditions, execute flash simulations, and visualize phase-split results.
"""
# pylint: disable=invalid-name, too-many-statements, broad-exception-caught, too-many-locals
import sys
import os
import streamlit as st
from equipments.flashtank.backend import FlashTank
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """Render the specialized equipment panel for the Flash Tank.
    Allows the user to specify inlet feed conditions, flash pressure specification mode,
    and execute backend flash separation simulations, visualizing individual vapor and
    liquid outlet stream properties, mass flow rates, and phase split performances metrics.
    """
    st.subheader("🪘 Equipment Module: Flash Tank (Separator Drum)")
    st.markdown("Configure the incoming feed stream and drum seperation"
                " operating conditions below.")

    control_mode= st.radio(
        "Pressure Specification Mode",
        ["Specified Flash Pressure (P_flash)", "Specified Pressure Drop (Delta P)"],
        key= "flash_ctrl_mode"
    )

    #Initialize variables to prevent NameError
    P_flash= None
    delta_P= None

    with st.form(key="flash_tank_input_form"):
        st.markdown("###📥 1. Inlet Feed Stream Specifications")
        col_in1, col_in2 = st.columns(2)

        with col_in1:
            fluid_name= st.text_input(
                "Fluid Name",
                value= "Water",
                key="flash_fluid",
                help="Fluid name supported by CoolProp or "
                "stream module (e.g., Water, R134a)"
            )
            p_in= st.number_input("Inlet Pressure P_in (Pa)", value=3000000.0,
                                  format="%.1f", help="flash_P_in")

        with col_in2:
            t_in= st.number_input("Inlet Temperature T_in (°C)", value=200.0,
                                  format="%.2f", help="flash_T_in")
            m_dot= st.number_input("Mass Flow Rate (kg/s)", value=5.0,
                                   format="%.1f", help="flash_m_in")

        st.markdown("---")

        st.markdown("#### 🪘 Flash Drum Operating Settings")

        if control_mode == "Specified Flash Pressure (P_flash)":
            P_flash= st.number_input("Flash Drum Pressure (Pa)",
                                    value=1500000.0, format="%.1f")
        else:
            delta_P= st.number_input("Pressure Drop Delta P (Pa)",
                                     value=1500000.0, format="%.1f")

        submitted=st.form_submit_button("🚀 Run Flash Tank Thermodynamic Simulation")

        if submitted:
            try:
                inlet_stream= Stream(name= "flash_inlet", fluid=fluid_name)
                inlet_stream.update_by_PT(P=p_in, T= t_in + 273.15, m_dot= m_dot)

                flash_system= FlashTank(name="Process_Flash_Tank")
                results= flash_system.run(
                    inlet_stream= inlet_stream,
                    P_flash= P_flash,
                    delta_P= delta_P
                )

                if results is None:
                    st.error("⚠️ Simulation failed. Please return to results.")
                    return
                vapor_out= results["vapor_outlet"]
                liquid_out= results["liquid_outlet"]

                st.session_state["current_stream"] = vapor_out

                st.markdown("---")
                st.markdown("### 📤 Flash Tank Separation Results "
                            "(Individual Stream Details)")

                out_col1, out_col2= st.columns(2)

                vap_temp_c= vapor_out.T - 273.15 if vapor_out.T else 0.0
                liq_temp_c= liquid_out.T - 273.15 if liquid_out.T else 0.0

                with out_col1:
                    st.markdown("#### 💭 1. Vapor Outlet Stream (Top)")
                    st.metric(label="Mass Flow Rate",
                              value=f"{vapor_out.m_dot:.3f} kg/s")
                    st.metric(label="Operating Pressure",
                              value=f"{vapor_out.P / 1e5:.1f} bar")
                    st.metric(label="Temperature",
                              value= f"{vap_temp_c:.2f} °C")
                    st.metric(label="Specific Enthalpy",
                              value=f"{vapor_out.h / 1000.0:.2f} kJ/kg")
                    st.metric(label= "Specific Entropy",
                              value= f"{vapor_out.s / 1000.0:.2f} kJ/kgK")

                with out_col2:
                    st.markdown("#### 💧 2. Liquid Outlet Stream(Bottom)")
                    st.metric(label="Mass Flow Rate",
                              value=f"{liquid_out.m_dot:.3f} kg/s")
                    st.metric(label="Operating Pressure",
                              value=f"{liquid_out.P / 1e5:.1f} bar")
                    st.metric(label="Temperature",
                              value= f"{liq_temp_c:.2f} °C")
                    st.metric(label="Specific Enthalpy",
                             value=f"{liquid_out.h / 1000.0:.2f} kJ/kg")
                    st.metric(label= "Specific Entropy",
                              value= f"{liquid_out.s / 1000.0:.2f} kJ/kgK")

                st.markdown("---")
                st.markdown("### 🔬 Thermodynamic Performance & Phase Split Metrics")
                pref_col1, pref_col2, pref_col3 = st.columns(3)
                pref_col1.metric(label= "Flash Vapor Quality",
                                 value= f"{results['vapor_quality']:.4f}")
                pref_col2.metric(label= "Vapor Mass Fraction",
                                 value= f"{results['vapor_quality'] * 100.0:.2f} %")
                pref_col3.metric(label= "Liquid Mass Fraction",
                                 value= f"{(1.0 - results['vapor_quality']) * 100.0:.2f} %")

                st.success("✅ Flash tank simulation, thermodynamic phase split,"
                           "and individual stream extraction completed successfully!")    
            except Exception as e:
                st.error(f"🚨 Thermodynamic Error: {e}")
