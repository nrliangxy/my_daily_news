import json
import requests


class Notification:
    def __init__(self, robot_url):
        self.robot_api = robot_url

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


if __name__ == '__main__':
    robot_api = "https://oapi.dingtalk.com/robot/send?access_token=9219c3463ad5a349650da5ecbe73ba2ffa5487ff36ad6cd8223ca668f305f9ee"
    n = Notification(robot_api)
    print(n.remind("haha"))