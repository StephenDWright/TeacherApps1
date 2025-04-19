import streamlit as st
from datetime import datetime
import math
from PIL import Image

# --- TW Solutions Logo and Branding Header ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image("tw_logo.png", width=800)
with col2:
    st.markdown("#### TW Solutions  \n*Empowering Educators with Insightful Tools*")

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

# --- Tabs ---
tabs = st.tabs(["Salary Step Checker", "Retirement Calculator"])

# --- Tab 1: Salary Step Checker ---
with tabs[0]:
    st.title("Teacher Salary Scale Checker")
    st.markdown("""
    Enter your information below. Click **Check Salary Step** to calculate your correct placement on the salary scale and compare it with your current salary.
    """)

    start_date = st.date_input("Date of Entry into the Teaching Service", value=datetime(2010, 9, 1), min_value=datetime(1985, 1, 1), max_value=datetime(2030, 12, 31))
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
        upgrade_date = st.date_input("Date of Upgrade", value=datetime(2015, 9, 1), min_value=datetime(1985, 1, 1), max_value=datetime(2030, 12, 31))
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
            scale = old_salary_scales.get(grade_key, {}) if show_old_scale else salary_scales.get(grade_key, {})
            expected_salary = scale.get(current_step)
            scale_label = "previous salary scale" if show_old_scale else "current salary scale"

            if expected_salary:
                st.success(f"Based on your service history, your expected placement is **{current_step}** under the **{scale_label}**, with an estimated salary of **${expected_salary:,.2f}**.")
                st.info(f"Years in Grade {current_grade}: {years_in_current_grade}")

                if entered_salary:
                    discrepancy = expected_salary - entered_salary
                    if discrepancy == 0:
                        st.success("Your salary matches the expected amount.")
                    elif discrepancy > 0:
                        st.warning(f"You may be underpaid by **${discrepancy:,.2f}**.")
                    else:
                        st.info(f"You may be overpaid by **${-discrepancy:,.2f}**.")
            else:
                st.error(f"No salary data available for {current_step} in Grade {current_grade}.")

    if st.button("Reset"):
        st.session_state.clear()

    st.markdown("""
    ---
    📅 **Salary Scale Reference:** Reflects adjustments from **October 1, 2023** to **September 30, 2026**, including the **$255 Cost of Living Allowance (COLA)**.
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
        key = (years_service, months_service)
        pension_percent = pension_table.get(key)

        if pension_percent is None:
            st.error("Pension percentage for this exact service time is not in the table.")
        else:
            monthly_pension = final_salary * (pension_percent / 100)
            annual_pension = monthly_pension * 12
            gratuity = monthly_pension * 50

            st.success(f"**Monthly Pension:** ${monthly_pension:,.2f}")
            st.info(f"**Annual Pension:** ${annual_pension:,.2f}")
            st.success(f"**Gratuity (Lump Sum):** ${gratuity:,.2f}")


st.markdown("""
---
<div style='text-align: center;'>Built with ❤️ by <strong>TW Solutions</strong></div>
""", unsafe_allow_html=True)
