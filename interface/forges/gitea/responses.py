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
from dataclasses import dataclass

import requests

# from flask import current_app
from interface.settings import settings

#
# from interface.forges.notifications import (
#    CreatePrEvent,
#    CreatePrMessage,
#    NotificationResolver,
#    RunNotification,
#    Notification,
#    PrEvent,
#    IssueEvent,
# )
# from interface.forges.gitea.utils import get_issue_index
# from interface.utils import clean_url, trim_url
from interface.db import DBRepo, DBIssue, DBUser, DBInterfaces, DBComment
from interface.utils import clean_url, trim_url, date_from_string, since_epoch

from .utils import get_issue_index, get_owner_repo_from_url, get_issue_api_url
from .admin import get_db_interface


@dataclass
class GiteaInternalTracker:
    enable_time_tracker: bool
    allow_only_contributors_to_track_time: bool
    enable_issue_dependencies: bool


@dataclass
class GiteaRepoPermissions:
    admin: bool
    push: bool
    pull: bool


@dataclass
class GiteaOwner:
    id: int
    login: str
    full_name: str
    email: str
    avatar_url: str
    language: str
    is_admin: bool
    last_login: str
    created: str
    restricted: bool
    active: bool
    prohibit_login: bool
    location: str
    website: str
    description: str
    visibility: str
    followers_count: int
    following_count: int
    starred_repos_count: int
    username: str

    def to_db_user(self) -> DBUser:
        """requires app context"""
        return DBUser(
            name=self.full_name,
            user_id=self.username,
            profile_url=f"{trim_url(clean_url(settings.GITEA.host))}/{self.username}",
            description=self.description,
            avatar_url=self.avatar_url,
        )


@dataclass
class GiteaRepo:
    id: int
    owner: GiteaOwner
    name: str
    full_name: str
    description: str
    empty: bool
    private: bool
    fork: bool
    template: bool
    parent: str
    mirror: bool
    size: int
    html_url: str
    ssh_url: str
    clone_url: str
    original_url: str
    website: str
    stars_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    open_pr_counter: int
    release_counter: int
    default_branch: str
    archived: bool
    created_at: str
    updated_at: str
    permissions: GiteaRepoPermissions
    has_issues: bool
    internal_tracker: GiteaInternalTracker
    has_wiki: bool
    has_pull_requests: bool
    has_projects: bool
    ignore_whitespace_conflicts: bool
    allow_merge_commits: bool
    allow_rebase: bool
    allow_rebase_explicit: bool
    allow_squash_merge: bool
    default_merge_style: str
    avatar_url: str
    internal: bool
    mirror_interval: str

    def to_db_repo(self) -> DBRepo:
        owner = self.owner.to_db_user()
        owner.save()
        return DBRepo(
            name=self.name,
            owner=owner,
            description=self.description,
            html_url=self.html_url,
        )


class GiteaNotificationSubject:
    title: str
    url: str
    latest_comment_url: str
    type: str
    state: str


@dataclass
class GiteaMinimalRepo:
    id: int
    name: str
    owner: str
    full_name: str


@dataclass
class GiteaIssue:
    id: int
    url: str
    html_url: str
    number: int
    user: GiteaOwner
    original_author: str
    original_author_id: int
    title: str
    body: str
    ref: str
    # TODO verify
    labels: [str]
    # TODO verify
    state: str
    is_locked: bool
    comments: int
    created_at: str
    updated_at: str
    closed_at: str
    due_date: str
    pull_request: str
    repository: GiteaMinimalRepo
    milestone: [str] = None
    # TODO verify
    assignee: str = None
    # TODO verify
    assignees: [str] = None

    def __post_init__(self):
        if not isinstance(self.user, GiteaOwner):
            self.user = GiteaOwner(**self.user)
        if not isinstance(self.repository, GiteaMinimalRepo):
            self.repository = GiteaMinimalRepo(**self.repository)

    @classmethod
    def get_issue(cls, owner: str, repo: str, issue_id) -> "GiteaIssue":
        url = get_issue_api_url(owner=owner, repo=repo, issue_id=issue_id)
        response = requests.get(url)
        if response.status_code == 200:
            return cls(**response.json())

        raise Exception(
            f"UNKNOWN ERROR while getting issue. Status code {response.status_code}, issue_url {url}"
        )

    def repo_scope_id(self) -> int:
        return get_issue_index(self.html_url)

    def get_updated_epoch(self) -> int:
        print(self.updated_at)
        print(f"foo {since_epoch(date_from_string(self.updated_at))}")
        return since_epoch(date_from_string(self.updated_at))

    def get_created_epoch(self) -> int:
        print(self.created_at)
        print(f"foo {since_epoch(date_from_string(self.created_at))}")
        return since_epoch(date_from_string(self.created_at))


#    def self_get_comments(self):
#        if self.comments > 0
#
#


@dataclass
class GiteaComment:
    id: int
    html_url: str
    pull_request_url: str
    issue_url: str
    user: GiteaOwner
    original_author: str
    original_author_id: int
    body: str
    created_at: str
    updated_at: str

    def __post_init__(self):
        if not isinstance(self.user, GiteaOwner):
            self.user = GiteaOwner(**self.user)

    @classmethod
    def from_issue(cls, issue: GiteaIssue) -> "[GiteaComment]":
        if issue.comments == 0:
            return None
        return cls.from_issue_url(issue.html_url)

    @classmethod
    def from_issue_url(cls, issue_html_url: str) -> "[GiteaComment]":
        comments = []
        (owner, repo) = get_owner_repo_from_url(issue_html_url)
        issue_index = get_issue_index(issue_html_url)
        # TODO use Gitea's(Forge subclass) url bulder
        url = f"{trim_url(clean_url(settings.GITEA.host))}/api/v1/repos/{owner}/{repo}/issues/{issue_index}/comments"
        resp = requests.get(url)

        if resp.status_code == 200:
            data = resp.json()
            ## TODO this doesn't take pagination into account
            for comment in data:
                comments.append(cls(**comment))
            if len(comments) == 0:
                return None
            return comments

        raise Exception(
            f"Error while fetching comments for issue: {issue_html_url} status_code {resp.status_code}"
        )

    def belongs_to_pull_request(self) -> bool:
        return len(self.pull_request_url) == 0

    def belongs_to_issue(self) -> bool:
        return len(self.issue_url) == 0

    def to_db_comment(self) -> DBComment:
        return DBComment(
            body=self.body,
            html_url=self.html_url,
            user=self.user.to_db_user(),
            created=since_epoch(date_from_string(self.created_at)),
            updated=since_epoch(date_from_string(self.updated_at)),
            comment_id=self.id,
            is_native=None,
            belongs_to_issue=DBIssue.load_with_html_url(
                self.issue_url if len(self.pull_request_url) == 0 else self.issue_url
            ),
        )
