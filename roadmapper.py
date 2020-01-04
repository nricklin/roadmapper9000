import pygsheets
import pandas as pd
import arrow
import math


AUTH_FILENAME = 'auth_file.json'
start_date = arrow.get("2020-01-01")
WORKBOOK_NAME = 'GCS Roadmap Stuff'
TEAMS_SHEET = 'Teams'
WORK_SHEET = 'Work'
OUTPUT_SHEET_NAME = 'Output-team-tasks'
MILESTONE_SHIFT = 42 # set milestone date this many days after last task is complete

def run():
	

	#authorization
	gc = pygsheets.authorize(service_file=AUTH_FILENAME)
	sh = gc.open(WORKBOOK_NAME)

	teams = sh.worksheet_by_title(TEAMS_SHEET)
	teamsdata = teams.get_all_records()

	work = sh.worksheet_by_title(WORK_SHEET)
	workdata = work.get_all_records()

	#2. Get start and stop times per task per team
	# Sort tasks by priority.
	all_sorted_team_tasks = []
	orphans = []
	for team in teamsdata:
		teamname = team['Team']
		train = team['Train']
		capacity = team['Capacity/qtr']
		#product = team['Product']
		
		
		points_per_day = capacity/90.0
		# get tasks that belong to this team
		team_tasks = [w for w in workdata if w['Team Affinity'] == teamname]

		# update team affinity name to contain train item:
		for t in team_tasks:
			t['Team Affinity'] = train + ': ' + t['Team Affinity']
			t['Train'] = train

		# sort tasks according to priority
		team_tasks = sorted(team_tasks, key=lambda k: k['Priority']) 

		# if a team has zero capacity, don't put anything in the roadmap:
		if capacity == 0:
			#  better idea, put these tasks into the orphans table.
			new_orphans = [teamname+':---- '+t['Work Item']for t in team_tasks]
			orphans.extend(team_tasks)
			continue

		# for each team task, add startdate and enddate
		day = start_date

		#print team_tasks
		for task in team_tasks:
			task['start_date'] = day
			points = task['Size (points)']
			day_shift = math.ceil(points/points_per_day)
			day = day.shift(days=+day_shift)
			task['end_date'] = day
			task['Quarter'] = str(day.year) + ' Q' + str((day.month-1)//3+1)

		all_sorted_team_tasks.extend( team_tasks )

	df = pd.DataFrame()
	df['Team'] = [t['Team Affinity'] for t in all_sorted_team_tasks]
	df['Work Item'] = [t['Product']+': '+t['Work Item']+ '\n\n' for t in all_sorted_team_tasks]
	df['Start Date'] = [t['start_date'].format('MM/DD/YY') for t in all_sorted_team_tasks]
	df['End Date'] = [t['end_date'].format('MM/DD/YY') for t in all_sorted_team_tasks]
	df['Product'] = [t['Product'] for t in all_sorted_team_tasks]
	df['Points'] = [t['Size (points)'] for t in all_sorted_team_tasks]
	df['Priority'] = [t['Priority'] for t in all_sorted_team_tasks]
	df['Dollars'] = [t['Dollars'] for t in all_sorted_team_tasks]
	df['MoSCoW'] = [t['MoSCoW'] for t in all_sorted_team_tasks]
	df['PM Priority'] = [t['PM Priority'] for t in all_sorted_team_tasks]
	df['Train'] = [t['Train'] for t in all_sorted_team_tasks]
	df['Quarter'] = [t['Quarter'] for t in all_sorted_team_tasks]
	output1 = sh.worksheet_by_title(OUTPUT_SHEET_NAME)
	output1.set_dataframe(df,(1,1))


	# make the orphans table
	df = pd.DataFrame()
	df['Tasks'] = [t['Product']+': '+t['Work Item'] for t in orphans]
	df['Team'] = [t['Team Affinity'] for t in orphans]
	df['Train'] = [t['Train'] for t in orphans]
	df['Product'] = [t['Product'] for t in orphans]
	df['Points'] = [t['Size (points)'] for t in orphans]
	df['Dollars'] = [t['Dollars'] for t in orphans]
	df['Priority'] = [t['Priority'] for t in orphans]
	df['PM Priority'] = [t['PM Priority'] for t in orphans]
	df['MoSCoW'] = [t['MoSCoW'] for t in orphans]
	output2 = sh.worksheet_by_title('Orphans')
	output2.set_dataframe(df,(1,1))

	# make the milestones output table
	all_orphaned_milestones = set([t['Milestone'] for t in orphans if t['Milestone'] != ''])
	all_milestones = list(set([t['Milestone'] for t in all_sorted_team_tasks if t['Milestone'] != '']).union(all_orphaned_milestones) )
	df = pd.DataFrame()
	df['Milestone'] = [m+ '\n\n' for m in all_milestones]

	# determine milestone dates
	dates = []
	milestone_products = []
	for m in all_milestones:
		if m in all_orphaned_milestones:
			date = 'orphaned'
		else:
			date = max([t['end_date'] for t in all_sorted_team_tasks if t['Milestone'] == m]).shift(days=+MILESTONE_SHIFT)
		dates.append(date)
		products = '; '.join(list(set([t['Product'] for t in all_sorted_team_tasks if t['Milestone'] == m])))
		milestone_products.append(products)

	dates_for_display = []
	quarters_for_display = []
	for d in dates:
		if d == 'orphaned':
			dates_for_display.append(d)
			quarters_for_display.append(d)
		else:
			dates_for_display.append(d.format('MM/DD/YY'))
			quarters_for_display.append(str(d.year) + ' Q' + str((d.month-1)//3+1))
	df['Date'] = dates_for_display
	df['Quarter'] = quarters_for_display
	df['Product'] = milestone_products
	output3 = sh.worksheet_by_title('Output-milestones')
	output3.set_dataframe(df,(1,1))


if __name__ == "__main__":
	run()