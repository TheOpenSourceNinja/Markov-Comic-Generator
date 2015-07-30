#!/usr/bin/python3

import getopt
import sys
import random
import os
import fontconfig
from PIL import Image, ImageFont, ImageDraw
from generator import Generator

silenceDefault = False
inDirDefault = "./"
outTextFileNameDefault = "default out.txt"
outImageFileNameDefault = "default out.png"
numberOfComicsDefault = 1
silence = silenceDefault
inDir = inDirDefault
outTextFileName = outTextFileNameDefault
outImageFileName = outImageFileNameDefault
numberOfComics = numberOfComicsDefault

def usage():
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out. Defaults to", silenceDefault ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --indir: The directory in which to look for inputs (must have images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", inDirDefault )
	print( "🞍 -o or --outtextfile: The name of a text file to save the resulting sentences to. Defaults to", outTextFileNameDefault )
	print( "🞍 -p or --outimagefile: The name of an image file to save the resulting comic to. Numbers will be appended if multiple comics are generated. Defaults to", outImageFileNameDefault )
	print( "🞍 -n or --number: The number of comics to generate. Defaults to", numberOfComicsDefault )

try:
	options, argsLeft = getopt.getopt( sys.argv[1:], "si:o:p:n:", ["silent", "indir=", "outtextfile=", "outimagefile=", "number="] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit(2);

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

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

wordBubblesDir = os.path.join( inDir, "word-bubbles" )
wordBubbleFileName = random.choice( os.listdir( wordBubblesDir ) )
comicID = os.path.splitext( wordBubbleFileName )[0]
wordBubbleFileName = os.path.join( wordBubblesDir, wordBubbleFileName )
if not silence:
	print( wordBubbleFileName )
wordBubbleFile = open( file=wordBubbleFileName, mode="rt" )

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

image = Image.open( inImageFileName )


try:
	font = ImageFont.truetype( "Nina fonts/NinaMedium.ttf" )
except IOError:
	font = ImageFont.load_default()

outFile = open( file=outTextFileName, mode="at" )

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
		
		print( line[ 1: ] )
		
		topLeftX = int( line[1] )
		topLeftY = int( line[2] )
		bottomRightX = int( line[3] )
		bottomRightY = int( line[4] )
		
		box = ( topLeftX, topLeftY, bottomRightX, bottomRightY )
		wordBubble = image.crop( box )
		draw = ImageDraw.Draw( wordBubble )
		
		draw.text( ( 0, 0 ), text, font=font )
		
		image.paste( wordBubble, box )

outFile.close()

image.save( outImageFileName )

wordBubbleFile.close()
