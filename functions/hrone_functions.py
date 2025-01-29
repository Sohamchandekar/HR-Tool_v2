import pandas as pd
from datetime import datetime, timedelta

def process_employee_hroneData(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Extract the columns with date data (adjust month filtering as needed)
    date_columns = [col for col in df.columns if 'Aug' in col or 'Jul' in col or 'Sep' in col or 'Jan' in col
                    or 'Feb' in col or 'Mar' in col or 'Apr' in col or 'May' in col or 'Jun' in col or 'Oct' in col
                    or 'Nov' in col or 'Dec' in col]

    # Initialize the employee dictionary
    employee_dict = {}

    # Loop through each employee
    for idx, row in df.iterrows():
        employee_name = row['Full name']  # Assuming 'Full name' is the column for employee names
        employee_dict[employee_name] = {"Days": [], "Status": [], "InTime": [], "OutTime": []}

        # Process each date column
        for date in date_columns:
            shift_data = str(row[date])  # Get the shift data for that day

            if '|' in shift_data:
                # Split the shift data by '|' and extract InTime and OutTime
                shift_parts = shift_data.split('|')

                # Handle InTime and OutTime: if '--:--', return NaT
                in_time = shift_parts[2].strip() if len(shift_parts) > 2 and shift_parts[
                    2].strip() != '--:--' else 'NaT'
                out_time = shift_parts[3].strip() if len(shift_parts) > 3 and shift_parts[
                    3].strip() != '--:--' else 'NaT'
            else:
                # If the data is missing or not properly formatted
                in_time, out_time = 'NaT', 'NaT'

            # Append the date, InTime, and OutTime to the employee's dictionary
            employee_dict[employee_name]["Days"].append(date)
            employee_dict[employee_name]["InTime"].append(in_time)
            employee_dict[employee_name]["OutTime"].append(out_time)
            employee_dict[employee_name]["Status"].append('')  # Status remains empty for now

    return employee_dict


def dict_cleaning_hrone(employee_dict):
    # Loop through each employee in the dictionary
    for employee, data in employee_dict.items():
        # Extract the list of days and their corresponding statuses
        days = data['Days']
        status = data['Status']

        # Loop through the days to find Sundays and update the status
        for i, day in enumerate(days):
            # Convert the string day to a datetime object
            date_object = pd.to_datetime(day, format="%d %b %Y")
            # Get the day of the week
            day_of_week = date_object.day_name()  # e.g., 'Monday'
            # Format the date to '1 July 2024, Day'
            formatted_day = f"{date_object.day} {date_object.strftime('%B %Y')}, {day_of_week}"
            # Update the Days with the formatted date
            days[i] = formatted_day
            # Check if the day is a Sunday and update the status accordingly
            if day_of_week == 'Sunday':
                status[i] = 'WO'  # Update status to 'WO' for Sundays

        # Update the employee's data with the modified lists
        data['Days'] = days
        data['Status'] = status

    # Return the updated employee dictionary
    return employee_dict


def update_weekdays_hrone(employee_dict):
    # Map the full weekday names to their corresponding abbreviations
    day_map = {
        'Monday': 'M',
        'Tuesday': 'T',
        'Wednesday': 'W',
        'Thursday': 'Th',
        'Friday': 'F',
        'Saturday': 'St',
        'Sunday': 'S'
    }

    for employee, data in employee_dict.items():
        days_list = data['Days']
        status_list = []

        for day in days_list:
            # Extract the weekday from the day string
            day_parts = day.split(', ')
            day_date = day_parts[0]  # e.g., '1 July 2024'
            weekday = day_parts[1]  # e.g., 'Monday'

            # Update status based on the weekday
            if weekday == 'Sunday':
                status_list.append('WO')
            else:
                status_list.append('P')

        # Update the employee's Status in the dictionary
        employee_dict[employee]['Status'] = status_list

    return employee_dict


def daily_working_hours_calculation_hrone(employee_dict):
    for employee, data in employee_dict.items():
        in_times = data['InTime']
        out_times = data['OutTime']
        daily_working_hours = []

        for in_time, out_time in zip(in_times, out_times):
            if in_time != 'NaT' and out_time != 'NaT':
                # Function to parse time strings
                def parse_time(time_str):
                    if ' ' in time_str:  # Check if it's a full datetime string
                        time_str = time_str.split(' ')[1]  # Get the time part
                    return datetime.strptime(time_str, '%H:%M') if len(time_str) == 5 else datetime.strptime(time_str,
                                                                                                             '%H:%M:%S')

                try:
                    in_time_dt = parse_time(in_time)
                    out_time_dt = parse_time(out_time)

                    # Calculate the difference in time
                    working_duration = out_time_dt - in_time_dt

                    # Handle cases where the out time is on the next day
                    if working_duration < timedelta(0):
                        working_duration += timedelta(days=1)

                    # Convert duration to HH:MM format
                    hours, remainder = divmod(working_duration.total_seconds(), 3600)
                    minutes = remainder // 60
                    daily_working_hours.append(f"{int(hours):02}:{int(minutes):02}")
                except ValueError:
                    daily_working_hours.append("NaT")  # Append "NaT" if parsing fails
            else:
                daily_working_hours.append("NaT")  # Append "NaT" if in_time or out_time is 'NaT'

        # Update the employee's dailyWorkingHours in the dictionary
        employee_dict[employee]['dailyWorkingHours'] = daily_working_hours

    return employee_dict


def holiday_calculation_hrone(employee_dict, holiday_dates):
    # Convert holiday_dates to a set for faster lookup
    holiday_set = set(holiday_dates)

    for employee, data in employee_dict.items():
        days = data['Days']
        status = data['Status']

        for i, day in enumerate(days):
            # Extract the date part from the day string
            date_str = day.split(',')[0]  # Get the date part (e.g., '1 July 2024')
            if date_str in holiday_set:
                status[i] = 'HO'  # Mark as holiday

        # Update the employee's Status in the dictionary
        employee_dict[employee]['Status'] = status

    return employee_dict


def matching_mechanism(employee_dict, employee_dict_hrone):
    for employee, biometric_data in employee_dict.items():
        in_time = biometric_data['InTime']
        out_time = biometric_data['OutTime']

        # Check if InTime or OutTime is 'NaT'
        if 'NaT' in in_time or 'NaT' in out_time:
            if employee in employee_dict_hrone:
                hr_data = employee_dict_hrone[employee]

                # Update InTime if it's 'NaT' and HR has a valid InTime
                for i in range(len(in_time)):
                    if in_time[i] == 'NaT' and hr_data['InTime'][i] != 'NaT':
                        biometric_data['InTime'][i] = hr_data['InTime'][i]

                # Update OutTime if it's 'NaT' and HR has a valid OutTime
                for i in range(len(out_time)):
                    if out_time[i] == 'NaT' and hr_data['OutTime'][i] != 'NaT':
                        biometric_data['OutTime'][i] = hr_data['OutTime'][i]



    # Remove employees from HR data who have been matched
    for employee in list(employee_dict_hrone.keys()):
        if employee in employee_dict:
            del employee_dict_hrone[employee]

    # Append remaining employees from HR data to biometric dictionary
    for employee, hr_data in employee_dict_hrone.items():
        if employee not in employee_dict:
            employee_dict[employee] = hr_data

    return employee_dict