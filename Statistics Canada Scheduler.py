#################################################################################
## Libraries
#################################################################################

import pandas as pd 
import numpy as np
from datetime import date, timedelta
import datetime
import holidays

#################################################################################
## CONSTANTS AND VARIABLES
#################################################################################

TASK_FILENAME = "task_listt.csv"

SCHEDULE_FILENAME = "Schedule Case 1 Aug 13 v2.xlsx"


# Reads in the task dependencies
tasks = pd.read_csv(TASK_FILENAME)

# Reads in the schedule dependencies
schedule = pd.read_excel(SCHEDULE_FILENAME)

# Convert column "Task ID" to list format to make use of list capabilities
id_list = tasks['Task ID'].to_list()

# Defining list to hold True or False for validity (will later become a column called "valid" in schedule)
schedule['Valid'] = ""

canadian_holidays = holidays.Canada()

#################################################################################
## FUNCTIONS
#################################################################################a

def getBusDaysInBetween(startDate, endDate):
	count = 0
	delta = endDate - startDate      
	for i in range(delta.days + 1):
	    day = startDate + timedelta(days=i)
	    if (day not in canadian_holidays and not(day.weekday() == 5) and not(day.weekday() == 6)):
	    	count += 1
	return count

def getBusDaysBeforeAfter(date, numDays, BA):
	if BA == "After":
		day_count = 0
		busday_count = 0
		while not(busday_count == numDays + 1):
			day = date + timedelta(days=day_count)
			if (day not in canadian_holidays and not(day.weekday() == 5) and not(day.weekday() == 6)):
				busday_count += 1
			day_count += 1

	if BA == "Before":
		day_count = 0
		busday_count = 0
		numDays = -1 * numDays
		while not(busday_count == numDays + 1):
			day = date - timedelta(days=day_count)
			if (day not in canadian_holidays and not(day.weekday() == 5) and not(day.weekday() == 6)):
				busday_count += 1
			day_count += 1
	return day


def scheduleSpecificationsStartEnd(id, startEnd, startEndDate, task_index, setdate):
	tasks.startEndColumn = ('(%s Date) Specified Task' %startEnd)
	tasks.startEndNumDays = ('(%s Date) Num Days' %startEnd)
	schedule.predStartEndColumn = ('Task Planned %s Date' %startEndDate)

	pred_index = schedule[schedule['Task ID']==tasks[tasks.startEndColumn][task_index]].index.values.astype(int)[0]
	offset = tasks[tasks.startEndNumDays][task_index]
	setdate = setdate.date()
	print("offset:", offset)
	print("setdate:", setdate)
	#print(schedule[schedule.predStartEndColumn][pred_index])

	if offset > 0:
		date = getBusDaysBeforeAfter(schedule[schedule.predStartEndColumn][pred_index].date(), offset, "After")
	elif offset < 0:
		date = getBusDaysBeforeAfter(schedule[schedule.predStartEndColumn][pred_index].date(), offset, "Before")
	else:
		date = schedule[schedule.predStartEndColumn][pred_index].date()
	#date = getBusDaysBeforeAfter(date, 1, "After")
	print("date:", date)
	if not(setdate == date):
		print("Task ID %d: The schedule specifications do not match your %s date" %(id, startEnd))
		return False
	else:
		return True


def validscheduleSpecifications(id, startDate, endDate):
	task_index = tasks[tasks['Task ID']==id].index.values.astype(int)[0]

	if not(pd.isnull(tasks['(Start Date) Specified Task'].iloc[task_index])):

		if not(tasks['(Start Date) Specified Task'][task_index] in schedule['Task ID'].tolist()):
			print("Task ID %d: The specified dependent task %d does not exist in the schedule" %(id, tasks['(Start Date) Specified Task'][task_index]))
			return False

		if not(scheduleSpecificationsStartEnd(id, "Start", tasks['(Start Date) Start or End'][task_index], task_index, startDate)):
			return False

	if not(pd.isnull(tasks['(End Date) Specified Task'].iloc[task_index])):

		if not(tasks['(End Date) Specified Task'][task_index] in schedule['Task ID'].tolist()):
			print("Task ID %d: The specified dependent task %s does not exist in the schedule" %(id, tasks['(End Date) Specified Task'][task_index]))
			return False

		if not(scheduleSpecificationsStartEnd(id, "End", tasks['(End Date) Start or End'][task_index], task_index, endDate)):
			return False
	return True


def idExist(id): 
	id_list = tasks['Task ID'].to_list()
	return (id in id_list)


