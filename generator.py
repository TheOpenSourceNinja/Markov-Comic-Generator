#!/usr/bin/python3

import getopt
import sys
import random

def usage():
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out." ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --infile: The name of a file to read as input." )
	print( "🞍 -o or --outfile: The name of a file to save the resulting sentences to." )
	print( "🞍 -n or --number: The number of sentences to generate (defaults to 1)." )

silence = False
inFileName = "default in.txt"
outFileName = "default out.txt"
numberOfSentences = 1

try:
	options, argsLeft = getopt.getopt( sys.argv[1:], "si:o:n:", ["silent", "infile=", "outfile=", "number="] )
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
	elif option[0] == "-n" or option[0] == "--number":
		numberOfSentences = int( option[1].strip( "=" ) )

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

inFile = open( file=inFileName, mode="rt" )

lines = []
for line in inFile:
	lines.append( line.strip().split() )

inFile.close()

class MarkovNode:
	def __init__( self, isEnd ):
		self.links = dict()
		self.isEndOfSentence = isEnd
	
	def getRandomLinkedWord( self ):
		return random.choice( list( self.links.keys() ) ) #TODO: Use weighted randomness
	
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
	if( len( line ) > 0 ):
		for word in line:
			isEnd = word.endswith( ( ".", "?", "!", '."', '?"', '!"' ) )
		
			if word not in nodes.keys():
				nodes[ word ] = MarkovNode( isEnd )
			if not previousWord == "":
				if nodes[ previousWord ].isEndOfSentence:
					sentenceStarts.append( word )
				else:
					numLinks = nodes[ previousWord ].addLink( word )
				
			else:
				sentenceStarts.append( word )
		
			previousWord = word

outFile = open( file=outFileName, mode="at" )

for i in range ( numberOfSentences ):
	currentWord = random.choice( sentenceStarts )
	sentence = currentWord
	while nodes[ currentWord ].hasLinks() and not nodes[ currentWord ].isEndOfSentence:
		currentWord = nodes[ currentWord ].getRandomLinkedWord()
		sentence += " " + currentWord

	print( sentence, file=outFile )
	if not silence:
		print( sentence )

outFile.close()
