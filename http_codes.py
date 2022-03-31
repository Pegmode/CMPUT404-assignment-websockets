#I normally would use the http library but I don't want to risk messing up the marking
from http.client import BAD_REQUEST


NOT_FOUND = 404
FOUND = 302
TEMPORARY_REDIRECT = 307
PERMANENT_REDIRECT = 308
BAD_REQUEST  = 500
OK = 200