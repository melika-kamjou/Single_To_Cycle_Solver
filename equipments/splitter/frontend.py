"""Streamlit frontend unterface module for the Stream Splitter equipment.
Handles user inputs for inlet stream and split ratios, and displays calculation outputs.
"""
#pylint: disable= invalid-name, too-many-locals, broad-exception-caught
import sys
import os
import streamlit as st
from equipments.splitter.backend import Splitter
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """Renders the specialized Streamlit UI panel for the Stream Splitter equipment."""

    st.subheader("⚓ Equipment Module: Stream Splitter")
    st.markdown("Configure an incoming feed stream and split it into"
                " multiple exit streams based on given ratios.")

    st.markdown("###📥 1. Inlet Feed Stream Specifications")
    fluid_name= st.text_input("Fluid Name", value= "Water", key="splitter_fluid_name")

    col1, col2, col3= st.columns(3)
    with col1:
        p_in= st.number_input("Inlet Pressure (Pa)", value=300000.0,
                              format="%.1f", key="splitter_p_in")
    with col2:
        t_in= st.number_input("Inlet Temperature (°C)", value=60.0,
                              format="%.2f", key="splitter_t_in")
    with col3:
        m_dot_in= st.number_input("Inlet Mass Flow Rate (kg/s)", value=5.0,
                                  format="%.1f", key="splitter_m_dot")

    st.markdown("---")
    st.markdown("### ⚙️ 2. Splitter Operating Setting")
    num_outlets= st.selectbox("Number of Outlet Streams",
                              options=[2,3,4], key="splitter_num_outlets")

    split_ratios= []
    st.markdown("#### Enter Split Ratios (Sum must equal 1.0)")
    cols= st.columns(num_outlets)

    default_ratios= {2: [0.4, 0.6], 3: [0.3, 0.3, 0.4], 4: [0.2, 0.2, 0.3, 0.3]}
    current_defaults= default_ratios.get(num_outlets, [1.0/num_outlets]*num_outlets)

    for i in range(num_outlets):
        with cols[i]:
            ratio= st.number_input(f"Fraction #{i+1}", value=current_defaults[i],
                                   format="%.2f", key= f"splitter_ratio_{i}")
            split_ratios.append(ratio)

    submitted=st.button("🚀 Run Splitter Thermodynamic Simulation",
                        key="splitter_run_btn")

    if submitted:
        try:
            inlet_stream= Stream(name="inlet_stream", fluid=fluid_name)
            inlet_stream.update_by_PT(P=p_in, T=t_in+273.15, m_dot=m_dot_in)

            splitter= Splitter(name="Process_Splitter")
            outlet_streams= splitter.run(inlet_stream=inlet_stream,
                                         split_ratios=split_ratios)

            if not outlet_streams:
                st.error("⚠️ Simulation failed.")
                return
            st.session_state["current_stream"]= outlet_streams[0]

            st.markdown("---")
            st.markdown("### 📊  Inlet Stream Summary")
            temp_c_in= inlet_stream.T - 273.15 if inlet_stream.T else 0.0
            st.markdown(f"**Inlet Stream:** Mass Flow= '{inlet_stream.m_dot:.2f} kg/s' "
                        f"| Pressure= '{inlet_stream.P/1e5:.1f} bar' "
                        f"| Temp= '{temp_c_in:.2f} °C' "
                        f"| Enthalpy= '{inlet_stream.h / 1000.0:.2f} kJ/kg' "
                        f"| Entropy= '{inlet_stream.s / 1000.0:.2f} kJ/kg K'")

            st.markdown("---")
            st.markdown("### 📤Mixed Outlet Stream Results")
            for idx, out_stm in enumerate(outlet_streams):
                st.markdown(f"#### Outlet Stream #{idx+1}")
                cols= st.columns(5)
                out_temp_c= out_stm.T - 273.15 if out_stm.T else 0.0

                cols[0].metric(label="Mass Flow (kg/s)",
                               value=f"{out_stm.m_dot:.2f}")
                cols[1].metric(label="Pressure (bar)",
                               value=f"{out_stm.P/1e5:.1f}")
                cols[2].metric(label="Temperature (°C)",
                               value=f"{out_temp_c:.2f}")
                cols[3].metric(label="Enthalpy (kJ/kg)",
                               value=f"{out_stm.h / 1000.0:.2f}")
                cols[4].metric(label="Entropy (kJ/kg.K)",
                               value=f"{out_stm.s / 1000.0:.2f}")

            st.success("✅ Splitter simulation completed successfully"
                       " with strict mass & energy balance!")
        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
