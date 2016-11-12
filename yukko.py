#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################LICENCE###################################
# Copyright (c) 2016 Faissal Bensefia
# This file is part of Yukko.
#
# Yukko is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Yukko is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Yukko.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################
import textwrap
import asciiArtLoader
import curses
import nntp
import os
import png
import postParsing
import json
import signal


def sigint_handler(signal, frame):
	curses.endwin()
	exit()

signal.signal(signal.SIGINT, sigint_handler)

# Load settings
with open("settings.json") as settingsFile:
	settings = json.load(settingsFile)

nntp.proxy = {
	"http": settings["http proxy"],
	"https": settings["http proxy"]
}
os.environ['ESCDELAY'] = '0'
scr = curses.initscr()
curses.start_color()
curses.noecho()
curses.curs_set(0)
curses.use_default_colors()
scr.keypad(True)
windowH, windowW = scr.getmaxyx()

with open(settings["theme folder"] + "posts.json") as postThemeFile:
	postStyle = json.load(postThemeFile)

errorRetrievingPage = asciiArtLoader.asciiImg(
	settings["theme folder"] + "errorRetrievingPage.txt")
boardListBg = asciiArtLoader.asciiImg(
	settings["theme folder"] + "boardListBg.txt")
emptyBoard = asciiArtLoader.asciiImg(
	settings["theme folder"] + "emptyBoard.txt")
logo = asciiArtLoader.asciiImg(settings["theme folder"] + "logo.txt")
attachments = asciiArtLoader.asciiImg(
	settings["theme folder"] + "attachmentsBg.txt")


