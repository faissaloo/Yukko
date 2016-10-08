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
import requests
import json
import datetime
import os
captchaID = ""
nodeList = []
node=""
proxy={
	"http":"",
	"https":""
}

# Reads nodes from a text file
def readNodes(nodeFile):
    global nodeList
    with open(nodeFile, 'r') as file:
        nodeList=[i.strip() for i in file]

# Picks a random new node
def cycleNode():
    global node
    global nodeList
    node = nodeList[int.from_bytes(os.urandom(4), "big") % len(nodeList)]

readNodes("nodeList.txt")
cycleNode()

class file():
    def __init__(self, jason):
        global node
        self.url = node + "img/" + jason["Path"]
        self.fileName = jason["Name"]

    def download(self, downloadDir=""):
        global proxy
        r = requests.get(self.url, proxies=proxy)
        with open(downloadDir + self.fileName, "wb") as f:
            for i in r:
                f.write(i)
        return r.status_code


class post():

    def __init__(self, jason, isOP=False):
        self.isOP = isOP
        self.name = jason["PostName"]
        self.subject = jason["PostSubject"]
        self.ID = jason["Message_id"]
        self.hash = jason["HashLong"]
        self.timestamp = datetime.datetime.fromtimestamp(jason["Posted"])
        self.text = jason["PostMessage"]
        self.files = []
        if jason["Files"] != None:
            for i in jason["Files"]:
                self.files.append(file(i))


class thread():

    def __init__(self, jason, parentBoard):
        self.parentBoard = parentBoard
        self.posts = []
        self.posts.append(post(jason[0], True))
        for i in jason[1:]:
            self.posts.append(post(i))

    def __len__(self):
        return len(self.posts)

    def __iter__(self):
        self.iteratorIndex = 0
        return self

    def __next__(self):
        if self.iteratorIndex >= len(self):
            raise StopIteration
        else:
            toRet = self[self.iteratorIndex]
            self.iteratorIndex += 1
            return toRet

    def __getitem__(self, key):
        return self.posts[key]

    def refresh(self):
        global proxy
        r = requests.get(node + "thread-" + str(self[0].hash) + ".json", proxies=proxy)
        self.status = r.status_code
        self.posts = []
        if self.status >= 200 and self.status < 300:
            jason = r.json()
            if jason:  # Only do this if None wasn't returned
                self.posts = []
                self.posts.append(post(jason[0], True))
                for i in jason[1:]:
                    self.posts.append(post(i))

    def overview(self, postCount):
        # Returns the first and last postCount posts
        if len(self.posts) > 1:
            postOverview = self.posts[max(1, len(self.posts) - postCount):]
        else:
            postOverview = []
        postOverview.insert(0, self.posts[0])
        return postOverview

    def post(self, name, sub, msg, captcha, *files):
        global proxy
        global node
        global captchaID
        filesToUpload = [("", "")]
        # Ability to use same key for multiple files
        for i in files:
            filesToUpload.append(("attachment_uploaded", open(i, "rb")))

        postArgs = {
            "reference": self.posts[0].ID,
            "name": name,
            "subject": sub,
            "message": msg,
            "captcha": captcha,
            "captcha_id": captchaID,
            "pow": ""
        }
        header = {
        }
        r = requests.post(node + "post/" + self.parentBoard.boardname,
                          files=filesToUpload, data=postArgs, headers=header, proxies=proxy)
        return r.status_code


class board():

    def __init__(self, boardname, page):
        global node
        global proxy
        cycleNode()
        r = requests.get(node + boardname + "-" + str(page) + ".json", proxies=proxy)
        self.status = r.status_code
        self.page = page
        self.boardname = boardname
        self.threadOverviews = []
        if self.status >= 200 and self.status < 300:
            jason = r.json()
            if jason:  # Only do this if None wasn't returned
                for i in jason:
                    self.threadOverviews.append(thread(i, self))

    def refresh(self):
        global node
        global proxy
        cycleNode()
        r = requests.get(node + self.boardname + "-" + str(self.page) + ".json", proxies=proxy)
        self.status = r.status_code
        self.threadOverviews = []
        if self.status >= 200 and self.status < 300:
            jason = r.json()
            if jason:  # Only do this if None wasn't returned
                for i in jason:
                    self.threadOverviews.append(thread(i, self))

    def __iter__(self):
        self.iteratorIndex = 0
        return self

    def __next__(self):
        if self.iteratorIndex >= len(self):
            raise StopIteration
        else:
            toRet = self[self.iteratorIndex]
            self.iteratorIndex += 1
            return toRet

    def __len__(self):
        return len(self.threadOverviews)

    def __getitem__(self, key):
        return self.threadOverviews[key]

    def post(self, name, sub, msg, captcha, *files):
        global proxy
        global node
        global captchaID
        filesToUpload = [("", "")]
        # Ability to use same key for multiple files
        for i in files:
            filesToUpload.append(("attachment_uploaded", open(i, "rb")))

        postArgs = {
            "reference": "",
            "name": name,
            "subject": sub,
            "message": msg,
            "captcha": captcha,
            "captcha_id": captchaID,
            "pow": ""
        }
        header = {
        }
        r = requests.post(node + "post/" + self.boardname,
                          files=filesToUpload, data=postArgs, headers=header, proxies=proxy)
        return r.status_code


def cleanupCaptcha():
    global captchaID
    try:
        # Get rid of the last CAPTCHA so we don't fill /tmp/ with crap
        os.remove("/tmp/" + captchaID + ".png")
    except:
        pass


def getCaptcha():
    global captchaID
    global proxy
    cleanupCaptcha()
    r = requests.get(node + "captcha/img", proxies=proxy)
    captchaID = r.url[len(node + "captcha/"):-4]
    # Download the file
    with open("/tmp/" + captchaID + ".png", "wb") as f:
        for i in r:
            f.write(i)
    return "/tmp/" + captchaID + ".png"


class boardList():

    def __init__(self):
        global proxy
        cycleNode()
        r = requests.get(node + "boards.json", proxies=proxy)
        self.boards = r.json()

    def __getitem__(self, key):
        return self.boards[key]

    def __iter__(self):
        self.iteratorIndex = 0
        return self

    def __next__(self):
        if self.iteratorIndex >= len(self):
            raise StopIteration
        else:
            toRet = self[self.iteratorIndex]
            self.iteratorIndex += 1
            return toRet

    def __len__(self):
        return len(self.boards)
