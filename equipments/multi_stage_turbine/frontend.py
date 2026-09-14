"""Frontend user interface module for unified turbine equipment.
This module provides an interactivate Streamlit-based graphical user interface (UI)
to configure single or multi-stage turbine operrating parameters, stage counts,
efficiency mods, and visualize comprehensive thermodynamic results and stage breakdowns.
"""
#pylint: disable= line-too-long, invalid-name, too-many-statements, too-many-locals, broad-exception-caught
import sys
import os
import streamlit as st
from equipments.multi_stage_turbine.backend import Turbine
from stream import Stream
current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir= os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def render():
    """
    Renders the unified equipment panel for the Turbine (Single_Stage & Multi_Stage).
    Allows the user to specify fluid properties, inlet conditions, final outlet pressure,
    and stage configuration modes, executing backend expansion simulations and
    displaying system performance metrics and detailed stage-by-stage brekdowns.
    """
    st.subheader("⚡Equipment Module: Turbine (Single_Stage & Multi_Stage)")
    st.markdown("Please enter the required inlet specifications,"
                "target outlet pressure,"
                "and configure the number of turbine stages.")
    num_stages= st.number_input("Number of Stages", min_value=1, max_value=10,
                                value=1,step=1,
                                help="Set to 1 for single_stage, >1 for multi_stage")

    eta_s_uniform= 0.88
    eta_s_list= []

    num_stages_int= int(num_stages)
    if num_stages_int > 1:
        st.markdown("#### Efficiency Configuration")
        efficiency_mode= st.radio(
            "Efficiency Mode",
            ["Uniform Efficiency for All Stages", "Custom Efficiency per Stage"],
            index=0,
            label_visibility="collapsed"
            )

        if efficiency_mode == "Uniform Efficiency for All Stages":
            eta_s_uniform= st.slider("Isentropic Efficiency (eta_s)",
                                     min_value=0.01, max_value=1.0,
                                     value=0.88, step=0.01)
        else:
            st.markdown("#### Enter Efficiency for Each Stage:")
            cols_eff= st.columns(min(int(num_stages), 4))
            for i in range (int(num_stages)):
                with cols_eff[i % 4]:
                    val = st.number_input(f"Stage {i+1} eta_s", min_value= 0.01,
                                          max_value=1.0, value=0.88,
                                          step=0.01, key=f"eta_stage_{i+1}")
                    eta_s_list.append(val)

    else:
        eta_s_uniform= st.slider("Isentropic Efficiency (eta_s)", min_value= 0.01,
                                 max_value= 1.0,value=0.88, step=0.01)
        efficiency_mode= "Uniform Efficiency for All stages"

    #User Inputs(Provided via UI Form)
    with st.form(key="turbine_input_form"):
        st.markdown("###📥 User Inputs")
        col1, col2 = st.columns(2)

        with col1:
            fluid_name= st.text_input(
                "Fluid Name (e.g., Water, R134a, Air, CarbonDioxide)",
                value="Water",
                help="Type any valid fluid name supported by CoolPropor or the Stream module"
            )
            p_in= st.number_input("Inlet Pressure (Pa)", value=2000000.0,
                                  format="%.1f", help="Inlet pressure in Pascals")
            t_in= st.number_input("Inlet Temperature (°C)", value=350.0,
                                  format="%.2f",
                                  help="Temperature in Celsius (must be vapor/gas)")

        with col2:
            p_out = st.number_input("Final Outlet Pressure (Pa)", value=100000.0,
                                    format="%.1f",
                                    help="Target final outlet pressure in Pascals")
            m_dot = st.number_input("Mass Flow Rate (kg/s)", value=1.0,
                                    format="%.2f",
                                    help="Mass flow rate through the turbine system")

        submitted = st.form_submit_button("🚀 Run Turbine Thermodynamic Simulation")

