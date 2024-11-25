import yaml
from collections import defaultdict

# Load YAML data
with open('schedule.yaml', 'r') as file:
    data = yaml.safe_load(file)

def parse_time_slots(data):
    return [(slot['day'], slot['time']) for slot in data['schedule']['time_slots']]

def parse_subjects(data):
    return {subject['name']: subject['hours'] for subject in data['schedule']['subjects']}

def parse_groups(data):
    groups = {}
    for group in data['schedule']['groups']:
        name = group['name']
        capacity = group['capacity']
        subject_names = group['subject_names']
        groups[name] = {'capacity': capacity, 'subjects': subject_names}
    return groups

def parse_lecturers(data):
    lecturers = defaultdict(list)
    for lecturer in data['schedule']['lecturers']:
        name = lecturer['name']
        for subject in lecturer['can_teach_subjects']:
            lecturers[subject].append(name)
    return lecturers

def parse_halls(data):
    return {hall['name']: hall['capacity'] for hall in data['schedule']['halls']}

# Parsing data from YAML
time_slots = parse_time_slots(data)
subjects = parse_subjects(data)
groups = parse_groups(data)
lecturers = parse_lecturers(data)
halls = parse_halls(data)

# Generate variables
variables = []
for group_name, group_info in groups.items():
    for subject_name in group_info['subjects']:
        hours = subjects[subject_name]
        for i in range(hours):  # Add variables for each hour of the subject
            variables.append((group_name, subject_name, i))

# Domain definitions
domains = {
    (group_name, subject_name, idx): [
        (day, time, hall, lecturer)
        for day, time in time_slots
        for hall, hall_capacity in halls.items() if hall_capacity >= groups[group_name]['capacity']
        for lecturer in lecturers.get(subject_name, [])
    ]
    for group_name, group_info in groups.items()
    for subject_name in group_info['subjects']
    for idx in range(subjects[subject_name])
}

# Constraints
def constraints(var1, val1, var2, val2):
    if var1 == var2 and val1 == val2:
        return True

    group1, subject1, idx1 = var1
    group2, subject2, idx2 = var2
    day1, time1, hall1, lecturer1 = val1
    day2, time2, hall2, lecturer2 = val2

    if day1 != day2 or time1 != time2:
        return True

    if hall1 == hall2 and day1 == day2 and time1 == time2:
        total_capacity = halls[hall1]
        total_students = groups[group1]['capacity'] + groups[group2]['capacity']
        if total_students <= total_capacity:
            return True

    if lecturer1 == lecturer2 and day1 == day2 and time1 == time2:
        return False

    return True

def is_consistent(assignment, variable, value, constraints):
    for other_variable, other_value in assignment.items():
        if not constraints(variable, value, other_variable, other_value):
            return False
    return True

def backtracking(variables, domains, constraints, assignment={}):
    if len(assignment) == len(variables):
        return assignment

    unassigned = [v for v in variables if v not in assignment]
    variable = min(unassigned, key=lambda var: len(domains[var]))

    for value in domains[variable]:
        if is_consistent(assignment, variable, value, constraints):
            assignment[variable] = value
            result = backtracking(variables, domains, constraints, assignment)
            if result:
                return result
            del assignment[variable]

    return None

# Find solution
assignment = backtracking(variables, domains, constraints)

if assignment:
    sorted_schedule = sorted(
        ((group, subject, idx, day, time, hall, lecturer) for (group, subject, idx), (day, time, hall, lecturer) in assignment.items()),
        key=lambda x: (x[3], x[4])
    )
    print("\nSchedule:")
    for group, subject, idx, day, time, hall, lecturer in sorted_schedule:
        print(f"Group: {group}, Subject: {subject}, Lesson {idx}, Day: {day}, Time: {time}, Hall: {hall}, Lecturer: {lecturer}")
else:
    print("No solution found.")
