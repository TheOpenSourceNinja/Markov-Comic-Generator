#!/usr/bin/python3

import getopt
import sys
import random
import os
import fontconfig
import textwrap
from PIL import Image, ImageFont, ImageDraw, ImageColor, ImageStat
from PIL.PngImagePlugin import PngInfo
from generator import Generator
from idchecker import idChecker
from markovnode import MarkovNode

#Exit statuses
#These are copied from my /usr/include/sysexits.h. Only statuses possibly relevant to this program were copied.
EX_OK = 0 #No problems
EX_USAGE = 64 #Command line error
EX_DATAERR = 65 #Data format error
EX_NOINPUT = 66 #Input not openable
EX_CANTCREAT = 73 #Can't create output file
EX_NOPERM = 77 #Permission error

#Set defaults
silence = silenceDefault = False
inDir = inDirDefault = "./"
outTextFileName = outTextFileNameDefault = "default out.txt"
outImageFileName = outImageFileNameDefault = "default out.png"
numberOfComics = numberOfComicsDefault = 1
saveForWeb = saveForWebDefault = False
commentMark = commentMarkDefault = "//" #If in the future we decide to use a different mark for comments, this is the only line we'll need to change.
commandLineFont = None #If a font file is specified on the command line, this will be set.
topImageFileName = None
randomizeCapitals = randomizeCapitalsDefault = False

def stringFromNodes( nodeList, useFormatting = True ):
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

def findCharsPerLine( text, normalFont, maxWidth ):
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
	
	charsPerLine = maxWidth // normalFont.getsize( "L" )[0]
	
	if charsPerLine < 1:
		charsPerLine = 1
	
	while normalFont.getsize( text[ :charsPerLine ] )[0] > maxWidth:
		charsPerLine -= 1
	
	if charsPerLine < 1:
		charsPerLine = 1
	
	return charsPerLine

def rewrap_nodelistlist( nodeList, normalFont, boldFont, maxWidth, fontSize = 10, center=True ):
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
		#print( "number:", number, "node:", node )
		lineWidth = normalFont.getsize( stringFromNodes( lineList ) )[ 0 ]
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
			node.word = "".join( [ ch for ch in node.word if ch.isprintable() ] )
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
				#print( "numberOfSpaces:", numberOfSpaces )
				for i in range( numberOfSpaces ):
					line.insert( 0, MarkovNode( word="", nonRandomizedWord="", font=normalFont ) ) #Spaces get inserted between nodes, so these nodes are blank
				#line = spacesString + line
		result.append( line )
	
	return result



