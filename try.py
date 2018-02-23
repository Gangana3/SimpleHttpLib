from httptypes import HttpServer


def main():
    server = HttpServer('127.0.0.1', 8820)
    server.start()


if __name__ == '__main__':
    main()