def validDuration(id, startDate, endDate):
	task_index = tasks[tasks['Task ID']==id].index.values.astype(int)[0]
	task_duration_min = tasks['Min'][task_index]
	task_duration_max = tasks['Max'][task_index]
	# Checks to see if the duration of the task is within Min and Max bounds
	duration = getBusDaysInBetween(startDate.date(), endDate.date()) #delete this later
	if ((duration < task_duration_min) or (duration > task_duration_max)):
		print("Task ID %d: The task duration does not fit within the required bounds" %id)
		return False
	return True


def validAndPredecessors(id, startDate):
	task_index = tasks[tasks['Task ID']==id].index.values.astype(int)[0]
	and_list = list(map(int, tasks['And'][task_index]))

	if not(len(and_list) == 0):
		for i in range(len(and_list)):
			# Check to see if predecessor task exists in task['Task ID']
			if (and_list[i] not in tasks['Task ID'].tolist()):
				print("Task ID %d: The predecessor task %d does not exist" %(id, and_list[i]))
				return False
			# Check to see if predecessor task exists in schedule['Task ID']
			if (and_list[i] not in schedule['Task ID'].tolist()):
				print("Task ID %d: The predecessor task %d has not been completed yet" %(id, and_list[i]))
				return False
			# Finds the index where the predecessor task was found in "schedule"
			pred_index = schedule[schedule['Task ID']==and_list[i]].index.values.astype(int)[0]
			# Checks to see if the end date of the predecessor task is before the start date of the task we're looking at
			if (schedule['Task Planned Start Date'][pred_index] > startDate): #***check this!**
				print("Task ID %d: The predecessor task %d has not been completed yet" %(id, and_list[i]))
				return False
	return True


def validOrPredecessors(id, startDate):
	task_index = tasks[tasks['Task ID']==id].index.values.astype(int)[0]
	or_list = list(map(int, tasks['Or'][task_index]))
	or_count = 0

	if not(len(or_list) == 0):
		for i in range(len(or_list)):
			if (or_list[i] not in id_list):
				continue
			if (or_list[i] not in schedule['Task ID'].tolist()):
				continue
			pred_index = schedule[schedule['Task ID']==or_list[i]].index.values.astype(int)[0]
			if (schedule['Task Planned Start Date'][pred_index] > schedule['Task Planned Start Date'][index]):
				continue
			or_count += 1

		if or_count == 0:
			print("Task ID %d: A predecessor task has not been completed yet" %id)
			return False
		else:
			return True
	return True


def sortSchedule(s):
	order = []
	for index, row in s.iterrows():
		id = row['Task ID']
		task_index = tasks[tasks['Task ID']==id].index.values.astype(int)[0]
		order.append(tasks['New sort order'][task_index])
	s['Order'] = order 
	s = s.sort_values(['Order'])
	del s['Order']
	print(s)
	return s
	

def scheduleCheck(s):
	valid_list = []
	# Iterate through rows in schedule
	for index, row in s.iterrows():
		id = row['Task ID']
		#print(id)
		startDate = row['Task Planned Start Date']
		endDate = row['Task Planned End Date']

		if not(idExist(id)):
			print("Task ID %d: This Task ID doesn't exist in the records" %id)
			valid_list.append("False")
			continue
		if not(validDuration(id, startDate, endDate)):
			valid_list.append("False")
			continue
		if not(validAndPredecessors(id, startDate)):
			valid_list.append("False")
			continue
		if not(validOrPredecessors(id, startDate)):
			valid_list.append("False")
			continue
		if not(validscheduleSpecifications(id, startDate, endDate)):
			valid_list.append("False")
			continue
		else:
			valid_list.append("True")
	s['Valid'] = valid_list
	print("Schedule has been updated!")


def validTask(task_id, start_date, end_date):
	validity = True

	if not(idExist(task_id)):
		print("That Task ID doesn't exist in the records")
		validity = False

	if not(validDuration(task_id, start_date, end_date) and validity == True):
		validity = False

	if not(validAndPredecessors(task_id, start_date) and validity == True):
		validity = False

	if not(validOrPredecessors(task_id, start_date) and validity == True):
		validity = False

	if not(validscheduleSpecifications(task_id, start_date, end_date) and validity == True):
		validity = False

	if validity == False:
		print("Sorry, there was an issue with your task.")
		return False

	return True


