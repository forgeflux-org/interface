#!venv/bin/python
"""
Run ForgeFed Interface flask application
"""
# Bridges software forges to create a distributed software development environment
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import time
from threading import Thread

from interface.app import create_app
from interface.runner import runner
from interface.git import get_forge


class Init:
    def __init__(self, app):
        self.app = app
        Thread(target=self.__run).start()

    def __run(self):
        with self.app.app_context():
            time.sleep(3)
            get_forge()

if __name__ == "__main__":
    app = create_app()

    Init(app=app)
    # worker = runner.init_app(app)
    app.run(threaded=True, host="0.0.0.0", port=8000)
    # worker.kill()
