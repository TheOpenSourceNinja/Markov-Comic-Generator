#!/usr/bin/python3

import getopt
import sys
import random
import os
import fontconfig
import textwrap
from PIL import Image, ImageFont, ImageDraw, ImageColor
from generator import Generator

#Exit statuses
#These are copied from my /usr/include/sysexits.h. Only statuses possibly relevant to this program were copied.
EX_OK = 0 #No problems
EX_USAGE = 64 #Command line error
EX_DATAERR = 65 #Data format error
EX_NOINPUT = 66 #Input not openable
EX_CANTCREAT = 73 #Can't create output file
EX_NOPERM = 77 #Permission error

silence = silenceDefault = False
inDir = inDirDefault = "./"
outTextFileName = outTextFileNameDefault = "default out.txt"
outImageFileName = outImageFileNameDefault = "default out.png"
numberOfComics = numberOfComicsDefault = 1
saveForWeb = saveForWebDefault = False

def findCharsPerLine( text, font, maxWidth ):
	charsPerLine = maxWidth // font.getsize( "L" )[0]
	
	while font.getsize( text[ :charsPerLine ] )[0] > maxWidth:
		charsPerLine -= 1
	
	return charsPerLine

def rewrap( text, font, maxWidth ):
	charsPerLine = findCharsPerLine( text, font, maxWidth )
	temp = textwrap.wrap( text, width = charsPerLine )
	
	result = []
	for line in temp:
		line = line.center( charsPerLine )
		result.append( line )
	
	return result

def usage():
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out. Defaults to", silenceDefault ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --indir: The directory in which to look for inputs (must have images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", inDirDefault )
	print( "🞍 -o or --outtextfile: The name of a text file to save the resulting sentences to. Defaults to", outTextFileNameDefault )
	print( "🞍 -p or --outimagefile: The name of an image file to save the resulting comic to. Numbers will be appended if multiple comics are generated. Defaults to", outImageFileNameDefault )
	print( "🞍 -n or --number: The number of comics to generate. Defaults to", numberOfComicsDefault )
	print( "🞍 -w or --saveforweb: If specified, saves the images using settings which result in a smaller file size, possibly at the expense of image quality." )

try:
	options, argsLeft = getopt.getopt( sys.argv[1:], "swi:o:p:n:", ["silent", "saveforweb", "indir=", "outtextfile=", "outimagefile=", "number="] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit( EX_USAGE );

for option in options:
	if option[0] == "-s" or option[0] == "--silence":
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

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

wordBubblesDir = os.path.join( inDir, "word-bubbles" )

try:
	wordBubbleFileName = random.choice( os.listdir( wordBubblesDir ) )
except IndexError as error:
	print( error, file=sys.stderr )
	exit( EX_NOINPUT )

comicID = os.path.splitext( wordBubbleFileName )[0]
wordBubbleFileName = os.path.join( wordBubblesDir, wordBubbleFileName )
if not silence:
	print( wordBubbleFileName )

try:
	wordBubbleFile = open( file=wordBubbleFileName, mode="rt" )
except OSError as erro:
	print( error, file=sys.stderr )
	exit( EX_NOINPUT )

lookForSpeakers = True
while lookForSpeakers:
	line = wordBubbleFile.readline()
	line = line.partition( "//" )[0].strip()
	if len( line ) > 0:
		speakers = line.split( "\t" )
		if len( speakers ) > 0:
			lookForSpeakers = False

if not silence:
	print( speakers )

generators = dict()
for speaker in speakers:
	newGenerator = Generator( charLabel = speaker )
	newGenerator.buildDatabase( inDir )
	generators[ speaker ] = newGenerator

if not silence:
	print( comicID )

imageDir = os.path.join( inDir, "images" )
inImageFileName = os.path.join( imageDir, comicID + ".png" )

try:
	image = Image.open( inImageFileName ).convert() #Text rendering looks better if we ensure the image's mode is not palette-based. Calling convert() with no mode argument does this.
except IOError as error:
	print( error, file=sys.stderr )
	exit( EX_NOINPUT )

normalFontSize = 30
try:
	font = ImageFont.truetype( "Nina fonts/NinaMedium.ttf", size=normalFontSize )
except IOError:
	print( error, "\nUsing default font instead.", file=sys.stderr )
	font = ImageFont.load_default()

try:
	outFile = open( file=outTextFileName, mode="at" )
except OSError as error:
	print( error, "\nUsing standard output instead", file=sys.stderr )
	outFile = sys.stdout

for line in wordBubbleFile:
	line = line.partition( "//" )[0].strip()
	if len( line ) > 0:
		line = line.split( "\t" )
		character = line[0]
		character = character.rstrip( ":" ).strip()
		
		generator = generators[ character ]
		text = generator.generate( 1 )
		print( character, ": ", text, sep="", file=outFile )
		if not silence:
			print( character, ": ", text, sep="" )
		
		topLeftX = int( line[1] )
		topLeftY = int( line[2] )
		bottomRightX = int( line[3] )
		bottomRightY = int( line[4] )
		
		box = ( topLeftX, topLeftY, bottomRightX, bottomRightY )
		wordBubble = image.crop( box )
		draw = ImageDraw.Draw( wordBubble )
		
		newText = rewrap( text, font, bottomRightX - topLeftX )
		
		margin = 0
		offset = originalOffset = 0
		fontSize = normalFontSize
		goodSizeFound = False
		usedFont = font
		while not goodSizeFound:
			offset = originalOffset
			for line in newText:
				offset += usedFont.getsize( line )[1]
			if offset > bottomRightY - topLeftY:
				fontSize -= 1
				try:
					usedFont = ImageFont.truetype( "Nina fonts/NinaMedium.ttf", size=fontSize )
				except IOError as error:
					print( error, "\nUsing default font instead.", file=sys.stderr )
					usedFont = ImageFont.load_default()
				newText = rewrap( text, usedFont, bottomRightX - topLeftX )
			else:
				goodSizeFound = True
		
		midX = int( wordBubble.size[0] / 2 )
		midY = int( wordBubble.size[1] / 2 )
		
		try: #Choose a text color that will be visible against the background
			backgroundColor = wordBubble.getpixel( ( midX, midY ) )
			textColor = ( 255-backgroundColor[0], 255-backgroundColor[1], 255-backgroundColor[2], 255 )
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
outFile.close()

try:
	if saveForWeb:
		image = image.convert( mode = "P", palette="WEB" )
		image.save( outImageFileName, format="PNG", optimize=True )
	else:
		image.save( outImageFileName, format="PNG" )
except IOError as error:
	print( error, file=sys.stderr )
	exit( EX_CANTCREAT )

exit( EX_OK )
