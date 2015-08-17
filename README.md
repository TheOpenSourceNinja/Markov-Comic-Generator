# Markov Comic Generator
A program for generating comic strip dialog using Markov chains

## Inspiration
This program was inspired by but is not otherwise connected with Josh Millard's "[Calvin and Markov](http://www.joshmillard.com/markov/calvin/)"

## Why?
For fun.

## Noteworthy files and folders in this repository
* generator.py: The Python module responsible for generating Markov chains
* main.py: The Python script responsible for everything else
* LICENSE: The copyright license governing the code (fonts and images are under separate licenses)
* README.md: This file
* fonts: The directory in which desired font(s) should be installed. Currently contains one variant of Nina Paley's handwriting-based TrueType font. This font is not part of the Markov Comic Generator project; it is included so that you will have at least one comic-ish font.
* Nina fonts/LICENSE AND ATTRIBUTION: License and attribution information for Nina's font.
* images: The directory in which input images should go. Contains one sample image.
* transcripts: The directory in which comic transcripts should go. Contains one sample transcript.
* word-bubbles: The directory in which definition files should go. Contains one sample file.

## Input file formats
## Common
Comments - that is, notes in the input files that are intended to be ignored by the program - are preceded by "//". The // and everything coming after the // until the next line break will be ignored.

Blank lines - either lines that are actually blank or that become blank after removal of comments - will be ignored.

ID numbers are integers used to uniquely identify the original comic strip from which images and dialog are taken. Dates of the form YYYYMMDD work well for this and are recommended.

Excluding image files, the first non-blank line of an input file is a number identifying which comic strip this file corresponds to. ID numbers in these files are only used by the program to quickly check whether the input file is in the correct format: the ID must be an integer and must be the same as the ID in the file name. It's like when Van Halen put a ["no brown M&Ms" requirement](http://www.snopes.com/music/artists/vanhalen.asp) in their contracts: the colors of the M&Ms were not actually important; brown M&Ms would serve as a sign that something else might be wrong.

Each character has a label. For the sake of flexibility, these labels are not hard-coded into the program. Differences in spelling will be interpreted by the program as different characters. For this reason, it is recommended that only the character's initials be used, e.g. M = Mimi and E = Eunice. Additionally, the following labels are recommended:

* MISC = miscellaneous/offscreen character dialogue (for when the character is not clearly identifiable)
* SFX = non-spoken sound effects such as BOOM or CRASH.

Labels are not case-sensitive.

All input files are either images (any common format is acceptable; PNG format is recommended) or text files. It is recommended that text files be encoded in UTF-8 and have Windows-style CR+LF newlines.

### Dialog transcript files
These transcript files should be in the transcripts/ folder. A transcript file's name should be its ID number followed by the ".txt" file extension.

All the lines after the ID represent dialog or sound effects. These lines take the form of a character label, a colon, a space, and then whatever dialog the character speaks.

Different panels or balloons go on different lines. This just makes for a cleaner representation of the original comics.

In the case of shared dialog (e.g. two or more characters say the same thing at the same time), a separate copy of the dialog should be given to each character on two consecutive lines.

This program will strip asterisks, forward slashes, and underscores from around individual words. However, it is recommended for the purpose of accurate transcription that emphasis be added to words in the following ways:

* \*asterisks\* surrounding a word represent bold text
* /forward slashes/ surrounding a word represent italic text
* \_underscores\_ surrounding a word represent underlined text.

Word capitalization should be as it is in the original comic strip.

If in the original comic, a word is hyphenated in order to split it between two lines of text, it is recommended that the word be kept on a single line in the transcript and the hyphen be replaced with a [soft hyphen](https://en.wikipedia.org/w/index.php?title=Soft_hyphen&oldid=625641896) (Unicode code point U+00AD). Soft hyphens are not normally visible in most text editors; they are used to mark a place where a visible hyphen can be automatically inserted if one is needed.

#### Example
	//This first line will be blank after the comment gets removed, so it is ignored.
	20101210 //Date serves as ID number
	E: WOULD YOU RATHER BE *RIGHT,* OR *HAP­PY?* //Eunice is talking. Also, the last word has a soft hyphen in the middle.
	M: *NEITHER!*
	//E: *NEITHER!* //If Mimi and Eunice both said this at the same time, we would uncomment this line.
	M: I'D RATHER BE *RICH!* //Note: For some reason Mimi and Eunice speak in all caps. See for yourself: http://mimiandeunice.com/2010/12/10/right-or-happy-iii/

### Image files
Each image file should be in the images/ folder. Its name should be its ID number followed by an extension appropriate for the format. The image should have all dialog blanked out so that empty word balloons are left.

### Word bubble files
Each word bubble file should be in the word-bubbles/ folder. Its name should consist of its ID number followed by ".tsv".

The first non-blank line of each file should be a tab-separated list of labels of all the characters who speak.

All following lines should take the form of one character label, a tab, the X coordinate of the top left corner of the word balloon, a tab, the Y coordinate of the top left corner, a tab, the X coordinate of the bottom right corner, a tab, and the Y coordinate of the bottom right corner. As this format may change depending on the needs of the program, to maintain compatibility between program versions, any data following this will be ignored. All coordinates are integers representing pixel coordinates in the image, with (0,0) being the top left corner.

If multiple characters use the same speech bubble (saying the same thing at the same time), create separate lines in the file - one for each speaker, one line coming immediately after the other - with identical speech bubble coordinates.

#### Example
	20101210//The image is stored as images/20101210.png; this definition file is stored as word-bubbles/20101210.tsv
	E	M //List of speakers
	//Speaker	X	Y	X	Y
	E	37	6	180	69
	M	280	48	370	76
	//E	280	48	370	76 //If this comic had Eunice sharing a speech bubble with Mimi, we would uncomment this line.
	M	488	30	586	82	00 //The 00 will be ignored by this program version. Later versions of this program might use it.

## Fonts
The program will use the first usable font it finds, searching in the following order:

1. A font file specified on the command line ("--font" on the command line)
2. Font files in the "fonts" subdirectory of the input directory ("--indir" on the command line)
3. [Nina](https://archive.org/details/NinaPaleyFonts)
4. [Humor Sans](http://antiyawn.com/uploads/humorsans.html)
5. [Tomson Talks](http://frabru.de/c.php/resource/font/TomsonTalks/)
6. Comic Sans MS
7. [Ubuntu Titling](http://www.fontsquirrel.com/fonts/Ubuntu-Titling)
8. Any other font