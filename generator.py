#!/usr/bin/python3

import random
import os
import sys

class Generator:
	class MarkovNode:
		def __init__( self, isEnd ):
			'''Initialize. Duh.
				Args:
					isEnd: A Boolean indicating whether this node is the end of a sentence.
			'''
			self.links = dict()
			self.isEndOfSentence = isEnd
	
		def getRandomLinkedWord( self ):
			'''Randomly select one of the nodes to which this node is linked.
			'''
			return random.choice( list( self.links.keys() ) ) #TODO: Use weighted randomness
	
		def hasLinks( self ):
			'''Determine whether this node has any links.
			'''
			return len( self.links ) > 0
	
		def addLink( self, other ):
			'''Add to this node a link to another node.
				Args:
					other: The other node to which to link.
				Returns:
					The number of links this node has after adding the new link.
			'''
			if other not in self.links:
				self.links[ other ] = 1
			else:
				self.links[ other ] += 1 #If there is already a link to the other node, increase the link's value.
			return len( self.links )
	
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
		
			keepLookingForHeader = True
			headerFound = False
		
			while keepLookingForHeader:
				line = inFile.readline().partition( self.commentMark )[0].strip()
				if line.isnumeric() and line == os.path.splitext( os.path.basename( inFileName ) )[0]: #Why enforce the file name requirement? It's about people, not code: it's to make sure transcribers have read all available documentation (README.md) about the transcription format.
					keepLookingForHeader = False
					headerFound = True
				elif len(line) > 0:
					keepLookingForHeader = False
			
			if not headerFound:
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
								self.nodes[ word ] = self.MarkovNode( isEnd )
							if not previousWord == "":
								if self.nodes[ previousWord ].isEndOfSentence and ( word not in self.sentenceStarts ):
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
