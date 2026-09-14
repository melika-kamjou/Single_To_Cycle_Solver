"""Frontend user interface module for the industrial heat exchanger equipment.
This module provides an interactive Streamlit-based graphical user interface (UI)
to configure hot and cold inlet stream properties, execution parameters,
and visualize heat exchanger performance metrics and outlet stream results.
"""
# pylint: disable=invalid-name, too-many-statements, broad-exception-caught, too-many-locals
import sys
import os
import streamlit as st
from equipments.heat_exchanger.backend import HeatExchanger
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def render():
    """Render the specialized equipment panel for the Heat Exchanger (HX).
    Allows the user to specify hot and cold inlet stream properties, effectiveness,
    and pressure drops directly within the module, running thermodynamic simulations
    nd displaying heat transfer summaries and detailed outlet conditions.
    """

    st.subheader("🔁 Equipment Module: Heat Exchanger (HX)")
    st.markdown("Configure hot and cold inlet streams to simulate thermal energy exchange.")

    st.markdown("###📥 1. Inlet Streams Configuration")

    st.markdown("#### 🔥 Hot Inlet Stream")
    col1, col2, col3, col4= st.columns(4)
    with col1:
        hot_fluid= st.text_input("Hot Fluid", value="Water", key= "hx_hot_fluid")
    with col2:
        p_hot= st.number_input("Hot Pressure (Pa)", value=400000.0,
                               format="%.1f", key="hx_p_hot")
    with col3:
        t_hot= st.number_input("Hot Temp (°C)", value=90.0,
                               format="%.2f", key="hx_t_hot")
    with col4:
        m_hot= st.number_input("Hot Mass Flow (kg/s)", value=3.0,
                               format="%.1f", key="hx_m_hot")

    st.markdown("#### ❄️ Cold Inlet Stream")
    col5, col6, col7, col8= st.columns(4)
    with col5:
        cold_fluid= st.text_input("Cold Fluid", value="Water", key= "hx_cold_fluid")
    with col6:
        p_cold= st.number_input("Cold Pressure (Pa)", value=300000.0,
                                format="%.1f", key="hx_p_cold")
    with col7:
        t_cold= st.number_input("Cold Temp (°C)", value=20.0,
                                format="%.2f", key="hx_t_cold")
    with col8:
        m_cold= st.number_input("Cold Mass Flow (kg/s)", value=5.0,
                                format="%.1f", key="hx_m_cold")

    st.markdown("---")
    st.markdown("### ⚙️ 2. Heat Exchanger Operating Setting")
    col_set1, col_set2= st.columns(2)
    with col_set1:
        effectiveness= st.number_input("Effectiveness (-)", value=0.80,
                                       format="%.2f", key="hx_eff")
    with col_set2:
        p_drop= st.number_input("Pressure Drop (Pa)", value=5000.0,
                                format="%.1f", key="hx_p_drop")

    submitted=st.button("🚀 Run Heat Exchanger Simulation", key="hx_run_btn")

    if submitted:
        try:
            hot_stream= Stream(name="hot_inlet", fluid=hot_fluid)
            hot_stream.update_by_PT(P=p_hot, T=t_hot + 273.15, m_dot=m_hot)

            cold_stream= Stream(name="cold_inlet", fluid=cold_fluid)
            cold_stream.update_by_PT(P=p_cold, T=t_cold + 273.15, m_dot=m_cold)

            hx= HeatExchanger(name="Process_HX", effectiveness= effectiveness)
            hot_out, cold_out= hx.run(hot_inlet=hot_stream,
                                      cold_inlet= cold_stream,
                                      P_drop_hot=p_drop, P_drop_cold=p_drop)

            if hot_out is None or cold_out is None:
                st.error("⚠️ Simulation failed.")
                return
            st.session_state["current_stream"]= hot_out

            st.markdown("---")
            st.markdown("### 📊  Heat Transfer Summary")
            st.markdown("**Total Heat Exchanged (Q):"
                        f"** '{hx.Q_dot / 1000.0:.2f} kW'")

            st.markdown("---")
            st.markdown("### 📤 Outlet Stream Results")

            st.markdown("#### 🔥 Hot Outlet Stream")
            cols_hot= st.columns(5)
            cols_hot[0].metric(label="Mass Flow (kg/s)",
                               value=f"{hot_out.m_dot:.2f}")
            cols_hot[1].metric(label="Pressure (bar)",
                               value=f"{hot_out.P/1e5:.1f}")
            cols_hot[2].metric(label= "Temperature (°C)",
                               value=f"{hot_out.T - 273.15:.2f}")
            cols_hot[3].metric(label="Enthalpy (kJ/kg)",
                               value=f"{hot_out.h / 1000.0:.2f}")
            cols_hot[4].metric(label="Entropy (kJ/kg.K)",
                               value= f"{hot_out.s / 1000.0:.2f}")

            st.markdown("#### ❄️ Cold Outlet Stream")
            cols_cold= st.columns(5)
            cols_cold[0].metric(label="Mass Flow (kg/s)",
                                value=f"{cold_out.m_dot:.2f}")
            cols_cold[1].metric(label="Pressure (bar)",
                                value=f"{cold_out.P/1e5:.1f}")
            cols_cold[2].metric(label= "Temperature (°C)",
                                value=f"{cold_out.T - 273.15:.2f}")
            cols_cold[3].metric(label="Enthalpy (kJ/kg)",
                                value=f"{cold_out.h / 1000.0:.2f}")
            cols_cold[4].metric(label="Entropy (kJ/kg.K)",
                                value= f"{cold_out.s / 1000.0:.2f}")

            st.success("✅ Heat Exchanger simulation completed successfully"
                       " with strict mass & energy balance!")

        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
