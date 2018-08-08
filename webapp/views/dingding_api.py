#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_restful import reqparse, Api, Resource
import json, collections
import requests

notice = collections.namedtuple('Notice', ['data', 'url'])

dingding_bp = Blueprint("dingding_view", __name__, url_prefix="/dingding")
api = Api(dingding_bp)




class Notification(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('data')
        self.parser.add_argument('url')
        self.robot_api = None
        self.data = None
    
    def post(self):
        args = self.parser.parse_args()
        data = args.get('data')
        url = args.get('url')
        notice_obj = notice(data, url)
        self.robot_api = notice_obj.url
        if self.robot_api:
            self.remind(data)

    def remind(self, msg):
        data = {
            "msgtype": "text",
            "text": {
                "content": f"{msg}"
            },
            "at": {"isAtAll": True}
        }
        r = requests.post(self.robot_api, data=json.dumps(data),
                          headers={'content-type': 'application/json'})
        return r.json()
    



    
api.add_resource(Notification, '/api/v1/notification')



