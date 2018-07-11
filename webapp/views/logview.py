#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Blueprint, render_template, request
from webapp import mongo_client
from webapp.utils.tools import session_load

log_bp = Blueprint("log_view", __name__, url_prefix="/logs")

def error_field_check_403(error_msg):
    return render_template("error/403.html", error_msg=error_msg)


# @log_bp.route('/index')