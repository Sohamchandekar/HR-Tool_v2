import pandas as pd
from datetime import datetime, timedelta

def create_employee_dict(excel_file):
    # Read the CSV file
    df = pd.read_excel(excel_file, header=None)
    df = df.dropna(axis=1, how='all')

    # Initialize the dictionary to hold the final data
    employee_data = {}

    # Loop through the DataFrame by locating the employee name and then slicing the DataFrame
    i = 0
    while i < len(df):
        if pd.notna(df.iloc[i, 0]):  # Find employee name
            employee_name = df.iloc[i, 0]
            i += 1  # Move to the next row
            employee_dict = {
                'Days': list(df.iloc[i, 1:]),
                'Status': list(df.iloc[i+1, 1:]),
                'InTime': [str(x) if pd.notna(x) else 'NaT' for x in df.iloc[i+2, 1:]],
                'OutTime': [str(x) if pd.notna(x) else 'NaT' for x in df.iloc[i+3, 1:]]
            }
            # Store the employee's data in the dictionary
            employee_data[ employee_name] = employee_dict
            # Skip over the processed rows
            i += 8
        i += 1  # Continue to the next employee section

    return employee_data


def pasting_date(employee_dict, month, year):
    # Map month abbreviations to full month names
    month_map = {
        "Jan": "January",
        "Feb": "February",
        "Mar": "March",
        "Apr": "April",
        "May": "May",
        "Jun": "June",
        "Jul": "July",
        "Aug": "August",
        "Sep": "September",
        "Oct": "October",
        "Nov": "November",
        "Dec": "December"
    }

    # Get the full month name from the abbreviation
    full_month = month_map.get(month[:3], month)  # Use the first three letters for mapping

    for employee, data in employee_dict.items():
        days_list = data['Days']
        formatted_days = []

        for day in days_list:
            if isinstance(day, str) and len(day) > 0:
                day_num, day_abbr = day.split()
                day_num = int(day_num)
                # Map the day abbreviation to the full weekday name
                day_map = {
                    'M': 'Monday',
                    'T': 'Tuesday',
                    'W': 'Wednesday',
                    'Th': 'Thursday',
                    'F': 'Friday',
                    'St': 'Saturday',
                    'S': 'Sunday'
                }
                weekday = day_map.get(day_abbr, 'Unknown')
                formatted_days.append(f"{day_num} {full_month} {year}, {weekday}")

        # Update the employee's Days in the dictionary
        employee_dict[employee]['Days'] = formatted_days

    return employee_dict


def update_weekdays(employee_dict):
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


def holiday_calculation(employee_dict, holiday_dates):
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


def daily_working_hours_calculation(employee_dict):
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

def calculate_absentees(employee_dict):
    for employee, data in employee_dict.items():
        in_times = data['InTime']
        out_times = data['OutTime']
        status = data['Status']

        # Determine the length to iterate over (minimum length of the lists)
        length = min(len(in_times), len(out_times), len(status))

        for i in range(length):
            # Check if both InTime and OutTime are missing and status is not WO or HO
            if (in_times[i] == 'NaT' and out_times[i] == 'NaT') and status[
                i] not in ['WO', 'HO']:
                status[i] = 'A'  # Mark as Absent

        # Update the employee's Status in the dictionary
        employee_dict[employee]['Status'] = status
        employee_dict[employee]['totalAbsentDays'] = data['Status'].count('A')

    return employee_dict


def calculating_half_day(employee_dict):
    for employee, data in employee_dict.items():
        daily_working_hours = data['dailyWorkingHours']
        status = data['Status']

        for i in range(len(daily_working_hours)):
            # Check if daily working hours is not NaT and less than 6 hours
            if daily_working_hours[i] != 'NaT':
                hours, minutes = map(int, daily_working_hours[i].split(':'))
                total_hours = hours + minutes / 60  # Convert to decimal hours

                if total_hours < 6:
                    status[i] = 'P1/2'  # Mark as half day

        # Update the employee's Status in the dictionary
        employee_dict[employee]['Status'] = status

    return employee_dict


