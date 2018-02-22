"""
Author: Or Gany.
Date: 21/2/2018
Overview: This code contains a few types that will be used on working
          conveniently with the HTTP protocol.

"""
import re
import os

# constants
ROOT_DIR = 'webroot/'


class HttpRequest(object):
    """
    This class represents an HTTP request

    TODO: Make it work better with post requests containing big data
    TODO: Make an __init__ method that take the actual HTTP header fields
    """
    def __init__(self, request, data=None):
        """
        :param request: http request
        :type request: bytes
        """
        # extract first line
        first_lf_index = request.find(b'\r\n')
        first_line = request[0: first_lf_index].split(b' ')
        self.method = first_line[0]     # Request method: GET, POST etc...
        self.resource = first_line[1]   # Requested resource such as index.html
        self.version = first_line[2]    # HTTP version

        if self.method == 'POST':
            length_regex = re.compile('Content-Length:(.+)\r\n')
            type_regex = re.compile('Content-Type:(.+)\r\n')
            data_regex = re.compile('\r\n\r\n(.+)')

            # extract the data
            data = data_regex.search(request).group(1)
            content_type = type_regex.search(request).group(1).strip()
            content_length = length_regex.search(request).group(1).strip()

            # assign the fields
            self.data = data
            self.content_type = content_type
            self.content_length = int(content_length)


class HttpResponse(object):
    """
    This class represents an HTTP response
    """
    code_phrases = {
        200: 'OK',
        300: 'Moved Permanently',
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed'
    }

    def __init__(self, http_request):
        """
        TODO: Take care of all code phrases
        This ctor forms an Http Response object using the http request
        :param http_request: HttpRequest object
        :type http_request: HttpRequest
        """
        

