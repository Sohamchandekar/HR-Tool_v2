import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import csv

from functions.biometric_functions import (create_employee_dict,
                                           pasting_date,
                                           update_weekdays,
                                           holiday_calculation,
                                           daily_working_hours_calculation,
                                           calculate_absentees,
                                           calculating_half_day,
                                           calculate_absolute_overtime,
                                           calculate_payable_overtime,
                                           saturday_compoff,
                                           calculate_latemark,
                                           calculating_workingsundays,
                                           calculate_metric,
                                           calculate_adjustment,
                                           half_day_map,
                                           early_leave, finalAdjustment)

from functions.hrone_functions import (process_employee_hroneData,
                                       dict_cleaning_hrone,
                                       update_weekdays_hrone,
                                       matching_mechanism)

from functions.dsahboard_functions import generate_working_hours_card

app = Flask(__name__)
app.secret_key = '123'  # Set a secret key for session management

# Configuring upload folder
UPLOAD_FOLDER = os.path.join('static', 'resources', 'uploads')
BIOMETRICPATH= os.path.join('static', 'resources', 'uploads','biometric_data.xlsx')
HRONEPATH = os.path.join('static', 'resources', 'uploads', 'hr_one_data.xlsx')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'xls', 'xlsx', 'csv'}

CREDENTIALS_FILE = os.path.join('static', 'resources', 'user_credentials', 'login_credential.csv')


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to validate user credentials
def validate_credentials(user_id, password):
    try:
        with open(CREDENTIALS_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['user_id'] == user_id and row['password'] == password:
                    return row['access'], row['name']
    except Exception as e:
        print(f"Error reading credentials file: {e}")
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form.get('user_id')
    password = request.form.get('password')

    access, name = validate_credentials(user_id, password)
    if access:
        session['user_id'] = user_id  # Store user ID in session
        session['access'] = access      # Store access level in session
        session['name'] = name          # Store user name in session
        if access == 'admin':
            return redirect(url_for('admin'))
        elif access == 'user':
            return redirect(url_for('home'))
    else:
        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('index'))

################################ Home ##################################
employee_dict = {}
@app.route('/home')
def home():
    global report_html
    global employee_dict

    employee_dict = create_employee_dict(BIOMETRICPATH)
    employee_dict_hrone = process_employee_hroneData(HRONEPATH)

    employee_dict=pasting_date(employee_dict,month,year)
    employee_dict_hrone = dict_cleaning_hrone(employee_dict_hrone)

    employee_dict=update_weekdays(employee_dict)
    employee_dict_hrone = update_weekdays_hrone(employee_dict_hrone)

    employee_dict = matching_mechanism(employee_dict, employee_dict_hrone)

    employee_dict=holiday_calculation(employee_dict, holiday_dates)
    employee_dict=daily_working_hours_calculation(employee_dict)
    employee_dict=calculate_absentees(employee_dict)
    employee_dict=calculating_half_day(employee_dict)
    employee_dict=calculate_absolute_overtime(employee_dict)
    employee_dict=calculate_payable_overtime(employee_dict)
    employee_dict=saturday_compoff(employee_dict)
    employee_dict=calculate_latemark(employee_dict)
    employee_dict=calculating_workingsundays(employee_dict)
    employee_dict=calculate_metric(employee_dict)
    employee_dict = half_day_map(employee_dict)
    employee_dict = early_leave(employee_dict)
    employee_dict=calculate_adjustment(employee_dict)
    employee_dict = finalAdjustment(employee_dict)


    reportdataframe_data = {
        employee: data['generate_dataframe']
        for employee, data in employee_dict.items()
    }
    reportDataframe = pd.DataFrame.from_dict(reportdataframe_data, orient='index')
    reportDataframe.reset_index(inplace=True)
    reportDataframe.rename(columns={'index': 'Employee'}, inplace=True)
    reportDataframe.rename(columns={
        'OfficeWorkingDays': 'Office Working',
        'EmployeeTotalWorkingDay':'Employee Total Working',
        'PublicHolidays': 'Public Holiday',
        'EmployeeAverageWorkingHours': 'Employee Average Working',
        'EmployeeTotalWorkingHours': 'Employee Total Working',
        'EmployeeActualAbsentee': 'Physical Absentee',
        'EmployeeLateMarksTotal': 'Late Marks',
        'EmployeeAbsenteeWithLateMark': 'Employee Total Absentee',
        'CompOffTotal': 'Compensatory Off',
        'AbsoluteOverTime': 'Over Time',
        'PayableOverTime': 'Payable Over Time',
        'incompleteHours': 'Incomplete Hours',
        'HalfDayTotal': 'Total Half Days',
        'totalEarlyLeave': 'Total Early Leaves'
    },inplace=True)

    # Convert DataFrame to HTML
    report_html = reportDataframe.to_html(index=False)


    # Retrieve the user's name from the session
    user_name = session.get('name', 'User ')  # Default to 'User ' if not found
    return render_template('home.html', user_name=user_name)



