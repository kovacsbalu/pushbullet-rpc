import json
import time
import mock
import pytest

from pushbulletrpc import pushbulletrpc


class PushbulletError(Exception):
    pass


class Device(object):

    def __init__(self, name, iden=None):
        self.nickname = name
        self.device_iden = iden


class FakePushbullet(object):

    def __init__(self, api_key=None):
        self.devices = [Device("test_dev")]


class TestPushbulletRPC(object):

    def setup_method(self, method):
        pushbulletrpc.pushbullet.Pushbullet = FakePushbullet
        pushbulletrpc.pushbullet.PushbulletError = PushbulletError
        pushbulletrpc.websocket = mock.Mock(return_value=None)
        self.pb_rpc = pushbulletrpc.PushbulletRPC("test api key", "test_dev")

    def test_init(self):
        assert self.pb_rpc.srv.nickname == "test_dev"
        assert isinstance(self.pb_rpc.last_check, float)
        assert self.pb_rpc.funcs == {}

    def test_get_srv_device_found(self):
        dev = self.pb_rpc.get_srv_device("test_dev")
        assert dev.nickname == "test_dev"

    def test_get_srv_device_create(self):
        self.pb_rpc.find_device_by_name = mock.Mock(return_value=None)
        self.pb_rpc.pb.new_device = mock.Mock(return_value=(Device("new_dev")))
        dev = self.pb_rpc.get_srv_device("test_dev")
        assert dev.nickname == "new_dev"

    def test_get_srv_device_error(self):
        self.pb_rpc.find_device_by_name = mock.Mock(return_value=None)
        self.pb_rpc.pb.new_device = mock.Mock(return_value=(None), side_effect=pushbulletrpc.pushbullet.PushbulletError)
        with pytest.raises(RuntimeError) as excinfo:
            self.pb_rpc.get_srv_device("test_dev")
        assert excinfo.value.message == "Error while creating new device."

    def test_recv_and_process(self):
        self.pb_rpc.socket_has_push = mock.Mock(return_value=True)
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True, "source_device_iden": "s_iden"}]
        self.pb_rpc.get_my_active_pushes = mock.Mock(return_value=test_pushes)
        test_source_dev = Device("test_source_dev", "dev_iden")
        self.pb_rpc.find_device_by_iden = mock.Mock(return_value=test_source_dev)
        self.pb_rpc.pb.push_note = mock.Mock()
        testfunc, testparams = "testfunc", "testparams"
        with mock.patch.object(pushbulletrpc.PushbulletRPC, 'parse_call', return_value=(testfunc, testparams)) as mock_parse_call:
            title, body = "result title", "result body"
            self.pb_rpc.process_push = mock.Mock(return_value=(title, body))
            self.pb_rpc.recv_and_process()
            mock_parse_call.assert_called_with(test_pushes[0])
            self.pb_rpc.process_push.assert_called_with(testfunc, testparams)
            self.pb_rpc.pb.push_note.assert_called_once_with(title, body, device=test_source_dev)

    def test_recv_and_process_error(self):
        self.pb_rpc.socket_has_push = mock.Mock(return_value=True)
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True, "source_device_iden": "s_iden"}]
        self.pb_rpc.get_my_active_pushes = mock.Mock(return_value=test_pushes)
        test_source_dev = Device("test_source_dev", "dev_iden")
        self.pb_rpc.find_device_by_iden = mock.Mock(return_value=test_source_dev)
        self.pb_rpc.pb.push_note = mock.Mock()
        with mock.patch.object(pushbulletrpc.PushbulletRPC, 'parse_call', return_value=("", "")) as mock_parse_call:
            self.pb_rpc.recv_and_process()
            mock_parse_call.assert_called_with(test_pushes[0])
            self.pb_rpc.pb.push_note.assert_called_once_with('Error', 'empty function name', device=test_source_dev)

    def test_socket_has_push(self):
        data = {"type": "tickle", "subtype": "push"}
        self.pb_rpc.pb_ws.recv = mock.Mock(return_value=json.dumps(data))
        assert self.pb_rpc.socket_has_push()

    def test_socket_has_no_push(self):
        data = {"type": "nop"}
        self.pb_rpc.pb_ws.recv = mock.Mock(return_value=json.dumps(data))
        assert not self.pb_rpc.socket_has_push()

    def test_find_device_by_name(self):
        test_dev = Device("dev_name")
        self.pb_rpc.pb.devices = [test_dev]
        dev = self.pb_rpc.find_device_by_name("dev_name")
        assert dev == test_dev

    def test_find_device_by_iden(self):
        test_dev = Device("test_dev", "dev_iden")
        self.pb_rpc.pb.devices = [test_dev]
        dev = self.pb_rpc.find_device_by_iden("dev_iden")
        assert dev == test_dev

    def test_get_my_active_pushes(self):
        self.pb_rpc.srv = Device("dev_name", "test_dev_iden")
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True}]
        self.pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = self.pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes == test_pushes

    def test_get_my_active_pushes_no_pushes_for_device(self):
        self.pb_rpc.srv = Device("dev_name", "no_dev_iden")
        test_pushes = [{"target_device_iden": "test_dev_iden", "active": True}]
        self.pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = self.pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes != test_pushes

    def test_get_my_active_pushes_no_pushes(self):
        self.pb_rpc.srv = Device("dev_name", "test_dev_iden")
        test_pushes = []
        self.pb_rpc.pb.get_pushes = mock.Mock(return_value=(True, test_pushes))
        active_pushes = self.pb_rpc.get_my_active_pushes(time.time(), limit=None)
        assert active_pushes == test_pushes

    def test_parse_call(self):
        test_push = {"title": "Func_Name ", "body": "Func_Params "}
        func_name, params = self.pb_rpc.parse_call(test_push)
        assert func_name == "func_name"
        assert params == "func_params"

    def test_register_function(self):
        def test_func():
            pass
        self.pb_rpc.register_function(test_func)
        assert self.pb_rpc.funcs["test_func"] == test_func

    def test_process_push(self):
        def test_func():
            return "test_ok"
        self.pb_rpc.register_function(test_func)
        result = self.pb_rpc.process_push("test_func")
        assert result == "test_ok"

    def test_process_push_args_error(self):
        def test_func():
            return "test_ok"
        self.pb_rpc.register_function(test_func)
        result = self.pb_rpc.process_push("test_func", "args")
        assert result == ("Error", "TypeError: test_func() takes no arguments (1 given)")

    def test_process_push_with_args(self):
        def test_func(args):
            return "test_args_ok: %s" % args
        self.pb_rpc.register_function(test_func)
        result = self.pb_rpc.process_push("test_func", "test_args")
        assert result == "test_args_ok: test_args"

    def test_process_push_with_args_error(self):
        def test_func(args):
            return "test_args_ok"
        self.pb_rpc.register_function(test_func)
        result = self.pb_rpc.process_push("test_func")
        assert result == ("Error", "TypeError: test_func() takes exactly 1 argument (0 given)")

    def test_process_push_not_supported(self):
        result = self.pb_rpc.process_push("test_func")
        assert result == ('Error', 'method test_func is not supported')
