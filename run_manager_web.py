from webapp import create_default_app
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


def run_tornado_server(host, port):
    app = create_default_app()
    print(app.config)
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port, host)
    IOLoop.instance().start()


if __name__ == '__main__':
    run_tornado_server(host="0.0.0.0", port=5657)