@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    global employee_dict  # Ensure you're using the global variable
    employee_names = list(employee_dict.keys())  # Extract employee names

    employee_dict_dashboard = {}  # Initialize an empty dictionary for the selected employee
    total_working_hours = None  # Initialize variable for total working hours
    average_working_hours = None  # Initialize variable for average working hours

    if request.method == 'POST':
        selected_employee = request.form.get('selected_employee')  # Get the selected employee name
        if selected_employee in employee_dict:
            employee_dict_dashboard = employee_dict[selected_employee]  # Get the employee's data
            print(employee_dict_dashboard)  # Print the employee's data for debugging

            # Extract total and average working hours from the nested structure
            total_working_hours = employee_dict_dashboard.get('generate_dataframe', {}).get('EmployeeTotalWorkingHours',
                                                                                            'N/A')
            average_working_hours = employee_dict_dashboard.get('generate_dataframe', {}).get(
                'EmployeeAverageWorkingHours', 'N/A')

    return render_template('user_dashboard.html',
                           employee_names=employee_names,
                           employee_dict=employee_dict,
                           employee_dict_dashboard=employee_dict_dashboard,
                           total_working_hours=total_working_hours,
                           average_working_hours=average_working_hours)  # Pass both values to the template


@app.route('/user_report')
def user_report():

    return render_template('user_report.html',
                           report_html=report_html,
                           upload_month=month,
                           upload_year = year)

############################# ADMIN ################################
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global month
    global year
    global holiday_dates

    if request.method == 'POST':
        biometric_file = request.files.get('biometric_file')
        hrone_file = request.files.get('hrone_file')
        uploaded_files = []

        month = request.form.get('upload_month')
        year = request.form.get('upload_year')

        # Store month and year in session
        session['upload_month'] = month
        session['upload_year'] = year

        print(f"Uploaded Month: {session['upload_month']}, Uploaded Year: {session['upload_year']}")  # Debugging line

        holiday_string = request.form.get('holiday_string')

        # Convert the holiday string to a list
        import ast
        try:
            holidays = ast.literal_eval(holiday_string)  # Convert string to list
            holiday_dates = []

            for holiday in holidays:
                # Parse the original format
                original_date = holiday.strip()  # Remove any extra spaces
                # Split the date into components
                month_day_year = original_date.split(' ')
                month = month_day_year[0]  # Get the month
                day = month_day_year[1].rstrip(',')  # Get the day and remove the comma
                year = month_day_year[2]  # Get the year

                # Reformat to desired format
                reformatted_date = f"{day} {month} {year}"
                holiday_dates.append(reformatted_date)

        except Exception as e:
            print(f"Error parsing holiday string: {e}")
            holiday_dates = []

        if biometric_file and allowed_file(biometric_file.filename):
            biometric_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'biometric_data.xlsx')
            biometric_file.save(biometric_file_path)
            uploaded_files.append('biometric_data.xlsx')

        if hrone_file and allowed_file(hrone_file.filename):
            hrone_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'hr_one_data.xlsx')
            hrone_file.save(hrone_file_path)
            uploaded_files.append('hr_one_data.xlsx')

        return render_template('upload_success.html', files=uploaded_files)

    return render_template('uploads.html')


@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        # Handle file uploads and processing logic
        return "Processing files..."
    return render_template('record_uploading.html')



@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)