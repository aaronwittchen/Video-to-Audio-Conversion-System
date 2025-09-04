import importlib
import types


def test_converter_module_loads():
    module = importlib.import_module("src.converter.consumer")
    assert hasattr(module, "main")

