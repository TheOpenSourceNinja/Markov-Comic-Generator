#!/usr/bin/python3

import getopt
import sys
import random

def usage():
	print( "Usage: Right now the program only takes one argument, -s, or its long form, --silent." )

silence = False
inFileName = "default in.txt"
outFileName = "default out.txt"

try:
	options, argsLeft = getopt.getopt( sys.argv[1:], "sio", ["silent", "infile", "outfile"] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit(2);

for option in options:
	if option[0] == "-s" or option[0] == "--silence":
		silence = True
	elif option[0] == "-i" or option[0] == "--infile":
		inFileName = option[1]
	elif option[0] == "-o" or option[0] == "--outfile":
		outFileName = option[1]

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

inFile = open( inFileName )

lines = []
for line in inFile:
	lines.append( line.strip().split() )

class MarkovNode:
	def __init__( self, isEnd ):
		self.links = dict()
		self.isEndOfSentence = isEnd
	
	def getRandomLinkedWord( self ):
		return random.choice( list( self.links.keys() ) )
	
	def hasLinks( self ):
		return len( self.links ) > 0
	
	def addLink( self, other ):
		if other not in self.links:
			self.links[ other ] = 1
		else:
			self.links[ other ] += 1
		return len( self.links )

nodes = dict()
sentenceStarts = []
previousWord = ""
for line in lines:
	for word in line:
		isEnd = "." in word
		if isEnd:
			word = word.strip( "." )
		
		if word not in nodes.keys():
			nodes[ word ] = MarkovNode( isEnd )
		if not previousWord == "":
			numLinks = nodes[ previousWord ].addLink( word ) #nodes[ word ] )
			if nodes[ previousWord ].isEndOfSentence:
				sentenceStarts.append( word )
		else:
			sentenceStarts.append( word )
		
		previousWord = word

currentWord = random.choice( sentenceStarts )
sentence = currentWord
while nodes[ currentWord ].hasLinks() and not nodes[ currentWord ].isEndOfSentence:
	currentWord = nodes[ currentWord ].getRandomLinkedWord()
	sentence += " " + currentWord

sentence += "."
print( sentence )
