# Interface ---  API-space federation for software forges
# Copyright © 2022 Aravinth Manivannan <realaravinth@batsense.net>
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
from datetime import datetime

from dateutil.parser import parse as date_parse

from interface.app import create_app
from interface.meta import VERSIONS
from interface.runner import runner

from tests.test_utils import register_ns
from tests.forges.gitea.test_utils import register_gitea


def test_supported_version(app, client, requests_mock):
    """Test version meta route"""

    worker = runner.init_app(app)
    assert worker.thread.is_alive() is True
    assert worker.get_switch().is_set() is False
    worker.kill()
    assert worker.thread.is_alive() is False
    assert worker.get_switch().is_set() is True

    last_run = worker.get_last_run()
    now = datetime.now()
    worker._update_time(now)
    assert date_parse(worker.get_last_run()) == now
