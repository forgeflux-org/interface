# Bridges software forges to create a distributed software development environment
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import sched
import threading
import time
import datetime


from interface import local_settings
from interface.forge import get_forge, Notification, PULL, ISSSUE
from interface.db import get_db
from interface.forges.gitea import date_parse



RUNNING = False
APP = ""

def init(app):
   # global APP
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        last_run = date_parse("2021-10-10T17:06:02+05:30")
        cur.execute(
            "INSERT OR IGNORE INTO interface_jobs_run (this_interface_url, last_run) VALUES (?, ?);",
            (local_settings.INTERFACE_URL, str(last_run)),
            )
        conn.commit()

def update_time(time: datetime.datetime, app):
   # global APP
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
                "UPDATE interface_jobs_run set last_run = ? WHERE this_interface_url = ?;",
                (str(time), local_settings.INTERFACE_URL),
            )
        conn.commit()


def get_last_run(app):
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        res = cur.execute(
                "SELECT last_run FROM interface_jobs_run WHERE this_interface_url = ?;",
                (local_settings.INTERFACE_URL,),
            ).fetchone()
        return res[0]

#def proces_pull_request():



def run(app):
    #global APP
    #APP = app
    with app.app_context():
        logging.getLogger('jobs').setLevel(logging.WARNING)
        logger = logging.getLogger('jobs')
        scheduler = sched.scheduler(time.time, time.sleep)

        init(app)

        def background_job(app):
            with app.app_context():
                global RUNNING
                print(RUNNING)
                if RUNNING:
                    scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job)
                    return
                else:
                    RUNNING = True

                last_run = get_last_run(app)
                print(last_run)

                forge = get_forge()
                notifications = forge.get_notifications(since=last_run).get_payload()
                print(notifications)
                #for n in notifications:
                #    import json
                #    print(json.dumps(n))

#               #     if all([n["type"] == PULL, n["owner"] == local_settings.ADMIN_USER]):

#               #     if n["type"] == 
                logger.warning('hello from background_job %s', time.time())
                scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job, argument=(app,))
                RUNNING = False

        scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job, argument=(app,))
        threading.Thread(target=scheduler.run).start()