def addTask():
	global schedule
	while True:
	    try:
	        task_id = int(input("Enter the Task ID: "))
	    except ValueError:
	        print("Sorry, your Task ID must be a numeric value.")
	        continue
	    else:
	        break

	task_name = input("Enter the Task Name: ")
	res_division = input("Enter the Responsible Division: ")


	while True:
		start_date = input("Enter the new start date in YYYY-MM-DD format: ")
		try:
			datetime.datetime.strptime(start_date, '%Y-%m-%d')
		except ValueError:
			print("Sorry, your date was not in a valid format.")
			continue
		else:
			start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
			if (start_date.weekday() == 5) or (start_date.weekday() == 6) or (start_date in canadian_holidays):
				print("Please enter a valid business day as your start date.")
				continue
			break

	while True:
		end_date = input("Enter the new end date in YYYY-MM-DD format: ")
		try:
			datetime.datetime.strptime(end_date, '%Y-%m-%d')

		except ValueError:
			print("Sorry, your date was not in a valid format.")
			continue
		else:
			end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
			if (end_date.weekday() == 5) or (end_date.weekday() == 6) or (end_date in canadian_holidays):
				print("Please enter a valid business day as your end date.")
				continue
			break

	if validTask(task_id, start_date, end_date):
		print("Your task was successfully added!")
		row = [task_id, task_name, start_date, end_date, getBusDaysInBetween(start_date, end_date) + 1, res_division, "True"]
		schedule.loc[len(schedule)] = row
		schedule = sortSchedule(schedule)


def addTaskStart():
	add_task_question = True
	while add_task_question == True:
		addTask()
		while True:
			cont = input("Would you like to add another Task? (Y/N): ")
			if cont == "Y":
				break
			if cont == "N":
				add_task_question = False
				print("Thank you for using this application! :)")
				break
			else:
				print("That is not a valid input!")
				continue


def editTask(task_id):
	global schedule
	sched_index = schedule[schedule['Task ID']==task_id].index.values.astype(int)[0]
	old_start_date = schedule["Task Planned Start Date"][sched_index]
	old_end_date = schedule["Task Planned End Date"][sched_index]
	start_date = schedule["Task Planned Start Date"][sched_index]
	end_date = schedule["Task Planned End Date"][sched_index]

	while True:
		edit_column = input("What would you like to edit? [start date, end date, both, duration]: ")
		if (edit_column == "start date"):
			while True:
				start_date = input("Enter the new start date in YYYY-MM-DD format: ")
				try:
					datetime.datetime.strptime(start_date, '%Y-%m-%d')
				except ValueError:
					print("Sorry, your date was not in a valid format.")
					continue
				else:
					start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
					if (start_date.weekday() == 5) or (start_date.weekday() == 6) or (start_date in canadian_holidays):
						print("Please enter a valid business day as your start date.")
						continue
					#schedule["Task Planned Start Date"][sched_index] = start_date
					#schedule.set_value(sched_index, 'Task Planned Start Date', start_date)
					schedule.at[sched_index, 'Task Planned Start Date'] = start_date
					break
			break

		elif (edit_column == "end date"):
			while True:
				end_date = input("Enter the new end date in YYYY-MM-DD format: ")
				try:
					datetime.datetime.strptime(end_date, '%Y-%m-%d')

				except ValueError:
					print("Sorry, your date was not in a valid format.")
					continue
				else:
					end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
					if (end_date.weekday() == 5) or (end_date.weekday() == 6) or (end_date in canadian_holidays):
						print("Please enter a valid business day as your end date.")
						continue
					#schedule["Task Planned End Date"][sched_index] = end_date
					#schedule.set_value(sched_index, 'Task Planned End Date', end_date)
					schedule.at[sched_index, 'Task Planned End Date'] = end_date
					break
			break

		elif (edit_column == "both"):
			while True:
				start_date = input("Enter the new start date in YYYY-MM-DD format: ")
				try:
					datetime.datetime.strptime(start_date, '%Y-%m-%d')
				except ValueError:
					print("Sorry, your date was not in a valid format.")
					continue
				else:
					start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
					if (start_date.weekday() == 5) or (start_date.weekday() == 6) or (start_date in canadian_holidays):
						print("Please enter a valid business day as your start date.")
						continue
					#schedule["Task Planned Start Date"][sched_index] = start_date
					#schedule.set_value(sched_index, 'Task Planned Start Date', start_date)
					schedule.at[sched_index, 'Task Planned Start Date'] = start_date
					break

			while True:
				end_date = input("Enter the new end date in YYYY-MM-DD format: ")
				try:
					datetime.datetime.strptime(end_date, '%Y-%m-%d')

				except ValueError:
					print("Sorry, your date was not in a valid format.")
					continue
				else:
					end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
					if (end_date.weekday() == 5) or (end_date.weekday() == 6) or (end_date in canadian_holidays):
						print("Please enter a valid business day as your end date.")
						continue
					#schedule["Task Planned End Date"][sched_index] = end_date
					#schedule.set_value(sched_index, 'Task Planned End Date', end_date)
					schedule.at[sched_index, 'Task Planned End Date'] = end_date
					break
			break

		elif (edit_column == "duration"):
			while True:
				dur = input("Enter the new duration (number of days): ")
				try:
					val = int(dur)

				except ValueError:
					print("Please enter a number as your duration.")
					continue
				else:
					end_date = getBusDaysBeforeAfter(start_date, dur - 1, "After")
					if (end_date.weekday() == 5) or (end_date.weekday() == 6) or (end_date in canadian_holidays):
						print("Please ensure your end date isn't a holiday or weekend.")
						continue
					#schedule["Task Planned End Date"][sched_index] = end_date
					#schedule.set_value(sched_index, 'Task Planned End Date', end_date)
					schedule.at[sched_index, 'Task Planned End Date'] = end_date
					break
			break

		else: 
			print("Please enter [start date, end date or both]: ")
			continue

	if validTask(task_id, start_date, end_date):
		schedule.at[sched_index, 'Duration'] = getBusDaysInBetween(start_date, end_date)
		print("Your task was edited successfully.")

	else: 
		while True:
			confirm = input("Your task does not follow all the requirements, would you still like to add it? (Y/N): ")
			if confirm == "Y":
				schedule.at[sched_index, 'Duration'] = getBusDaysInBetween(start_date, end_date)
				print("Your task as been edited (override).")
				break
			elif confirm == "N":
				#schedule["Task Planned Start Date"][sched_index] = old_start_date
				#schedule.set_value(sched_index, 'Task Planned Start Date', old_start_date)
				schedule.at[sched_index, 'Task Planned Start Date'] = old_start_date
				#schedule["Task Planned End Date"][sched_index] = old_start_date
				#schedule.set_value(sched_index, 'Task Planned End Date', old_end_date)
				schedule.at[sched_index, 'Task Planned End Date'] = old_end_date
				print("Your changes have been reverted.")
				break
			else:
				print("Please enter Y or N")
				continue


