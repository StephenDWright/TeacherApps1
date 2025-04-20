import streamlit as st
from datetime import datetime
import math
from PIL import Image

st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #b2c8b2;  /* Sage green */
    color: black;
    font-weight: 600;
    border-radius: 6px;
    padding: 0.5em 1.2em;
    transition: all 0.2s ease-in-out;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    border: 2px solid transparent;
}
div.stButton > button:first-child:hover {
    background-color: #a0b89a;
    transform: scale(1.03);
    border: 2px solid #ffe066; /* Yellow outline */
}
</style>
""", unsafe_allow_html=True)

# --- Salary Scales (Current and Placeholder for Previous) ---
import json

with open("salary_scales.json", "r") as f:
    salary_scales = json.load(f)

with open("old_salary_scales.json", "r") as f:
    old_salary_scales = json.load(f)

# Full pension percentage lookup table (10 years 0 months to 33 years 11 months)
pension_table = {
    (y, m): round(15 + ((y - 10) * 1.5 + m * (1.5 / 12)), 3) for y in range(10, 34) for m in range(0, 12)
}

step_labels = [
    "Minimum", "A", "B", "C", "D", "E", "F", "G",
    "1st Longevity", "2nd Longevity", "3rd Longevity",
    "4th Longevity", "5th Longevity"
]

def compute_service_years(start: datetime, reference: datetime) -> int:
    start_year = start.year
    if start.month < 9:
        start_year -= 1

    ref_year = reference.year
    if reference.month < 9:
        ref_year -= 1

    return ref_year - start_year


def calculate_step_placement(start_date, upgrade_date, was_upgraded, current_grade):
    today = datetime.today().date()
    effective_start = upgrade_date if was_upgraded else start_date
    years_in_current_grade = compute_service_years(effective_start, today)

    if years_in_current_grade == 0:
        step_index = 0
    elif years_in_current_grade <= 7:
        step_index = years_in_current_grade
    else:
        longevity_years = years_in_current_grade - 7
        longevity_steps = longevity_years // 2
        step_index = 7 + longevity_steps

    grade_key = str(current_grade)
    available_steps = list(salary_scales[grade_key].keys())
    max_valid_index = max(step_labels.index(step) for step in available_steps if step in step_labels)
    step_index = min(step_index, max_valid_index)

    current_step = step_labels[step_index]
    return step_index, current_step, years_in_current_grade

def calculate_pension_benefits(final_salary, years_service, months_service):
    key = (years_service, months_service)
    pension_percent = pension_table.get(key)

    if pension_percent is None:
        return None, None, None, None

    monthly_pension = final_salary * (pension_percent / 100)
    annual_pension = monthly_pension * 12
    gratuity = monthly_pension * 50

    return pension_percent, monthly_pension, annual_pension, gratuity

if "started" not in st.session_state:
    col1, col2 = st.columns([1, 4])
    with col1:
        try:
            st.image("tw_logo.png", width=150)
        except:
            pass
    with col2:
        st.markdown("#### TW Solutions Empowering Educators with Insightful Tools")

    st.title("TW Solutions – Teacher Salary Tool")
    st.markdown("""
    Welcome to your personalized salary and pension estimator for educators.

    🔍 **What you can do with this app:**
    - Estimate your correct salary step based on years of service
    - Compare it with your current salary
    - Calculate your expected pension and gratuity upon retirement

    This tool reflects the **2023–2026 salary updates**, including the $255 COLA.

    ---
    """)
    if st.button("Start Now"):
        st.session_state.started = True
        st.rerun()
    st.stop()

# --- Tabs ---
tabs = st.tabs(["Salary Step Checker", "Retirement Calculator"])

# --- Tab 1: Salary Step Checker ---
with tabs[0]:
    st.title("Teacher Salary Scale Checker")
    st.markdown("""
    Enter your information below. Click **Check Salary Step** to calculate your correct placement on the salary scale and compare it with your current salary.
    """)

    start_date = st.date_input("Date of Entry into the Teaching Service", value=datetime(2010, 9, 1), min_value=datetime(1985, 1, 1), max_value=datetime(2030, 12, 31), key="start_date")
    with st.expander("ℹ️ What do these grades mean?", expanded=False):
        st.markdown("""
        - **Grade 2** — Assistant Teacher Primary (ATP)  
        - **Grade 3** — Teacher I (Primary) or Teacher II (Secondary)  
        - **Grade 4** — Teacher III (Secondary)  
        - **Grade 5** — Dean or Head of Department (HOD)
        """)

    entry_grade = st.selectbox(
        "Grade at Entry",
        [2, 3, 4, 5],
        help="Grade 2: ATP | Grade 3: T1 (Primary)/T2 (Secondary) | Grade 4: T3 | Grade 5: Dean/HOD"
    )

    was_upgraded = st.checkbox("Were you upgraded to another grade?")
    upgrade_date = None
    current_grade = entry_grade
    if was_upgraded:
        upgrade_date = st.date_input("Date of Upgrade", value=datetime(2015, 9, 1), min_value=datetime(1985, 1, 1), max_value=datetime(2030, 12, 31), key="upgrade_date")
        current_grade = st.selectbox(
            "Current Grade",
            [2, 3, 4, 5],
            index=[2, 3, 4, 5].index(entry_grade),
            help="Grade 2: ATP | Grade 3: T1 (Primary)/T2 (Secondary) | Grade 4: T3 | Grade 5: Dean/HOD"
        )

    entered_salary = st.number_input("Your Current Salary (Optional)", min_value=0, value=0)

    show_old_scale = st.checkbox("Show salary using previous (pre-2023) rates")

    if st.button("Check Salary Step"):
        with st.spinner("Calculating your salary step..."):
            step_index, current_step, years_in_current_grade = calculate_step_placement(
                start_date, upgrade_date, was_upgraded, current_grade
            )

            grade_key = str(current_grade)
            scale = old_salary_scales.get(grade_key, {}) if show_old_scale else salary_scales.get(grade_key, {})
            expected_salary = scale.get(current_step)
            scale_label = "previous salary scale" if show_old_scale else "current salary scale"

            st.session_state.salary_result = {
                "step_index": step_index,
                "current_step": current_step,
                "years_in_current_grade": years_in_current_grade,
                "expected_salary": expected_salary,
                "scale_label": scale_label,
                "scale": scale,
                "grade_key": grade_key,
                "entered_salary": entered_salary,
                "current_grade": current_grade
            }

    if "salary_result" in st.session_state:
        r = st.session_state.salary_result
        if r["expected_salary"]:
            st.success(f"Based on your service history, your expected placement is **{r['current_step']}** under the **{r['scale_label']}**, with an estimated salary of **${r['expected_salary']:,.2f}**.")
            st.info(f"Years in Grade {r['current_grade']}: {r['years_in_current_grade']}")

            

            if r["entered_salary"]:
                discrepancy = r["expected_salary"] - r["entered_salary"]
                if discrepancy == 0:
                    st.success("Your salary matches the expected amount.")
                elif discrepancy > 0:
                    st.warning(f"You may be underpaid by **${discrepancy:,.2f}**.")
                else:
                    st.info(f"You may be overpaid by **${-discrepancy:,.2f}**.")
        else:
            st.error(f"No salary data available for {r['current_step']} in Grade {r['current_grade']}.")

    if st.button("Reset"):
        st.session_state.clear()

    st.markdown("""
    ---
    📅 **Salary Scale Reference:** Reflects adjustments from **October 1, 2020** to **September 30, 2023**, including the **$255 Cost of Living Allowance (COLA)**.
    """)

# --- Tab 2: Retirement Calculator ---
with tabs[1]:
    st.title("Retirement Benefits Calculator")
    st.markdown("""
    Enter your final monthly salary and total years + months of service. The calculator will return your monthly pension and gratuity.
    """)

    final_salary = st.number_input("Final Monthly Salary", min_value=0.0, step=100.0)
    years_service = st.selectbox("Years of Service", list(range(10, 34)))
    months_service = st.selectbox("Additional Months of Service", list(range(0, 12)))

    if st.button("Calculate Pension and Gratuity"):
        pension_percent, monthly_pension, annual_pension, gratuity = calculate_pension_benefits(final_salary, years_service, months_service)

        if pension_percent is None:
            st.error("Pension percentage for this exact service time is not in the table.")
        else:
            st.success(f"**Monthly Pension:** ${monthly_pension:,.2f}")
            st.info(f"**Annual Pension:** ${annual_pension:,.2f}")
            st.success(f"**Gratuity (Lump Sum):** ${gratuity:,.2f}")

    st.markdown("""
    🔎 *Each grade has its own salary scale. You receive annual increments within a grade, and biennial increments once you reach longevity steps.*

    Keep in mind that your actual grade depends on your position and appointment from the Teaching Service Commission.
    """)

st.markdown("""
---
<div style='text-align: center;'>Built with ❤️ by <strong>TW Solutions</strong></div>
""", unsafe_allow_html=True)
