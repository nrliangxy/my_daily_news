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
    run_tornado_server(os.environ.get("PATSNAP360_SPIDER_WEBUI_HOST", "0.0.0.0"),
                       os.environ.get("PATSNAP360_SPIDER_WEBUI_PORT", 5555))
