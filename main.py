#!/usr/bin/python3

import getopt
import sys
from generator import Generator

silenceDefault = False
inDirDefault = "./"
outFileNameDefault = "default out.txt"
numberOfComicsDefault = 1
silence = silenceDefault
inDir = inDirDefault
outFileName = outFileNameDefault
numberOfComics = numberOfComicsDefault

def usage():
	print( "😕" ) #In case of transcoding errors: this should be U+1F615, "confused face"
	print( "Usage: The program takes the following command line arguments:" )
	print( "🞍 -s or --silent: Prevents output on standard out. Defaults to", silenceDefault ) #the first character of each of these should be U+1F78D, "black slightly small square"
	print( "🞍 -i or --indir: The directory in which to look for inputs (must have images/, transcripts/, and word-bubbles/ subdirectories). Defaults to", inDirDefault )
	print( "🞍 -o or --outfile: The name of a file to save the resulting sentences to. Defaults to", outFileNameDefault )
	print( "🞍 -n or --number: The number of comics to generate. Defaults to", numberOfComicsDefault )

try:
	options, argsLeft = getopt.getopt( sys.argv[1:], "si:o:n:", ["silent", "indir=", "outfile=", "number="] )
except getopt.GetoptError as error:
	print( error )
	usage()
	sys.exit(2);

for option in options:
	if option[0] == "-s" or option[0] == "--silence":
		silence = True
	elif option[0] == "-i" or option[0] == "--indir":
		inDir = option[1]
	elif option[0] == "-o" or option[0] == "--outfile":
		outFileName = option[1]
	elif option[0] == "-n" or option[0] == "--number":
		numberOfComics = int( option[1].strip( "=" ) )

if not silence:
	print( "Copyright 2015 James Dearing. Licensed under the GNU Affero General Public License (AGPL), either version 3.0 or (at your option) any later version published by the Free Software Foundation. You should have received a copy of the AGPL with this program. If you did not, you can find version 3 at https://www.gnu.org/licenses/agpl-3.0.html or the latest version at https://www.gnu.org/licenses/agpl.html" )

mimi = Generator( charLabel="M" )
eunice = Generator( charLabel="E" )
mimi.buildDatabase( inDir )
eunice.buildDatabase( inDir )

outFile = open( file=outFileName, mode="at" )

mimisDialog = mimi.generate( 1 )
eunicesDialog = eunice.generate( 1 )
print( mimi.charLabel, ": ", mimisDialog, sep="", file=outFile )
print( eunice.charLabel, ": ", eunicesDialog, sep="", file=outFile )
if not silence:
	print( mimi.charLabel, ": ", mimisDialog, sep="" )
	print( eunice.charLabel, ": ", eunicesDialog, sep="" )

outFile.close()
