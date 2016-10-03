#!/usr/bin/env python3
import re
def parse(string):
	postDict={
		"Name":"",
		"Subject":"",
		"Body":""
	}
	#Split by body first
	bodyList=string.split("Body:",1)
	if len(bodyList)>0:
		postDict["Body"] = bodyList[1]
	
	nameList=re.findall("(?i)Name\:[\W]*(.*)\n",bodyList[0])
	if len(nameList)>0:
		postDict["Name"] = nameList[0]
	
	subList=re.findall("(?i)Subject\:[\W]*(.*)\n",bodyList[0])
	if len(subList)>0:
		postDict["Subject"] = subList[0]
	return postDict
