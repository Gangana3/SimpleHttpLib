"""
Author: Or Gany.
Date: 21/2/2018
Overview: This code contains a few types that will be used on working
          conveniently with the HTTP protocol.

"""

import re
import socket
from os import path
from select import select

# constants
ENCODING = 'utf-8'
ROOT_DIR = b'webroot'
DEFAULT_TIMEOUT = 5             # Timeout to close connection with the client
DEFAULT_ERRORS = {
    400: b"""
    <html>
    <head>
    <title>400 Bad Request </title>
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
    <title>403 Forbidden </title>
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
    <title>404 Not Found </title>
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
DEFAULT_BUFFER_SIZE = 1024      # Size of the buffer to receive from client
DEFAULT_PROCESSING_SIZE = 1024  # Bytes that will be processed together
HTTP_METHODS = (b'GET', b'POST')   # supported HTTP request methods


class HttpRequest(object):
    """
    This class represents an HTTP request

    TODO: Make it work better with post requests containing big data
    """
    def __init__(self, request):
        """
        This __init__ receives a request and makes an HttpRequest object
        out of it

        :param request: http request
        :type request: bytes
        """
        self.is_valid = True    # whether the request is valid or not

        # extract first line
        first_lf_index = request.find(b'\r\n')
        first_line = request[0: first_lf_index].split(b' ')

        if len(first_line) != 3:
            # In case first line of the request is invalid
            self.is_valid = False
            return

        self.method = first_line[0]      # Request method: GET, POST etc...
        self.resource = first_line[1]    # Requested resource such as index.html
        self.version = first_line[2]     # HTTP version

        # Home page
        if self.resource == b'/':
            self.resource = b'/index.html'

        # The resource is placed in ROOT directory
        self.resource = ROOT_DIR + self.resource

        if self.method == b'POST':
            length_regex = re.compile(b'Content-Length:(.+)\r\n')
            type_regex = re.compile(b'Content-Type:(.+)\r\n')
            data_regex = re.compile(b'\r\n\r\n(.+)')

            # extract the data and header fields
            data_result = data_regex.search(request)
            type_result = type_regex.search(request)
            length_result = length_regex.search(request)
            data, content_length, content_type = None, None, None
            if data_result:
                data = data_result.group(1).strip()
            if type_result:
                content_type = type_result.group(1).strip()
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
        request = b' '.join((self.method, self.resource, self.version))
        return request.decode(ENCODING)

    def __bytes__(self):
        first_line = '{} {} {}'.format(self.method, self.resource, self.version)
        request = first_line.encode(ENCODING) + b'\r\n'
        if self.method == b'POST':

            # add headers
            request += b'Content-Length: ' + \
                       bytes(str(self.content_length), encoding=ENCODING) + \
                       b'\r\n'
            request += b'Content-Type: ' + self.content_type + b'\r\n'

            # Add data
            request += b'\r\n'
            request += self.data
        return request

    def create_response(self, forbidden_resources=None):
        """
        Creates a response for the request
        :param forbidden_resources: Resources that the user is not supposed
            to have access to.
        :rtype: HttpResponse
        :return: A response to the request
        """
        # check if response is valid
        if not self.is_valid:
            # assign the fields
            self.resource = b'/'
            self.content_length = 0
            self.version = b'HTTP/1.1'
            self.method = b'GET'

        return HttpResponse(self, forbidden_resources=forbidden_resources)


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
        '.ico': b'image/x-icon',

        # Text
        '.css': b'text/css',
        '.html': b'text/html',
        '.txt': b'text/plain',

        # Application
        '.pdf': b'application/pdf',
        '.json': b'application/json',
        '.js': b'application/javascript',
    }

    def __init__(self, http_request, timeout=DEFAULT_TIMEOUT,
                 forbidden_resources=None):
        """
        This ctor forms an Http Response object using the http request
        :param http_request: HttpRequest object
        :type http_request: HttpRequest
        :param forbidden_resources: Resources that the user is not supposed
            to have access to.
        :param timeout: Timeout to close connection with client (in seconds).
        TODO: Make it work with code 300
        TODO: Make it work with custom pages to each error
        """
        self.timeout = timeout
        self.code = HttpResponse.__get_code(http_request, forbidden_resources)
        self.code_phrase = HttpResponse.code_phrases[self.code]
        self.version = http_request.version
        self.connection = b'keep-alive'     # Type of the connection

        # Take care of the request errors
        if self.code != 200 and self.code != 300:
            # if Not Found
            self.content_type = HttpResponse.content_types['.html']
            self.data = DEFAULT_ERRORS[self.code]
            self.content_length = len(self.data)
            # Whether the response is big or not
            self._is_big_response = self.content_length > \
                DEFAULT_PROCESSING_SIZE

        # Take care of a valid request
        if self.code == 200:
            resource_extension = path.splitext(http_request.resource)[1].\
                decode(ENCODING)
            self.content_type = HttpResponse.content_types[resource_extension]
            self.content_length = path.getsize(http_request.resource)

            # Whether the response is big or not
            self._is_big_response = self.content_length > \
                DEFAULT_PROCESSING_SIZE

            # Take care of big files more efficiently
            if not self._is_big_response:
                # Data for small files
                with open(http_request.resource, 'rb') as resource_data:
                    self.data = resource_data.read()
            else:
                # Data for big files
                self.data = HttpResponse.__iter_resource_data(
                    http_request.resource)

    def __repr__(self):
        # First response line
        response = b' '.join((self.version,
                              str(self.code).encode(ENCODING),
                              self.code_phrase))
        return response.decode(ENCODING)

    def __bytes__(self):
        first_line = b' '.join((self.version, str(self.code).encode(ENCODING),
                                self.code_phrase))
        response = first_line + b'\r\n'

        # Add header fields
        response += b'Content-Length: ' + \
                    str(self.content_length).encode(ENCODING) + b'\r\n'
        response += b'Content-Type: ' + self.content_type + b'\r\n'
        response += b'Keep-Alive: timeout=' + str(self.timeout).encode(
            ENCODING) + b'\r\n'
        response += b'Connection: ' + self.connection + b'\r\n'

        # Add data
        response += b'\r\n'
        if not self._is_big_response:
            # For small files
            response += self.data
        else:
            # For big files
            response += next(self.data)    # get the first part of the data
        return response

    def send(self, connection_socket):
        """
        Sends the response through the connection socket
        :param connection_socket:
        :return: None
        """
        if not self._is_big_response:
            # For small files
            connection_socket.send(bytes(self))
        else:
            # For big files
            connection_socket.send(bytes(self))
            for part in self.data:
                connection_socket.send(part)

    @staticmethod
    def __iter_resource_data(filename):
        """
        Returns a view object that contains parts of the data
        :param filename: name of the file/resource
        :return: view object
        :rtype: generator
        """
        file_length = path.getsize(filename)
        with open(filename, 'rb') as resource:
            for i in range(file_length // DEFAULT_PROCESSING_SIZE):
                yield resource.read(DEFAULT_PROCESSING_SIZE)
            yield resource.read()

    @staticmethod
    def __get_code(http_request, forbidden_resources=None):
        """
        returns the matching code phrase for the request
        :param http_request: http request
        :type http_request: HttpRequest
        :return: matching status code for the given request
        """
        if not http_request.is_valid:
            return 400  # Bad Request

        if path.isfile(http_request.resource):
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


class HttpServer(object):
    """
    This class represents an http server
    """
    def __init__(self, ip, port, verbose=True, forbidden_resources=None):
        """
        HttpServer constructor
        :param ip: ip address that the server will be bind in
        :param port: specific port that the server will be bind in
        :param verbose: whether should pring debug messages or not
        :param forbidden_resources: All the resources that the user is NOT
        supposed to have access to.
        """
        self.ip = ip
        self.port = port
        self.verbose = verbose
        self.forbidden_resources = forbidden_resources

    def run(self):
        """
        runs the server
        :return:
        """
        if self.verbose:
            print('Starting Server...')

        # Start serving clients
        self.__serve_clients()

    def __serve_clients(self):
        """
        This method serves clients for they need.
        This method makes use of select() method in order to serve a few
        clients simontaniously
        :return: None
        """
        # Create a tcp socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.ip, self.port))
        server_socket.listen(10)

        if self.verbose:
            print("""
=======================================================

                    Server started!
                    --------------
    port: {0}
    ip address: {1}

            Open the browser and type in the 
            address bar:
            {1}:{0}
            in order to view the website.

=======================================================
                    """.format(self.port, self.ip, self.ip))

        client_sockets = []
        pending_responses = []  # list of tuples contains (socket, response)

        try:
            while True:
                # Filter the sockets that the server can communicate with
                rlist, wlist, xlist = select([server_socket] + client_sockets,
                                             client_sockets, [])

                # Read requests
                for _socket in rlist:
                    if _socket is server_socket:
                        # In case a new client wants to create connection
                        client_socket = server_socket.accept()[0]
                        client_socket.settimeout(DEFAULT_TIMEOUT)
                        client_sockets.append(client_socket)
                    else:
                        request_data = _socket.recv(DEFAULT_BUFFER_SIZE)
                        if request_data:
                            request = HttpRequest(request_data)
                            response = request.create_response()

                            if self.verbose:
                                print(
                                    """
______________________________________________________________

request: {}
response: {}
______________________________________________________________
                                    """.format(repr(request), repr(response)))

                            pending_responses.append((_socket, response))
                        else:
                            # In case socket received empty data
                            client_sockets.remove(_socket)
                            _socket.close()

                # Send responses
                for response in pending_responses:
                    response_dest = response[0]  # Response destination (socket)
                    response_obj = response[1]   # The HttpResponse object
                    if response_dest in wlist:
                        # In case the server can write to the socket
                        try:
                            response_obj.send(response_dest)
                        except BrokenPipeError:
                            pass
                        finally:
                            pending_responses.remove(response)

        except KeyboardInterrupt:
            print('\rShutting Down!')
        finally:
            server_socket.close()
            for _socket in client_sockets:
                _socket.close()