def findSuitableFont( fontsDir = "fonts", charToCheck = None, size = 10, commandLineFont = None, preferBold = False, preferNormal = True ):
	fontLoaded = False
	fontFile = None
	
	if not silence:
		print( "fontsDir is", fontsDir, "and commandLineFont is", commandLineFont )
		if preferBold:
			print( "Looking for a BOLD font." )
	
	if commandLineFont is None:
		commandLineFont = ""
	
	try:
		if not silence:
			print( "Trying to load font from file", commandLineFont )
		normalFont = ImageFont.truetype( commandLineFont, size=size )
		fontFile = commandLineFont
		fontLoaded = True
		if preferBold:
			testFile = fontconfig.FcFont( commandLineFont )
			fontLoaded = False
			for language, style in testFile.style:
				if language.lower() == "en":
					if style.lower() == "bold":
						fontLoaded = True
				#default
				if style.lower() == "bold":
					fontLoaded = True
			if not fontLoaded and not silence:
				print( "The command line font is not bold." )
		elif preferNormal:
			testFile = fontconfig.FcFont( commandLineFont )
			fontLoaded = False
			for language, style in testFile.style:
				if language.lower() == "en":
					if style.lower() == "medium" or style.lower() == "regular":
						fontLoaded = True
				#default
				if style.lower() == "medium" or style.lower() == "regular":
					fontLoaded = True
			if not fontLoaded and not silence:
				print( "The command line font is not normal." )
	except ( IOError, OSError ):
		pass
	
	if not fontLoaded:
		fileList = os.listdir( fontsDir )
		for testFileName in fileList:
			testFileName = os.path.join( fontsDir, testFileName )
			if not silence:
				print( "Trying to load font from file", testFileName )
			try:
				testFile = fontconfig.FcFont( testFileName )
				if not silence:
					print( "Trying to load font", testFile.fullname, "from file", testFile.file )
				if charToCheck == None or testFile.has_char( charToCheck ):
					normalFont = ImageFont.truetype( testFile.file, size=size )
					fontLoaded = True
					fontFile = testFile.file
					if preferBold:
						#testFile = fontconfig.FcFont( fontFile )
						fontLoaded = False
						fontFile = None
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "bold":
									fontLoaded = True
									fontFile = testFile.file
							#default
							if style.lower() == "bold":
								fontLoaded = True
								fontFile = testFile.file
						if not silence:
							if not fontLoaded:
								print( "This font is not bold." )
							else:
								print( "This font is bold." )
					elif preferNormal:
						testFile = fontconfig.FcFont( fontFile )
						fontLoaded = False
						fontFile = None
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "medium" or style.lower() == "regular":
									fontLoaded = True
									fontFile = testFile.file
							#default
							if style.lower() == "medium" or style.lower() == "regular":
								fontLoaded = True
								fontFile = testFile.file
						if not silence:
							if not fontLoaded:
								print( "This font is not normal." )
							else:
								print( "This font is normal." )
					if fontLoaded:
						break
			except ( IOError, OSError ):
				pass
		
		if not fontLoaded:
			families = [ "Nina", "Humor Sans", "Tomson Talks", "Nibby", "Vipond Comic LC", "Vipond Comic UC", "Comic Neue", "Comic Relief", "Dekko", "Ruji's Handwriting Font", "Open Comic Font", "Comic Sans MS", "Ubuntu Titling" ]
			for family in families:
				if fontLoaded:
					break
				fontList = fontconfig.query( family=family )
				for testFileName in fontList:
					if fontLoaded:
						break
					testFile = fontconfig.FcFont( testFileName )
					valid = False
					if preferBold:
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "bold":
									valid = True
									break
							if style.lower() == "bold":
								valid = True
								break;
						if valid:
							if not silence:
								print( "This font is bold." )
							try:
								if not silence:
									print( "Trying to load font", testFile.fullname, "from file", testFile.file )
								if charToCheck == None or testFile.has_char( charToCheck ):
									normalFont = ImageFont.truetype( testFile.file, size=size )
									fontLoaded = True
									fontFile = testFile.file
									break
							except ( IOError, OSError ):
								pass
					elif preferNormal:
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "medium" or style.lower() == "regular":
									valid = True
									break
							if style.lower() == "medium" or style.lower() == "regular":
								valid = True
								break;
						if valid:
							if not silence:
								print( "This font is normal." )
							try:
								if not silence:
									print( "Trying to load font", testFile.fullname, "from file", testFile.file )
								if charToCheck == None or testFile.has_char( charToCheck ):
									normalFont = ImageFont.truetype( testFile.file, size=size )
									fontLoaded = True
									fontFile = testFile.file
									break
							except ( IOError, OSError ):
								pass
			if not fontLoaded:
				fontList = fontconfig.query() #Gets a list of all fonts
				for testFileName in fontList:
					if fontLoaded:
						break
					testFile = fontconfig.FcFont( testFileName )
					valid = False
					if preferBold:
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "bold":
									valid = True
									break
							if style.lower() == "bold":
								valid = True
								break;
						if valid:
							if not silence:
								print( "This font is bold." )
							try:
								if not silence:
									print( "Trying to load font", testFile.fullname, "from file", testFile.file )
								if charToCheck == None or testFile.has_char( charToCheck ):
									normalFont = ImageFont.truetype( testFile.file, size=size )
									fontLoaded = True
									fontFile = testFile.file
									break
							except ( IOError, OSError ):
								pass
					elif preferNormal:
						for language, style in testFile.style:
							if language.lower() == "en":
								if style.lower() == "medium" or style.lower() == "regular":
									valid = True
									break
							if style.lower() == "medium" or style.lower() == "regular":
								valid = True
								break;
						if valid:
							if not silence:
								print( "This font is normal." )
							try:
								if not silence:
									print( "Trying to load font", testFile.fullname, "from file", testFile.file )
								if charToCheck == None or testFile.has_char( charToCheck ):
									normalFont = ImageFont.truetype( testFile.file, size=size )
									fontLoaded = True
									fontFile = testFile.file
									break
							except ( IOError, OSError ):
								pass
				if not fontLoaded:
					#This should only be reachable if the system has absolutely no fonts
					if not silence:
						print( "No usable fonts found. Using default font." )
					normalFont = ImageFont.load_default()
					fontFile = None
	return fontFile

