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
commandLineFont = "" #If a font file is specified on the command line, this will be set.
topImageFileName = None

def findCharsPerLine( text, font, maxWidth ):
	'''Find how many characters will fit within the specified width.
		Args:
			text: The string whose contents are used to test character width.
			font: The font used to test character width.
			maxWidth: The maximum width in pixels.
		Returns:
			An integer indicating how many characters fit within maxWidth.
	'''
	
	if maxWidth < 1:
		maxWidth = 1
	
	charsPerLine = maxWidth // font.getsize( "L" )[0]
	
	if charsPerLine < 1:
		charsPerLine = 1
	
	while font.getsize( text[ :charsPerLine ] )[0] > maxWidth:
		charsPerLine -= 1
	
	if charsPerLine < 1:
		charsPerLine = 1
	
	return charsPerLine

def rewrap( text, font, maxWidth, center=True ):
	'''Rewrap and center text.
		Args:
			text: A string containing the text to be wrapped.
			font: Gets passed to findCharsPerLine().
			maxWidth: Gets passed to findCharsPerLine().
			center: A Boolean indicating whether text should be centered after wrapping. Spaces will be added around each line of text if true. Defaults to True.
		Returns:
			A list of strings.
	'''
	charsPerLine = findCharsPerLine( text, font, maxWidth )
	temp = textwrap.wrap( text, width = charsPerLine, break_long_words = False )
	
	result = []
	for line in temp:
		if len( line ) > charsPerLine:
			middle = len( line ) // 2
			firstHalf = line[ :middle ] + "-"
			secondHalf = line[ middle: ]
			if center:
				firstHalf = firstHalf.center( charsPerLine )
				secondHalf = secondHalf.center( charsPerLine )
			result.append( firstHalf )
			result.append( secondHalf )
		else:
			if center:
				line = line.center( charsPerLine )
			result.append( line )
	
	return result

def usage():
	'''Print command line usage info.
	'''
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out. Defaults to", silenceDefault ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --indir: The directory in which to look for inputs (must have images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", inDirDefault )
	print( "🞍 -o or --outtextfile: The name of a text file to save the resulting sentences to. Defaults to", outTextFileNameDefault )
	print( "🞍 -p or --outimagefile: The name of an image file to save the resulting comic to. Numbers will be appended if multiple comics are generated. Defaults to", outImageFileNameDefault )
	print( "🞍 -n or --number: The number of comics to generate. Defaults to", numberOfComicsDefault )
	print( "🞍 -w or --saveforweb: If specified, saves the images using settings which result in a smaller file size, possibly at the expense of image quality." )
	print( "🞍 -h or --help: Display this usage info." )
	print( "🞍 -f or --font: The path to a font file to use." )
	print( "🞍 -t or --top: The path to an image which will be appended at the top of each comic. Should be the same width as the comic images. Good for names or logos." )

