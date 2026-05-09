import streamlit as st
import pandas as pd
import re
import json
import random

# ==========================================
# MATH & PARSING HELPER FUNCTIONS
# ==========================================
def extract_average_cost(raw_cost_str):
    """Helper function to turn '15000-20000' into a mathematical average for the pipeline."""
    if not raw_cost_str or raw_cost_str == "0-0" or raw_cost_str == "N/A (Design Phase)" or raw_cost_str == "N/A (Engineering Phase)":
        return 0
    
    numbers = re.findall(r'\d+', str(raw_cost_str).replace(',', ''))
    if not numbers:
        return 0
    if len(numbers) == 1:
        return int(numbers[0])
    if len(numbers) >= 2:
        return (int(numbers[0]) + int(numbers[1])) / 2
    return 0

def parse_time_to_days(time_str):
    """Converts AI timeline strings (e.g., '4-6 Weeks') into base working days."""
    if not time_str or time_str in ["TBD", "Unknown"]:
        return 30 # Default assumption
        
    numbers = [int(n) for n in re.findall(r'\d+', str(time_str))]
    if not numbers:
        return 30
        
    avg_val = sum(numbers) / len(numbers)
    lower_str = str(time_str).lower()
    
    if "week" in lower_str:
        return int(avg_val * 5) # 5 working days a week
    elif "month" in lower_str:
        return int(avg_val * 20) # 20 working days a month
    elif "day" in lower_str:
        return int(avg_val)
    else:
        return int(avg_val * 5) # Default assumption is weeks

# ==========================================
# THE MONTE CARLO BURN-RATE ENGINE
# ==========================================
def run_monte_carlo(budget, estimated_days, complexity):
    """Runs 1,000 probabilistic simulations of the project lifecycle."""
    
    # 1. Calibrate Risk Probability based on AI Complexity Score
    if "Red" in str(complexity) or "High" in str(complexity):
        delay_chance = 0.35  # 35% chance every day is a blocker/delay
    elif "Yellow" in str(complexity) or "Medium" in str(complexity):
        delay_chance = 0.20  # 20% chance
    else:
        delay_chance = 0.05  # 5% chance (Standard friction)

    daily_burn = budget / estimated_days if estimated_days > 0 else 0
    
    all_runs = []
    bankruptcies = 0
    
    # 2. Run 1,000 Independent Project Lifecycles
    for _ in range(1000):
        work_done = 0
        cash_remaining = budget
        run_path = [cash_remaining]

        # The project isn't over until 'estimated_days' of actual work is completed
        while work_done < estimated_days:
            if random.random() < delay_chance:
                # Developer is blocked: We pay them (burn cash), but make 0 progress
                cash_remaining -= daily_burn 
            else:
                # Productive day: We pay them, and make 1 day of progress
                cash_remaining -= daily_burn
                work_done += 1
                
            run_path.append(cash_remaining)

        if cash_remaining < 0:
            bankruptcies += 1
            
        all_runs.append(run_path)

    # 3. Pad the arrays so they are all the same length for dataframe alignment
    max_duration = max(len(r) for r in all_runs)
    for r in all_runs:
        while len(r) < max_duration:
            r.append(r[-1]) # Project finished, cash remains flat
    
    # 4. Calculate P10, P50, and P90 Percentiles per day
    chart_data = []
    for day in range(max_duration):
        day_vals = [r[day] for r in all_runs]
        day_vals.sort()
        
        chart_data.append({
            "Day": day,
            "Worst Case (P10)": day_vals[int(1000 * 0.1)],
            "Expected Path (P50)": day_vals[int(1000 * 0.5)],
            "Best Case (P90)": day_vals[int(1000 * 0.9)],
            "Zero Line (Bankruptcy)": 0
        })
        
    df = pd.DataFrame(chart_data).set_index("Day")
    prob_loss = (bankruptcies / 1000) * 100
    
    # Calculate Cross-Over points (When does cash drop below $0?)
    exp_cross = next((i for i, v in enumerate(df["Expected Path (P50)"]) if v <= 0), None)
    worst_cross = next((i for i, v in enumerate(df["Worst Case (P10)"]) if v <= 0), None)
    
    return df, prob_loss, exp_cross, worst_cross


