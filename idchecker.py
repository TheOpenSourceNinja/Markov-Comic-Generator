from os import path

class idChecker:
	def __init__( self ):
		'''Do nothing'''
	
	def checkFile( self, theFile, theFileName, commentMark ):
		'''Check whether a file has a valid ID number in its name and first non-blank-after-comment-removal line.
			Args:
				theFile: The file to check. Must already be open. Will not be closed by this function.
				theFileName: The name of the file.
				commentMark: The separator used to mark the start of a comment in the file. Comments are ignored.
			Returns:
				A Boolean indicating whether the file is valid.'''
		keepLookingForID = True
		IDFound = False
		
		while keepLookingForID:
			line = theFile.readline().partition( commentMark )[0].strip()
			if line.isnumeric() and line == path.splitext( path.basename( theFileName ) )[0]: #Why enforce the file name requirement? It's about people, not code: it's to make sure transcribers have read all available documentation (README.md) about the transcription format.
				keepLookingForID = False
				IDFound = True
			elif len( line ) > 0:
				keepLookingForID = False
		
		return IDFound