def calculate_absolute_overtime(employee_dict):
    for employee, data in employee_dict.items():
        daily_working_hours = data['dailyWorkingHours']

        # Initialize variables
        total_absolute_overtime_minutes = 0
        over_time_list = []

        for hours in daily_working_hours:
            if hours != 'NaT':  # Check if the hours are valid
                h, m = map(int, hours.split(':'))
                total_minutes = h * 60 + m  # Convert to total minutes

                # Calculate Overtime
                if total_minutes > 540:  # 540 minutes = 9 hours
                    overtime_minutes = total_minutes - 540
                    over_time = f"{overtime_minutes // 60:02}:{overtime_minutes % 60:02}"  # Format as HH:MM
                    over_time_list.append(over_time)
                    total_absolute_overtime_minutes += overtime_minutes  # Keep total in minutes
                else:
                    over_time_list.append("00:00")  # No overtime

        # Convert total absolute overtime from minutes to HH:MM format
        absolute_hours = total_absolute_overtime_minutes // 60
        absolute_minutes = total_absolute_overtime_minutes % 60
        data['AbsoluteOverTime'] = f"{absolute_hours:02}:{absolute_minutes:02}"

        # Store results in the employee's data
        data['OverTime'] = over_time_list

    return employee_dict


def calculate_payable_overtime(employee_dict):
    for employee, data in employee_dict.items():
        overtime_list = data['OverTime']

        # Initialize total payable overtime in minutes
        total_payable_minutes = 0

        # Iterate through the OverTime list
        for overtime in overtime_list:
            if overtime != "NaT" and overtime != "00:00":  # Check if the value is valid
                h, m = map(int, overtime.split(':'))
                total_overtime_minutes = h * 60 + m  # Convert to total minutes

                # Add to payable overtime if it exceeds 1 hour (60 minutes)
                if total_overtime_minutes > 60:
                    total_payable_minutes += total_overtime_minutes

        # Calculate PayableOverTime
        payable_minutes = total_payable_minutes

        # Convert back to HH:MM format
        if payable_minutes < 0:
            payable_minutes = 0  # Ensure it doesn't go negative

        payable_hours = payable_minutes // 60
        payable_remainder_minutes = payable_minutes % 60
        data['PayableOverTime'] = f"{payable_hours:02}:{payable_remainder_minutes:02}"

    return employee_dict


def saturday_compoff(employee_dict):
    """
    Function to calculate CompOffTotal and update employee's Saturday statuses based on attendance rules.

    Args:
        employee_dict (dict): Dictionary containing employee data.

    Returns:
        dict: Updated employee dictionary with CompOffTotal and modified Saturday statuses.
    """
    for employee, data in employee_dict.items():
        # Initialize variables
        comp_off_total = 0
        status_list = data['Status']  # List of statuses for each day of the month
        days_list = data['Days']  # List of corresponding days

        absent_saturdays = 0
        working_saturdays = 0  # Saturdays excluding holidays

        # Iterate over days to evaluate Saturdays
        for i in range(len(days_list)):
            if 'Saturday' in days_list[i]:  # Check if the day is a Saturday
                if status_list[i] == 'HO':
                    continue  # Skip public holidays
                working_saturdays += 1
                if status_list[i] == 'A':
                    absent_saturdays += 1
                if status_list[i] == 'P1/2':
                    absent_saturdays += 0.5

        # Add 1 to CompOffTotal only if all working Saturdays are attended
        if absent_saturdays == 0 and working_saturdays > 0:
            comp_off_total += 1

        if absent_saturdays == 0.5 and working_saturdays > 0:
            comp_off_total += 0.5

        # Handle absences based on the number of missed Saturdays
        if absent_saturdays == 1:
            # Change the status of the missed Saturday to "WOS"
            for i in range(len(status_list)):
                if 'Saturday' in days_list[i] and status_list[i] == 'A':
                    status_list[i] = 'WOS'
                    break
        elif absent_saturdays == 2:
            # Change one "A" to "WOS" and keep the other as "A"
            wos_found = False
            for i in range(len(status_list)):
                if 'Saturday' in days_list[i]:
                    if status_list[i] == 'A' and not wos_found:
                        status_list[i] = 'WOS'
                        wos_found = True
                    elif status_list[i] == 'A':
                        status_list[i] = 'A'  # Keep as absent
        elif absent_saturdays >= 3:
            # Change one "A" to "WOS" and leave the rest as "A"
            wos_found = False
            for i in range(len(status_list)):
                if 'Saturday' in days_list[i]:
                    if status_list[i] == 'A' and not wos_found:
                        status_list[i] = 'WOS'
                        wos_found = True
                    elif status_list[i] == 'A':
                        status_list[i] = 'A'  # Keep as absent

        # Update employee data
        data['CompOffTotal'] = comp_off_total
        data['Status'] = status_list

    return employee_dict


