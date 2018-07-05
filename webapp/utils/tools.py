from functools import wraps
import time
import base64
from flask import request, redirect, url_for
from flask import jsonify, make_response, session


def make_succeed_resp(message="success", status_code=200, **kwargs):
    return make_response(jsonify(response_code=1, message=message, **kwargs), status_code)


def make_failed_resp(status_code, message, **kwargs):
    return make_response(jsonify(response_code=0, message=message, **kwargs), status_code)


def encode_token(token):
    t = str(int(time.time()))
    return base64.encodebytes("{0}{1}{2}".format(token[:3], t, token[3:]).encode("utf-8"))


def clear_user_session():
    session.pop("userinfo")


# ====================================
# 装饰器相关验证
# ====================================
def request_method_check(method="GET"):
    def decorated(func):
        @wraps(func)
        def decorated_fn(*args, **kwargs):
            if request.method.upper() != method:
                return make_failed_resp(status_code=405, message="{0} method is not allow".format(request.method))
            return func(*args, **kwargs)
        return decorated_fn
    return decorated


def post_check():
    return request_method_check("POST")


def ajax_check():
    def decorated(func):
        @wraps(func)
        def decorated_fn(*args, **kwargs):
            if not request.is_xhr:
                return make_failed_resp(status_code=403, message="ajax requests require")
            return func(*args, **kwargs)
        return decorated_fn
    return decorated


def session_check():
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            userinfo = session.get("userinfo")
            if userinfo is None:
                return redirect(url_for("index_view.index"))
            return f(*args, **kwargs)
        return decorated_fn
    return decorated


def session_load(load):
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            session["load"] = load
            return f(*args, **kwargs)
        return decorated_fn
    return decorated

