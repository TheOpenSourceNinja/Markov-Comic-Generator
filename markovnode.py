#!/usr/bin/python3

import random

class MarkovNode:
	def __init__( self, word, isEnd = False, isBold = False, isItalic = False, isUnderlined = False ):
		'''Initialize. Duh.
			Args:
				isEnd: A Boolean indicating whether this node is the end of a sentence.
		'''
		self.links = []
		self.isEnd = isEnd
		
		self.numTotal = 0
		self.numBold = 0
		self.numItalic = 0
		self.numUnderlined = 0
		
		if isBold:
			self.addBold()
		if isItalic:
			self.addItalic()
		if isUnderlined:
			self.addUnderlined()
		
		self.word = word
		self.font = None #Will be set in main.py
	
	def randomBoolean( self, probability ):
		'''Get a random true or false value, with the given probability of being true.
			Args:
				probability: a number between 0.0 and 1.0 inclusive.
			Returns:
				A Boolean.
		'''
		if probability < 0 or probability > 1:
			raise ValueError( "probability must be between 0 and 1 inclusive" )
		
		return( random.random() <= probability )
	
	def isBold( self ):
		'''Determine randomly whether this node should be rendered as bold text.
		'''
		return self.randomBoolean( self.numBold / self.numTotal )
	
	def isItalic( self ):
		'''Determine randomly whether this node should be rendered as italicized text.
		'''
		return self.randomBoolean( self.numItalic / self.numTotal )
	
	def isUnderlined( self ):
		'''Determine randomly whether this node should be rendered as underlined text.
		'''
		return self.randomBoolean( self.numUnderlined / self.numTotal )
	
	def addNormal( self ):
		'''Increment the total counter only.
		'''
		self.numTotal += 1
	
	def addBold( self ):
		'''Increment the bold and total counters.
		'''
		self.numBold += 1
		self.numTotal += 1
	
	def addItalic( self ):
		'''Increment the italic and total counters.
		'''
		self.numItalic += 1
		self.numTotal += 1
	
	def addUnderlined( self ):
		'''Increment the underlined and total counters.
		'''
		self.numUnderlined += 1
		self.numTotal += 1

	def getRandomLinkedNode( self ):
		'''Randomly select one of the nodes to which this node is linked.
		'''
		return random.choice( self.links )

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
		self.links.append( other )
		#if other not in self.links:
		#	self.links[ other ] = 1
		#else:
		#	self.links[ other ] += 1 #If there is already a link to the other node, increase the link's value.
		return len( self.links )
