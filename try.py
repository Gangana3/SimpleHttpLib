from httptypes import HttpServer


def main():
    server = HttpServer('127.0.0.1', 1234, verbose=False)
    server.start()


if __name__ == '__main__':
    main()