def calculate_latemark(employee_dict):
    for employee, data in employee_dict.items():
        in_time_list = data['InTime']  # Get the InTime list
        late_mark = []  # Initialize the lateMark list
        late_count = 0  # Counter for late marks

        # Initialize lateMarkAbsentee if not present
        if 'lateMarkAbsentee' not in data:
            data['lateMarkAbsentee'] = 0.0

        for in_time in in_time_list:
            if in_time and in_time != 'NaT':  # Check if the InTime is valid
                try:
                    hours, minutes = map(int, in_time.split(':'))
                    if (hours == 10 and minutes > 0) or (10 < hours < 12) or (hours == 12 and minutes == 0):
                        late_mark.append(1)  # Mark as late
                        late_count += 1
                    else:
                        late_mark.append(0)  # Not late
                except ValueError:
                    late_mark.append(0)  # Handle unexpected formats
            else:
                late_mark.append(0)  # Handle NaT cases

        # Calculate absentee days due to late marks
        data['lateMarkAbsentee'] += (late_count // 3) * 0.5

        # Store the lateMark in the employee's data
        data['lateMark'] = late_mark
        data['lateMarkCount'] = data['lateMark'].count(1)

    return employee_dict


def calculating_workingsundays(employee_dict):
    """
    This function calculates compensatory off based on working hours on Sundays.
    If an employee works less than 6 hours, they receive 0.5 CompOff.
    If they work 6 hours or more, they receive 1 CompOff.
    """

    six_hours = timedelta(hours=6)  # Convert 6 hours to timedelta

    def convert_to_timedelta(time_str):
        """Convert HH:MM formatted string to timedelta object."""
        try:
            h, m = map(int, time_str.split(':'))  # Split HH:MM format
            return timedelta(hours=h, minutes=m)
        except ValueError:
            print(f"Invalid time format: {time_str}")
            return timedelta(0)  # Default to 0 if invalid

    for emp_id, data in employee_dict.items():
        in_time_list = data.get('InTime', [])
        out_time_list = data.get('OutTime', [])
        working_hours_list = data.get('WorkingHours', [])

        for i in range(len(working_hours_list)):
            if in_time_list[i] != 'NaT' and out_time_list[i] != 'NaT':
                # Check if both InTime and OutTime are present

                working_hours = convert_to_timedelta(working_hours_list[i])  # Convert to timedelta

                if working_hours < six_hours:  # Compare with 6 hours
                    data['CompOffTotal'] += 0.5
                else:
                    data['CompOffTotal'] += 1

    return employee_dict

def calculate_metric(employee_dict):
    for employee, data in employee_dict.items():
        # Initialize the reportMetric dictionary
        report_metric = {
            "OfficeWorkingDays": 0,
            "EmployeeTotalWorkingDay": 0,
            "PublicHolidays": 0,
            "EmployeeAverageWorkingHours": "00:00",
            "EmployeeTotalWorkingHours": "00:00",
            "EmployeeActualAbsentee": 0
        }

        # Calculation 1: OfficeWorkingDays
        total_days = len(data['Days'])
        holidays = data['Status'].count('HO')
        sundays = sum(1 for day in data['Days'] if 'Sunday' in day)
        report_metric["OfficeWorkingDays"] = total_days - holidays - sundays - 1

        # Calculation 2: EmployeeTotalWorkingDay
        total_working_days = 0
        for status in data['Status']:
            if status == 'P':
                total_working_days += 1
            elif status == 'P1/2':
                total_working_days += 0.5
            elif status in ['WOP']:
                total_working_days += 1
            elif status in ['WOP1/2']:
                total_working_days += 0.5
        report_metric["EmployeeTotalWorkingDay"] = total_working_days

        # Calculation 3: PublicHolidays
        report_metric["PublicHolidays"] = holidays

        # Calculation 4: EmployeeAverageWorkingHours
        total_working_hours = timedelta()
        valid_days = 0
        for hours in data['dailyWorkingHours']:
            if hours != 'NaT':
                h, m = map(int, hours.split(':'))
                total_working_hours += timedelta(hours=h, minutes=m)
                valid_days += 1

        if valid_days > 0:
            avg_working_hours = total_working_hours / valid_days
            avg_hours, rem = divmod(avg_working_hours.total_seconds(), 3600)
            avg_minutes = rem // 60
            report_metric["EmployeeAverageWorkingHours"] = f"{int(avg_hours):02}:{int(avg_minutes):02}"

        # Calculation 5: EmployeeTotalWorkingHours
        total_hours, rem = divmod(total_working_hours.total_seconds(), 3600)
        total_minutes = rem // 60
        report_metric["EmployeeTotalWorkingHours"] = f"{int(total_hours):02}:{int(total_minutes):02}"

        # Calculation 6: EmployeeTotalAbsentee
        report_metric["EmployeeActualAbsentee"] = data['Status'].count('A')

        # Calculation 7: EmployeeTotalAbsentee including Late marks
        report_metric["EmployeeAbsenteeWithLateMark"] = data['Status'].count('A') + data['lateMarkAbsentee']

        # Add reportMetric to the employee's data
        data['reportMetric'] = report_metric

    return employee_dict

def half_day_map(employee_dict, half_day_threshold=6):
    for employee, data in employee_dict.items():
        daily_working_hours = data.get('dailyWorkingHours', [])
        half_day_mapping = []  # Initialize a list to store half day mappings

        for hours in daily_working_hours:
            if hours != 'NaT':
                # Convert hours to total hours in decimal
                h, m = map(int, hours.split(':'))
                total_hours = h + m / 60  # Convert to decimal hours

                # Map to 0 if less than threshold, else map to 1
                if total_hours < half_day_threshold:
                    half_day_mapping.append(1)  # Less than 6 hours
                else:
                    half_day_mapping.append(0)  # 6 hours or more
            else:
                half_day_mapping.append(0)  # Handle NaT cases as half day

        # Count the number of full days (1s in the mapping)
        half_day_count = half_day_mapping.count(1)

        # Update the employee's HalfDayMapping and HalfDayTotal in the dictionary
        employee_dict[employee]['HalfDayMapping'] = half_day_mapping
        employee_dict[employee]['HalfDayTotal'] = half_day_count  # Store the total number of full days

    return employee_dict


def early_leave(employee_dict, expected_work_hours=9):
    for employee, data in employee_dict.items():
        status = data.get('Status', [])
        in_time = data.get('InTime', [])
        out_time = data.get('OutTime', [])

        early_leave_map = []  # List to store early leave mappings
        early_leave_time = []  # List to store early leave times in HH:MM format
        total_early_leave = 0  # Counter for total early leaves
        total_incomplete_minutes = 0  # Counter for total early leave time in minutes

        for i in range(len(status)):
            if status[i] == 'P':  # Check if status is P
                if in_time[i] != 'NaT' and out_time[i] != 'NaT':
                    # Parse InTime and OutTime
                    in_h, in_m = map(int, in_time[i].split(':'))
                    out_h, out_m = map(int, out_time[i].split(':'))

                    # Adjust for midnight crossing
                    if out_h < in_h or (out_h == in_h and out_m < in_m):
                        out_h += 24

                    # Calculate total working hours
                    total_working_minutes = (out_h * 60 + out_m) - (in_h * 60 + in_m)
                    total_working_hours = total_working_minutes / 60  # Convert to hours

                    # Calculate early leave time
                    expected_working_minutes = expected_work_hours * 60
                    if total_working_minutes < expected_working_minutes:
                        early_leave_map.append(1)  # Mark as early leave
                        total_early_leave += 1  # Increment early leave count

                        # Calculate early leave time in minutes
                        early_minutes = expected_working_minutes - total_working_minutes
                        total_incomplete_minutes += early_minutes

                        # Convert early leave time to HH:MM format
                        early_h = early_minutes // 60
                        early_m = early_minutes % 60
                        early_leave_time.append(f"{early_h:02}:{early_m:02}")
                    else:
                        early_leave_map.append(0)  # Did not leave early
                        early_leave_time.append("00:00")
                else:
                    early_leave_map.append(0)  # Handle NaT cases as not early leave
                    early_leave_time.append("00:00")
            else:
                early_leave_map.append(0)  # Ignore other statuses
                early_leave_time.append("00:00")

        # Convert total incomplete minutes to HH:MM format
        incomplete_h = total_incomplete_minutes // 60
        incomplete_m = total_incomplete_minutes % 60
        incomplete_hours = f"{incomplete_h:02}:{incomplete_m:02}"

        # Update the employee's dictionary with new data
        employee_dict[employee]['earlyLeaveMap'] = early_leave_map
        employee_dict[employee]['earlyLeaveTime'] = early_leave_time
        employee_dict[employee]['totalEarlyLeave'] = total_early_leave
        employee_dict[employee]['incompleteHours'] = incomplete_hours

    return employee_dict


def calculate_adjustment(employee_dict):
    """
    Adjust the absentee data using the CompOffTotal and update other metrics.

    Args:
        employee_dict (dict): Dictionary containing employee details.

    Returns:
        dict: Updated employee dictionary.
    """
    def subtract_time(time1, time2):
        """
        Subtract two time durations in HH:MM format.

        Args:
            time1 (str): The first time duration (minuend) in HH:MM format.
            time2 (str): The second time duration (subtrahend) in HH:MM format.

        Returns:
            str: The resulting time duration in HH:MM format (capped at 0:00 if negative).
        """
        h1, m1 = map(int, time1.split(':'))
        h2, m2 = map(int, time2.split(':'))

        # Convert both times to minutes
        total_minutes1 = h1 * 60 + m1
        total_minutes2 = h2 * 60 + m2

        # Subtract minutes and ensure no negative value
        remaining_minutes = max(0, total_minutes1 - total_minutes2)

        # Convert back to HH:MM format
        remaining_h = remaining_minutes // 60
        remaining_m = remaining_minutes % 60

        return f"{remaining_h:02}:{remaining_m:02}"

    for employee, data in employee_dict.items():
        # Adjustment: Minimize absentee using CompOffTotal
        comp_off_days = data.get("CompOffTotal", 0)
        absentee_with_late_mark = data.get("reportMetric", {}).get("EmployeeAbsenteeWithLateMark", 0)

        if comp_off_days > 0 and absentee_with_late_mark > 0:
            adjusted_absentee = max(0, absentee_with_late_mark - comp_off_days)
            data["reportMetric"]["EmployeeAbsenteeWithLateMark"] = adjusted_absentee

            # Update CompOffTotal to reflect used days
            data["CompOffTotal"] = max(0, comp_off_days - (absentee_with_late_mark - adjusted_absentee))

        # Subtract incompleteHours from PayableOverTime
        incomplete_hours = data.get("incompleteHours", "0:00")
        absolute_overtime = data.get("AbsoluteOverTime", "0:00")
        updated_absolute_overtime = subtract_time(absolute_overtime, incomplete_hours)
        data["AbsoluteOverTime"] = updated_absolute_overtime

        # Generate 'generate_dataframe' key with selected metrics
        data["generate_dataframe"] = {
            "OfficeWorkingDays": data["reportMetric"].get("OfficeWorkingDays", 0),
            "EmployeeTotalWorkingDay": data["reportMetric"].get("EmployeeTotalWorkingDay", 0),
            "PublicHolidays": data["reportMetric"].get("PublicHolidays", 0),
            "EmployeeAverageWorkingHours": data["reportMetric"].get("EmployeeAverageWorkingHours", "0:00"),
            "EmployeeTotalWorkingHours": data["reportMetric"].get("EmployeeTotalWorkingHours", "0:00"),
            "EmployeeActualAbsentee": data["reportMetric"].get("EmployeeActualAbsentee", 0),
            "EmployeeLateMarkCount": data.get('lateMarkCount', 0),
            "EmployeeLateMarksTotal": data.get("lateMarkAbsentee", 0),
            "EmployeeAbsenteeWithLateMark": data["reportMetric"].get("EmployeeAbsenteeWithLateMark", 0),
            "CompOffTotal": data.get("CompOffTotal", 0),
            "AbsoluteOverTime": updated_absolute_overtime,
            "incompleteHours": incomplete_hours,  # Add incompleteHours
            "PayableOverTime": data.get("PayableOverTime", "0:00"),
            "HalfDayTotal": data.get("HalfDayTotal", 0),  # Add HalfDayTotal
            "totalEarlyLeave": data.get("totalEarlyLeave", 0),  # Add totalEarlyLeave
        }

    return employee_dict


def finalAdjustment(employee_dict):
    for employee, data in employee_dict.items():
        office_working_days = data['generate_dataframe']['OfficeWorkingDays']
        employee_total_working_day = data['generate_dataframe']['EmployeeTotalWorkingDay']

        # Check if EmployeeTotalWorkingDay is greater than OfficeWorkingDays
        if employee_total_working_day > office_working_days:
            # Calculate the difference
            difference = employee_total_working_day - office_working_days

            # Update CompOffTotal
            data['generate_dataframe']['CompOffTotal'] += difference
            data['generate_dataframe']['EmployeeTotalWorkingDay'] -= difference

    return employee_dict

