#  conftest.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import pytest


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture(scope="module")
def vcr_config():
    return {
        "allow_playback_repeats": True,
    }
