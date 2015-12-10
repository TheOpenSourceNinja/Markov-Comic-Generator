#!/usr/bin/python3

import os
import random
import sys

from idchecker import idChecker
from markovnode import MarkovNode


class Generator:
	def __init__( self, charLabel, cm = "//", randomizeCapitals = False ):
		'''Just does what the name implies.
			Args:
				charLabel: A string naming which comic character this generator represents.
				cm: A string used to mark the beginning of comments. Including it here ensures that this object will use the same kind of comment marker as the rest of the program. Defaults to "//".
				randomizeCapitals: Whether to randomize the capitalization of each letter.
		'''
		self.charLabel = charLabel.upper()
		self.lines = []
		self.commentMark = cm
		self.randomizeCapitals = randomizeCapitals
	
	def randomBoolean( self, probability = 0.5 ):
		'''Get a random true or false value, with the given probability of being true.
			Args:
				probability: a number between 0.0 and 1.0 inclusive. Defaults to 0.5.
			Returns:
				A Boolean.
		'''
		if probability < 0 or probability > 1:
			raise ValueError( "probability must be between 0 and 1 inclusive" )
		
		return( random.random() <= probability )
	
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
			previousWord = None
			for line in self.lines:
				if( len( line ) > 0 ):
					for word in line:
						isBold = "*" in word
						isItalic = "/" in word
						isUnderlined = "_" in word
						word = word.strip("*/_") #Remove emphasis
						
						if len( word ) > 0:
							isEnd = ( word.endswith( ( ".", "?", "!", '."', '?"', '!"', ".'", "?'", "!'" ) ) or word == line[ -1 ].strip("*/_") )
			
							if word not in self.nodes.keys():
								wordRandomized = ""
								if self.randomizeCapitals:
									for letter in word:
										if self.randomBoolean():
											letter = letter.upper()
										else:
											letter = letter.lower()
										wordRandomized += letter
								else:
									wordRandomized = word
								self.nodes[ word ] = MarkovNode( wordRandomized, word, isEnd )
								
							if not previousWord == None:
								if self.nodes[ previousWord ].isEnd:
									self.sentenceStarts.append( word )
								else:
									self.nodes[ previousWord ].addLink( self.nodes[ word ] )
							else:
								if word not in self.sentenceStarts:
									self.sentenceStarts.append( word )
							
							if isBold:
								self.nodes[ word ].addBold()
							if isItalic:
								self.nodes[ word ].addItalic()
							if isUnderlined:
								self.nodes[ word ].addUnderlined()
							
							if not isBold and not isItalic and not isUnderlined:
								self.nodes[ word ].addNormal()
							
							previousWord = word
			
	def generateSentences(self, numberOfSentences = 1):
		'''Generate some number of sentences (paths through the Markov graph).
			Args:
				numberOfSentences: The number of sentences to generate. Defaults to 1.
			Returns:
				A list of ( lists of( Markov nodes ) ), each Markov node representing one word and each list of Markov nodes representing one sentence.
		'''
		result = []
		for i in range ( numberOfSentences ):
			currentWord = random.choice( self.sentenceStarts )
			sentence = [ self.nodes[ currentWord ] ]
			while self.nodes[ currentWord ].hasLinks() and not self.nodes[ currentWord ].isEnd:
				currentWord = self.nodes[ currentWord ].getRandomLinkedNode().nonRandomizedWord
				#sentence += " " + currentWord
				sentence.append( self.nodes[ currentWord ] )
			
			result.append( sentence )
		return result
