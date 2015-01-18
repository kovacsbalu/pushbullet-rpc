import time
import mock
import pytest

from pushbulletrpc import pushbulletrpc


class Device(object):

    def __init__(self, name, iden=None):
        self.nickname = name
        self.device_iden = iden


class FakePushBullet(object):

    def __init__(self, api_key=None):
        self.devices = [Device("test_dev")]


class TestPushbulletRPC(object):

    @classmethod
    def setup_class(cls):
        pushbulletrpc.pushbullet.PushBullet = FakePushBullet

    def test_init(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        assert pb_rpc.srv.nickname == "test_dev"
        assert isinstance(pb_rpc.last_check, float)
        assert pb_rpc.funcs == {}

    def test_get_srv_device_found(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        dev = pb_rpc.get_srv_device("test_dev")
        assert dev.nickname == "test_dev"

    def test_get_srv_device_create(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.find_device_by_name = mock.Mock(return_value=None)
        pb_rpc.pb.new_device = mock.Mock(return_value=(True, Device("new_dev")))
        dev = pb_rpc.get_srv_device("test_dev")
        assert dev.nickname == "new_dev"

    def test_get_srv_device_error(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.find_device_by_name = mock.Mock(return_value=None)
        pb_rpc.pb.new_device = mock.Mock(return_value=(False, None))
        with pytest.raises(RuntimeError) as excinfo:
            pb_rpc.get_srv_device("test_dev")
        assert excinfo.value.message == "Error while creating new device."

    def test_find_device_by_name(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        test_dev = Device("dev_name")
        pb_rpc.pb.devices = [test_dev]
        dev = pb_rpc.find_device_by_name("dev_name")
        assert dev == test_dev

    def test_find_device_by_iden(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        test_dev = Device("test_dev", "dev_iden")
        pb_rpc.pb.devices = [test_dev]
        dev = pb_rpc.find_device_by_iden("dev_iden")
        assert dev == test_dev

    def test_get_my_active_pushes(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.srv = Device("dev_name", "test_dev_iden")
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True}]
        pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes == test_pushes

    def test_get_my_active_pushes_no_pushes_for_device(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.srv = Device("dev_name", "no_dev_iden")
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True}]
        pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes != test_pushes

    def test_get_my_active_pushes_no_pushes(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.srv = Device("dev_name", "test_dev_iden")
        test_pushes = []
        pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes == test_pushes

    def test_parse_call(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        test_push = {"title": "Func_Name ", "body": "Func_Params "}
        func_name, params = pb_rpc.parse_call(test_push)
        assert func_name == "func_name"
        assert params == "func_params"

    def test_register_function(self):
        def test_func():
            pass
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.register_function(test_func)
        assert pb_rpc.funcs["test_func"] == test_func

    def test_process_push(self):
        def test_func():
            return "test_ok"
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.register_function(test_func)
        result = pb_rpc.process_push("test_func")
        assert result == "test_ok"

    def test_process_push_args_error(self):
        def test_func():
            return "test_ok"
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.register_function(test_func)
        result = pb_rpc.process_push("test_func", "args")
        assert result == ("Error", "TypeError: test_func() takes no arguments (1 given)")

    def test_process_push_with_args(self):
        def test_func(args):
            return "test_args_ok: %s" % args
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.register_function(test_func)
        result = pb_rpc.process_push("test_func", "test_args")
        assert result == "test_args_ok: test_args"

    def test_process_push_with_args_error(self):
        def test_func(args):
            return "test_args_ok"
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        pb_rpc.register_function(test_func)
        result = pb_rpc.process_push("test_func")
        assert result == ("Error", "TypeError: test_func() takes exactly 1 argument (0 given)")

    def test_process_push_not_supported(self):
        pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")
        result = pb_rpc.process_push("test_func")
        assert result == ('Error', 'method test_func is not supported')
