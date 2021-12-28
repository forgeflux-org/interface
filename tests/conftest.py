# Interface ---  API-space federation for software forges
# Copyright © 2021 Aravinth Manivannan <realaravinth@batsense.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import tempfile

import pytest
import requests_mock
from dynaconf import settings

from interface.app import create_app
from interface.db import get_db, init_db


from tests.test_utils import register_ns
from tests.forges.gitea.test_utils import register_gitea
from tests.meta_utils import mock_key, mock_version


@pytest.fixture
def app():
    """App instance with test configuration"""
    db_fd, db_path = tempfile.mkstemp()
    # db_path = os.path.join(db_path, "northstar.db")

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": db_path,
        }
    )

    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test runner for the app's CLI commands"""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def set_test_settings():
    settings.configure(FORCE_ENV_FOR_DYNACONF="testing")


@pytest.fixture(autouse=True)
def register_mocks(requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)
    mock_key(requests_mock)
    mock_version(requests_mock)
