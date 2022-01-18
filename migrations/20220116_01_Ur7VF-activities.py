"""
activities
"""

from yoyo import step

__depends__ = {"20220102_01_q4rHE-events"}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS activities (
            ID INTEGER PRIMARY KEY NOT NULL,
            user_id INTEGER REFERENCES gitea_users(ID) ON DELETE CASCADE NOT NULL,
            activity INTEGER NOT NULL, -- type CREATE, DELETE, etc.
            comment_id INTEGER REFERENCES gitea_issue_comments(ID) ON DELETE CASCADE,
            issue_id INTEGER REFERENCES gitea_forge_issues(ID) ON DELETE CASCADE,
            created INTEGER NOT NULL,
            CONSTRAINT CK_ATleastOneObj CHECK (
                comment_id IS NOT NULL OR
                issue_id IS NOT NULL
            )
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS shared_inboxes (
            ID INTEGER PRIMARY KEY NOT NULL,
            url TEXT NOT NULL UNIQUE
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS foreign_actors (
            ID INTEGER PRIMARY KEY NOT NULL,
            actor TEXT NOT NULL UNIQUE, -- URL
            inbox_url TEXT NOT NULL UNIQUE,
            outbox_url TEXT NOT NULL UNIQUE,
            shared_inbox_id INTEGER REFERENCES shared_inboxes(ID) ON DELETE CASCADE,
            public_key TEXT NOT NULL
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS user_followers (
            user_id INTEGER REFERENCES gitea_users(ID) ON DELETE CASCADE,
            actor_id INTEGER REFERENCES foreign_actors(ID) ON DELETE CASCADE,
            UNIQUE(user_id, actor_id)
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS repository_followers (
            repo_id INTEGER REFERENCES gitea_forge_repositories(ID) ON DELETE CASCADE,
            actor_id INTEGER REFERENCES foreign_actors(ID) ON DELETE CASCADE,
            UNIQUE(repo_id, actor_id)
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS issue_followers (
            issue_id INTEGER REFERENCES gitea_forge_issues(ID) ON DELETE CASCADE,
            actor_id INTEGER REFERENCES foreign_actors(ID) ON DELETE CASCADE,
            UNIQUE(issue_id, actor_id)
        );
    """
    ),
]
