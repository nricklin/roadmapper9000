import roadmapper

def handler(event, context):
	print event
	print context

	try:
		roadmapper.run()
	except Exception as e:
		print str(e)
		return str(e)