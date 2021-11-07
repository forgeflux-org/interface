/* git interface for forgefedv2 interface
 * Bridges software forges to create a distributed software development environment
 * Copyright © 2021 Aravinth Manivannan <realaravinth@batsense.net>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

use std::fs;
use std::path::Path;
use std::path::PathBuf;

use git2::build::CheckoutBuilder;
use git2::ApplyLocation;
use git2::Cred;
use git2::DiffFile;
use git2::IndexAddOption;
use git2::ObjectType;
use git2::PushOptions;
use git2::Remote;
use git2::RemoteCallbacks;
use git2::Repository;
use git2::Signature;
use pyo3::prelude::*;
use url::Url;

pub mod error;
pub mod system;
use error::*;
pub use system::System;

#[pyclass(name = "Patch", module = "libgit")]
#[derive(Debug, Clone)]
pub struct Patch {
    #[pyo3(get, set)]
    pub message: String,
    #[pyo3(get, set)]
    pub author_email: String,
    #[pyo3(get, set)]
    pub author_name: String,
    #[pyo3(get, set)]
    pub patch: String,
}

#[pyclass(name = "InterfaceAdmin", module = "libgit")]
#[derive(Debug, Clone)]
pub struct InterfaceAdmin {
    #[pyo3(get, set)]
    pub email: String,
    #[pyo3(get, set)]
    pub name: String,
}

#[pymethods]
impl InterfaceAdmin {
    #[new]
    pub fn new(email: String, name: String) -> FResult<Self> {
        if !validator::validate_email(&email) {
            return Err(FError::NotAnEmail(email));
        };
        Ok(Self { email, name })
    }
}

#[pymethods]
impl Patch {
    #[new]
    pub fn new(
        message: String,
        author_name: String,
        author_email: String,
        patch: String,
    ) -> FResult<Self> {
        if !validator::validate_email(&author_email) {
            return Err(FError::NotAnEmail(author_email));
        };

        Ok(Self {
            message,
            author_email,
            author_name,
            patch,
        })
    }
}

pub const UPSTREAM_REMOTE: &str = "forgefed_remote_upstream";
pub const LOCAL_REMOTE: &str = "forgefed_remote_local";
pub const IGNORE_FILE: &str = ".fignore";
pub const CONFIG_FILE: &str = "forgefed.toml";

#[pyclass(name = "Repo", module = "libgit")]
pub struct Repo {
    #[allow(dead_code)]
    upstream: Url,
    #[allow(dead_code)]
    #[pyo3(get)]
    local: String,
    repo: Repository,
    #[pyo3(get)]
    path: PathBuf,
}

#[pymethods]
impl Repo {
    /// Add remote to repository
    pub(crate) fn add_remote(&self, name: &str, url: &str) -> FResult<()> {
        match self.repo.find_remote(name) {
            Err(_) => {
                let mut remote = self.repo.remote(name, &url)?;
                remote.disconnect()?;
            }
            Ok(remote) => {
                if remote.url() != Some(url) {
                    return Err(FError::RemoteNameExists);
                }
            }
        }
        Ok(())
    }

    pub fn get_upstream(&self) -> String {
        self.upstream.to_string()
    }

    #[new]
    /// Create new instance of repository
    /// ```rust,no_run
    /// let repo = Repo::new("/srv/ff/",git@git.batsense.net:realaravinth/tmp.git", "https://github.com/forgefedv2/interface").unwrap();
    /// ```
    pub(crate) fn new(base: &str, local: String, upstream: String) -> FResult<Self> {
        fn set_path(base: &str, upstream: &Url) -> FResult<PathBuf> {
            let domain = match upstream.domain() {
                Some(d) => d,
                None => return Err(FError::NoDirInvalidUpstreamUrl(upstream.to_string())),
            };

            let path = Path::new(base).join(domain);
            let path = path.join(&upstream.path()[1..]);
            if !path.exists() {
                fs::create_dir_all(&path)?;
            }
            Ok(path)
        }

        let upstream = Url::parse(&upstream)?;
        let path = set_path(base, &upstream)?;

        let repo = Repository::open(&path);

        let repo = if repo.is_err() {
            Repository::clone(&upstream.as_str(), &path).unwrap()
        } else {
            repo?
        };

        let obj = Self {
            upstream,
            local,
            repo,
            path,
        };

        obj.add_remote(UPSTREAM_REMOTE, &obj.upstream.as_str())?;
        obj.add_remote(LOCAL_REMOTE, &obj.local)?;
        Ok(obj)
    }

    /// `git fetch upstream <default-branch>`
    pub(crate) fn fetch_upstream(&self) -> FResult<()> {
        let mut remote = connect_upstream(&self)?;
        let default_branch = remote.default_branch()?;
        remote.fetch(&[default_branch.as_str().unwrap()], None, None)?;
        remote.disconnect()?;
        Ok(())
    }

    /// get default branch of a repository from the upstream remote
    pub fn default_branch(&self) -> FResult<String> {
        let mut remote = connect_upstream(&self)?;
        let default_branch = remote.default_branch()?;
        remote.disconnect()?;
        Ok(default_branch.as_str().unwrap().to_string())
    }

    /// push changes to local repository
    pub(crate) fn push_local(&self, branch: &str) -> FResult<()> {
        let mut upstream = connect_upstream(&self)?;
        let mut local = connect_local(&self)?;

        let mut callbacks = RemoteCallbacks::new();
        callbacks.credentials(|_, username_from_url, _| {
            Cred::ssh_key_from_agent(username_from_url.unwrap())
        });
        let mut push_options = PushOptions::new();
        push_options.remote_callbacks(callbacks);

        local
            .push(&[&get_ref(branch)], Some(&mut push_options))
            .unwrap();
        upstream.disconnect()?;
        local.disconnect()?;
        Ok(())
    }

    /// Apply a patch
    pub(crate) fn apply_patch(
        &self,
        patch: Patch,
        admin: &InterfaceAdmin,
        branch_name: String,
    ) -> FResult<()> {
        if !validator::validate_email(&patch.author_email) {
            return Err(FError::NotAnEmail(patch.author_email.into()));
        };
        if !validator::validate_email(&admin.email) {
            return Err(FError::NotAnEmail(admin.email.clone()));
        };
        let buf: Vec<u8> = patch.patch.into();
        let diff = git2::Diff::from_buffer(&buf)?;
        let head = self.repo.head()?;
        let head_commit = head.peel_to_commit()?;
        let tmp_branch = self.repo.branch(&branch_name, &head_commit, false)?;
        self.repo.set_head(tmp_branch.get().name().unwrap())?;

        self.repo.apply(&diff, ApplyLocation::Both, None)?;
        let mut index = self.repo.index()?;
        let id_mailmap = index.write_tree()?;
        let tree_mailmap = self.repo.find_tree(id_mailmap)?;

        let author = Signature::now(&patch.author_name, &patch.author_email)?;
        let committer = Signature::now(&admin.name, &admin.email)?;
        let tmp_ref = tmp_branch.into_reference();
        //  let commit_tree = tmp_ref.peel_to_tree()?;
        let commit = tmp_ref.peel_to_commit()?;
        self.repo.commit(
            Some("HEAD"),
            &author,
            &committer,
            &patch.message,
            &tree_mailmap,
            &[&commit],
        )?;

        let mut checkout_options = CheckoutBuilder::new();
        checkout_options.force();
        let head_obj = head.peel(ObjectType::Tree)?;
        self.repo
            .checkout_tree(&head_obj, Some(&mut checkout_options))?;
        self.repo.set_head(head.name().unwrap())?;
        Ok(())
    }

    /// process patch for federated transport
    pub(crate) fn process_patch(&self, patch: String, branch_name: String) -> FResult<String> {
        let buf: Vec<u8> = patch.into();
        let diff = git2::Diff::from_buffer(&buf).unwrap();
        let head = self.repo.head()?;
        let head_commit = head.peel_to_commit()?;
        let mut tmp_branch = self.repo.branch(&branch_name, &head_commit, false)?;

        self.repo.set_head(tmp_branch.get().name().unwrap())?;

        self.repo.apply(&diff, git2::ApplyLocation::WorkDir, None)?;

        self.repo.add_ignore_rule(IGNORE_FILE)?;
        let path = self.path.clone();
        let ignore = path.join(IGNORE_FILE);
        if ignore.exists() {
            let ignore_rules = fs::read_to_string(&ignore)?;
            for rule in ignore_rules.lines() {
                self.repo.add_ignore_rule(&rule)?;
            }
        }

        let mut index = self.repo.index()?;

        index.add_all(["*"].iter(), IndexAddOption::DEFAULT, None)?;

        index.write()?;
        let mut processed_diff =
            self.repo
                .diff_tree_to_index(Some(&head_commit.tree().unwrap()), Some(&index), None)?;

        let processed_patch = processed_diff.format_email(1, 1, &head_commit, None)?;
        index.remove_all(["*"].iter(), None)?;

        self.repo.clear_ignore_rules()?;
        let mut checkout_options = CheckoutBuilder::new();
        checkout_options.force();
        let head_obj = head.peel(ObjectType::Tree)?;
        self.repo
            .checkout_tree(&head_obj, Some(&mut checkout_options))?;
        self.repo.set_head(head.name().unwrap())?;
        tmp_branch.delete()?;

        for d in diff.deltas().into_iter() {
            let old_file = d.old_file();
            let new_file = d.new_file();
            rm_file(&self, &old_file)?;
            rm_file(&self, &new_file)?;
        }
        self.repo.reset(
            &head_commit.into_object(),
            git2::ResetType::Hard,
            Some(&mut checkout_options),
        )?;
        let patch = processed_patch.as_str().unwrap().to_owned();
        println!("{}", patch);
        Ok(patch)
    }
}

fn rm_file(repo: &Repo, file: &DiffFile) -> FResult<()> {
    if let Some(path) = file.path() {
        let path = repo.path.clone().join(path);
        if path.exists() {
            if path.is_file() {
                fs::remove_file(&path)?;
            } else {
                fs::remove_dir_all(&path)?;
            }
        };
    };
    Ok(())
}

fn get_ref(branch: &str) -> String {
    if branch.contains("refs/heads/") {
        branch.to_owned()
    } else {
        format!("refs/heads/{}", branch)
    }
}

fn connect_upstream(repo: &Repo) -> FResult<Remote> {
    let mut remote = repo.repo.find_remote(UPSTREAM_REMOTE)?;
    remote.connect(git2::Direction::Fetch)?;
    Ok(remote)
}

fn connect_local(repo: &Repo) -> FResult<Remote> {
    let mut local = repo.repo.find_remote(LOCAL_REMOTE)?;
    let mut callbacks = RemoteCallbacks::new();
    callbacks.credentials(|_, username_from_url, _| {
        Cred::ssh_key_from_agent(username_from_url.unwrap())
    });
    local.connect_auth(git2::Direction::Push, Some(callbacks), None)?;
    Ok(local)
}

#[pymodule]
#[pyo3(name = "libgit")]
fn my_extension(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Repo>()?;
    m.add_class::<System>()?;
    m.add_class::<InterfaceAdmin>()?;
    m.add_class::<Patch>()?;
    m.add("RemoteNameExists", py.get_type::<RemoteNameExists>())?;
    m.add("IOError", py.get_type::<error::PyIOError>())?;
    m.add("GitError", py.get_type::<error::GitError>())?;
    m.add("NotUrl", py.get_type::<error::NotUrl>())?;
    m.add("NotAnEmail", py.get_type::<error::NotAnEmail>())?;
    m.add(
        "InvalidUpstreamUrl",
        py.get_type::<error::InvalidUpstreamUrl>(),
    )?;
    Ok(())
}

pub(crate) mod tests {
    use super::*;

    use std::env;
    use std::fs;
    use std::io::Write;

    pub const AUTHOR: &str = "Tester";
    pub const AUTHOR_EMAIL: &str = "tester@foo.com";

    pub fn make_changes(repo: &Repo, branch_name: &str) -> String {
        fn change_and_commit(repo: &Repo, file: &str, change: &str) {
            let path = repo.path.join(file);
            let mut options = fs::OpenOptions::new();
            options.write(true).append(true).create_new(!path.exists());
            let mut fd = options
                .open(&path)
                .expect(&format!("{:?}", path.as_os_str()));

            fd.write_all(change.as_bytes()).unwrap();
            fd.flush().unwrap();
            let author = Signature::now(AUTHOR, AUTHOR_EMAIL).unwrap();

            let mut index = repo.repo.index().unwrap();
            index
                .add_all(["*"].iter(), IndexAddOption::DEFAULT, None)
                .unwrap();
            index.write().unwrap();
            let id_mailmap = index.write_tree().unwrap();
            let tree_mailmap = repo.repo.find_tree(id_mailmap).unwrap();

            let cur_head = repo.repo.head().unwrap();
            //  let commit_tree = tmp_ref.peel_to_tree()?;
            let commit = cur_head.peel_to_commit().unwrap();

            repo.repo
                .commit(
                    Some("HEAD"),
                    &author,
                    &author,
                    &file,
                    &tree_mailmap,
                    &[&commit],
                )
                .unwrap();
        }
        // src/lib.rs
        let files = [
            ("src/lib.rs", "change lib.rs"),
            ("README.md", "change readme"),
        ];

        let head = repo.repo.head().unwrap();

        let tmp_branch = repo
            .repo
            .branch(
                &branch_name,
                &repo.repo.head().unwrap().peel_to_commit().unwrap(),
                false,
            )
            .unwrap();

        repo.repo
            .set_head(tmp_branch.get().name().unwrap())
            .unwrap();

        for (file, change) in files {
            change_and_commit(repo, &file, change);
        }

        let new_files = ["foo", "bar"];
        let mut ignore = String::new();
        for i in new_files {
            ignore.push_str(i);
            ignore.push('\n');
            change_and_commit(repo, &i, i);
        }

        change_and_commit(&repo, IGNORE_FILE, &ignore);

        let mut diff = repo
            .repo
            .diff_tree_to_tree(
                Some(&head.peel_to_tree().unwrap()),
                Some(&repo.repo.head().unwrap().peel_to_tree().unwrap()),
                None,
            )
            .unwrap();
        let patch = diff
            .format_email(
                1,
                1,
                &repo.repo.head().unwrap().peel_to_commit().unwrap(),
                None,
            )
            .unwrap();

        let mut checkout_options = CheckoutBuilder::new();
        checkout_options.force();
        let head_obj = head.peel(ObjectType::Tree).unwrap();

        let mut tmp_branch = repo.repo.head().unwrap();

        repo.repo
            .checkout_tree(&head_obj, Some(&mut checkout_options))
            .unwrap();
        repo.repo.set_head(head.name().unwrap()).unwrap();
        tmp_branch.delete().unwrap();

        patch.as_str().unwrap().to_owned()
    }

    #[test]
    fn repo_works() {
        const NAME: &str = "REPO_WORKS";
        const UPSTREAM: &str = "https://github.com/realaravinth/actix-auth-middleware";
        let tmp = env::temp_dir();
        let base_dir = tmp.join(NAME);
        let local = base_dir.join("local");
        let _ = fs::remove_dir_all(&base_dir);
        fs::create_dir_all(&local).unwrap();
        let local_bare_repo = Repository::init_bare(&local).unwrap();
        let local_repo = Repo::new(
            base_dir.as_os_str().to_str().unwrap(),
            local.as_os_str().to_str().unwrap().to_owned(),
            UPSTREAM.into(),
        )
        .unwrap();

        local_repo.fetch_upstream().unwrap();

        let default_branch = local_repo.default_branch().unwrap();
        local_repo.push_local(&default_branch).unwrap();

        assert_eq!(
            local_repo.repo.head().unwrap().peel_to_tree().unwrap().id(),
            local_bare_repo
                .head()
                .unwrap()
                .peel_to_tree()
                .unwrap()
                .as_object()
                .id(),
        );

        let patch = make_changes(&local_repo, NAME);
        println!("{}", patch);
        let processed_patch = local_repo.process_patch(patch, NAME.into()).unwrap();
        println!("{}", processed_patch);
        assert!(!processed_patch.contains(IGNORE_FILE));
        assert!(!processed_patch.contains("foo"));
        assert!(!processed_patch.contains("bar"));
        assert!(processed_patch.contains("lib.rs"));
        assert!(processed_patch.contains("README.md"));

        let patch = Patch::new(
            NAME.into(),
            AUTHOR.into(),
            AUTHOR_EMAIL.into(),
            processed_patch,
        )
        .unwrap();

        let admin = InterfaceAdmin::new(AUTHOR_EMAIL.into(), AUTHOR.into()).unwrap();

        local_repo.apply_patch(patch, &admin, NAME.into()).unwrap();
        //  let head = local_repo.repo.head().unwrap();
        let tmp_branch = local_repo.repo.find_reference(&get_ref(NAME)).unwrap();

        let mut checkout_options = CheckoutBuilder::new();
        checkout_options.force();
        let branch_head_obj = tmp_branch.peel(ObjectType::Tree).unwrap();

        local_repo
            .repo
            .checkout_tree(&branch_head_obj, Some(&mut checkout_options))
            .unwrap();
        local_repo.repo.set_head(&get_ref(NAME)).unwrap();

        assert!(fs::read_to_string(local_repo.path.join("src/lib.rs"))
            .unwrap()
            .contains("change lib.rs"));

        assert!(fs::read_to_string(local_repo.path.join("README.md"))
            .unwrap()
            .contains("change readme"));

        local_repo.push_local(NAME).unwrap();
        let tmp_branch_remote = local_bare_repo.find_reference(&get_ref(NAME)).unwrap();

        assert_eq!(
            local_repo.repo.head().unwrap().peel_to_tree().unwrap().id(),
            tmp_branch_remote.peel_to_tree().unwrap().as_object().id(),
        );
    }

    #[test]
    fn get_ref_works() {
        let branches = [
            ("master", "refs/heads/master"),
            ("refs/heads/master", "refs/heads/master"),
        ];
        for (name, ref_) in branches.iter() {
            assert_eq!(get_ref(name), *ref_);
        }
    }
}
