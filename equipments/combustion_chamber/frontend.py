"""Frontend module for the industrial combustion chamber equipment in Streamlit."""
# pylint: disable=invalid-name, too-many-locals too-many-statements, broad-exception-caught, raise-missing-from
import sys
import os
import streamlit as st
from equipments.combustion_chamber.backend import CombustionChamber
from stream import Stream

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """Render the Streamlit user interface for the combustion chamber equipment.
    Constructs the input forms for feed streams and fuel operating parameters,
    executes the backend thermodynamic simulation, and displas performance metrics
    and results using interactive Streamlit components.
    """
    st.subheader("🔥 Equipment Module: Combustion Chamber (Combustor)")
    st.markdown("Configure incoming feed streams and fuel combustion parameters"
                "to simulate thermal energy release.")

    st.markdown("###📥 1. Inlet Streams Configuration")
    num_streams= st.selectbox("Number of Inlet Feed Streams",
                              options=[1,2], key="comb_num_streams")
    fluid_name= st.text_input("Fluid Name Common for streams",
                              value="Water", key="comb_fluid_name")
    inlet_configs= []
    for i in range(num_streams):
        st.markdown(f"#### Stream #{i+1}")
        col1, col2, col3= st.columns(3)
        with col1:
            p_in= st.number_input(f"Pressure P{i+1} (Pa)", value=300000.0,
                                  format="%.1f", key=f"comb_p_{i}")
        with col2:
            t_in= st.number_input(f"Temperature T{i+1} (°C)", value=25.0 + 1*20.0,
                                  format="%.2f", key=f"comb_t_{i}")
        with col3:
            m_dot= st.number_input(f"Mass Flow Rate m{i+1} (kg/s)",
                                   value=5.0+ i*1.0, format="%.1f", key=f"comb_m_{i}")
        inlet_configs.append({"P":p_in, "T":t_in+273.15, "m_dot": m_dot})
        st.markdown("---")
    st.markdown("### ⚙️ 2. Combustion Operating Settings")
    col_set1, col_set2, col_set3= st.columns(3)
    with col_set1:
        fuel_m_dot= st.number_input("Fuel Mass Flow (kg/s)", value=0.1,
                                    format="%.2f", key="comb_fuel_m")
    with col_set2:
        fuel_lhv= st.number_input("Fuel LHV (kJ/kg)", value=50000.0,
                                  format="%.1f", key="comb_fuel_lhv")
    with col_set3:
        comb_eff= st.number_input("Combustion Efficiency (-)", value=0.98,
                                  format="%.2f", key="comb_eff")
    use_custom_p= st.checkbox("Enable custom outlet pressure",
                              key="comb_custom_p_check")
    p_out_custom= None
    if use_custom_p:
        p_out_custom= st.number_input("Custom Outlet Pressure (Pa)", value=290000.0,
                                      format="%.1f", key= "comb_custom_p_input")

    submitted=st.button("🚀 Run Combustion Chamber Simulation", key="comb_run_btn")

    if submitted:
        try:
            stream_list= []
            for idx, cfg in enumerate(inlet_configs):
                stm= Stream(name=f"inlet_stream_{idx+1}",fluid= fluid_name)
                stm.update_by_PT(P= cfg["P"], T= cfg["T"], m_dot=cfg["m_dot"])
                stream_list.append(stm)

            chamber= CombustionChamber(name="Process_Chamber", combustion_efficiency=comb_eff)
            outlet_stream= chamber.run(inlet_streams= stream_list,
                                       fuel_mass_flow=fuel_m_dot,
                                       fuel_lhv=fuel_lhv, P_out= p_out_custom)
            if outlet_stream is None:
                st.error("⚠️ Simulation failed.")
                return
            st.session_state["current_stream"]= outlet_stream

            st.markdown("---")
            st.markdown("### 📊 Separate Inlet Streams Summary")
            for idx, stm in enumerate(stream_list):
                temp_c= sum.T - 273.15 if stm.T else 0.0
                st.markdown(f"**Stream #{idx+1}: Mass Flow= '{stm.m_dot:.2f} kg/s' | "
                            f"Pressure= '{stm.P/1e5:.1f} bar' | Temp= '{temp_c:.2f} °C' "
                            f"| Enthalpy= '{stm.h / 1000.0:.2f} kJ/kg' | "
                            f"Entropy= '{stm.s / 1000.0:.2f} kJ/kg K'")

            st.markdown("---")
            st.markdown("### 📤Mixed Outlet Stream Results")
            cols= st.columns(5)
            outlet_temp_c= outlet_stream.T - 273.15 if outlet_stream.T else 0.0
            cols[0].metric(label="Mass Flow (kg/s)",value=
                           f"{outlet_stream.m_dot:.2f}")
            cols[1].metric(label="Pressure (bar)", value=
                           f"{outlet_stream.P/1e5:.1f}")
            cols[2].metric(label="Temperature (°C)", value=
                           f"{outlet_temp_c:.2f}")
            cols[3].metric(label="Enthalpy (kJ/kg)", value=
                           f"{outlet_stream.h / 1000.0:.2f}")
            cols[4].metric(label="Entropy (kJ/kg.K)", value=
                           f"{outlet_stream.s / 1000.0:.2f}")

            st.success("✅ Mixing Chamber simulation completed"
                       " successfully with strict mass & energy balance!")

        except Exception as e:
            st.error(f"🚨 Thermodynamic Error: {e}")