#Program Calculation Outputs (Isolated from user inputs)
    if submitted:
        try:
            inlet_stream = Stream(name="turbine_inlet", fluid=fluid_name)
            inlet_stream.update_by_PT(p_in, t_in+273.15, m_dot= m_dot)
            outlet_stream= Stream(name="turbine_outlet", fluid=fluid_name)
            eff_param=(
                eta_s_list
                if (
                    num_stages > 1
                    and "efficiency_mode" in locals()
                    and efficiency_mode== "Custom Efficiency per Stage"
                )
                else eta_s_uniform
            )

            turbine_system = Turbine(
                name="Process_Turbine",
                num_stages= int(num_stages),
                eta_s_list= eff_param
            )

            final_outlet = turbine_system.run(
                inlet_stream=inlet_stream,
                outlet_stream=outlet_stream,
                P_out=p_out,
                eta_s_list=eff_param
            )

            if final_outlet is None:
                st.error("⚠️ Thermodynamic calculation could not be completed."
                         " Please check inlet conditions, "
                         "fluid name validity, or constraints.")
                return

            st.markdown("---")
            st.markdown("### 📤 Program Calculation Outputs & System Summary")
            st.info("These overall metrics are computed directly "
                    "by the thermodynamic backend model.")

            out_col1, out_col2 = st.columns(2)

            with out_col1:
                st.metric(
                    label="System Inlet Enthalpy (h_in)",
                    value=f"{inlet_stream.h / 1000.0:.2f} kJ/kg" if inlet_stream.h is not None else "N/A",
                )
                st.metric(
                    label="Final Outlet Enthalpy (h_out)",
                    value=f"{final_outlet.h / 1000.0:.2f} kJ/kg" if final_outlet is not None else "N/A",
                    delta=f"{(final_outlet.h - inlet_stream.h) / 1000.0:.2f} kJ/kg" if (final_outlet.h is not None and inlet_stream.h is not None) else None
                )
                st.metric(
                    label="Total Power Output (W_dot)",
                    value= f"{turbine_system.W_dot:.3f} kW"
                )

            with out_col2:
                st.metric(
                    label="System Inlet Entropy (s_in)",
                    value=f"{inlet_stream.s / 1000.0:.4f} kJ/kg.K" if inlet_stream.s is not None else "N/A",
                    )

                final_temp_c= (final_outlet.T - 273.15) if hasattr(final_outlet, "T") and final_outlet.T else None
                st.metric(
                    label= "Final Outlet Temperature (T_out)",
                    value=f"{final_temp_c:.2f} °C" if final_temp_c is not None else "Calculated via P-h model"
                )
                st.metric(
                    label="Final Outlet Entropy (s_out)",
                    value=f"{final_outlet.s / 1000.0:.4f} kJ/kg.K" if final_outlet is not None and final_outlet.s is not None else "N/A"
                )
            # Show stage breakdown only if multi_stage, or show detailed info
            if int(num_stages)> 1:
                st.markdown("---")
                st.markdown("### 🔍 Detailed Stage-by-Stage & Intermidiate Streams Breakdown")

                streams= turbine_system.stage_streams
                stages= turbine_system.stages

                for i, stage_info in enumerate(stages):
                    in_stream= streams[i]
                    out_stream= streams[i+1]

                    with st.expander(f"⚙️ Stage {i+1}: {stage_info['name']} "
                                     f"| Pressure Drop: {in_stream.P/1e5:.2f} bar ➡️ "
                                     f"{out_stream.P/1e5:.2f} bar", expanded= i==0):
                        sc1, sc2, sc3 = st.columns(3)

                        with sc1:
                            st.markdown("**Stage Operating Info**")
                            st.write(rf"- Efficiency ($\eta_s$): '{stage_info['eta_s']:.2f}'")
                            st.write(rf"- Stage Power ($\dot{{W}}$): "
                                     f"'{stage_info['W_dot']:.3f} kW'")

                        with sc2:
                            st.markdown("**Inlet Stream**")
                            st.write(f"- Pressure: '{in_stream.P:.1f} Pa' "
                                     f"('{in_stream.P/1e5:.2f} bar')")
                            st.write(f"- Temperature: '{(in_stream.T - 273.15):.2f} °C'" if in_stream.T else "- Temperature: N/A")
                            st.write(f"- Enthalpy: '{in_stream.h / 1000.0:.2f} kJ/kg'" if in_stream.h else "- Enthalpy: N/A")

                        with sc3:
                            st.markdown("**Outlet / Intermediate Stream**")
                            st.write(f"- Pressure: '{out_stream.P:.1f} Pa' "
                                     f"('{out_stream.P/1e5:.2f} bar')")
                            st.write(f"- Temperature: '{(out_stream.T -273.15):.2f} °C'" if out_stream.T else "- Temperature: N/A")
                            st.write(f"- Enthaloy: '{out_stream.h / 1000.0:.2f} kJ/kg'" if out_stream.h else "- Enthalpy: N/A")
                            if out_stream.x is not None:
                                st.write(f"- Vapor Quality ($x$): '{out_stream.x:.3f}'")
            else:
                st.success("✅ Thermodynamic simulation completed succesfully"
                               " without constraint violations!")

        except Exception as e:
            st.error("🚨 Thermodynamic Error in Turbine Execution "
                     f"(Ensure the fluid name is recognized by CoolProp): {e}")
