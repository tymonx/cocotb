# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

"""Testing Cocotb regression manager."""

import os
import sys
from collections.abc import Generator
from types import ModuleType

import pytest

from cocotb.regression import RegressionManager

# https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-package-metadata
if sys.version_info < (3, 10):
    import importlib_metadata
    from importlib_metadata import EntryPoint, EntryPoints
else:
    import importlib.metadata as importlib_metadata
    from importlib.metadata import EntryPoint, EntryPoints


@pytest.fixture(name="entry_points")
def entry_points_fixture() -> Generator[list[EntryPoint], None, None]:
    """It allows to mock Python entry points.

    https://docs.python.org/3/library/importlib.metadata.html#importlib.metadata.entry_points

    Yields:
        List of mocked entry points. By default it is empty and should be filled by tests.
    """
    # Fixture setup
    entry_points: list[EntryPoint] = []
    restore_entry_points = importlib_metadata.entry_points
    restore_env: str | None = os.environ.get("COCOTB_REGRESSION_MANAGER")

    def mock_entry_points(**params) -> EntryPoints:
        return EntryPoints(entry_points).select(**params)

    os.environ["COCOTB_REGRESSION_MANAGER"] = "mock"
    importlib_metadata.entry_points = mock_entry_points

    yield entry_points

    # Fixture teardown
    importlib_metadata.entry_points = restore_entry_points

    if restore_env is not None:
        os.environ["COCOTB_REGRESSION_MANAGER"] = restore_env
    else:
        del os.environ["COCOTB_REGRESSION_MANAGER"]


@pytest.fixture(name="module")
def module_fixture() -> Generator[ModuleType, None, None]:
    """It allows to mock Python module. Mocked module is added to global modules scope.

    Yields:
        New created mock of Python module. Tests can modify it using `setattr`.
    """
    # Fixture setup
    name: str = "mock_cocotb_plugin"
    module: ModuleType = ModuleType(name)
    restore_module: ModuleType | None = sys.modules.get(name)
    sys.modules[name] = module

    yield module

    # Fixture teardown
    if restore_module is not None:
        sys.modules[name] = restore_module
    else:
        del sys.modules[name]


def test_create_default() -> None:
    """Test if `RegressionManager.create()` will create new instance of regression manager."""
    instance: RegressionManager = RegressionManager.create()

    assert instance is not None
    assert isinstance(instance, RegressionManager)


def test_create_raise_not_registered(entry_points: list[EntryPoint]) -> None:
    """Test if `RegressionManager.create()` will raise an exception when Cocotb plugin was not registered."""
    with pytest.raises(RuntimeError) as e:
        RegressionManager.create("mock")

    assert str(e.value) == "Cocotb plugin 'mock' wasn't registered!"


def test_create_raise_not_module_found(entry_points: list[EntryPoint]) -> None:
    """Test if `RegressionManager.create()` will raise an exception when Cocotb plugin was not found."""
    entry_points.append(EntryPoint(name="mock", value="not_found", group="cocotb"))

    with pytest.raises(ModuleNotFoundError):
        RegressionManager.create("mock")


def test_create_raise_no_attribute(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will raise an exception when Cocotb plugin has missing attribute."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))

    with pytest.raises(RuntimeError) as e:
        RegressionManager.create("mock")

    assert (
        str(e.value)
        == "Cocotb plugin 'mock' doesn't provide 'cocotb_register_regression_manager' attribute!"
    )


def test_create_raise_attribute_not_callable(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will raise an exception when Cocotb plugin attribute is not callable."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))
    setattr(module, "cocotb_register_regression_manager", 1234)

    with pytest.raises(RuntimeError) as e:
        RegressionManager.create("mock")

    assert (
        str(e.value)
        == "Cocotb plugin attribute 'mock.cocotb_register_regression_manager' is not callable!"
    )


def test_create_raise_returned_value_not_callable(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will raise an exception when returned value from attribute is not callable."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))
    setattr(module, "cocotb_register_regression_manager", lambda: None)

    with pytest.raises(RuntimeError) as e:
        RegressionManager.create("mock")

    assert (
        str(e.value)
        == "Returned None from Cocotb plugin 'mock.cocotb_register_regression_manager()' is not callable!"
    )


def test_create_raise_wrong_type(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will raise an exception when created wrong type of instance."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))
    setattr(module, "cocotb_register_regression_manager", lambda: dict)

    with pytest.raises(RuntimeError) as e:
        RegressionManager.create("mock")

    assert (
        str(e.value)
        == "Cocotb plugin 'mock' doesn't implement <class 'cocotb.regression.RegressionManager'>!"
    )


def test_create_mock_from_name(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will return created instance of regression manager from name."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))
    setattr(module, "cocotb_register_regression_manager", lambda: RegressionManager)

    instance: RegressionManager = RegressionManager.create("mock")

    assert instance is not None
    assert isinstance(instance, RegressionManager)


def test_create_mock_from_env(
    entry_points: list[EntryPoint], module: ModuleType
) -> None:
    """Test if `RegressionManager.create()` will return created instance of regression manager from environment variable."""
    entry_points.append(EntryPoint(name="mock", value=module.__name__, group="cocotb"))
    setattr(module, "cocotb_register_regression_manager", lambda: RegressionManager)

    instance: RegressionManager = RegressionManager.create()

    assert instance is not None
    assert isinstance(instance, RegressionManager)
