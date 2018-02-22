"""
Author: Or Gany.
Date: 21/2/2018
Overview: This code contains a few types that will be used on working
          conveniently with the HTTP protocol.

"""
import re
from os import path

# constants
ROOT_DIR = b'webroot'
DEFAULT_ERRORS = {
    400: b"""
    <html>
    <head>
    <title>Bad Request </title>
    </head>
    <body>
        <h1 style="text-align: center">Bad Request 400</h1> 
        <p style="text-align: center">
        bad request to the server!
        </p>
    </body>
</html>
    """,
    403: b"""
    <html>
    <head>
    <title>Forbidden </title>
    </head>
    <body>
        <h1 style="text-align: center">Forbidden 403</h1> 
        <p style="text-align: center">
        Action Forbidden
        </p>
    </body>
</html>
    """,
    404: b"""
<html>
    <head>
    <title>File Not Found </title>
    </head>
    <body>
        <h1 style="text-align: center">File Not Found! 404</h1> 
        <p style="text-align: center">
        The requested file was not found.
        </p>
    </body>
</html>
"""
}


class HttpRequest(object):
    """
    This class represents an HTTP request

    TODO: Make it work better with post requests containing big data
    TODO: Make an __init__ method that take the actual HTTP header fields
    """
    def __init__(self, request):
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

        # Home page
        if self.resource == b'/':
            self.resource = b'index.html'

        # The resource is placed in ROOT directory
        self.resource = path.join(ROOT_DIR, self.resource)

        if self.method == b'POST':
            length_regex = re.compile(b'Content-Length:(.+)\r\n')
            type_regex = re.compile(b'Content-Type:(.+)\r\n')
            data_regex = re.compile(b'\r\n\r\n(.+)')

            # extract the data
            data = data_regex.search(request).group(1)
            type_result = type_regex.search(request)
            length_result = length_regex.search(request)
            if type_result:
                content_type = type_result.group(1).split()
            else:
                content_type = b''
            if length_result:
                content_length = length_result.group(1).strip()
            else:
                content_length = 0

            # assign the fields
            self.data = data
            self.content_type = content_type
            self.content_length = int(content_length)

    def __repr__(self):
        return b' '.join((self.method, self.resource, self.version))

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

    def __bytes__(self):
        return bytes(self.__str__())


class HttpResponse(object):
    """
    This class represents an HTTP response
    """
    code_phrases = {
        200: b'OK',
        300: b'Moved Permanently',
        400: b'Bad Request',
        403: b'Forbidden',
        404: b'Not Found',
    }

    content_types = {
        # Image
        '.jpg': b'image/jpeg',
        '.jpeg': b'image/jpeg',
        '.png': b'image/png',
        '.gif': b'image/gif',

        # Text
        '.css': b'text/css',
        '.html': b'text/html',
        '.txt': b'text/plain',

        # Application
        '.pdf': b'application/pdf',
        '.json': b'application/json',
        '.js': b'application/javascript',
    }

    def __init__(self, http_request, forbidden_resources=None):
        """
        This ctor forms an Http Response object using the http request
        :param http_request: HttpRequest object
        :type http_request: HttpRequest
        :param forbidden_resources: Resources that the user is not supposed
            to have access to.
        TODO: Make it work better with big files
        TODO: Make it work with code 300
        TODO: Make it work with custom pages to each error
        """
        self.code = HttpResponse.__get_code(http_request, forbidden_resources)
        self.code_phrase = HttpResponse.code_phrases[self.code]
        self.version = http_request.version

        # Take care of the request errors
        if self.code != 200 and self.code != 300:
            # if Not Found
            self.content_type = HttpResponse.content_types['.html']
            self.data = DEFAULT_ERRORS[self.code]
            self.content_length = len(self.data)

        # Take care of a valid request
        if self.code == 200:
            resource_extension = path.splitext(http_request.resource)[1]
            self.content_type = HttpResponse.content_types[resource_extension]
            self.content_length = path.getsize(http_request.resource)
            with open(http_request.resource, 'r') as resource_data:
                self.data = resource_data.read()

    def __repr__(self):
        # First response line
        return '{} {} {}'.format(self.version, self.code,
                                 HttpResponse.code_phrases[self.code])

    def __str__(self):
        first_line = self.version + self.code + self.code_phrase + b'\r\n'
        response = first_line + b'\r\n'
        # Add header fields
        response += b'Content-Length: ' + self.content_length + b'\r\n'
        response += b'Content-Type: ' + self.content_type + b'\r\n'
        # Add data
        response += '\r\n{}'.format(self.data)

    @staticmethod
    def __get_code(http_request, forbidden_resources=None):
        """
        returns the matching code phrase for the request
        :param http_request: http request
        :type http_request: HttpRequest
        :return: matching status code for the given request
        """
        if path.exists(http_request.resource):
            # in case requested resource exists
            # Check if resource path is harmful or not
            if b'..' in http_request.resource:
                return 403  # Forbidden
            if forbidden_resources and http_request.resource in \
                    forbidden_resources:
                return 403  # Forbidden

            if http_request.method == b'GET':
                return 200  # OK
            elif http_request.method == b'POST':
                # validate that the request contains all the headers
                content_length = http_request.content_length
                content_type = http_request.content_type
                if not all((content_type, content_length)):
                    return 400  # Bad Request
        else:
            # in case requested resource does not exist
            return 404  # Not Found


def main():
    req = b'POST / HTTP/1.1\r\nContent-Type: text/plain\r\n\r\nmymydatadata'
    request = HttpRequest(req)
    response = HttpResponse(request)
    print(response.data)


if __name__ == '__main__':
    main()
