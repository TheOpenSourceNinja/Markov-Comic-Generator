#!/usr/bin/python3

import random
import os
import sys
from idchecker import idChecker
from markovnode import MarkovNode

class Generator:
	def __init__( self, charLabel, cm = "//" ):
		'''Just does what the name implies.
			Args:
				charLabel: A string naming which comic character this generator represents.
				cm: A string used to mark the beginning of comments. Including it here ensures that this object will use the same kind of comment marker as the rest of the program. Defaults to "//".
		'''
		self.charLabel = charLabel.upper()
		self.lines = []
		self.commentMark = cm
	
	def buildGraph( self, inDir ):
		'''Build the Markov graph for this generator's comic character.
			Args:
				inDir: The directory in which to find the 'transcripts' subdirectory. The 'transcripts' subdirectory is where we will actually look for everything.
		'''
		transcriptDir = os.path.join( inDir, "transcripts" )
		for inFileName in os.listdir( transcriptDir ):
			inFileName = os.path.join( transcriptDir, inFileName )
			inFile = open( file=inFileName, mode="rt" )
			
			idc = idChecker()
			if not idc.checkFile( inFile, inFileName, self.commentMark ):
				print( "Error: File", inFileName, "is not a properly formatted transcript.", file=sys.stderr )
				break;
		
			for line in inFile:
				line = line.partition( self.commentMark )[0].strip()
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
						word = word.strip("*/_") #Remove emphasis
						word = word.strip() #Remove whitespace
						if len( word ) > 0:
							isEnd = ( word.endswith( ( ".", "?", "!", '."', '?"', '!"', ".'", "?'", "!'" ) ) or word == line[ -1 ] )
			
							if word not in self.nodes.keys():
								self.nodes[ word ] = MarkovNode( isEnd )
							if not previousWord == "":
								if self.nodes[ previousWord ].isEndOfSentence:
									self.sentenceStarts.append( word )
								else:
									self.nodes[ previousWord ].addLink( word )
				
							else:
								if word not in self.sentenceStarts:
									self.sentenceStarts.append( word )
			
							previousWord = word
			
	def generateSentences(self, numberOfSentences = 1):
		'''Generate some number of sentences (paths through the Markov graph).
			Args:
				numberOfSentences: The number of sentences to generate. Defaults to 1.
			Returns:
				A list of strings, each string containing one sentence.
		'''
		result = []
		for i in range ( numberOfSentences ):
			currentWord = random.choice( self.sentenceStarts )
			sentence = currentWord
			while self.nodes[ currentWord ].hasLinks() and not self.nodes[ currentWord ].isEndOfSentence:
				currentWord = self.nodes[ currentWord ].getRandomLinkedWord()
				sentence += " " + currentWord
			
			result.append( sentence )
		return result
