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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse as date_parse


from .conn import get_db
from .users import DBUser
from .repo import DBRepo
from .interfaces import DBInterfaces

OPEN = "open"
MERGED = "merged"
CLOSED = "closed"


@dataclass
class DBIssue:
    """Issue information as stored in database"""

    title: str
    description: str
    html_url: str
    created: str
    updated: str
    repo_scope_id: str
    repository: DBRepo
    user: DBUser
    signed_by: DBInterfaces
    id: int = None
    is_closed: bool = False
    # is_merged only makes sense for PR, therefore it's absence(=None) is
    # used to denote the Issue is an Issue and not a PR
    is_merged: bool = None
    #    -- is_native:
    #        -- false: issue is PR and not merged
    #        -- true: issue is PR and merged
    #        -- false && val(is_closed) == true: issue is PR and is closed
    is_native: bool = True

    def __set_sqlite_to_bools(self):
        """
        sqlite returns 0 for False and 1 for True and is not automatically typecast
        into bools. This method typecasts all bool values of this class.

        To be invoked by every load_* invocation
        """
        self.is_merged = None if self.is_merged is None else bool(self.is_merged)
        self.is_native = bool(self.is_native)
        self.is_closed = bool(self.is_closed)

    def state(self) -> str:
        """Get state of an issue"""
        # if is_merged is None, then issue is an Issue and not a PR
        # since is_merged doesn't make sense for an aissue
        if self.is_merged is None:
            # Issue can only assume two states: open and close
            # So return state only based on is_closed
            return CLOSED if self.is_closed else OPEN

        # If is_merged is True, then issue is PR and is merged
        if self.is_merged:
            return MERGED

        # if is_merged is False then issue is PR and state needs to be
        # determied based on is_closed
        return CLOSED if self.is_closed else OPEN

    def is_pr(self) -> bool:
        """is Issue a PR"""
        return self.is_merged is not None

    def set_closed(self, updated: str):
        """
        Mark an Issue to be closed.
        """
        self.is_closed = True
        self.updated = updated
        self.__update()

    def set_merged(self, updated: str):
        """
        Set PR as merged
        Since GitHub family of forges close a PR at the same time it's merged,
        the issue will also be marked as closed. However, the ultimiate state of the
        PR is said to be "merged"
        """
        if self.is_pr():
            self.is_merged = True
            self.set_closed(updated)
        #    commented out because self.is_closed() is already setting updated time
        #    and committing changes to database but leaving it here for clarity
        #    self.updated = updated
        #    self.__update()
        else:
            raise TypeError("Issue is not a PR, can't be merged")

    def set_open(self, updated: str):
        """Re-open an issue"""
        # TODO I couldn't find an option to revert a commit on Gitea but GitHub
        # seems to have it. What happens to state in notification if PR is reverted?
        # I'm assuming that the state would be set to not merged
        # and not closed but requires investigation.
        self.is_closed = False
        self.updated = updated
        if self.is_pr():
            self.is_merged = False
        self.__update()

    def __update(self):
        """
        Update changes in database
        Only fields that can be mutated on the forge will be updated in the DB
        """
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE gitea_forge_issues
            SET
                title = ?,
                description = ?,
                updated = ?,
                is_closed = ?,
                is_merged = ?,
                signed_by = (SELECT ID from interfaces WHERE url  = ?)
            WHERE
                id = ?
            """,
            (
                self.title,
                self.description,
                self.updated,
                self.is_closed,
                self.is_merged,
                self.signed_by.url,
                self.id,
            ),
        )
        conn.commit()

    def save(self):
        """Save Issue to database"""
        self.user.save()
        self.signed_by.save()
        self.repository.save()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO gitea_forge_issues
                (
                    title, description, html_url, created,
                    updated, is_closed, is_merged, is_native,
                    repo_scope_id, user_id, repository, signed_by
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?,
                    (SELECT ID from gitea_users WHERE user_id  = ?),
                    (SELECT ID from gitea_forge_repositories WHERE owner  = ? AND name = ?),
                    (SELECT ID from interfaces WHERE url  = ?)
                )
            """,
            (
                self.title,
                self.description,
                self.html_url,
                self.created,
                self.updated,
                self.is_closed,
                self.is_merged,
                self.is_native,
                self.repo_scope_id,
                self.user.user_id,
                self.repository.owner,
                self.repository.name,
                self.signed_by.url,
            ),
        )
        conn.commit()
        self.id = cur.execute(
            """
                SELECT id FROM gitea_forge_issues
                WHERE repo_scope_id = ? AND html_url = ?
                """,
            (self.repo_scope_id, self.html_url),
        ).fetchone()[
            0
        ]  # If sqlite result doesn't contain anything at [0]
        # pos then save wasn't successful or some other
        # error occurred
        self.__update()

    @classmethod
    def load(cls, repository: DBRepo, repo_scope_id: str) -> "DBIssue":
        """Load issue from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             issues.ID,
             issues.title,
             issues.description,
             issues.html_url,
             issues.created,
             issues.updated,
             issues.is_closed,
             issues.is_merged,
             issues.is_native,
             users.name,
             users.user_id,
             users.profile_url,
             users.ID,
             user_was_signed_by.ID,
             user_was_signed_by.url,
             user_was_signed_by.public_key,
             interfaces.url,
             interfaces.public_key,
             interfaces.ID,
             repositories.ID
        FROM
             gitea_forge_issues AS issues
        INNER JOIN gitea_forge_repositories AS repositories
            ON issues.repository = repositories.ID
        INNER JOIN gitea_users AS users
             ON issues.user_id = users.ID
        INNER JOIN interfaces AS interfaces
            ON issues.signed_by = interfaces.ID
        INNER JOIN interfaces AS user_was_signed_by
            ON users.signed_by = user_was_signed_by.ID
        WHERE
            issues.repo_scope_id = ?
        AND
            repositories.name = ?
        AND
            repositories.owner = ?;
        """,
            (repo_scope_id, repository.name, repository.owner),
        ).fetchone()
        if data is None:
            return None

        repository.id = data[17]

        issue = cls(
            id=data[0],
            title=data[1],
            description=data[2],
            html_url=data[3],
            created=data[4],
            updated=data[5],
            is_closed=data[6],
            is_merged=data[7],
            is_native=data[8],
            repo_scope_id=repo_scope_id,
            user=DBUser(
                name=data[9],
                user_id=data[10],
                profile_url=data[11],
                id=data[12],
                signed_by=DBInterfaces(
                    id=data[13],
                    url=data[14],
                    public_key=data[15],
                ),
            ),
            signed_by=DBInterfaces(
                url=data[16],
                public_key=data[17],
                id=data[18],
            ),
            repository=repository,
        )

        issue.__set_sqlite_to_bools()
        return issue

    @classmethod
    def load_with_id(cls, db_id: str) -> "DBIssue":
        """
        Load issue from database using database ID
        This ID very different from the one assigned by the forge
        """
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             issues.title,
             issues.description,
             issues.html_url,
             issues.created,
             issues.updated,
             issues.is_closed,
             issues.is_merged,
             issues.is_native,
             issues.repo_scope_id,
             users.name,
             users.user_id,
             users.profile_url,
             users.ID,
             user_was_signed_by.ID,
             user_was_signed_by.url,
             user_was_signed_by.public_key,
             interfaces.url,
             interfaces.public_key,
             interfaces.ID,
             repositories.ID,
             repositories.name,
             repositories.owner
        FROM
             gitea_forge_issues AS issues
        INNER JOIN gitea_forge_repositories AS repositories
            ON issues.repository = repositories.ID
        INNER JOIN gitea_users AS users
             ON issues.user_id = users.ID
        INNER JOIN interfaces AS interfaces
            ON issues.signed_by = interfaces.ID
        INNER JOIN interfaces AS user_was_signed_by
            ON users.signed_by = user_was_signed_by.ID
        WHERE
            issues.ID = ?
        """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None

        issue = cls(
            id=db_id,
            title=data[0],
            description=data[1],
            html_url=data[2],
            created=data[3],
            updated=data[4],
            is_closed=data[5],
            is_merged=data[6],
            is_native=data[7],
            repo_scope_id=data[8],
            user=DBUser(
                name=data[9],
                user_id=data[10],
                profile_url=data[11],
                id=data[12],
                signed_by=DBInterfaces(
                    id=data[13],
                    url=data[14],
                    public_key=data[15],
                ),
            ),
            signed_by=DBInterfaces(
                url=data[16],
                public_key=data[17],
                id=data[18],
            ),
            repository=DBRepo(
                id=data[19],
                name=data[20],
                owner=data[21],
            ),
        )
        issue.__set_sqlite_to_bools()
        return issue

    @classmethod
    def load_with_html_url(cls, html_url: str) -> "DBIssue":
        """
        Load issue from database using HTML URL
        """
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             issues.title,
             issues.description,
             issues.ID,
             issues.created,
             issues.updated,
             issues.is_closed,
             issues.is_merged,
             issues.is_native,
             issues.repo_scope_id,
             users.name,
             users.user_id,
             users.profile_url,
             users.ID,
             user_was_signed_by.ID,
             user_was_signed_by.url,
             user_was_signed_by.public_key,
             interfaces.url,
             interfaces.public_key,
             interfaces.ID,
             repositories.ID,
             repositories.name,
             repositories.owner
        FROM
             gitea_forge_issues AS issues
        INNER JOIN gitea_forge_repositories AS repositories
            ON issues.repository = repositories.ID
        INNER JOIN gitea_users AS users
             ON issues.user_id = users.ID
        INNER JOIN interfaces AS interfaces
            ON issues.signed_by = interfaces.ID
        INNER JOIN interfaces AS user_was_signed_by
            ON users.signed_by = user_was_signed_by.ID
        WHERE
            issues.html_url = ?
        """,
            (html_url,),
        ).fetchone()
        if data is None:
            return None

        issue = cls(
            html_url=html_url,
            title=data[0],
            description=data[1],
            id=data[2],
            created=data[3],
            updated=data[4],
            is_closed=data[5],
            is_merged=data[6],
            is_native=data[7],
            repo_scope_id=data[8],
            user=DBUser(
                name=data[9],
                user_id=data[10],
                profile_url=data[11],
                id=data[12],
                signed_by=DBInterfaces(
                    id=data[13],
                    url=data[14],
                    public_key=data[15],
                ),
            ),
            signed_by=DBInterfaces(
                url=data[16],
                public_key=data[17],
                id=data[18],
            ),
            repository=DBRepo(
                id=data[19],
                name=data[20],
                owner=data[21],
            ),
        )
        issue.__set_sqlite_to_bools()
        return issue
