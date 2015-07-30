#!/usr/bin/python3

import random
import os

class Generator:
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
	
	def __init__( self, charLabel ):
		self.charLabel = charLabel.upper()
		self.lines = []
	
	def buildDatabase( self, inDir ):
		transcriptDir = os.path.join( inDir, "transcripts" )
		for inFileName in os.listdir( transcriptDir ):
			inFileName = os.path.join( transcriptDir, inFileName )
			inFile = open( file=inFileName, mode="rt" )
		
			keepLookingForHeader = True
			headerFound = False
		
			while keepLookingForHeader:
				line = inFile.readline()
				line = line.partition( "//" )[0].strip()
				if line.isnumeric() and line == os.path.basename( inFileName ):
					keepLookingForHeader = False
					headerFound = True
				elif len(line) > 0:
					keepLookingForHeader = False
		
			for line in inFile:
				line = line.partition( "//" )[0].strip()
				if( len( line ) > 0 ):
					line = line.split()
					speaker = line[0].rstrip(":").strip()
					if speaker.upper() == self.charLabel:
						dialog = line[1:]
						self.lines.append( dialog )
		
			inFile.close()
		
			self.nodes = dict()
			self.sentenceStarts = []
			previousWord = ""
			for line in self.lines:
				if( len( line ) > 0 ):
					for word in line:
						word = word.strip("*/") #Remove emphasis
						word = word.strip() #Remove whitespace
						if len( word ) > 0:
							isEnd = word.endswith( ( ".", "?", "!", '."', '?"', '!"' ) ) or word == line[-1]
		
							if word not in self.nodes.keys():
								self.nodes[ word ] = self.MarkovNode( isEnd )
							if not previousWord == "":
								if self.nodes[ previousWord ].isEndOfSentence:
									self.sentenceStarts.append( word )
								else:
									numLinks = self.nodes[ previousWord ].addLink( word )
				
							else:
								self.sentenceStarts.append( word )
		
							previousWord = word

	def generate(self, numberOfSentences):
		result = ""
		for i in range ( numberOfSentences ):
			currentWord = random.choice( self.sentenceStarts )
			sentence = currentWord
			while self.nodes[ currentWord ].hasLinks() and not self.nodes[ currentWord ].isEndOfSentence:
				currentWord = self.nodes[ currentWord ].getRandomLinkedWord()
				sentence += " " + currentWord
			
			result += sentence + " "
		return result


