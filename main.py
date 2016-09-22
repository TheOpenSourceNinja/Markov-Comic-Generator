#!/usr/bin/python2
# coding=utf-8

__version__ = "0.9"
#I feel almost done with this, so 0.9 for now. I'll probably change it to 1.0 if/when I figure out how to share images with other apps.

import six
import getopt
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont, ImageStat
from PIL.PngImagePlugin import PngInfo

import pygame
from generator import Generator
from idchecker import idChecker
from markovnode import MarkovNode
from uploader import DrupalUploader, WordPressUploader
import kivy
kivy.require("1.9.1") #my current version as of 2016-09-13. Beware of using older versions.
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics.texture import Texture
import string

idChecker = idChecker()

#Exit statuses
#These are copied from my /usr/include/sysexits.h. Only statuses possibly relevant to this program were copied.
EX_OK = 0 #No problems
EX_USAGE = 64 #Command line error
EX_DATAERR = 65 #Data format error
EX_NOINPUT = 66 #Input not openable
EX_CANTCREAT = 73 #Can't create output file
EX_NOPERM = 77 #Permission error

class MarkovApp( App ):
	
	class MarkovGUI( Widget ):
		def __init__( self,  **kwargs ):
			'''Initialize the generator object.
				Args:
					**kwargs: Ignored by this class, passed to parent class.
			'''
			super( MarkovApp.MarkovGUI, self ).__init__( **kwargs );
			#self.generateButton.bind( on_press=generateComics )
	
	def build( self ):
		'''Create whatever widgets the app needs to start. Other widgets may be created later.
		'''
		self.gui = MarkovApp.MarkovGUI();
		self.gui.generateButton.bind( on_press=self.generateComics )
		return self.gui
	
	def __init__( self ):
		super( MarkovApp, self ).__init__()
		self.silence = self.silenceDefault = False
		
		if not self.silence:
			six.print_( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )
		
		
		self.inDir = self.inDirDefault = "./data/"
		self.outTextFileName = self.outTextFileNameDefault = "default out.txt"
		self.outImageFileName = self.outImageFileNameDefault = "default out.png"
		self.numberOfComics = self.numberOfComicsDefault = 1
		self.saveForWeb = self.saveForWebDefault = False
		self.commentMark = self.commentMarkDefault = "}}" #If in the future we decide to use a different mark for comments, this is the only line we'll need to change.
		self.commandLineFont = None #If a font file is specified on the command line, this will be set.
		self.topImageFileName = None
		self.randomizeCapitals = self.randomizeCapitalsDefault = False
		self.WordPressURI = self.WordPressURIDefault = None
		self.loginName = self.loginNameDefault = None
		self.loginPassword = self.loginPasswordDefault = None
		self.shortName = self.shortNameDefault = None
		self.longName = None #longName's default is not specified here
		self.commandLineComicID = None
		self.noGUI = self.noGUIDefault = False
		
		self.wordBubblesDir = os.path.join( self.inDir, "word-bubbles" )
		self.fontsDir = os.path.join( self.inDir, "fonts" )
		self.imageDir = os.path.join( self.inDir, "images" )
		
		self.normalFontFile = self.findSuitableFont( preferBold = False, preferNormal = True )
		self.boldFontFile = self.findSuitableFont( preferBold = True, preferNormal = False )
		
		self.blogUploaders = []
		if self.WordPressURI is not None:
			self.blogUploaders.append( WordPressUploader( self.WordPressURI, self.loginName, self.loginPassword ) )
		
		self.generators = dict() #A dictionary of Markov chain generators, one per character. Moved this line out of the for loop so we don't have to waste time regenerating Markov graphs when two or more comics have the same characters in them. Search for "for speaker in speakers:\nif speaker not in generators:" - this was originally just above that.
		

	def stringFromNodes( self, nodeList, useFormatting = True ):
		'''Given a list of nodes, put them all into a string.
		'''
		result = ""
		for node in nodeList:
			prefix = ""
			postfix = ""
			
			if useFormatting:
				if node.isBold():
					prefix = "*" + prefix
					postfix = postfix + "*"
				if node.isItalic():
					prefix = "/" + prefix
					postfix = postfix + "/"
				if node.isUnderlined():
					prefix = "_" + prefix
					postfix = postfix + "_"
			
			result += prefix + node.word + postfix + " "
		result.rstrip()
		return result

	def findCharsPerLine( self, text, normalFont, maxWidth ):
		'''Find how many characters will fit within the specified width.
			Args:
				text: The string whose contents are used to test character width.
				normalFont: The font used to test character width.
				maxWidth: The maximum width in pixels.
			Returns:
				An integer indicating how many characters fit within maxWidth.
		'''
		
		if maxWidth < 1:
			maxWidth = 1
		
		charsPerLine = maxWidth // normalFont.getsize( "L" )[ 0 ] #Capital L is generaly a pretty wide character
		
		if charsPerLine < 1:
			charsPerLine = 1
		
		while normalFont.getsize( text[ :charsPerLine ] )[ 0 ] > maxWidth:
			charsPerLine -= 1
		
		if charsPerLine < 1:
			charsPerLine = 1
		
		return charsPerLine

	def rewrap_nodelistlist( self, nodeList, normalFont, boldFont, maxWidth, fontSize = 10, center=True ):
		'''Rewrap and center text.
			Args:
				nodeList: A list of nodes containing the text to be wrapped.
				normalFont: A non-bold font.
				boldFont: A bold font.
				maxWidth: The maximum width in pixels.
				fontSize: Ignored.
				center: A Boolean indicating whether text should be centered after wrapping. Spaces will be added around each line of text if true. Defaults to True.
			Returns:
				A list of lists of nodes.
		'''
		
		boldNodes = dict()
		italicNodes = dict()
		underlinedNodes = dict()
		for node in nodeList:
			boldNodes[ node ] = node.isBold()
			italicNodes[ node ] = node.isItalic()
			underlinedNodes[ node] = node.isUnderlined()
			if boldNodes[ node ]:
				node.font = boldFont
			else:
				node.font = normalFont
		
		lineList = []
		temp = []
		for node in nodeList:
			lineWidth = normalFont.getsize( self.stringFromNodes( lineList ) )[ 0 ]
			wordWidth = node.font.getsize( node.word )[ 0 ]
			if lineWidth + wordWidth <= maxWidth:
				lineList.append( node )
			elif wordWidth <= maxWidth:
				temp.append( lineList )#stringFromNodes( lineList, useFormatting = False ) )
				lineList = [ node ]
			else:
				#temp.append( stringFromNodes( lineList, useFormatting = False ) )#.rstrip() )
				#line = node.word + " "
				if "\N{SOFT HYPHEN}" in node.word:
					#Split on hyphens if there are any...
					splitted = node.word.split( "\N{SOFT HYPHEN}", 1 )
					firstSection = splitted[ 0 ] + "-"
					secondSection = splitted[ 1 ]
				elif "-" in node.word:
					splitted = node.word.split( "-", 1 )
					firstSection = splitted[ 0 ] + "-"
					secondSection = splitted[ 1 ]
				else:
					middle = len( node.word ) // 2
					firstSection = node.word[ :middle ] + "-"
					secondSection = node.word[ middle: ]
				
				firstSectionNode = MarkovNode( firstSection, node.isEnd, isBold = boldNodes[ node ], isItalic = italicNodes[ node ], isUnderlined = underlinedNodes[ node ], font = node.font )
				secondSectionNode = MarkovNode( secondSection, node.isEnd, isBold = boldNodes[ node ], isItalic = italicNodes[ node ], isUnderlined = underlinedNodes[ node ], font = node.font )
				lineList.append( firstSectionNode )
				temp.append( lineList )#stringFromNodes( lineList, useFormatting = False ) )
				lineList = [ secondSectionNode ]
		#line = line.rstrip()
		temp.append( lineList )#stringFromNodes( lineList, useFormatting = False ) )
		
		temp2 = []
		for nodeList in temp:
			line = []
			for node in nodeList:
				try:
					node.word = "".join( [ ch for ch in node.word if ch.isprintable() ] )
				except AttributeError:
					node.word = "".join( [ ch for ch in node.word if ch in string.printable ] )
				
				line.append( node )
			temp2.append( line )
		
		result = []
		for line in temp2:
			lineWidth = 0 #normalFont.getsize( line )[ 0 ]
			
			for node in line:
				lineWidth += normalFont.getsize( " " )[ 0 ] + node.font.getsize( node.word )[ 0 ]
			
			lineWidth -= normalFont.getsize( " " )[ 0 ]
			
			if center and lineWidth < maxWidth:
				difference = maxWidth - lineWidth
				spaceWidth = normalFont.getsize( " " )[ 0 ]
				if spaceWidth > 0 and spaceWidth < difference:
					difference = difference - spaceWidth
					numberOfSpaces = int( ( difference / spaceWidth ) // 2 )
					for i in range( numberOfSpaces ):
						line.insert( 0, MarkovNode( word="", nonRandomizedWord="", font=normalFont ) ) #Spaces get inserted between nodes, so these nodes are blank
					#line = spacesString + line
			result.append( line )
		
		return result



	def findSuitableFont( self, charToCheck = None, preferBold = False, preferNormal = True ):
		'''Find a font that fits the given requirements.
			Args:
				preferBold: A Boolean indicating whether bold fonts will be preferred over non-bold.
				preferNormal: A Boolean indicating whether fonts of the style "medium", "regular", or "normal" will be preferred.
			Returns:
				A string representing a path to a suitable font file, or None if none could be found.
			'''
		
		#There's no standard "comic" font style, so instead we use a list of known comic-ish font families. Feel free to add to the list or to reorder it however you want. Ubuntu Titling isn't very comic-ish; I just wanted something that doesn't resemble Arial or Times to come after Comic Sans.
		#families = [ "Nina Improved", "Nina", "Humor Sans", "Tomson Talks", "Nibby", "Vipond Comic LC", "Vipond Comic UC", "Comic Neue", "Comic Neue Angular", "Comic Relief", "Dekko", "Ruji's Handwriting Font", "Open Comic Font", "Comic Sans MS", "Ubuntu Titling" ]
		families = [ "ninaimproved", "nina", "humorsans", "tomsontalks", "nibby", "vipondcomiclc", "vipondcomicuc", "comicneue", "comicneueangular", "comicrelief", "dekko", "ruji'shandwritingfont", "opencomicfont", "comicsansms", "ubuntutitling" ]
		for family in families:
			fontFile = pygame.font.match_font( family, bold=preferBold )
			if fontFile is not None:
				break
		return fontFile

	def usage( self ):
		'''Print command line usage info.
		'''
		six.print_( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
		six.print_( "Usage: The program takes the following command line arguments:" )
		 #the first character of each of these should be U+1F78D, "black slightly small square":
		six.print_( "🞍 -a or --login-password: a password to log in to WordPress with. Only applicable in combination with --login-name and --WordPress-uri. Defaults to", self.loginPasswordDefault )
		six.print_( "🞍 -b or --long-name: The comic's name, long form. Used when uploading to blogs. Defaults to the short form." )
		six.print_( "🞍 -c or --comic-id: The ID number of a specific comic image to use. Useful for debugging. Defaults to a randomly selected ID." )
		six.print_( "🞍 -d or --short-name: The comic's name, short form. Used when uploading to blogs. Defaults to", self.shortNameDefault )
		six.print_( "🞍 -f or --font: The path to a font file to use." )
		six.print_( "🞍 -g or --generate: The number of comics to generate. Defaults to", self.numberOfComicsDefault )
		six.print_( "🞍 -h or --help: Display this usage info." )
		six.print_( "🞍 -i or --indir: The directory in which to look for inputs (must have fonts/, images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", self.inDirDefault )
		six.print_( "🞍 -l or --login-name: a username to log in to WordPress with. Only applicable in combination with --login-password and --WordPress-uri. Defaults to", self.loginNameDefault )
		six.print_( "🞍 -n or --no-gui: Do not show a GUI. Defaults to ", self.noGUIDefault )
		six.print_( "🞍 -o or --outtextfile: The name of a text file to save the resulting sentences to. Defaults to", self.outTextFileNameDefault )
		six.print_( "🞍 -p or --outimagefile: The name of an image file to save the resulting comic to. Numbers will be appended if multiple comics are generated. Defaults to", self.outImageFileNameDefault )
		six.print_( '🞍 -r or --randomize-capitals: Some comic fonts have alternate capital letter forms instead of lower-case letters. In that case, using random "upper-case" and "lower-case" letters actually results in all upper-case letters but with a somewhat more handwriting-like look. Defaults to', self.randomizeCapitalsDefault )
		six.print_( "🞍 -s or --silent: Prevents output on standard out. Defaults to", self.silenceDefault )
		six.print_( "🞍 -t or --top: The path to an image which will be appended at the top of each comic. Should be the same width as the comic images. Good for names or logos." )
		six.print_( "🞍 -u or --WordPress-uri: The URI of a WordPress blog's xmlrpc.php file. Specify this if you want the comic automatically uploaded as a blog post. Will probably require that --login-name and --login-password be specified too (this is up to WordPress, not us). Defaults to", self.WordPressURIDefault )
		six.print_( "🞍 -w or --saveforweb: If specified, saves the images using settings which result in a smaller file size, possibly at the expense of image quality." )


	def isWritable( self, fileName ):
		'''Tests whether a given file can be opened for writing.
			Args:
				fileName: A string representing the path to the file to be tested.
			Returns:
				True if file is writable, False otherwise
		'''
		if os.access( fileName, os.F_OK ): #file exists
			return os.access( fileName, os.W_OK )
		else: #file doesn't exist
			try:
				open( fileName, "w" )
			except OSError:
				return False
			else:
				os.remove( fileName )
				return True



	def parseOptions( self ):
		try:
			options, argsLeft = getopt.getopt( sys.argv[ 1: ], "swhni:o:p:g:f:t:ru:l:a:c:b:d:", [ "silent", "saveforweb", "help", "no-gui", "indir=", "outtextfile=", "outimagefile=", "generate=", "font=", "top=", "randomize-capitals", "WordPress-uri=", "login-name=", "login-password=", "comic-id=", "long-name=", "short-name=" ] )
		except getopt.GetoptError as error:
			six.print_( error )
			self.usage()
			sys.exit( EX_USAGE );

		for option in options:
			if option[ 0 ] == "-s" or option[ 0 ] == "--silent":
				self.silence = True
			elif option[ 0 ] == "-i" or option[ 0 ] == "--indir":
				self.inDir = option[ 1 ]
			elif option[ 0 ] == "-o" or option[ 0 ] == "--outtextfile":
				self.outTextFileName = option[ 1 ]
			elif option[ 0 ] == "-p" or option[ 0 ] == "--outimagefile":
				self.outImageFileName = option[ 1 ]
			elif option[ 0 ] == "-n" or option[ 0 ] == "--number":
				self.numberOfComics = int( option[ 1 ] )
			elif option[ 0 ] == "-w" or option[ 0 ] == "--saveforweb":
				self.saveForWeb = True
			elif option[ 0 ] == "-h" or option[ 0 ] == "--help":
				self.usage()
				sys.exit( EX_OK )
			elif option[ 0 ] == "-f" or option[ 0 ] == "--font":
				self.commandLineFont = option[ 1 ]
			elif option[ 0 ] == "-t" or option[ 0 ] == "--top":
				self.topImageFileName = option[ 1 ]
			elif option[ 0 ] == "-r" or option[ 0 ] == "--randomize-capitals":
				self.randomizeCapitals = True
			elif option[ 0 ] == "-u" or option[ 0 ] == "--WordPress-uri":
				self.WordPressURI = option[ 1 ]
			elif option[ 0 ] == "-l" or option[ 0 ] == "--login-name":
				self.loginName = option[ 1 ]
			elif option[ 0 ] == "-a" or option[ 0 ] == "--login-password":
				self.loginPassword = option[ 1 ]
			elif option[ 0 ] == "-d" or option[ 0 ] == "--short-name":
				self.shortName = option[ 1 ]
			elif option[ 0 ] == "-b" or option[ 0 ] == "--long-name":
				self.longName = option[ 1 ]
			elif option[ 0 ] == "-c" or option[ 0 ] == "--comic-id":
				self.commandLineComicID = option[ 1 ]

		if self.longName is None:
			self.longName = self.shortName


		#Verify user input
		#commandLineFont is not verified here; it will be verified when loading the font.
		if not os.path.isdir( self.inDir ):
			six.print_( "Error:", self.inDir, "is not a directory.", file=sys.stderr )
			exit( EX_NOINPUT )
		elif os.path.exists( self.outTextFileName ) and not os.path.isfile(self. outTextFileName ):
			six.print_( "Error:", self.outTextFileName, "is not a file.", file=sys.stderr )
			exit( EX_CANTCREAT )
		elif not self.isWritable( self.outTextFileName ):
			six.print_( "Error:", self.outTextFileName, "is not writable.", file=sys.stderr )
			exit( EX_CANTCREAT )
		elif os.path.exists( self.outImageFileName ) and not os.path.isfile( self.outImageFileName ):
			six.print_( "Error:",self. outImageFileName, "is not a file.", file=sys.stderr )
			exit( EX_CANTCREAT )
		elif not self.isWritable( self.outImageFileName ):
			six.print_( "Error:", self.outImageFileName, "is not writable.", file = sys.stderr )
			exit( EX_CANTCREAT )
		elif self.numberOfComics < 1:
			six.print_( "Error: Number of comics (", self.numberOfComics, ") is less than 1.", file=sys.stderr )
			exit( EX_USAGE )
		elif self.topImageFileName != None:
			if not os.path.exists( self.topImageFileName ):
				six.print_( "Error:", self.topImageFileName, "does not exist.", file=sys.stderr )
				exit( EX_NOINPUT )
			elif not os.path.isfile( self.topImageFileName ):
				six.print_( "Error:", self.topImageFileName, "is not a file.", file=sys.stderr )
				exit( EX_NOINPUT )
			elif not os.access( self.topImageFileName, os.R_OK ):
				six.print_( "Error:", self.topImageFileName, "is not readable (permission error - did you mess up a chmod?)", file = sys.stderr )
				exit( EX_NOPERM )
		elif self.loginName is not None and len( self.loginName ) < 1:
			six.print_( "Error: loginName has length zero." )
			exit( EX_USAGE )
		elif self.loginPassword is not None and len( self.loginPassword ) < 1:
			six.print_( "Error: loginPassword has length zero." )
			exit( EX_USAGE )
		elif ( self.commandLineComicID is not None ) and not idChecker.checkString( self.commandLineComicID ):
			six.print_( "Error:", self.commandLineComicID, "is not a valid comic ID" )
			exit( EX_USAGE )


	
	def generateComics( self, instance ):
		image = Image.new( mode="1", size=(0, 0) )
		for self.generatedComicNumber in range( self.numberOfComics ):
			try:
				if self.commandLineComicID is None:
					wordBubbleFileName = random.choice( os.listdir( self.wordBubblesDir ) )
				else:
					wordBubbleFileName = os.path.join( self.wordBubblesDir, self.commandLineComicID + ".tsv" )
			except IndexError as error:
				six.print_( error, file=sys.stderr )
				exit( EX_NOINPUT )
			
			if not self.silence:
				six.print_( "wordBubbleFileName:", wordBubbleFileName )
			
			if self.commandLineComicID is None:
				comicID = os.path.splitext( wordBubbleFileName )[ 0 ]
			else:
				comicID = self.commandLineComicID
			wordBubbleFileName = os.path.join( self.wordBubblesDir, wordBubbleFileName )
			if not self.silence:
				six.print_( "Loading word bubbles from", wordBubbleFileName )

			try:
				wordBubbleFile = open( wordBubbleFileName, mode="rt" )
			except OSError as error:
				six.print_( error, file=sys.stderr )
				exit( EX_NOINPUT )
			
			if not idChecker.checkFile( wordBubbleFile, wordBubbleFileName, self.commentMark ):
				six.print_( "Error: Word bubble file", wordBubbleFileName, "is not in the correct format." )
				exit( EX_DATAERR )
			
			lookForSpeakers = True
			speakers = []
			while lookForSpeakers:
				line = wordBubbleFile.readline()
				if len( line ) > 0:
					line = line.partition( self.commentMark )[0].strip()
					if len( line ) > 0:
						speakers = line.upper().split( "\t" )
						if len( speakers ) > 0:
							lookForSpeakers = False
				else:
					lookForSpeakers = False; #End of file reached, no speakers found
			
			if len( speakers ) == 0:
				six.print_( "Error: Word bubble file", wordBubbleFileName, "contains no speakers." )
				exit( EX_DATAERR )
			
			if not self.silence:
				six.print_( "These characters speak:", speakers )
			
			for speaker in speakers:
				if speaker not in self.generators:
					if not self.silence:
						six.print_( "Now building a Markov graph for character", speaker, "..." )
					newGenerator = Generator( charLabel = speaker, cm = self.commentMark, randomizeCapitals = self.randomizeCapitals )
					newGenerator.buildGraph( self.inDir )
					
					if not self.silence:
						newGenerator.showStats()
					
					self.generators[ speaker ] = newGenerator
			
			if not self.silence:
				six.print_( comicID )
			
			inImageFileName = os.path.join( self.imageDir, comicID + ".png" )
			
			try:
				image = Image.open( inImageFileName ).convert() #Text rendering looks better if we ensure the image's mode is not palette-based. Calling convert() with no mode argument does this.
			except IOError as error:
				six.print_( error, file=sys.stderr )
				exit( EX_NOINPUT )
			
			transcript = str( comicID ) + "\n"
			
			previousBox = ( int( -1 ), int( -1 ), int( -1 ), int( -1 ) ) #For detecting when two characters share a speech bubble; don't generate text twice.
			
			for line in wordBubbleFile:
				line = line.partition( self.commentMark )[ 0 ].strip()
				
				if len( line ) > 0:
					line = line.split( "\t" )
					character = line[ 0 ].rstrip( ":" ).strip().upper()
					
					try:
						generator = self.generators[ character ]
					except:
						six.print_( "Error: Word bubble file", wordBubbleFileName, "does not list", character, "in its list of speakers.", file=sys.stderr )
						exit( EX_DATAERR )
					
					topLeftX = int( line[ 1 ] )
					topLeftY = int( line[ 2 ] )
					bottomRightX = int( line[ 3 ] )
					bottomRightY = int( line[ 4 ] )
					
					box = ( topLeftX, topLeftY, bottomRightX, bottomRightY )
					
					if box != previousBox:
						previousBox = box
						
						text = ""
						nodeList = generator.generateSentences( 1 )[ 0 ]
						for node in nodeList:
							text += node.word + " "
						text.rstrip()
						
						oneCharacterTranscript = character + ": "
						oneCharacterTranscript += self.stringFromNodes( nodeList )
						if not self.silence:
							six.print_( oneCharacterTranscript )
						oneCharacterTranscript += "\n"
						transcript += oneCharacterTranscript
						
						wordBubble = image.crop( box )
						draw = ImageDraw.Draw( wordBubble )
						
						width = bottomRightX - topLeftX
						if width <= 0: #Width must be positive
							width = 1
						height = bottomRightY - topLeftY
						if height <= 0:
							height = 1
						
						size = int( height * 1.2 ) #Contrary to the claim by PIL's documentation, font sizes are apparently in pixels, not points. The size being requested is the height of a generic character; the actual height of any particular character will be approximately (not exactly) the requested size. We will try smaller and smaller sizes in the while loop below. The 1.2, used to account for the fact that real character sizes aren't exactly the same as the requested size, I just guessed an appropriate value.
						
						normalFont = ImageFont.truetype( self.normalFontFile, size = size )
						boldFont = ImageFont.truetype( self.boldFontFile, size = size )
						
						listoflists = self.rewrap_nodelistlist( nodeList, normalFont, boldFont, width, fontSize = size )
						
						margin = 0
						offset = originalOffset = 0
						goodSizeFound = False
						
						while not goodSizeFound:
							goodSizeFound = True
							totalHeight = 0
							for line in listoflists:
								
								lineWidth = 0
								lineHeight = 0
								for node in line:
									wordSize = normalFont.getsize( node.word + " " )
									lineWidth += wordSize[ 0 ]
									lineHeight = max( lineHeight, wordSize[ 1 ] )
								lineWidth -= normalFont.getsize( " " )[ 0 ]
								totalHeight += lineHeight
								if lineWidth > width:
									goodSizeFound = False
							
							if totalHeight > height:
								goodSizeFound = False
							
							if not goodSizeFound:
								size -= 1
								try:
									normalFont = ImageFont.truetype( self.normalFontFile, size = size )
									boldFont = ImageFont.truetype( self.boldFontFile, size = size )
								except IOError as error:
									six.print_( error, "\nUsing default font instead.", file=sys.stderr )
									normalFont = ImageFont.load_default()
									boldFont = ImageFont.load_default()
								listoflists = self.rewrap_nodelistlist( nodeList, normalFont, boldFont, width, fontSize = size )
						
						midX = int( wordBubble.size[ 0 ] / 2 )
						midY = int( wordBubble.size[ 1 ] / 2 )
						
						try: #Choose a text color that will be visible against the background
							backgroundColor = ImageStat.Stat( wordBubble ).mean #wordBubble.getpixel( ( midX, midY ) )
							textColorList = []
							
							useIntegers = False
							useFloats = False
							if wordBubble.mode.startswith( "1" ):
								bandMax = 1
								useIntegers = True
							elif wordBubble.mode.startswith( "L" ) or wordBubble.mode.startswith( "P" ) or wordBubble.mode.startswith( "RGB" ) or wordBubble.mode.startswith( "CMYK" ) or wordBubble.mode.startswith( "YCbCr" ) or wordBubble.mode.startswith( "LAB" ) or wordBubble.mode.startswith( "HSV" ):
								bandMax = 255
								useIntegers = True
							elif wordBubble.mode.startswith( "I" ):
								bandMax = 2147483647 #max for a 32-bit signed integer
								useIntegers = True
							elif wordBubble.mode.startswith( "F" ):
								bandMax = float( "infinity" )
								useFloats = True
							else: #I've added all modes currently supported according to Pillow documentation; this is for future compatibility
								bandMax = max( ImageStat.Stat( image ).extrema )
							
							for c in backgroundColor:
								d = bandMax - ( c * 1.5 )
								
								if d < 0:
									d = 0
								
								if useIntegers:
									d = int( d )
								elif useFloats:
									d = float( d )
								
								textColorList.append( d )
							
							if wordBubble.mode.endswith( "A" ): #Pillow supports two modes with alpha channels
								textColorList[ -1 ] = bandMax
							
							textColor = tuple( textColorList )
							
						except ValueError:
							textColor = "black"
						
						offset = originalOffset
						for line in listoflists:
							xOffset = 0
							yOffsetAdditional = 0
							for node in line:
								usedFont = node.font
								draw.text( ( margin + xOffset, offset ), node.word + " ", font = usedFont, fill = textColor )
								tempSize = usedFont.getsize( node.word + " " )
								xOffset += tempSize[ 0 ]
								yOffsetAdditional = max( yOffsetAdditional, tempSize[ 1 ] )
								node.unselectStyle()
							offset += yOffsetAdditional
						
						image.paste( wordBubble, box )
						
			wordBubbleFile.close()
			
			if self.numberOfComics > 1:
				oldOutTextFileName = self.outTextFileName
				temp = os.path.splitext(self.outTextFileName )
				self.outTextFileName = temp[ 0 ] + str( self.generatedComicNumber ) + temp[ 1 ]
			
			#---------------------------Split into separate function
			try:
				#os.makedirs( os.path.dirname( outTextFileName ), exist_ok = True )
				outFile = open( self.outTextFileName, mode="wt" )
			except OSError as error:
				six.print_( error, "\nUsing standard output instead", file=sys.stderr )
				outFile = sys.stdout
			
			if self.numberOfComics > 1:
				self.outTextFileName = oldOutTextFileName
			
			six.print_( transcript, file=outFile )
			
			outFile.close()
			
			if self.numberOfComics > 1:
				oldOutImageFileName = self.outImageFileName
				temp = os.path.splitext( self.outImageFileName )
				outImageFileName = temp[ 0 ] + str( self.generatedComicNumber ) + temp[ 1 ]
			
			if self.topImageFileName != None:
				try:
					topImage = Image.open( self.topImageFileName ).convert( mode=image.mode )
				except IOError as error:
					six.print_( error, file=sys.stderr )
					exit( EX_NOINPUT )
				oldSize = topImage.size
				size = ( max( topImage.size[ 0 ], image.size[ 0 ] ), topImage.size[ 1 ] + image.size[ 1 ] )
				
				newImage = Image.new( mode=image.mode, size=size )
				newImage.paste( im=topImage, box=( 0, 0 ) )
				newImage.paste( im=image, box=( 0, oldSize[ 1 ] ) )
				image = newImage
			
			
			
			originalURL = None
			URLFile = open( os.path.join( self.inDir, "sources.tsv" ), "rt" )
			for line in URLFile:
				line = line.partition( self.commentMark )[ 0 ].strip()
				
				if len( line ) > 0:
					line = line.split( "\t" )
					
					if comicID == line[ 0 ]:
						originalURL = line[ 1 ]
						break;
			URLFile.close()
			
			transcriptWithURL = transcript + "\n" + originalURL #The transcript that gets embedded into the image file should include the URL. The transcript that gets uploaded to blogs doesn't need it, as the URL gets sent anyway.
			
			infoToSave = PngInfo()
			
			encodingErrors = "backslashreplace" #If we encounter errors during text encoding, I feel it best to replace unencodable text with escape sequences; that way it may be possible for reader programs to recover the original unencodable text.
			
			#According to the Pillow documentation, key names should be "latin-1 encodable". I take this to mean that we ourselves don't need to encode it in latin-1.
			key = "transcript"
			keyUTF8 = key.encode( "utf-8", errors=encodingErrors )
			
			#uncomment the following if using Python 3
			#transcriptISO = transcriptWithURL.encode( "iso-8859-1", errors=encodingErrors )
			#transcriptUTF8 = transcriptWithURL.encode( "utf-8", errors=encodingErrors )
			
			#python 2:
			tempencode = transcriptWithURL.decode( 'ascii', errors='replace' ) # I really don't like using this ascii-encoded intermediary called tempencode, but i couldn't get the program to work when encoding directly to latin-1
			transcriptISO = tempencode.encode( "iso-8859-1", errors='replace' )
			transcriptUTF8 = tempencode.encode( "utf-8", errors='replace' )
			
			
			infoToSave.add_itxt( key=key, value=transcriptUTF8, tkey=keyUTF8 )
			infoToSave.add_text( key=key, value=transcriptISO )
			
			#GIMP only recognizes comments
			key = "Comment"
			keyUTF8 = key.encode( "utf-8", errors=encodingErrors )
			
			infoToSave.add_text( key=key, value=transcriptISO )
			infoToSave.add_itxt( key=key, value=transcriptUTF8, tkey=keyUTF8 )
			
			try:
				#os.makedirs( os.path.dirname( outImageFileName ), exist_ok = True )
				if self.saveForWeb:
					image = image.convert( mode = "P", palette="ADAPTIVE", dither=False ) #Try turning dithering on or off.
					image.save( self.outImageFileName, format="PNG", optimize=True, pnginfo=infoToSave )
				else:
					image.save( self.outImageFileName, format="PNG", pnginfo=infoToSave )
			except IOError as error:
				six.print_( error, file = sys.stderr )
				exit( EX_CANTCREAT )
			except OSError as error:
				six.print_( error, file = sys.stderr )
				exit( EX_CANTCREAT )
			
			if not self.silence:
				six.print_( "Original comic URL:", originalURL )
			
			for blog in self.blogUploaders:
				blog.upload( postStatus = "publish", inputFileName = outImageFileName, shortComicTitle = self.shortName, longComicTitle = self.longName, transcript = transcript, originalURL = originalURL, silence = self.silence )
			
			if self.numberOfComics > 1:
				outImageFileName = oldOutImageFileName
		#end of loop: for generatedComicNumber in range( numberOfComics ):
		
		#---------------------------It's display time!
		if image.mode != "RGB":
			image = image.convert( mode = "RGB" )
		self.gui.comicArea.texture = Texture.create( size = image.size, colorfmt = 'rgb' )
		self.gui.comicArea.texture.blit_buffer( pbuffer = image.transpose( Image.FLIP_TOP_BOTTOM ).tobytes(), colorfmt = 'rgb' )
	
	def runGUI( self ):
		self.run()

if __name__ == "__main__":
	m = MarkovApp()
	m.parseOptions()
	if m.noGUI:
		m.generateComics()
	else:
		m.runGUI()

exit( EX_OK )
