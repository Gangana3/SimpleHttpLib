"""
Author: Or Gany.
Date: 21/2/2018
Overview: This code contains a few types that will be used on working
          conveniently with the HTTP protocol.

"""
import re


# constants
ROOT_DIR = 'webroot/'


class HttpRequest(object):
    """
    This class represents an HTTP request

    TODO: Make it work better with post requests containing big data
    """
    def __init__(self, request):
        """
        :param request: http request
        :type request: bytes
        """
        # extract first line
        first_lf_index = request.find(b'\r\n')
        first_line = request[0: first_lf_index].split(b' ')
        self.method = first_line[0]    # Request method: GET, POST etc...
        self.resource = first_line[1]  # Requested resource such as index.html
        self.version = first_line[2]   # HTTP version

        if self.method == 'POST':
            length_regex = re.compile('Content-Length:(.+)\r\n')
            result = length_regex.search(request)
            if result:
                self.length = int(result.group(0).strip())