def scheduleBuilder(startDate):
	global schedule
	setStartDate = startDate
	column_names = ["Task ID", "Task Name", "Task Planned Start Date", "Task Planned End Date", "Duration",
	"Responsible Division", "Valid"]
	new_schedule = pd.DataFrame(columns = column_names)
	oldStartDate = schedule['Task Planned Start Date'][0]
	for index, row in schedule.iterrows():
		offset = getBusDaysInBetween(oldStartDate, row['Task Planned Start Date']) - 1
		startDate = getBusDaysBeforeAfter(setStartDate, offset, "After")
		#print(offset)
		row = [row['Task ID'], row['Task Name'], startDate, getBusDaysBeforeAfter(startDate, 
			getBusDaysInBetween(row['Task Planned Start Date'], row['Task Planned End Date']) - 1, "After"), 
			getBusDaysInBetween(row['Task Planned Start Date'], row['Task Planned End Date']), 
			row['Responsible Division'], "True"]
		new_schedule.loc[len(new_schedule)] = row

	#print(new_schedule)
	#print(new_schedule['Task Planned Start Date'])
	#print(new_schedule['Task Planned End Date'])
	return new_schedule


def makeNewSchedule():
	while True:
		start_date = input("Enter the start date in YYYY-MM-DD format: ")
		try:
			datetime.datetime.strptime(start_date, '%Y-%m-%d')
		except ValueError:
			print("Sorry, your date was not in a valid format.")
			continue
		else:
			start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
			if (start_date.weekday() == 5) or (start_date.weekday() == 6) or (start_date in canadian_holidays):
				print("Please enter a valid business day as your start date.")
				continue
			break

	return scheduleBuilder(start_date)


#################################################################################
## MAIN CALLS
#################################################################################

# Makes the And and Or columns in "tasks" into lists of integers
tasks['And'] = tasks['And'].str.split(',')
tasks['Or'] = tasks['Or'].str.split(',')

# Makes the Min and Max columns in "tasks" into integers (mainly to catch error inputs)
tasks['Min'].astype(str).astype(int)
tasks['Max'].astype(str).astype(int)

# Insert empty lists into "And" and "Or" columns to avoid NaNs
for row in tasks.loc[tasks['And'].isnull(), 'And'].index:
    tasks.at[row, 'And'] = []
for row in tasks.loc[tasks['Or'].isnull(), 'Or'].index:
    tasks.at[row, 'Or'] = []

# Date formatting in "schedule"
schedule['Task Planned Start Date'] = pd.to_datetime(schedule['Task Planned Start Date'], format = '%d-%b-%Y')
schedule['Task Planned End Date'] = pd.to_datetime(schedule['Task Planned End Date'], format = '%d-%b-%Y')


x = datetime.datetime(2020, 5, 7)
#print(getBusDaysBeforeAfter(x, 39, "After"))
'''
y = datetime.datetime(2021, 5, 17)

print(getBusDaysBeforeAfter(x, 1, "After"))
print(getBusDaysInBetween(x, y))
'''

#editTask(222)

new_schedule = scheduleBuilder(x)
scheduleCheck(new_schedule)
print(new_schedule)

addTaskStart()
#print(schedule)