# ==========================================
# ADMIN DASHBOARD RENDERER
# ==========================================
def render_admin_dashboard(supabase):
    st.title("Admin Control Center")
    st.markdown("### BridgeBuild AI Global Oversight & Access Control")
    
    # --- ADDED TAB 4 FOR MONTE CARLO ---
    tab1, tab2, tab3, tab4 = st.tabs(["Global Analytics", "Team Management", "Profitability Engine", "Monte Carlo Risk Engine"])

    try:
        all_tickets_response = supabase.table("tickets").select("*").execute()
        all_tickets = all_tickets_response.data
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        all_tickets = []

    # ==========================================
    # TAB 1: THE "GOD VIEW" ANALYTICS
    # ==========================================
    with tab1:
        if not all_tickets:
            st.info("No projects generated in the company yet.")
        else:
            total_projects = len(all_tickets)
            total_pipeline_value = sum([extract_average_cost(t.get('raw_cost', '0-0')) for t in all_tickets if t.get('status') != 'Completed & Billed'])
            
            pm_queue = len([t for t in all_tickets if t.get('target_department') == 'PM'])
            design_queue = len([t for t in all_tickets if t.get('target_department') == 'Design'])
            eng_queue = len([t for t in all_tickets if t.get('target_department') == 'Engineering'])
            completed = len([t for t in all_tickets if t.get('status') == 'Ready for Dev'])

            st.markdown("#### Organization Pipeline Overview")
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                with st.container(border=True):
                    st.metric("Total AI Generations", total_projects)
            with col_m2:
                with st.container(border=True):
                    st.metric("Active Pipeline Value", f"${total_pipeline_value:,.2f}")
            with col_m3:
                with st.container(border=True):
                    st.metric("Ready for Dev", completed)

            st.write("")
            st.markdown("#### Live Department Bottlenecks")
            
            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                st.markdown("**Current Queue Load**")
                st.metric("Awaiting PM", pm_queue)
                st.metric("Awaiting Design", design_queue)
                st.metric("Awaiting Engineering", eng_queue)
                
            with col_b2:
                bottleneck_data = {
                    "Department": ["PM Scoping", "UI/UX Design", "Engineering"],
                    "Tickets in Queue": [pm_queue, design_queue, eng_queue]
                }
                bottleneck_df = pd.DataFrame(bottleneck_data).set_index("Department")
                st.bar_chart(bottleneck_df, color="#ef4444", height=250)

            st.divider()
            st.markdown("#### Live Project Radar")
            
            radar_data = []
            for t in all_tickets:
                if t.get("status") != "Completed & Billed":
                    radar_data.append({
                        "Creation Date": t.get("created_at", "").split("T")[0],
                        "Project Summary": t.get("summary", "Unknown")[:80] + "...",
                        "Current Status": t.get("status", "Unknown"),
                        "Target Dept": t.get("target_department", "None"),
                        "Est. Time": t.get("time", "Unknown"),
                    })
            
            if radar_data:
                radar_df = pd.DataFrame(radar_data).sort_values(by="Creation Date", ascending=False)
                st.dataframe(
                    radar_df, 
                    use_container_width=True, 
                    hide_index=True,
                    height=300,
                    column_config={
                        "Creation Date": st.column_config.TextColumn("Date", width="small"),
                        "Project Summary": st.column_config.TextColumn("Project Vision", width="large"),
                        "Current Status": st.column_config.TextColumn("Status", width="medium"),
                        "Target Dept": st.column_config.TextColumn("Owner", width="small"),
                        "Est. Time": st.column_config.TextColumn("Timeline", width="small")
                    }
                )
            else:
                st.info("No active projects in the pipeline.")

    # ==========================================
    # TAB 2: TEAM MANAGEMENT 
    # ==========================================
    with tab2:
        st.write("")
        st.markdown("#### Active Directory")
        st.info("Assign department dashboards to users by clicking their 'Role' cell below, selecting a new department, and hitting Save.")

        try:
            response = supabase.table("profiles").select("*").execute()
            profiles_data = response.data
            
            if not profiles_data:
                st.warning("No user profiles found.")
            else:
                df = pd.DataFrame(profiles_data)
                roles_list = ["pm", "sales", "engineering", "design", "freelancer", "admin", "marketing"]
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "id": st.column_config.TextColumn("User ID", disabled=True, width="medium"),
                        "role": st.column_config.SelectboxColumn(
                            "Department Role",
                            options=roles_list,
                            required=True,
                            width="medium"
                        ),
                        "currency": st.column_config.TextColumn("Currency", disabled=True, width="small"),
                        "rate_standard": st.column_config.TextColumn("Rate Standard", disabled=True, width="medium"),
                        "ai_model": st.column_config.TextColumn("AI Model", disabled=True, width="medium"),
                        "dark_mode": st.column_config.CheckboxColumn("Dark Mode", disabled=True, width="small")
                    },
                    hide_index=True,
                    key="admin_role_editor",
                    use_container_width=True,
                    height=300
                )
                
                if st.button("Save Changes to Database", type="primary"):
                    with st.spinner("Pushing updates to enterprise servers..."):
                        updates_made = False
                        for index, row in edited_df.iterrows():
                            if df.loc[index, 'role'] != row['role']:
                                supabase.table("profiles").update({"role": row['role']}).eq("id", row['id']).execute()
                                updates_made = True
                        
                        if updates_made:
                            st.success("User roles updated successfully!")
                            st.rerun() 
                        else:
                            st.info("No changes detected.")
        except Exception as e:
            st.error(f"Error loading Admin Directory: {str(e)}")

    # ==========================================
    # TAB 3: THE PROFITABILITY ENGINE
    # ==========================================
    with tab3:
        st.write("")
        st.markdown("#### Project Financial Close-Out")
        st.info("Log actual costs for completed projects to calibrate AI estimations and track agency profitability.")

        ready_tickets = [t for t in all_tickets if t.get('status') == 'Ready for Dev']
        
        with st.expander("Log a Completed Project", expanded=False):
            if not ready_tickets:
                st.success("No active projects pending close-out. All completed!")
            else:
                ticket_options = {f"{t['summary'][:60]}...": t for t in ready_tickets}
                selected_ticket_name = st.selectbox("Select Project to Close Out:", list(ticket_options.keys()))
                
                if selected_ticket_name:
                    active_t = ticket_options[selected_ticket_name]
                    est_cost = extract_average_cost(active_t.get('raw_cost', '0'))
                    
                    st.caption(f"**AI Estimated Budget:** ${est_cost:,.2f}")
                    
                    col_close1, col_close2 = st.columns(2)
                    with col_close1:
                        actual_cost = st.number_input("Actual Total Cost ($)", min_value=0, value=int(est_cost), step=500)
                    with col_close2:
                        actual_time = st.text_input("Actual Time Spent", placeholder="e.g., 6 Weeks")
                        
                    if st.button("Finalize & Log Financials", type="primary", use_container_width=True):
                        try:
                            full_data = json.loads(active_t['full_data']) if active_t.get('full_data') else {}
                            full_data['actual_cost'] = actual_cost
                            full_data['actual_time'] = actual_time
                            
                            supabase.table("tickets").update({
                                "status": "Completed & Billed",
                                "target_department": "None",
                                "full_data": json.dumps(full_data)
                            }).eq("id", active_t['id']).execute()
                            
                            st.success("Project finalized! Financials logged.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to log project: {str(e)}")

        st.divider()
        st.markdown("#### Margin & Variance Analytics")
        
        completed_tickets = [t for t in all_tickets if t.get('status') == 'Completed & Billed']
        
        if not completed_tickets:
            st.info("Complete your first project above to generate financial analytics.")
        else:
            analytics_data = []
            chart_data = [] 
            total_est = 0
            total_actual = 0
            
            for t in completed_tickets:
                try:
                    data = json.loads(t['full_data'])
                    est = extract_average_cost(t.get('raw_cost', '0'))
                    act = float(data.get('actual_cost', est))
                    
                    total_est += est
                    total_actual += act
                    
                    variance = est - act
                    margin_status = "✅ Profitable" if variance >= 0 else "🔴 Loss / Over-budget"
                    
                    proj_name = t.get("summary", "Unknown")[:30] + "..."
                    
                    analytics_data.append({
                        "Project": proj_name,
                        "AI Estimate": f"${est:,.2f}",
                        "Actual Cost": f"${act:,.2f}",
                        "Variance": f"${variance:,.2f}",
                        "Health": margin_status
                    })
                    
                    chart_data.append({
                        "Project": proj_name,
                        "AI Estimate ($)": est,
                        "Actual Logged Cost ($)": act
                    })
                except:
                    continue
            
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.metric("Total Billed Revenue", f"${total_actual:,.2f}")
            with col_a2:
                variance_total = total_est - total_actual
                st.metric("Total AI Estimation Variance", f"${variance_total:,.2f}")
            with col_a3:
                margin_health = "Healthy" if total_actual <= total_est else "Needs Calibration"
                st.metric("Estimation Health", margin_health)

            st.write("")
            st.markdown("##### Estimate vs. Actuals Tracker")
            if chart_data:
                chart_df = pd.DataFrame(chart_data).set_index("Project")
                st.bar_chart(chart_df, color=["#3b82f6", "#ef4444"], height=300) 
            
            st.write("")
            st.markdown("##### Completed Project Ledger")
            analytics_df = pd.DataFrame(analytics_data)
            st.dataframe(analytics_df, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 4: THE MONTE CARLO RISK ENGINE (NEW)
    # ==========================================
    with tab4:
        st.write("")
        st.markdown("#### Quantitative Margin Predictor")
        st.info("Run 1,000 probabilistic simulations against an active project to predict exactly when the agency will start burning cash.")

        active_projects = [t for t in all_tickets if t.get('status') != 'Completed & Billed' and t.get('status') != 'Draft']
        
        if not active_projects:
            st.warning("No active projects found in the pipeline. Please generate an Agile Ticket first.")
        else:
            mc_options = {f"{t['summary'][:60]}...": t for t in active_projects}
            selected_mc_proj = st.selectbox("Select Active Project to Simulate:", list(mc_options.keys()))
            
            if selected_mc_proj:
                mc_ticket = mc_options[selected_mc_proj]
                
                # Extract Base Metrics
                mc_budget = extract_average_cost(mc_ticket.get('raw_cost', '0'))
                mc_time_str = mc_ticket.get('time', 'TBD')
                mc_days = parse_time_to_days(mc_time_str)
                mc_complexity = mc_ticket.get('complexity', 'Unknown')
                
                with st.container(border=True):
                    col_b1, col_b2, col_b3 = st.columns(3)
                    with col_b1: st.metric("Base AI Budget", f"${mc_budget:,.2f}")
                    with col_b2: st.metric("Base Timeline", mc_time_str, help=f"Parsed as {mc_days} working days.")
                    with col_b3: st.metric("Complexity Risk", mc_complexity)

                if st.button("Run 1,000 Monte Carlo Simulations", type="primary", use_container_width=True):
                    if mc_budget == 0 or mc_days == 0:
                        st.error("Cannot run simulation: Budget or Timeline is zero. Please use God-Mode in the PM Hub to set proper estimates.")
                    else:
                        with st.status("Initializing Quantitative Engine...", expanded=True) as status:
                            st.write("Extracting volatility modifiers...")
                            st.write("Running 1,000 independent statistical lifetimes...")
                            st.write("Aggregating percentiles...")
                            
                            try:
                                mc_df, prob_loss, exp_cross, worst_cross = run_monte_carlo(mc_budget, mc_days, mc_complexity)
                                status.update(label="Simulation Complete!", state="complete", expanded=False)
                                
                                st.write("")
                                st.markdown("### Margin Burndown Forecast")
                                st.caption("This chart tracks 'Remaining Cash' over 'Days in Development'. If a line drops below the white zero-line, the agency is actively losing money on the project.")
                                
                                # Render the visual! Streamlit maps colors to dataframe columns in order.
                                # Colors: Red (Worst), Blue (Expected), Green (Best), Gray (Zero Line)
                                st.line_chart(mc_df, color=["#ef4444", "#3b82f6", "#22c55e", "#d1d5db"], height=400)
                                
                                st.divider()
                                st.markdown("#### Executive Risk Analysis")
                                
                                col_r1, col_r2, col_r3 = st.columns(3)
                                with col_r1:
                                    risk_color = "normal" if prob_loss < 20 else "inverse"
                                    st.metric("Probability of Net Loss", f"{prob_loss:.1f}%", delta_color=risk_color)
                                    
                                with col_r2:
                                    if exp_cross:
                                        st.error(f"**Expected Bankruptcy:** Day {exp_cross}")
                                        st.caption("Statistically, the most likely path wipes out the margin on this day.")
                                    else:
                                        st.success("**Expected Bankruptcy:** None")
                                        st.caption("The median simulation finishes profitably.")
                                        
                                with col_r3:
                                    if worst_cross:
                                        st.warning(f"**Worst Case Bankruptcy:** Day {worst_cross}")
                                        st.caption("The 10th percentile disaster scenario wipes out margin here.")
                                    else:
                                        st.success("**Worst Case Bankruptcy:** None")
                                        st.caption("Even disaster scenarios remain profitable.")
                                        
                            except Exception as e:
                                status.update(label="Simulation Failed", state="error", expanded=True)
                                st.error(f"Mathematical Error: {str(e)}")
