#!/usr/bin/python3

import xmlrpc.client as client
from sys import stderr
from datetime import datetime
from os import path
import mimetypes
from urllib.parse import urlparse

class Uploader:
	def __init__( self ):
		'''Do any initialization stuff common to all derived classes.'''
		#nothing to do so far
	
	def upload( self ):
		'''Do stuff common to all derived classes' upload() functions. This function does not itself upload anything.'''
		self.blah = 0

class DrupalUploader( Uploader ):
	def __init__( self ):
		Uploader.__init__( self )
	
	def upload( self ):
		self.blah = 0

class WordPressUploader( Uploader ):
	def __init__( self, uri, username, password, blogID = None ):
		'''Connect to the server.
			Relevant WordPress docs:
				https://codex.WordPress.org/XML-RPC_WordPress_API/Users#wp.getUsersBlogs
			Args:
				uri: The URI to connect to with XMLRPC. This should be the xmlrpc.php file in your WordPress install directory, e.g. https://www.example.com/xmlrpc.php . SECURITY WARNING: If this URI does not use encryption (e.g. starting with httpS), then USERNAMES and PASSWORDS will be transmitted in CLEARTEXT!
				username: The username under which these posts are made.
				password: The password for the account.
				blogID: The ID number of the blog to post to. Will be auto-detected if not specified.'''
		
		Uploader.__init__( self )
		
		self.uri = str( uri )
		
		#if not self.uri.startswith( "https://" ):
		if urlparse( self.uri ).scheme not in [ "file", "https", "sftp", "shttp", "sips", "snews", "svn+ssh" ]:
			print( "SECURITY WARNING: URI does not use any known secure protocol. USERNAMES and PASSWORDS are being transmitted in CLEARTEXT!", "\nThis is the URI:", uri, file = stderr )
		
		self.username = str( username )
		self.password = str( password )
		
		self.server = client.ServerProxy( self.uri )
		try:
			blogInfo = self.server.wp.getUsersBlogs( self.username, self.password )
		except client.Fault as fault: #How is a fault different from an error? Beats me.
			print( "A fault occurred. Fault code %d." % fault.faultCode, file = stderr )
			print( "Fault string: %s" % fault.faultString, file = stderr )
			print( "Username:", self.username, "Password:", self.password )
			return
		except client.ProtocolError as error:
			print( "A protocol error occurred. URL: %s" % error.url, file = stderr )
			print( "HTTP(S) headers: %s" % error.headers, file = stderr )
			print( "Error code: %d" % error.errcode, file = stderr )
			print( "Error message: %s" % error.errmsg, file = stderr )
			return
		except client.Error as error:
			print( "An error occurred:", error, file = stderr )
			return
		
		if blogID is None:
			for blog in blogInfo:
				if blog[ "xmlrpc" ] == self.uri:
					blogID = blog[ "blogid" ]
					break
		else:
			blogID = int( blogID )
		
		if blogID is None:
			blogID = 0

		self.blogID = blogID
		
		for blog in blogInfo:
			if self.blogID == blog[ "blogid" ]:
				if self.uri != blog[ "xmlrpc" ]:
					self.uri = blog[ "xmlrpc" ]
					self.server = client.ServerProxy( self.uri )
	
	def upload( self, inputFileName = "default out.png", shortComicTitle = "", longComicTitle = None, postCategories = None, postTime = datetime.now(), postStatus = "draft", transcript = None, originalURL = None, silence = False ):
		'''Upload the comic (must be a readable image file) as a blog post.
			Relevant WordPress docs:
				https://codex.WordPress.org/XML-RPC_WordPress_API/Posts#wp.newPost
				https://codex.WordPress.org/Function_Reference/wp_insert_post
				https://codex.WordPress.org/XML-RPC_WordPress_API/Media#wp.uploadFile
				https://codex.wordpress.org/Post_Formats
			Args:
				inputFileName: The name of the image file to upload. Defaults to "default out.png"
				shortComicTitle: The title of the comic, in short form. Will be the first part of the image file's name as uploaded to the server (the local copy will not be renamed). Defaults to the empty string.
				longComicTitle: The title of the comic, in long form. Will be the first part of the post's title. Defaults to whatever shortComicTitle is.
				postCategories: A list of strings, each string representing a post category. Defaults to one string, longComicTitle.
				postTime: The timestamp to be attached to the post. Defaults to now. The date (excluding time) will also be used as the second parts of the image file's name as uploaded to the server (the local copy will not be renamed) and of the post's title.
				postStatus: A string indicating the status to assign to the post. Defaults to "draft". See the relevant WP docs for a list of acceptable values.
				transcript: A string containing the text of the comic being uploaded. Will be read from "default out.txt" if not specified.
				originalURL: The URL of the source comic image from which the current comic was generated. Defaults to None.
				silence: A Boolean indicating whether to keep quiet (True) or output status messages to standard output (False)
				
			Returns:
				0 if everything worked, no errors.
				WordPress-provided fault codes if a fault (e.g. invalid username/password) occurs.
				Server-provided error codes if a protocol error (i.e. 404: file not found) occurs.
				-1 if some other type of error occurs.'''
		inputFileName = str( inputFileName )
		shortComicTitle = str( shortComicTitle )
		postStatus = str( postStatus )
		
		if longComicTitle is None:
			longComicTitle = shortComicTitle
		else:
			longComicTitle = str( longComicTitle )
		
		if postCategories is None:
			postCategories = [ longComicTitle ]
		
		post = dict()
		dateString = datetime.date( postTime ).isoformat()
		post[ "post_title" ] = longComicTitle + " " + dateString
		post[ "post_date" ] = client.DateTime( postTime ) #WordPress post 'dates' include time of day
		post[ "post_status" ] = postStatus
		post[ "post_format" ] = "image" #WordPress themes are not required to support every format. If posts from this program look wonky, try commenting this line out or changing to a different format string.
		
		post[ "comment_status" ] = "open" #NOTE: Workaround for a Wordpress bug. WordPress 4.3.1 by default disallows comments on posts sent using XML PRC, even if its settings are supposed to allow them by default.
		
		post[ "terms_names" ] = dict()
		post[ "terms_names" ][ "category" ] = postCategories
		
		fileData = dict()
		fileData[ "name" ] = shortComicTitle + " " + dateString + path.splitext( inputFileName )[ 1 ]
		
		fileType = mimetypes.guess_type( inputFileName )
		if fileType[ 0 ] is None:
			print( 'Warning: MIME type could not be guessed. Uploading with no MIME type specified.', file = stderr )
		else:
			fileData[ "type" ] = fileType[ 0 ]
			
		fileHandle = open( inputFileName, "rb" )
		fileData[ "bits" ] = client.Binary( fileHandle.read() )
		fileHandle.close()
		
		if transcript is None:
			transcriptFileHandle = open( "default out.txt", "rt" )
			transcript = ""
			for line in transcriptFileHandle:
				transcript += line
			transcriptFileHandle.close()
		try:
			
			fileUploadResult = self.server.wp.uploadFile( self.blogID, self.username, self.password, fileData )
			
			if not silence:
				print( "File upload result:", fileUploadResult )
			
			post[ "post_content" ] = '<a href="' + fileUploadResult[ "url" ] + '"><img class="aligncenter size-full img-zoomable wp-image-' + fileUploadResult[ "id" ] + '" src="' + fileUploadResult[ "url" ] + '" alt="' + transcript + '" /></a>Click the image for full size.<p>Transcript:</p><p class="comic-transcript">' + transcript + '</p>'
			
			if originalURL is not None:
				originalURL = str( originalURL )
				post[ "post_content" ] = post[ "post_content" ] + '<p class="comic-original-url"><a href="' + originalURL + '">Original</a></p>'
			
			postUploadResult = self.server.wp.newPost( self.blogID, self.username, self.password, post )
			
			if not silence:
				print( "Post upload result:", postUploadResult )
			
		except client.Fault as fault:
			print( "A fault occurred. Fault code %d." % fault.faultCode, file = stderr )
			print( "Fault string: %s" % fault.faultString, file = stderr )
			return fault.faultCode
		except client.ProtocolError as error:
			print( "A protocol error occurred. URL: %s" % error.url, file = stderr )
			print( "HTTP(S) headers: %s" % error.headers, file = stderr )
			print( "Error code: %d" % error.errcode, file = stderr )
			print( "Error message: %s" % error.errmsg, file = stderr )
			return error.errcode
		except client.Error as error:
			print( "An error occurred:", error, file = stderr )
			return -1
		
		
		return 0
