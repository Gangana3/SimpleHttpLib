from httptypes import HttpServer


def main():
    server = HttpServer('0.0.0.0', 8820)
    server.start()


if __name__ == '__main__':
    main()
