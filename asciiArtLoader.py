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
class asciiImg():

    def __init__(self, asciiFile):
        self.height = 0
        self.width = 0
        self.data = []
        with open(asciiFile, 'r') as file:
            for i in file:
                self.height += 1
                self.width = max(len(i), self.width)
                self.data.append(i.rstrip())  # Remove newlines and append

    def __getitem__(self, key):
        return self.data[key]

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
        return len(self.data)
