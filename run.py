import os
from webapp import create_default_app
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


def run_tornado_server(host, port):
    app = create_default_app()
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port, host)
    IOLoop.instance().start()


if __name__ == '__main__':
    app = create_default_app()
    app.run(host="0.0.0.0", port=5556, debug=True)
