"""
Author: Or Gany.
Date: 21/2/2018
Overview: This code contains a few types that will be used on working
          conveniently with the HTTP protocol.

"""
import re
from os import path

# constants
ROOT_DIR = 'webroot'


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

    def __repr__(self):
        return '{} {} {}'.format(self.method, self.resource, self.version)

    def __str__(self):
        first_line = '{} {} {}'.format(self.method, self.resource, self.version)
        request = first_line + '\r\n'
        if self.method == 'POST':
            # add headers
            request += 'Content-Length: {}\r\n'.format(self.content_length)
            request += 'Content-Type: {}\r\n'.format(self.content_type)
            request += '\r\n'
            # add data
            request += self.data
        return request


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
    }

    def __init__(self, http_request, forbidden_resources=None):
        """
        This ctor forms an Http Response object using the http request
        :param http_request: HttpRequest object
        :type http_request: HttpRequest
        :param forbidden_resources: Resources that the user is not supposed
            to have access to.
        """
        self.code = HttpResponse.__get_code(http_request, forbidden_resources)
        self.code_phrase = HttpResponse.code_phrases[self.code]
        self.version = http_request.version

    @staticmethod
    def __get_code(http_request, forbidden_resources=None):
        """
        returns the matching code phrase for the request
        :param http_request: http request
        :type http_request: HttpRequest
        :return: matching status code for the given request
        """
        if path.exists(path.join(ROOT_DIR, http_request.resource)):
            # in case requested resource exists
            # Check if resource path is harmful or not
            if '..' in http_request.resource:
                return 403  # Forbidden
            if forbidden_resources and http_request.resource in \
                    forbidden_resources:
                return 403  # Forbidden

            if http_request.method == 'GET':
                return 200  # OK
            elif http_request.method == 'POST':
                # validate that the request contains all the headers
                content_length = http_request.content_length
                content_type = http_request.content_type
                if not all((content_type, content_length)):
                    return 400  # Bad Request
        else:
            # in case requested resource does not exist
            return 404  # Not Found



