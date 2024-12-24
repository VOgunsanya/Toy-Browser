import socket
import ssl
REQUEST_HEADERS= { "User-Agent": "Victor", "Connection": "close"}
# Data not yet implemented
SUPPORTED_SCHEMES = {"http",'https','file','view-source'}
REDIRECT_COUNT = 0
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
        if self.scheme == "view-source":
            self.protocol, url = url.split("://",1)
            if self.protocol =="http":
                self.port = 80
            elif self.protocol == "https":
                self.port = 443
        elif self.scheme == "http":
            self.port = 80
            url = url[2:]
        elif self.scheme == "https":
            self.port = 443
            url = url[2:]
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
        # Build a request, \r\n are newlines to satisfy http protocol
        s = self.create_socket()
        request = self.build_request()
        # Conversion of request string to bytes
        s.send(request.encode("utf8"))
        response = self.read_response(s)
        return response
    def open_file(self):
        '''
        Opens a local file on the computer, used for the file scheme
        '''
        with open(self.file_path,'r') as f:
            content = f.read()
        return content
    def create_socket(self):
        """
        Creates a socket
        """
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto= socket.IPPROTO_TCP
        )
        #Protocol check accounts for https view-source
        s.connect((self.host,self.port))
        if self.scheme == "https":
            print("Wrapping https socket")
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
            print(f"SSL Connection Established using {s.version()}")
        elif self.scheme == "view-source" and self.protocol == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        return s
    def build_request(self):
        """
        Builds an http request
        """
        request = f"GET {self.path} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        for header,value in REQUEST_HEADERS.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        return request
    def read_response(self,s):
        """
        Reads a response from the server
        """
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
        if int(status) in range(300,400) and REDIRECT_COUNT <5:
            print("Initiating redirect")
            # Initiate redirect
            redirect_location = response_headers["location"]
            if redirect_location[0] == "/":
                if self.scheme == "http" or self.scheme == "https":
                    redirect_location = (self.scheme + "://" + self.host + redirect_location)
                elif self.scheme == "view-source":
                    print(f"Redirecting source scheme")
                    redirect_location = (self.scheme + ":" + self.protocol + "://" + self.host + redirect_location)
            if self.scheme == "view-source":
                redirect_location = "view-source:" + redirect_location
            new_url = URL(redirect_location)
            load(new_url)
            return
        elif REDIRECT_COUNT >=5:
            print(f" Too many redirects!")
            return
        else:
            # Remaining part of response is its body
            if "content-length" in response_headers:
                content = response.read(int(response_headers["content-length"]))
            s.close()
            return content

def show(body, viewing_source = False):
    """
    Displays the result of an http request and response

    Parameters

    Body: String
        Content of an http response
    viewing_source: Boolean
        Differentiates between printing the raw HTML source vs
        creating a rendered page
    """
    # To print entities, we will jump around the giant body response string
    if viewing_source:
        print("Viewing source")
        i = 0
        # Include tags
        while i < len(body):
            if body[i] == "&":
                # Look ahead for HTML entities and replace them
                if body[i:i+4] == '&lt;':
                    print('<', end="")
                    i += 4
                elif body[i:i+4] == '&gt;':
                    print('>', end="")
                    i += 4
                elif body[i:i+5] == '&amp;':
                    print('&', end="")
                    i += 5
                elif body[i:i+6] == '&quot;':
                    print('"', end="")
                    i += 6
                elif body[i:i+6] == '&apos;':
                    print("'", end="")
                    i += 6
                else:
                    # Print the regular ampersand
                    print(body[i], end="")
                    i += 1
            else:
                print(body[i], end="")
                i+=1
    else:
        #Ignore tags
        in_tag = False
        i = 0
        while i < len(body):
            if body[i] == "&":
                # Look ahead for HTML entities and replace them
                if body[i:i+4] == '&lt;':
                    print('<', end="")
                    i += 4
                elif body[i:i+4] == '&gt;':
                    print('>', end="")
                    i += 4
                elif body[i:i+5] == '&amp;':
                    print('&', end="")
                    i += 5
                elif body[i:i+6] == '&quot;':
                    print('"', end="")
                    i += 6
                elif body[i:i+6] == '&apos;':
                    print("'", end="")
                    i += 6
                else:
                    # Print the regular ampersand
                    if not in_tag:
                         print(body[i], end="")
                    i += 1
            if body[i] == "<":
                in_tag = True
            elif body[i] == ">":
                in_tag = False
            elif not in_tag:
                # Print characters inside tags as they are
                print(body[i], end="")
            i += 1
def load(url):
    """
    Loads a webpage by initializing an http request

    Parameters
    url: A URL Object
    """
    if url.scheme in {"http","https"}:
        body = url.request_response()
        if body:
            show(body)
    elif url.scheme == "file":
        body = url.open_file()
    elif url.scheme == "view-source":
        body = url.request_response()
        if body:
            show(body,viewing_source=True)

if __name__ == "__main__":
    while True:
        Selected_server = input("Enter the URL for a webpage. Type exit to quit: ")
        if Selected_server == "exit":
            break
        else:
            load(URL(Selected_server))
