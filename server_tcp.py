import socket
import os
import sys

FILE_EXIST = "HTTP/1.1 200 OK\r\nConnection: "
LEN_MSG = "\r\nContent-Length: "
FILE_NOT_EXIST_CASE_404 = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
REDIRECT_CASE_301 = "HTTP/1.1 301 Moved Permanently\r\nConnection: close\r\nLocation: /result.html\r\n\r\n"


# Function :find_path
# Get the path between 'GET' and 'HTTP/1.1'
# Return the path
def find_path(client_request):
    start = client_request.find('GET') + len('GET')
    end = client_request.find('HTTP/1.1')
    return client_request[start: end].strip()


# Function: read_file
# Read the file
# Return the contents of the file and his size.
def read_file(modes, path):
    if os.path.isfile(path):
        content_len = os.path.getsize(path)
        with open(path, modes) as f:
            return f.read(), str(content_len)
    return "", ""


# Function: close_or_keep_alive
# Get the client request that contains the connection info
# Return close or keep alive.
def close_or_keep_alive(req):
    if req.find('keep-alive') != -1:
        return 'keep-alive'
    return 'close'


# Function: server_tcp
# Server that connects to clients and handles their requests
# Special cases of client request: '/' - "index.html", "redirect" - case 301, case 404 - not found.
def server_tcp(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    while True:
        client_socket, client_address = server.accept()
        # print('Connection from: ', client_address)
        client_socket.settimeout(1)
        is_case_404_or_301 = False
        client_connect = True
        while client_connect:
            try:
                original_req = ''
                original_req += client_socket.recv(1024).decode('utf-8')
                # empty request or contains only whitespace chars
                if not original_req or original_req.isspace():
                    client_socket.close()
                    break
                # print user request
                print(original_req)
                list_req = original_req.split("\r\n\r\n")
            except socket.timeout:
                client_socket.close()
                break
            for req in list_req[:-1]:
                server_response = ''
                connection = close_or_keep_alive(req)
                # serve get empty request , close the cur socket
                path = find_path(req)
                if path.startswith('/redirect'):
                    server_response = REDIRECT_CASE_301.encode('utf-8')
                    is_case_404_or_301 = True
                elif path == '/':
                    path = 'files/index.html'
                else:
                    path = 'files' + path
                if path.endswith('.jpg') or path.endswith('.ico') and not is_case_404_or_301:
                    file_content, content_len = read_file("rb", path)
                else:
                    file_content, content_len = read_file("rb", path)
                # file dose not exist
                if file_content == "" and not is_case_404_or_301:
                    server_response = FILE_NOT_EXIST_CASE_404.encode('utf-8')
                    is_case_404_or_301 = True
                if is_case_404_or_301:
                    client_socket.send(server_response)
                    client_connect = False
                    break
                else:
                    server_response = (FILE_EXIST + connection + LEN_MSG + content_len + "\r\n\r\n").encode('utf-8')
                    if type(file_content) is str:
                        file_content = file_content.encode('utf-8')
                    client_socket.send(server_response + file_content)
                if connection == 'close':
                    client_connect = False
                    break
        client_socket.close()


if __name__ == '__main__':
    server_port = sys.argv[1]
    server_tcp(int(server_port))
