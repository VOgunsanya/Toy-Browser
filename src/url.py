import socket
import ssl
REQUEST_HEADERS= {"Connection": "close",
                   "User-Agent": "Victor"}
SUPPORTED_SCHEMES = {"http",'https','file','data','view-source'}
class URL:
    def __init__(self,url):
        """
        Constructs a URL object

        Parameters

        url: String
            String containing a typical website url, which can contain varous schemes and hosts
        """
        # Breaking down URL into defining parts
        self.scheme, url = url.split(":",1)
        assert self.scheme in SUPPORTED_SCHEMES
        if self.scheme == "file":
            self.file_path = url[2:]
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
        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        for header,value in REQUEST_HEADERS.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        # request = "GET {} HTTP/1.0\r\n".format(self.path)
        # request += "Host: {}\r\n".format(self.host)
        # request += "\r\n"
        print(request)
        # Conversion of rezquest string to bytes
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
    def open_file(self):
        '''
        Opens a local file on the computer, used for the file scheme
        '''
        with open(self.file_path,'r') as f:
            content = f.read()
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
    if url.scheme == 'http' or url.scheme == 'https':
        body = url.request_response()
    if url.scheme == "file":
        body = url.open_file()
    show(body)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        load(URL("file:///mnt/c/Users/user/Desktop/MIT/repos/Toy-Browser/src/yadda.html"))
    else:
        load(URL(sys.argv[1]))
