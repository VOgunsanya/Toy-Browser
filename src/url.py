import socket
import ssl
class URL:
    def __init__(self,url):
        """
        Constructs a URL object

        Parameters

        url: String
            String containing a typical website url, which can contain varous schemes and hosts
        """
        # Breaking down URL into defining parts
        self.scheme, url = url.split("://",1)
        assert self.scheme in {"http", "https"}
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        # Force the / to exist as part of path of every url
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/",1)
        if ":" in self.host:
            self.host, port = self.host.split(":",1)
            self.port = int(port)
        self.path = "/" + url
    def request_response(self):
        """
        Initializes an http request and evaluates the response
        """
        #Establish a connection
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto= socket.IPPROTO_TCP
        )
        s.connect((self.host,self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        # Build a request, \r\n are newlines to satisfy http protocol
        request = f"GET {self.path} HTTP/1.0/\r\n"
        request += f"Host: {self.host}\r\n"
        request += "\r\n"
        # Conversion of request string to bytes
        s.send(request.encode("utf8"))
        # Break down the subsequent response
        response = s.makefile('r', encoding='utf8', newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ",2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":",1)
            # Usage of casefold to acommodate more languages
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        # Remaining part of response is its body
        content = response.read()
        s.close()
        return content
def show(body):
    """
    Displays the result of an http request and response

    Parameters

    Body: String
        Content of an http response
    """
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c ==">":
            in_tag = False
        elif not in_tag:
            # Don't want a newline to print after a character
            print(c, end="")
def load(url):
    """
    Loads a webpage by initializing an http request

    Parameters
    url: A URL Object
    """
    body = url.request_response()
    show(body)

if __name__ == "__main__":
    import sys
    load(URL(sys.argv[1]))
