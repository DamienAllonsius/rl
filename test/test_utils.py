# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import argparse
import os
import sys

import _utils_internal
import mock
import pytest

from torchrl._utils import get_binary_env_var, implement_for
from torchrl.envs.libs.gym import GymEnv, set_gym_backend


@pytest.mark.parametrize("value", ["True", "1", "true"])
def test_get_binary_env_var_positive(value):
    try:
        key = "SOME_ENVIRONMENT_VARIABLE_UNLIKELY_TO_BE_IN_ENVIRONMENT"

        assert key not in os.environ

        os.environ[key] = value
        assert get_binary_env_var(key)

    finally:
        if key in os.environ:
            del os.environ[key]


@pytest.mark.parametrize("value", ["False", "0", "false"])
def test_get_binary_env_var_negative(value):
    try:
        key = "SOME_ENVIRONMENT_VARIABLE_UNLIKELY_TO_BE_IN_ENVIRONMENT"

        assert key not in os.environ

        os.environ[key] = "True"
        assert get_binary_env_var(key)
        os.environ[key] = value
        assert not get_binary_env_var(key)

    finally:
        if key in os.environ:
            del os.environ[key]


def test_get_binary_env_var_missing():
    try:
        key = "SOME_ENVIRONMENT_VARIABLE_UNLIKELY_TO_BE_IN_ENVIRONMENT"

        assert key not in os.environ
        assert not get_binary_env_var(key)

    finally:
        if key in os.environ:
            del os.environ[key]


def test_get_binary_env_var_wrong_value():
    try:
        key = "SOME_ENVIRONMENT_VARIABLE_UNLIKELY_TO_BE_IN_ENVIRONMENT"

        assert key not in os.environ
        os.environ[key] = "smthwrong"
        with pytest.raises(ValueError):
            get_binary_env_var(key)

    finally:
        if key in os.environ:
            del os.environ[key]


class implement_for_test_functions:
    """
    Groups functions that are used in tests for `implement_for` decorator.
    """

    @staticmethod
    @implement_for("_utils_internal", "0.3")
    def select_correct_version():
        """To test from+ range and that this function is correctly selected as the implementation."""
        return "0.3+"

    @staticmethod
    @implement_for("_utils_internal", "0.2", "0.3")
    def select_correct_version():  # noqa: F811
        """To test that right bound is not included."""
        return "0.2-0.3"

    @staticmethod
    @implement_for("_utils_internal", "0.1", "0.2")
    def select_correct_version():  # noqa: F811
        """To test that function with missing from-to range is ignored."""
        return "0.1-0.2"

    @staticmethod
    @implement_for("missing_module")
    def missing_module():
        """To test that calling decorated function with missing module raises an exception."""
        return "missing"

    @staticmethod
    @implement_for("_utils_internal", None, "0.3")
    def missing_version():
        return "0-0.3"

    @staticmethod
    @implement_for("_utils_internal", "0.4")
    def missing_version():  # noqa: F811
        return "0.4+"


def test_implement_for():
    assert implement_for_test_functions.select_correct_version() == "0.3+"


def test_implement_for_missing_module():
    msg = r"Supported version of .*test_utils.missing_module' has not been found."
    with pytest.raises(ModuleNotFoundError, match=msg):
        implement_for_test_functions.missing_module()


def test_implement_for_missing_version():
    msg = r"Supported version of .*test_utils.missing_version' has not been found."
    with pytest.raises(ModuleNotFoundError, match=msg):
        implement_for_test_functions.missing_version()


def test_implement_for_reset():
    assert implement_for_test_functions.select_correct_version() == "0.3+"
    _impl = implement_for._implementations
    assert _impl is implement_for._implementations
    implement_for.reset()
    assert implement_for_test_functions.select_correct_version() == "0.3+"
    assert _impl is not implement_for._implementations


@pytest.mark.parametrize(
    "version, from_version, to_version, expected_check",
    [
        ("0.21.0", "0.21.0", None, True),
        ("0.21.0", None, "0.21.0", False),
        ("0.9.0", "0.11.0", "0.21.0", False),
        ("0.9.0", "0.1.0", "0.21.0", True),
        ("0.19.99", "0.19.9", "0.21.0", True),
        ("0.19.99", None, "0.19.0", False),
        ("5.61.77", "0.21.0", None, True),
        ("5.61.77", None, "0.21.0", False),
    ],
)
def test_implement_for_check_versions(
    version, from_version, to_version, expected_check
):
    assert (
        implement_for.check_version(version, from_version, to_version) == expected_check
    )


@pytest.mark.parametrize(
    "gymnasium_version, expected_from_version_gymnasium, expected_to_version_gymnasium",
    [
        ("0.27.0", "0.27.0", None),
        ("0.27.2", "0.27.0", None),
        ("5.1.77", "0.27.0", None),
    ],
)
@pytest.mark.parametrize(
    "gym_version, expected_from_version_gym, expected_to_version_gym",
    [
        ("0.21.0", "0.21.0", None),
        ("0.22.0", "0.21.0", None),
        ("5.61.77", "0.21.0", None),
        ("0.9.0", None, "0.21.0"),
        ("0.20.0", None, "0.21.0"),
        ("0.19.99", None, "0.21.0"),
    ],
)
def test_set_gym_environments(
    gym_version,
    expected_from_version_gym,
    expected_to_version_gym,
    gymnasium_version,
    expected_from_version_gymnasium,
    expected_to_version_gymnasium,
):
    # mock gym and gymnasium imports
    mock_gym = mock.MagicMock()
    mock_gym.__version__ = gym_version
    mock_gym.__name__ = "gym"
    sys.modules["gym"] = mock_gym

    mock_gymnasium = mock.MagicMock()
    mock_gymnasium.__version__ = gymnasium_version
    mock_gymnasium.__name__ = "gymnasium"
    sys.modules["gymnasium"] = mock_gymnasium

    import gym
    import gymnasium

    # look for the right function that should be called according to gym versions (and same for gymnasium)
    for impfor in implemetn_for._setters:
        if impfor.fn.__name__ == "_set_gym_environments":
            if (impfor.module_name, impfor.from_version, impfor.to_version) == (
                "gym",
                expected_from_version_gym,
                expected_to_version_gym,
            ):
                expected_fn_gym = impfor.fn
            elif (impfor.module_name, impfor.from_version, impfor.to_version) == (
                "gymnasium",
                expected_from_version_gymnasium,
                expected_to_version_gymnasium,
            ):
                expected_fn_gymnasium = impfor.fn

    with set_gym_backend(gym):
        assert _utils_internal._set_gym_environments == expected_fn_gym

    with set_gym_backend(gymnasium):
        assert _utils_internal._set_gym_environments == expected_fn_gymnasium


def test_set_gym_environments_no_version_gymnasium():
    mock_gymnasium = mock.MagicMock()
    mock_gymnasium.__version__ = "0.26.0"
    mock_gymnasium.__name__ = "gymnasium"
    sys.modules["gymnasium"] = mock_gymnasium

    import gymnasium


    with pytest.raises(ImportError) as exc_info:
        with set_gym_backend(gymnasium):
            pass
    assert (
        str(exc_info.value)
        == f"Impossible to set the gym backend for {mock_gymnasium.__name__} with version {mock_gymnasium.__version__ }"
    )


if __name__ == "__main__":
    args, unknown = argparse.ArgumentParser().parse_known_args()
    pytest.main([__file__, "--capture", "no", "--exitfirst"] + unknown)
