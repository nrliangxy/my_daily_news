import time
import base64
import atexit
import redis
from flask import Flask, g, request, Markup
from werkzeug.contrib.profiler import ProfilerMiddleware
from webapp.log import create_logger, generate_logger_handler
from backend.task import BackgroundTaskManager, SchedulerTaskManager
from database import create_default_client, init_mongonengin_connect

# 初始化mongo服务
mongo_client = create_default_client()
init_mongonengin_connect()

# 初始化后台任务
stm_manager = SchedulerTaskManager(mongo_client)

bg_manager = BackgroundTaskManager(mongo_client)
bg_manager.start()
atexit.register(lambda: bg_manager.shutdown())



def create_default_app(profile=False, debug=False):
    app = Flask(__name__)
    app.config.from_object("webapp.config.DefaultConfig")
    app.url_map.strict_slashes = False
    if profile:
        """
        请求性能测试参数说明：
            tottime : 在这个函数中所花费所有时间。
            percall : 是 tottime 除以 ncalls 的结果。
            cumtime : 花费在这个函数以及任何它调用的函数的时间。
            percall : cumtime 除以 ncalls。
            filename:lineno(function) : 函数名以及位置。
        """
        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
    # 初始化蓝图
    from webapp.views.indexView import index_bp
    from webapp.views.qualityView import quality_bp
    from webapp.views.schedulerView import sche_bp
    from webapp.views.dingding_api import dingding_bp
    app.register_blueprint(index_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(sche_bp)
    app.register_blueprint(dingding_bp)

    # 通用视图注册
    register_common_view(app)
    if not debug:
        app.config["PREFERRED_URL_SCHEME"] = "https"
    # 初始化logger配置
    app.logger_name = "app"
    app.logger.setLevel(10)
    app.logger.handlers = generate_logger_handler("app")

    return app


def register_common_view(app):
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        start_time = g.start_time
        cost_time = 0
        if start_time:
            cost_time = round((time.time() - start_time) * 1000, 3)
        method = request.method
        status_code = response.status_code
        path = request.path
        app.logger.info("%s %s %s-->cost:%s ms" % (method, status_code, path, cost_time))
        return response

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            # todo
            pass

    @app.template_filter('urlsafe_base64')
    def urlsafe_base64_encode(s):
        if type(s) == 'Markup':
            s = s.unescape()
        s = base64.urlsafe_b64encode(s)
        s = s.decode("utf-8")
        return Markup(s)

    @app.template_filter('b2u')
    def byte_to_unicode(s):
        return s.decode()