def drawCaptcha(y, x):  # An image drawer geared towards CAPTCHAs
	global scr
	global windowH
	global windowW
	image = png.Reader("/tmp/" + nntp.captchaID + ".png").read()
	width = image[0]
	height = image[1]
	if windowW - 1 < x + (width // 4) or windowH - 1 < y + (height // 8):
		scr.clear()
		scr.addstr(y, x, "Terminal too small for CAPTCHA, please resize")
		return 0

	yy = 0
	for i in image[2]:
		xx = 0
		for ii in i:
			# The foreground will always be color 1 in the pallette
			# only include foreground to make it easier for the user
			if ii == 1:
				scr.addstr(y + (yy // 8), x + (xx // 4), "░", curses.A_REVERSE)

			xx += 1
		yy += 1
	return 1


def getPostHeight(post, ypad):
	global windowW
	splitText = []
	for i in post.text.split("\n"):
		if post.isOP:
			for ii in textwrap.wrap(i, windowW - 1):
				splitText.append(ii)
		else:
			for ii in textwrap.wrap(i, windowW - 3):
				splitText.append(ii)
	return ypad + len(splitText)


def threadLength(thread, ypad, offset):
	# Offset is added to the total value (for stuff like op)
	# ypad is added to each post
	total = offset
	for i in thread.posts:
		total += getPostHeight(i, ypad)
	return total


def threadOverviewLength(thread, ypad, offset, maxlines, maxposts):
	# Offset is added to the total value (for stuff like op)
	# ypad is added to each post
	total = offset
	for i in thread.overview(3):
		# Maxlines+1 because a message is appended to those that exceed it
		total += min(getPostHeight(i, ypad), ypad + maxlines + 1)
	return total

# Like addstr but errors silently


def drawText(y, x, string, attributes=0):
	global scr
	try:
		scr.addstr(y, x, string, attributes)
	except curses.error:
		pass


def textBox(y, x, default, length, intOnly=False, maxlen=0):
	global scr
	string = default
	last_ch = 0
	cursor_pos = 0
	scope_pos = 0
	curses.curs_set(True)
	while not (last_ch == 27 or last_ch == ord("\n")):
		scr.addstr(y, x, string[scope_pos:scope_pos + length].ljust(length))
		scr.move(y, x + cursor_pos - scope_pos)
		scr.refresh()
		last_ch = scr.getch()
		if last_ch == curses.KEY_LEFT:
			if cursor_pos > 0:
				cursor_pos -= 1
				if cursor_pos < scope_pos:
					scope_pos -= 1
		elif last_ch == curses.KEY_RIGHT:
			if cursor_pos < len(string):
				cursor_pos += 1
				if cursor_pos > length + scope_pos:
					scope_pos += 1
		elif last_ch == curses.KEY_DC:
			if cursor_pos < len(string):
				string = string[:cursor_pos] + string[cursor_pos + 1:]
		elif last_ch == curses.KEY_BACKSPACE:
			if cursor_pos > 0:
				cursor_pos -= 1
				string = string[:cursor_pos] + string[cursor_pos + 1:]
				if cursor_pos < scope_pos:
					scope_pos -= 1
		elif (not (last_ch == 27 or last_ch == ord("\n") or intOnly)
			) or ((not (last_ch == 27 or last_ch == ord("\n")))
				and intOnly and last_ch <= ord("9")
				and last_ch >= ord("0")
			) and (maxlen == 0 or len(string) < maxlen):
			string = string[:cursor_pos] + chr(last_ch) + string[cursor_pos:]
			cursor_pos += 1
			if cursor_pos > length + scope_pos:
				scope_pos += 1

	curses.curs_set(False)
	# Escape = Throw away, enter = save
	if last_ch == 27:
		return default
	else:
		return string


def boardView(board):
	global errorRetrievingPage
	global emptyBoard
	global postStyle
	global settings
	global ypad
	global scr
	global windowH
	global windowW
	selectionBarY = 0
	page = 0
	currBoard = nntp.board(board, page)
	y = 0
	scr.clear()
	while True:
		windowH, windowW = scr.getmaxyx()
		# If the board was loaded successfully
		if currBoard.status == 200:
			if len(currBoard) > 0:
				postY = 0  # Post y in the whole page
				selected = False

				prevThread = None
				prevThreadHeight = 0
				for iThread in currBoard:
					# If any part of the thread hits the middle of the screen then select that
					selected = not (selectionBarY -
							y < postY -
							y or (postY -
						y) +
						threadOverviewLength(iThread,
							3,
							0,
							settings["max overview lines"],
							settings["max overview posts"]) -
							1 < selectionBarY -
							y)

					if selected:
						selectedThread = iThread
						selectedThreadHeight = threadOverviewLength(
							iThread, 3, 0,
							settings["max overview lines"],
							settings["max overview posts"])
						if prevThread:
							# Height of the thread before the selected thread
							prevThreadHeight = threadOverviewLength(
								prevThread, 3, 0,
								settings["max overview lines"],
								settings["max overview posts"])

					for iPost in iThread.overview(settings["max overview posts"]):
						drawText(postY - y, 0, postStyle["local"]
							["OP" if iPost.isOP else "default"]
							["selected" if selected else "unselected"]
							["seperator"] +
							(postStyle["local"]["OP" if iPost.isOP else "default"]
								["selected" if selected else "unselected"]
								["seperator repeat"] * (windowW -
									len(postStyle["local"]
										["OP" if iPost.isOP else "default"]
										["selected" if selected else "unselected"]["seperator"]
									)
								)
							)
						)

						postY += 1

						drawText(postY - y, 0,
							postStyle["local"]
								["OP" if iPost.isOP else "default"]
								["selected" if selected else "unselected"]
								["header"].format(
									iPost.name,
									iPost.subject,
									iPost.hash,
									iPost.timestamp,
									postStyle["global"]
										["attachment character"] if len(iPost.files) else ""
									)
							)
						postY += 1
						splitText = []
						# Wrap the text
						for iLine in iPost.text.split("\n"):
							if iPost.isOP:
								for iLineWrapped in textwrap.wrap(iLine, windowW - 1):
									splitText.append(iLineWrapped)
							else:
								for iLineWrapped in textwrap.wrap(iLine, windowW - 3):
									splitText.append(iLineWrapped)

						# Draw the text in the post up to settings["max overview lines"]
						for yText, iText in enumerate(splitText):
							if yText < settings["max overview lines"]:
								drawText(postY - y,
									0,
									postStyle["local"]
										["OP" if iPost.isOP else "default"]
										["selected" if selected else "unselected"]
										["body"] +
									iText)
								postY += 1
							else:
								drawText(postY - y,
									0,
									postStyle["local"]
										["OP" if iPost.isOP else "default"]
										["selected" if selected else "unselected"]
										["body"] +
									"[POST CONTRACTED]")
								postY += 1
								break
						drawText(
							postY - y,
							0,
							postStyle["local"]
								["OP" if iPost.isOP else "default"]
								["selected" if selected else "unselected"]
								["footer"] +
							postStyle["local"]
								["OP" if iPost.isOP else "default"]
								["selected" if selected else "unselected"]
								["footer repeat"] *
							(windowW - len(
									postStyle["local"]
										["OP" if iPost.isOP else "default"]
										["selected" if selected else "unselected"]
										["footer"]
									)
								)
							)
						postY += 1
						prevThread = iThread
			else:
				for yArt, iArt in enumerate(emptyBoard):
					drawText((windowH - errorRetrievingPage.height) // 2 + yArt,
							(windowW - errorRetrievingPage.width) // 2, iArt)

		else:
			for yArt, iArt in enumerate(errorRetrievingPage):
				drawText((windowH - errorRetrievingPage.height) // 2 + yArt,
									(windowW - errorRetrievingPage.width) // 2,
									iArt.format(currBoard.status)
					)
		currKey = 0
		scr.refresh()
		while not (currKey == curses.KEY_UP
			or currKey == curses.KEY_DOWN
			or currKey == curses.KEY_LEFT
			or currKey == curses.KEY_RIGHT
			or currKey == ord('b')
			or currKey == ord('p')
			or currKey == ord('r')
			or currKey == ord('\n')
			or currKey == 27):  # Add keys that cause updates as nessecary
			currKey = scr.getch()
		if currKey == curses.KEY_UP:
			if selectionBarY > 0:
				selectionBarY -= prevThreadHeight
				if selectionBarY < y:
					# bind to prevent it going below 0
					y = max(0, y - prevThreadHeight)
		elif currKey == curses.KEY_DOWN:
			if selectionBarY + selectedThreadHeight < postY:
				selectionBarY += selectedThreadHeight
				if selectionBarY + selectedThreadHeight > y + windowH - 1:
					# bind to prevent it going higher than 0
					y = min(postY - windowH - 1, y + selectedThreadHeight)
		elif currKey == curses.KEY_LEFT:
			if page > 0:
				selectionBarY = 0
				y = 0
				page -= 1
				scr.addstr(
					0, 0,
					("Loading page " +
						str(page) +
						" of " +
						board).ljust(windowW),
					curses.A_REVERSE)
				scr.refresh()
				currBoard = nntp.board(board, page)
		elif currKey == curses.KEY_RIGHT:
			selectionBarY = 0
			page += 1
			y = 0
			scr.addstr(
				0, 0,
				("Loading page " +
					str(page) +
					" of " +
					board).ljust(windowW),
				curses.A_REVERSE)
			scr.refresh()
			currBoard = nntp.board(board, page)
		elif currKey == 27:
			scr.attron(curses.A_REVERSE)
			scr.addstr(0, 0, "Board: ")
			next_board = textBox(
				0, len("Board: "),
				board, windowW -
				len("Board: "),
				False)
			scr.attroff(curses.A_REVERSE)
			if next_board != board:
				board = next_board
				page = 0
				y = 0
				selectionBarY = 0
			currBoard = nntp.board(board, page)
		elif currKey == ord('b'):
			selectionBarY = 0
			next_board = boardListView(board)
			if next_board != board:
				board = next_board
			page = 0
			y = 0
			currBoard = nntp.board(board, page)
		elif currKey == ord('p'):
			scr.addstr(0, 0, ("Loading CAPTCHA").ljust(windowW), curses.A_REVERSE)
			scr.refresh()
			post(currBoard, settings["text editor"])

			y = 0
			selectionBarY = 0
		elif currKey == ord('r'):
			scr.addstr(0, 0, ("Refreshing").ljust(windowW), curses.A_REVERSE)
			scr.refresh()
			currBoard.refresh()
			# We have to jump back selectionBarY might end up in the middle of a post
			y = 0
			selectionBarY = 0

		elif currKey == ord('\n'):
			threadView(selectedThread)
		scr.clear()


def threadView(thread):
	global postStyle
	global ypad
	global settings
	global scr
	global windowH
	global windowW
	scr.clear()
	selectionBarY = 0
	y = 0
	selectedPostHeight = 0
	while True:
		windowH, windowW = scr.getmaxyx()
		postY = 0  # Post y in the whole page
		prevPost = None
		selected = False
		selectedPost = None
		for iPost in thread:
			# 1D collision detection between postY and selectionBarY
			selected = not (selectionBarY -
				y < postY -
				y or (postY -
					y) +
				getPostHeight(
					iPost,
					3) -
				1 < selectionBarY -
				y)
			if selected:
				selectedPost = iPost
				selectedPostHeight = getPostHeight(iPost, 3)
				if prevPost:
					# Height of the post before the selected post
					prevPostHeight = getPostHeight(prevPost, 3)
			drawText(postY - y, 0,
				postStyle["local"]
					["OP" if iPost.isOP else "default"]
					["selected" if selected else "unselected"]
					["seperator"] +
					(
						postStyle["local"]
							["OP" if iPost.isOP else "default"]
							["selected" if selected else "unselected"]
							["seperator repeat"] *
						(
							windowW - len(
								postStyle["local"]
								["OP" if iPost.isOP else "default"]
								["selected" if selected else "unselected"]
								["seperator"]
							)
						)
					)
				)
			postY += 1

			drawText(postY - y, 0,
				postStyle["local"]
					["OP" if iPost.isOP else "default"]
					["selected" if selected else "unselected"]
					["header"].format(iPost.name,
						iPost.subject,
						iPost.hash,
						iPost.timestamp,
						postStyle["global"]
							["attachment character"]
							if len(iPost.files) else ""
						)
				)
			postY += 1
			splitText = []
			for iLine in iPost.text.split("\n"):
				for iLineWrapped in textwrap.wrap(
					iLine, windowW - (1 if iPost.isOP else 3)):
					splitText.append(iLineWrapped)

			for iText in splitText:
				drawText(
									postY -
									y,
									0,
									postStyle["local"][
										"OP" if iPost.isOP else "default"][
										"selected" if selected else "unselected"]["body"] +
									iText)
				postY += 1
			drawText(
				postY -
				y,
				0,
				postStyle["local"]
					["OP" if iPost.isOP else "default"]
					["selected" if selected else "unselected"]
					["footer"] +
				postStyle["local"]
					["OP" if iPost.isOP else "default"]
					["selected" if selected else "unselected"]["footer repeat"] *
				(windowW -
					len(
						postStyle["local"]
							["OP" if iPost.isOP else "default"]
							["selected" if selected else "unselected"]
							["footer"]
						)
					)
				)
			postY += 1
			prevPost = iPost
		scr.refresh()
		currKey = 0
		while not (currKey == curses.KEY_UP
				or currKey == curses.KEY_DOWN
				or currKey == curses.KEY_LEFT
				or currKey == ord('p')
				or currKey == ord('r')
				or currKey == curses.KEY_BACKSPACE
				or currKey == ord('\n')
				or currKey == 27):  # Add keys that cause updates as nessecary
			currKey = scr.getch()
		if currKey == curses.KEY_UP:
			if selectionBarY > 0:
				selectionBarY -= prevPostHeight
				if selectionBarY < y:
					# Bind to prevent it going below 0
					y = max(y - prevPostHeight, 0)
		elif currKey == curses.KEY_DOWN:
			if selectionBarY + selectedPostHeight < postY:
				selectionBarY += selectedPostHeight
				if selectionBarY + selectedPostHeight > y + windowH - 1:
					# Bind to the height of the page
					y = min(postY - windowH - 1, y + selectedPostHeight)
		elif currKey == ord('p'):
			scr.addstr(0, 0, ("Loading CAPTCHA").ljust(windowW), curses.A_REVERSE)
			scr.refresh()
			post(thread, settings["text editor"])
		elif currKey == ord('r'):
			scr.addstr(0, 0, ("Refreshing").ljust(windowW), curses.A_REVERSE)
			scr.refresh()
			thread.refresh()
		elif currKey == ord('\n'):
			# Only display if there are files
			if len(selectedPost.files) > 0:
				viewAttachments(selectedPost)
		elif (currKey == 27
			or currKey == curses.KEY_BACKSPACE
			or currKey == curses.KEY_LEFT):
			return
		scr.clear()


def boardListView(default):
	global boardListBg
	global windowH
	global windowW
	global scr
	scr.clear()
	scopeY = 0
	selector = 0
	currKey = 0
	boardList = nntp.boardList()
	while True:
		windowH, windowW = scr.getmaxyx()
		# Background
		for yArt, iArt in enumerate(boardListBg):
			drawText(windowH -
				boardListBg.height +
				yArt,
				windowW -
				boardListBg.width,
				iArt)

		for yBoard, iBoard in enumerate(boardList[scopeY:], scopeY):
			drawText(yBoard -
				scopeY,
				1,
				iBoard,
				curses.A_REVERSE if selector == yBoard else 0)
		scr.refresh()
		currKey = 0
		while not (currKey == curses.KEY_UP
				or currKey == curses.KEY_DOWN
				or currKey == 27
				or currKey == ord("\n")):  # Add keys that cause updates as nessecary
			currKey = scr.getch()

		if currKey == curses.KEY_UP:
			if selector > 0:
				selector -= 1
				if selector < scopeY:
					scopeY = selector
		elif currKey == curses.KEY_DOWN:
			if selector < len(boardList) - 1:
				selector += 1
				if scopeY + windowH <= selector and scopeY <= len(boardList) - windowH:
					scopeY += 1
		elif currKey == 27:
			return default
		elif currKey == ord("\n"):
			return boardList[selector]
		scr.clear()

# Object can be either a thread or a board


def post(object, editorCommand):
	global scr
	global windowH
	global windowW
	nntp.getCaptcha()
	textFileID = nntp.captchaID
	# Create the post form template
	with open("/tmp/post" + textFileID + ".txt", "w") as file:
		file.write(
			"Name: Anonymous\n" +
			"Subject: \n" +
			"Body: \n")
	# Open the file in text editor of choice
	curses.endwin()
	os.system(editorCommand + " /tmp/post" + textFileID + ".txt")
	with open("/tmp/post" + textFileID + ".txt", "r") as file:
		postDict = postParsing.parse(file.read())

	captchaString = ""
	response = 0
	while response != 201:
		while captchaString == "":
			scr.clear()
			windowH, windowW = scr.getmaxyx()
			while not drawCaptcha(3, 0):
				# Wait for the user to resize the terminal to an acceptable size
				scr.refresh()
				scr.clear()
				windowH, windowW = scr.getmaxyx()
			scr.refresh()
			scr.addstr(0, 0, "CAPTCHA", curses.A_BOLD)
			scr.addstr(1, 0, "Too hard? Hit escape to generate a new CAPTCHA")
			scr.addstr(2, 0, ">")
			captchaString = textBox(2, 1, "", windowW, True, 6)
			if captchaString == "":  # Regen new captcha if we have to
				nntp.cleanupCaptcha()
				nntp.getCaptcha()
			scr.refresh()
		response = object.post(postDict['Name'], postDict['Subject'],
			postDict['Body'],
			captchaString)

		if response == 200:
			scr.addstr(0,
				0,
				("CAPTCHA failed, please try again.").ljust(windowW),
				curses.A_REVERSE)
			scr.refresh()
			captchaString = ""
			nntp.cleanupCaptcha()
			nntp.getCaptcha()
			scr.getch()
		elif response == 504:
			scr.addstr(0,
				0,
				("Gateway timeout, press any key to try again").ljust(
					windowW),
				curses.A_REVERSE)
			scr.refresh()
			scr.getch()

	try:
		os.remove("/tmp/post" + textFileID + ".txt")
	except:
		pass
	scr.addstr(0, 0, ("Post successful!").ljust(windowW), curses.A_REVERSE)
	scr.refresh()
	object.refresh()


def viewAttachments(post):
	global scr
	global windowH
	global windowW
	global attachments
	scopeY = 0
	selector = 0
	selectedFile = None
	while True:
		scr.clear()
		windowH, windowW = scr.getmaxyx()
		# Background
		for i, j in enumerate(attachments):
			drawText(windowH - attachments.height + i, windowW - attachments.width, j)

		for yFile, iFile in enumerate(post.files[scopeY:], scopeY):
			if selector == yFile:
				selectedFile = iFile
				scr.addstr(yFile - scopeY, 1, iFile.fileName, curses.A_REVERSE)
			elif yFile - scopeY < windowH:
				scr.addstr(yFile - scopeY, 1, post.iFile.fileName)

		scr.refresh()
		currKey = 0
		while (not (currKey == curses.KEY_UP
				or currKey == curses.KEY_DOWN
				or currKey == 27
				or currKey == curses.KEY_BACKSPACE
				or currKey == curses.KEY_LEFT
				or currKey == ord("\n")
				)
			):
			currKey = scr.getch()
		if currKey == curses.KEY_UP:
			if selector > 0:
				selector -= 1
				if selector < scopeY:
					scopeY -= 1
		if currKey == curses.KEY_DOWN:
			if selector < len(post.files) - 1:
				selector += 1
				if scopeY + windowH <= selector and scopeY <= len(post.files) - windowH:
					scopeY += 1
		elif currKey == ord("\n"):
			scr.addstr(0, 0, ("Downloading file").ljust(windowW), curses.A_REVERSE)
			scr.refresh()
			r = selectedFile.download(settings["download directory"])
			if r == 200:
				scr.addstr(0,
					0,
					("Saved to " +
						settings["download directory"] +
						selectedFile.fileName).ljust(windowW),
					curses.A_REVERSE)
			scr.refresh()
			scr.getch()
		elif (currKey == 27
			or currKey == curses.KEY_BACKSPACE
			or currKey == curses.KEY_LEFT):
			return

boardView(settings["default board"])
