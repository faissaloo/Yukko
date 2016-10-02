#!/usr/bin/env python3
def expect(toExpect):
	global textCursor
	global textContents
	if textContents[textCursor:textCursor+len(toExpect)]==toExpect:
		textCursor+=len(toExpect)
		return True
	else:
		return False

def skipWhitespace():
	global textCursor
	global textContents
	while expect(" ") or expect("\t"):
		pass
	

def parse(string):
	global textCursor
	global textContents
	postDict={
		"Name":"",
		"Subject":"",
		"Body":""
	}
	textCursor=0
	textContents=string
	skipWhitespace()
	while textCursor<len(textContents):
		if expect("Name:"):
			skipWhitespace()
			while textContents[textCursor]!="\n":
				postDict["Name"]+=textContents[textCursor]
				textCursor+=1
		elif expect("Subject:"):
			skipWhitespace()
			while textContents[textCursor]!="\n":
				postDict["Subject"]+=textContents[textCursor]
				textCursor+=1
		elif expect("Body:"):
			while textCursor<len(textContents):
				postDict["Body"]+=textContents[textCursor]
				textCursor+=1
		textCursor+=1
	return postDict
