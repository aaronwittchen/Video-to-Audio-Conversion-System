import importlib


def test_notification_module_loads():
    module = importlib.import_module("src.notification.consumer")
    assert hasattr(module, "main")