def usage():
	'''Print command line usage info.
	'''
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out. Defaults to", silenceDefault ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --indir: The directory in which to look for inputs (must have fonts/, images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", inDirDefault )
	print( "🞍 -o or --outtextfile: The name of a text file to save the resulting sentences to. Defaults to", outTextFileNameDefault )
	print( "🞍 -p or --outimagefile: The name of an image file to save the resulting comic to. Numbers will be appended if multiple comics are generated. Defaults to", outImageFileNameDefault )
	print( "🞍 -n or --number: The number of comics to generate. Defaults to", numberOfComicsDefault )
	print( "🞍 -w or --saveforweb: If specified, saves the images using settings which result in a smaller file size, possibly at the expense of image quality." )
	print( "🞍 -h or --help: Display this usage info." )
	print( "🞍 -f or --font: The path to a font file to use." )
	print( "🞍 -t or --top: The path to an image which will be appended at the top of each comic. Should be the same width as the comic images. Good for names or logos." )
	print( '🞍 -r or --randomize-capitals: Some comic fonts have alternate capital letter forms instead of lower-case letters. In that case, using random "upper-case" and "lower-case" letters actually results in all upper-case letters but with a somewhat more handwriting-like look. Defaults to', randomizeCapitalsDefault )

try:
	options, argsLeft = getopt.getopt( sys.argv[ 1: ], "swhi:o:p:n:f:t:r", [ "silent", "saveforweb", "help", "indir=", "outtextfile=", "outimagefile=", "number=", "font=", "top=", "randomize-capitals" ] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit( EX_USAGE );

for option in options:
	if option[ 0 ] == "-s" or option[ 0 ] == "--silent":
		silence = True
	elif option[ 0 ] == "-i" or option[ 0 ] == "--indir":
		inDir = option[ 1 ]
	elif option[ 0 ] == "-o" or option[ 0 ] == "--outtextfile":
		outTextFileName = option[ 1 ]
	elif option[ 0 ] == "-p" or option[ 0 ] == "--outimagefile":
		outImageFileName = option[ 1 ]
	elif option[ 0 ] == "-n" or option[ 0 ] == "--number":
		numberOfComics = int( option[ 1 ].strip( "=" ) )
	elif option[ 0 ] == "-w" or option[ 0 ] == "--saveforweb":
		saveForWeb = True
	elif option[ 0 ] == "-h" or option[ 0 ] == "--help":
		usage()
		sys.exit( EX_OK )
	elif option[ 0 ] == "-f" or option[ 0 ] == "--font":
		commandLineFont = option[ 1 ]
	elif option[ 0 ] == "-t" or option[ 0 ] == "--top":
		topImageFileName = option[ 1 ]
	elif option[ 0 ] == "-r" or option[ 0 ] == "--randomize-capitals":
		randomizeCapitals = True

#Verify user input
#commandLineFont is not verified here; it will be verified when loading the font.
if not os.path.isdir( inDir ):
	print( "Error:", inDir, "is not a directory.", file=sys.stderr )
	exit( EX_NOINPUT )
if os.path.exists( outTextFileName ) and not os.path.isfile( outTextFileName ):
	print( "Error:", outTextFileName, "is not a file.", file=sys.stderr )
	exit( EX_CANTCREAT )
if os.path.exists( outImageFileName ) and not os.path.isfile( outImageFileName ):
	print( "Error:", outImageFileName, "is not a file.", file=sys.stderr )
	exit( EX_CANTCREAT )
if numberOfComics < 1:
	print( "Error: Number of comics (", numberOfComics, ") is less than 1.", file=sys.stderr )
	exit( EX_USAGE )
if topImageFileName != None:
	if not os.path.exists( topImageFileName ):
		print( "Error:", topImageFileName, "does not exist.", file=sys.stderr )
		exit( EX_NOINPUT )
	elif not os.path.isfile( topImageFileName ):
		print( "Error:", topImageFileName, "is not a file.", file=sys.stderr )
		exit( EX_NOINPUT )

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

wordBubblesDir = os.path.join( inDir, "word-bubbles" )
fontsDir = os.path.join( inDir, "fonts" )
imageDir = os.path.join( inDir, "images" )

normalFontFile = findSuitableFont( fontsDir = fontsDir, commandLineFont = commandLineFont, preferBold = False, preferNormal = True )
boldFontFile = findSuitableFont( fontsDir = fontsDir, commandLineFont = commandLineFont, preferBold = True, preferNormal = False )

for generatedComicNumber in range( numberOfComics ):

	try:
		wordBubbleFileName = random.choice( os.listdir( wordBubblesDir ) )
	except IndexError as error:
		print( error, file=sys.stderr )
		exit( EX_NOINPUT )

	comicID = os.path.splitext( wordBubbleFileName )[0]
	wordBubbleFileName = os.path.join( wordBubblesDir, wordBubbleFileName )
	if not silence:
		print( "Loading word bubbles from", wordBubbleFileName )

	try:
		wordBubbleFile = open( file=wordBubbleFileName, mode="rt" )
	except OSError as erro:
		print( error, file=sys.stderr )
		exit( EX_NOINPUT )
	
	idChecker = idChecker()
	if not idChecker.checkFile( wordBubbleFile, wordBubbleFileName, commentMark ):
		print( "Error: Word bubble file", wordBubbleFileName, "is not in the correct format." )
		exit( EX_DATAERR )
	
	lookForSpeakers = True
	speakers = []
	while lookForSpeakers:
		line = wordBubbleFile.readline()
		if len( line ) > 0:
			line = line.partition( commentMark )[0].strip()
			if len( line ) > 0:
				speakers = line.upper().split( "\t" )
				if len( speakers ) > 0:
					lookForSpeakers = False
		else:
			lookForSpeakers = False; #End of file reached, no speakers found
	
	if len( speakers ) == 0:
		print( "Error: Word bubble file", wordBubbleFileName, "contains no speakers." )
		exit( EX_DATAERR )
	
	if not silence:
		print( "These characters speak:", speakers )

	generators = dict()
	for speaker in speakers:
		newGenerator = Generator( charLabel = speaker, cm = commentMark, randomizeCapitals = randomizeCapitals )
		newGenerator.buildGraph( inDir )
		generators[ speaker ] = newGenerator

	if not silence:
		print( comicID )
	
	inImageFileName = os.path.join( imageDir, comicID + ".png" )

	try:
		image = Image.open( inImageFileName ).convert() #Text rendering looks better if we ensure the image's mode is not palette-based. Calling convert() with no mode argument does this.
	except IOError as error:
		print( error, file=sys.stderr )
		exit( EX_NOINPUT )
	
	transcript = str( comicID ) + "\n"
	
	previousBox = ( int( -1 ), int( -1 ), int( -1 ), int( -1 ) ) #For detecting when two characters share a speech bubble; don't generate text twice.
	
	for line in wordBubbleFile:
		line = line.partition( commentMark )[ 0 ].strip()
		
		if len( line ) > 0:
			line = line.split( "\t" )
			character = line[ 0 ].rstrip( ":" ).strip().upper()
			
			try:
				generator = generators[ character ]
			except:
				print( "Error: Word bubble file", wordBubbleFileName, "does not list", character, "in its list of speakers.", file=sys.stderr )
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
				oneCharacterTranscript += stringFromNodes( nodeList )
				if not silence:
					print( oneCharacterTranscript )
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
	
				normalFont = ImageFont.truetype( normalFontFile, size = size )
				boldFont = ImageFont.truetype( boldFontFile, size = size )
				
				listoflists = rewrap_nodelistlist( nodeList, normalFont, boldFont, width, fontSize = size )
				
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
							normalFont = ImageFont.truetype( normalFontFile, size = size )
							boldFont = ImageFont.truetype( boldFontFile, size = size )
						except IOError as error:
							print( error, "\nUsing default font instead.", file=sys.stderr )
							normalFont = ImageFont.load_default()
							boldFont = ImageFont.loa_default()
						listoflists = rewrap_nodelistlist( nodeList, normalFont, boldFont, width, fontSize = size )
		
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
						bandMax = float( infinity )
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
				
				########################################################################################################################################
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
					if offset > bottomRightY - topLeftY and not silence:
						print( "Warning: Text is too big vertically.", file=sys.stderr )
					
				image.paste( wordBubble, box )
		
	wordBubbleFile.close()
	
	if numberOfComics > 1:
		oldOutTextFileName = outTextFileName
		temp = os.path.splitext( outTextFileName )
		outTextFileName = temp[0] + str( generatedComicNumber ) + temp[1]
	
	try:
		outFile = open( file=outTextFileName, mode="wt" )
	except OSError as error:
		print( error, "\nUsing standard output instead", file=sys.stderr )
		outFile = sys.stdout
	
	if numberOfComics > 1:
		outTextFileName = oldOutTextFileName
	
	print( transcript, file=outFile )
	
	outFile.close()
	
	if numberOfComics > 1:
		oldOutImageFileName = outImageFileName
		temp = os.path.splitext( outImageFileName )
		outImageFileName = temp[0] + str( generatedComicNumber ) + temp[1]
	
	if topImageFileName != None:
		try:
			topImage = Image.open( topImageFileName ).convert( mode=image.mode )
		except IOError as error:
			print( error, file=sys.stderr )
			exit( EX_NOINPUT )
		oldSize = topImage.size
		size = ( max( topImage.size[0], image.size[0] ), topImage.size[1] + image.size[1] )
		
		newImage = Image.new( mode=image.mode, size=size )
		newImage.paste( im=topImage, box=( 0, 0 ) )
		newImage.paste( im=image, box=( 0, oldSize[1] ) )
		image = newImage
	
	infoToSave = PngInfo()
	
	encodingErrors = "backslashreplace" #If we encounter errors during text encoding, I feel it best to replace unencodable text with escape sequences; that way it may be possible for reader programs to recover the original unencodable text.
	
	#According to the Pillow documentation, key names should be "latin-1 encodable". I take this to mean that we ourselves don't need to encode it in latin-1.
	key = "transcript"
	keyUTF8 = key.encode( "utf-8", errors=encodingErrors )
	valueISO = transcript.encode( "iso-8859-1", errors=encodingErrors )
	valueUTF8 = transcript.encode( "utf-8", errors=encodingErrors )
	
	infoToSave.add_itxt( key=key, value=valueUTF8, tkey=keyUTF8 )
	infoToSave.add_text( key=key, value=valueISO )
	
	#GIMP only recognizes comments
	key = "Comment"
	keyUTF8 = key.encode( "utf-8", errors=encodingErrors )
	
	infoToSave.add_text( key=key, value=valueISO )
	infoToSave.add_itxt( key=key, value=valueUTF8, tkey=keyUTF8 )
	
	try:
		if saveForWeb:
			image = image.convert( mode = "P", palette="WEB", dither=False ) #"ADAPTIVE" palette might look better for some images. Also try turning dithering on or off.
			image.save( outImageFileName, format="PNG", optimize=True, pnginfo=infoToSave )
		else:
			image.save( outImageFileName, format="PNG", pnginfo=infoToSave )
	except IOError as error:
		print( error, file=sys.stderr )
		exit( EX_CANTCREAT )
	
	if numberOfComics > 1:
		outImageFileName = oldOutImageFileName
#end of loop: for generatedComicNumber in range( numberOfComics ):

exit( EX_OK )
