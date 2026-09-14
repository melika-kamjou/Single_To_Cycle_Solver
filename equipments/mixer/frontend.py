"""Frontend user interface module for the industrial mixing chamber equipment.
This module provides an interactive Streamlit-based graphical user interface (UI)
to configure multiple incoming feed streams, operating settings, and visualize
adiabatic mixing results and ouutlet stream parameters.
"""
# pylint: disable=invalid-name, broad-exception-caught, too-many-locals
import sys
import os
import streamlit as st
from equipments.mixer.backend import MixingChamber
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """Render the specialized equipment panel for the Mixing Chamber (Mixer).
    Allows the user to specify multiple inlet stream properties, fluid names,
    and custom outlet pressure modes, executing backend mixing simulations
    and displaying individual stream summaries and mixed outlet performance metrics.
    """

    st.subheader("🔀 Equipment Module: Mixing Chamber (Mixer)")
    st.markdown("Configure multiple incoming feed streams separatly "
                "to simulate adiabatic mixing.")

    st.markdown("###📥 1. Inlet Streams Configuration")
    num_streams= st.selectbox("Number of Inlet Streams to Mix", options=[2,3,4])

    inlet_configs= []
    fluid_name= st.text_input("Fluid Name Common for all streams", value="Water")

    for i in range(num_streams):
        st.markdown(f"#### Stream #{i+1}")
        col1, col2, col3= st.columns(3)
        with col1:
            p_in= st.number_input(f"Pressure P{i+1} (Pa)", value=300000.0,
                                  format="%.1f", key=f"mix_p_{i}")
        with col2:
            t_in= st.number_input(f"Temperature T{i+1} (°C)", value=50.0 + i*20.0,
                                  format="%.2f", key=f"mix_t_{i}")
        with col3:
            m_dot= st.number_input(f"Mass Flow Rate m{i+1} (kg/s)",
                                   value=2.0 + i*1.0, format="%.1f", key=f"mix_m_{i}")
        inlet_configs.append({"P":p_in, "T":t_in+273.15, "m_dot": m_dot})

        st.markdown("---")
    st.markdown("### ⚙️ 2. Mixer Operating Setting")
    use_custom_p= st.checkbox("Enable stream option", key="mixer_custom_p_check")
    p_out_custom= None
    if use_custom_p:
        p_out_custom= st.number_input("Custom Outlet Pressure (Pa)",
                                      value=280000.0, format="%.1f", key= "custom_p_input")

    submitted=st.button("🚀 Run Mixing Chamber Thermodynamic Simulation")

    if submitted:
        try:
            stream_list= []
            for idx, cfg in enumerate(inlet_configs):
                stm= Stream(name=f"inlet_stream_{idx+1}",fluid= fluid_name)
                stm.update_by_PT(P= cfg["P"], T= cfg["T"], m_dot=cfg["m_dot"])
                stream_list.append(stm)

            mixer= MixingChamber(name="Process_Mixer")
            outlet_stream= mixer.run(inlet_streams= stream_list, P_out= p_out_custom)
            if outlet_stream is None:
                st.error("⚠️ Simulation failed.")
                return
            st.session_state["current_stream"]= outlet_stream

            st.markdown("---")
            st.markdown("### 📊 Separate Inlet Streams Summary")
            for idx, stm in enumerate(stream_list):
                temp_c= stm.T - 273.15 if stm.T else 0.0
                st.markdown(f"**Stream #{idx+1}: Mass Flow= '{stm.m_dot:.2f} kg/s' "
                            f"| Pressure= '{stm.P/1e5:.1f} bar'"
                            f" | Temp= '{temp_c:.2f} °C' "
                            f"| Enthalpy= '{stm.h / 1000.0:.2f} kJ/kg' "
                            f"| Entropy= '{stm.s / 1000.0:.2f} kJ/kg K'")

                st.markdown("---")
                st.markdown("### 📤Mixed Outlet Stream Results")
                out_col1, out_col2, out_col3, out_col4, out_col5= st.columns(5)
                outlet_temp_c= outlet_stream.T - 273.15 if outlet_stream.T else 0.0

                out_col1.metric(label="Total Mass Flow (kg/s)",
                                value=f"{outlet_stream.m_dot:.2f}")
                out_col2.metric(label="Outlet Pressure (bar)",
                                value=f"{outlet_stream.P/1e5:.1f}")
                out_col3.metric(label="Outlet Temperature (°C)",
                                value=f"{outlet_temp_c:.2f}")
                out_col4.metric(label="Mixed Enthalpy (kJ/kg)",
                                value=f"{outlet_stream.h / 1000.0:.2f}")
                out_col5.metric(label="Mixed Entropy (kJ/kg.K)",
                                value=f"{outlet_stream.s / 1000.0:.2f}")

            st.success("✅ Mixing Chamber simulation completed successfully"
                       " with strict mass & energy balance!")

        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
