#!/usr/bin/python2
# coding=utf-8

from __future__ import division
import random

class MarkovNode:
	def __init__( self, word, nonRandomizedWord, isEnd = False, isBold = False, isItalic = False, isUnderlined = False, font = None ):
		'''Initialize. Duh.
			Args:
				word: The word this node represents. May or may not have randomized capitalization.
				nonRandomizedWord: The non-randomized version of the word.
				isEnd: A Boolean indicating whether this node is the end of a sentence.
				isBold: Whether this node, newly created, represents a bold word (after the node is created, this status can be affected by calling addBold() or addNormal() )
				isItalic: Whether this node, newly created, represents an italic word (after the node is created, this status can be affected by calling addItalic() or addNormal() )
				isUnderlined: Whether this node, newly created, represents an underlined word (after the node is created, this status can be affected by calling addUnderlined() or addNormal() )
				font: The PIL ImageFont associated with this node.
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
		if not isBold and not isItalic and not isUnderlined:
			self.addNormal()
		
		self.boldDecided = False #We only want to randomly decide boldness once
		self.bold = False
		self.italicDecided = False #We only want to randomly decide boldness once
		self.italic = False
		self.underlinedDecided = False #We only want to randomly decide boldness once
		self.underlined = False
		
		self.word = word
		self.nonRandomizedWord = nonRandomizedWord
		self.font = font
	
	def unselectStyle( self ):
		'''Set boldDecided, italicDecided, and underlinedDecided to False.
		'''
		self.boldDecided = False
		self.italicDecided = False
		self.underlinedDecided = False
	
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
	
	def isBold( self ):
		'''Determine randomly whether this node should be rendered as bold text.
		'''
		if not self.boldDecided:
			self.bold = self.randomBoolean( self.numBold / self.numTotal )
			self.boldDecided = True
		
		return self.bold
	
	def isItalic( self ):
		'''Determine randomly whether this node should be rendered as italicized text.
		'''
		if not self.italicDecided:
			self.italic = self.randomBoolean( self.numItalic / self.numTotal )
			self.italicDecided = True
			
		return self.italic
	
	def isUnderlined( self ):
		'''Determine randomly whether this node should be rendered as underlined text.
		'''
		if not self.underlinedDecided:
			self.underlined = self.randomBoolean( self.numUnderlined / self.numTotal )
			self.underlinedDecided = True
		
		return self.underlined
	
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
