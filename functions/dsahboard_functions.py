def generate_working_hours_card(employee_dict_dashboard):
    total_working_hours = employee_dict_dashboard.get("EmployeeTotalWorkingHours", "N/A")

    card_html = f"""
    <div class="card">
        <h3>Working Hours</h3>
        <p>{total_working_hours}</p>
    </div>
    """
    return card_html