try:
	options, argsLeft = getopt.getopt( sys.argv[ 1: ], "swhi:o:p:n:f:t:", [ "silent", "saveforweb", "help", "indir=", "outtextfile=", "outimagefile=", "number=", "font=", "top=" ] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit( EX_USAGE );

for option in options:
	if option[0] == "-s" or option[0] == "--silent":
		silence = True
	elif option[0] == "-i" or option[0] == "--indir":
		inDir = option[1]
	elif option[0] == "-o" or option[0] == "--outtextfile":
		outTextFileName = option[1]
	elif option[0] == "-p" or option[0] == "--outimagefile":
		outImageFileName = option[1]
	elif option[0] == "-n" or option[0] == "--number":
		numberOfComics = int( option[1].strip( "=" ) )
	elif option[0] == "-w" or option[0] == "--saveforweb":
		saveForWeb = True
	elif option[0] == "-h" or option[0] == "--help":
		usage()
		sys.exit( EX_OK )
	elif option[0] == "-f" or option[0] == "--font":
		commandLineFont = option[1]
	elif option[0] == "-t" or option[0] == "--top":
		topImageFileName = option[1]

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

	lookForSpeakers = True
	while lookForSpeakers:
		line = wordBubbleFile.readline()
		line = line.partition( commentMark )[0].strip()
		if len( line ) > 0:
			speakers = line.split( "\t" )
			if len( speakers ) > 0:
				lookForSpeakers = False

	if not silence:
		print( "These characters speak:", speakers )

	generators = dict()
	for speaker in speakers:
		newGenerator = Generator( charLabel = speaker, cm = commentMark )
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

	initialFontSize = image.size[1] // 2 #Contrary to the claim by PIL's documentation, font sizes are apparently in pixels, not points. The size being requested is the height of a generic character; the actual height of any particular character will be approximately (not exactly) the requested size. Assume here that we want one line of text to fill half the height of the image; we will try smaller and smaller sizes later.
	
	fontLoaded = False
	fontFile = ""
	try:
		font = ImageFont.truetype( commandLineFont, size=initialFontSize )
		fontFile = commandLineFont
		fontLoaded = True
	except IOError:
		if len( commandLineFont ) > 0: #We don't want to give an error message if no font was specified
			print( commandLineFont, "could not be loaded as a font.", file=sys.stderr )
		fileList = os.listdir( fontsDir )
		for testFile in fileList:
			testFile = os.path.join( "fonts", testFile )
			try:
				print( "Trying to load font", testFile )
				font = ImageFont.truetype( testFile, size=initialFontSize )
				fontLoaded = True
				fontFile = testFile
				break
			except IOError:
				pass
		
		if not fontLoaded:
			families = [ "Nina", "Humor Sans", "Tomson Talks", "Comic Sans MS", "Ubuntu Titling" ]
			for family in families:
				if fontLoaded:
					break
				fontList = fontconfig.query( family=family )
				for testFile in fileList:
					try:
						font = ImageFont.truetype( testFile, size=initialFontSize )
						fontLoaded = True
						fontFile = testFile
						break
					except IOError:
						pass
			
			if not fontLoaded:
				fontList = fontconfig.query()
				for testFile in fileList:
					try:
						font = ImageFont.truetype( testFile, size=initialFontSize )
						fontLoaded = True
						fontFile = testFile
						break
					except IOError:
						pass
				if not fontLoaded:
					#This should only be reachable if the system has absolutely no fonts
					font = ImageFont.load_default()
	
	transcript = str( comicID ) + "\n"
	
	for line in wordBubbleFile:
		line = line.partition( commentMark )[0].strip()
		if len( line ) > 0:
			line = line.split( "\t" )
			character = line[0]
			character = character.rstrip( ":" ).strip()
			
			try:
				generator = generators[ character ]
			except:
				print( "Error: Word bubble file", wordBubbleFileName, "does not list", character, "in its list of speakers.", file=sys.stderr )
				exit( EX_DATAERR )
			
			text = " ".join( generator.generateSentences( 1 ) )
			transcript += character + ": " + text + "\n" #print( character, ": ", text, sep="", file=outFile )
			if not silence:
				print( character, ": ", text, sep="" )
		
			topLeftX = int( line[1] )
			topLeftY = int( line[2] )
			bottomRightX = int( line[3] )
			bottomRightY = int( line[4] )
		
			box = ( topLeftX, topLeftY, bottomRightX, bottomRightY )
			wordBubble = image.crop( box )
			draw = ImageDraw.Draw( wordBubble )
			
			width = bottomRightX - topLeftX
			if width <= 0: #Width must be positive
				width = 1
			
			newText = rewrap( text, font, width )
			
			margin = 0
			offset = originalOffset = 0
			fontSize = initialFontSize
			goodSizeFound = False
			usedFont = font
			while not goodSizeFound:
				offset = originalOffset
				for line in newText:
					offset += usedFont.getsize( line )[1]
				if offset > bottomRightY - topLeftY:
					fontSize -= 1
					try:
						usedFont = ImageFont.truetype( fontFile, size=fontSize )
					except IOError as error:
						print( error, "\nUsing default font instead.", file=sys.stderr )
						usedFont = ImageFont.load_default()
					newText = rewrap( text, usedFont, bottomRightX - topLeftX )
				else:
					goodSizeFound = True
		
			midX = int( wordBubble.size[ 0 ] / 2 )
			midY = int( wordBubble.size[ 1 ] / 2 )
		
			try: #Choose a text color that will be visible against the background
				backgroundColor = ImageStat.Stat( wordBubble ).mean #wordBubble.getpixel( ( midX, midY ) )
				textColorList = []
				
				if wordBubble.mode.startswith( "1" ):
					bandMax = 1
				elif wordBubble.mode.startswith( "L" ) or wordBubble.mode.startswith( "P" ) or wordBubble.mode.startswith( "RGB" ) or wordBubble.mode.startswith( "CMYK" ) or wordBubble.mode.startswith( "YCbCr" ) or wordBubble.mode.startswith( "LAB" ) or wordBubble.mode.startswith( "HSV" ):
					bandMax = 255
				elif wordBubble.mode.startswith( "I" ):
					bandMax = 2147483647 #max for a 32-bit signed integer
				elif wordBubble.mode.startswith( "F" ):
					bandMax = float( infinity )
				else: #I've added all modes currently supported according to Pillow documentation; this is for future compatibility
					bandMax = max( ImageStat.Stat( wordBubble ).extrema )
				
				for c in backgroundColor:
					textColorList.append( int( bandMax - c ) )
				
				if wordBubble.mode.endswith( "A" ): #Pillow supports two modes with alpha channels
					textColorList[ -1 ] = bandMax
				
				textColor = tuple( textColorList )
				
			except ValueError:
				textColor = "black"
			
			offset = originalOffset
			for line in newText:
				draw.text( ( margin, offset ), line, font=usedFont, fill=textColor )
				offset += usedFont.getsize( line )[1]
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
