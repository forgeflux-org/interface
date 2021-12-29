"""
forge data
"""

from yoyo import step

__depends__ = {"20211223_01_pFC7s-interface-forks"}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS gitea_users(
            name VARCHAR(250) NOT NULL,
            user_id VARCHAR(250) UNIQUE NOT NULL,
            profile_url TEXT UNIQUE NOT NULL,
            ID INTEGER PRIMARY KEY NOT NULL,
            signed_by INTEGER REFERENCES interfaces(ID) ON DELETE CASCADE DEFAULT NULL
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS gitea_forge_repositories(
            owner VARCHAR(250) NOT NULL,
            name VARCHAR(250) NOT NULL,
            ID INTEGER PRIMARY KEY NOT NULL
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS gitea_forge_issues(
            ID INTEGER PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            html_url TEXT NOT NULL UNIQUE,
            created VARCHAR(50) NOT NULL,
            updated VARCHAR(50) NOT NULL,
            is_closed BOOLEAN NOT NULL DEFAULT FALSE,
            is_merged BOOLEAN DEFAULT NULL,
            -- is_native:
                -- false: issue is PR and not merged
                -- true: issue is PR and merged
                -- false && val(is_closed) == true: issue is PR and is closed
            is_native BOOLEAN NOT NULL DEFAULT TRUE,
            repo_scope_id INTEGER NOT NULL,
            user_id INTEGER REFERENCES gitea_users(ID) ON DELETE CASCADE DEFAULT NULL,
            repository INTEGER REFERENCES gitea_forge_repositories(ID) ON DELETE CASCADE DEFAULT NULL,
            signed_by INTEGER REFERENCES interfaces(ID) ON DELETE CASCADE DEFAULT NULL
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS gitea_issue_comments(
            ID INTEGER PRIMARY KEY NOT NULL,
            body TEXT,
            html_url TEXT NOT NULL UNIQUE,
            created VARCHAR(50) NOT NULL,
            updated VARCHAR(50) NOT NULL,
            issue_scope_id INTEGER NOT NULL,
            parent_of REFERENCES issue_comments(ID),
            is_native BOOLEAN NOT NULL DEFAULT TRUE,
            signed_by INTEGER REFERENCES interfaces(ID) ON DELETE CASCADE DEFAULT NULL
        );
    """
    ),
]
