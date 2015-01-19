import json
import time

import pushbullet
import websocket

API_CHECK_FREQUENCY = 5
PB_WS_URL = "wss://stream.pushbullet.com/websocket/"


class PushbulletRPC(object):

    def __init__(self, api_key, srv_dev_name):
        self.pb = pushbullet.PushBullet(api_key)
        self.pb_ws = websocket.create_connection(PB_WS_URL + api_key)
        self.srv = self.get_srv_device(srv_dev_name)
        self.last_check = time.time()
        self.funcs = {}

    def get_srv_device(self, srv_dev_name):
        dev = self.find_device_by_name(srv_dev_name)
        if dev:
            return dev
        print "Device not found. Creating ..."
        success, dev = self.pb.new_device(srv_dev_name)
        if success:
            return dev
        raise RuntimeError("Error while creating new device.")

    def start(self):
        while True:
            if self.socket_has_push():
                for push in self.get_my_active_pushes(self.last_check):
                    source_device = self.find_device_by_iden(push["source_device_iden"])
                    func_name, params = PushbulletRPC.parse_call(push)
                    print "Push back to %s" % source_device.nickname
                    if func_name:
                        title, body = self.process_push(func_name, params)
                    else:
                        title, body = "Error", "empty function name"
                    self.pb.push_note(title, body, device=source_device)

    def socket_has_push(self):
        json_data = self.pb_ws.recv()
        data = json.loads(json_data)
        if data.get("type") == "tickle" and data.get("subtype") == "push":
            return True
        return False

    def find_device_by_name(self, name):
        for dev in self.pb.devices:
            if dev.nickname == name:
                return dev

    def find_device_by_iden(self, iden):
        for dev in self.pb.devices:
            if dev.device_iden == iden:
                return dev

    def get_my_active_pushes(self, modified_after, limit=None):
        my_pushes = []
        self.last_check = time.time()
        success, pushes = self.pb.get_pushes(modified_after, limit)
        if success:
            for push in pushes:
                if push.get("target_device_iden") == self.srv.device_iden and push["active"]:
                    my_pushes.append(push)
        return my_pushes

    @staticmethod
    def parse_call(push):
        func_name = push.get("title")
        params = push.get("body")
        if func_name:
            func_name = func_name.lower().strip()
        if params:
            params = params.lower().strip()
        return func_name, params

    def register_function(self, function, name=None):
        if name is None:
            name = function.__name__
        self.funcs[name] = function

    def process_push(self, method, params=None):
        try:
            func = self.funcs[method]
        except KeyError:
            return "Error", "method %s is not supported" % method
        try:
            result = func(params) if params else func()
        except Exception as exc:
            return "Error", "%s: %s" % (exc.__class__.__name__, exc)
        return result
