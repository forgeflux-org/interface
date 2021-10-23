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
use error::*;

#[pyclass(name = "Repo")]
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

#[derive(Debug, Clone)]
#[pyclass(name = "Patch")]
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

#[derive(Debug, Clone)]
#[pyclass(name = "InterfaceAdmin")]
pub struct InterfaceAdmin {
    #[pyo3(get, set)]
    pub email: String,
    #[pyo3(get, set)]
    pub name: String,
}

pub const UPSTREAM_REMOTE: &str = "upstream";
pub const LOCAL_REMOTE: &str = "local";
pub const IGNORE_FILE: &str = ".fignore";

#[pymethods]
impl Repo {
    /// Add remote to repository
    pub fn add_remote(&self, name: &str, url: &str) -> FResult<()> {
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
    pub fn new(base: &str, local: String, upstream: String) -> FResult<Self> {
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

    pub fn fetch_upstream(&self) -> FResult<()> {
        let mut remote = connect_upstream(&self)?;
        let default_branch = remote.default_branch()?;
        remote.fetch(&[default_branch.as_str().unwrap()], None, None)?;
        remote.disconnect()?;
        Ok(())
    }

    pub fn push_local(&self, branch: &str) -> FResult<()> {
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

    pub fn apply_patch(
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
        Ok(())
    }

    pub fn process_patch(&self, patch: String, branch_name: String) -> FResult<String> {
        let buf: Vec<u8> = patch.into();
        let diff = git2::Diff::from_buffer(&buf)?;
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
        Ok(processed_patch.as_str().unwrap().to_owned())
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
    format!("refs/heads/{}", branch)
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
