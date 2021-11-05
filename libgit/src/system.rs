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
use std::str;

use chrono::DateTime;
use chrono::Utc;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use sled::{Db, Tree};

use crate::error::*;
use crate::{InterfaceAdmin, Patch, Repo};

#[pyclass(name = "System", module = "libgit")]
pub struct System {
    #[allow(dead_code)]
    db: Db,
    pub remotes: Tree,
    pub lock: Tree,
    pub base: String,
}

#[derive(Deserialize, Serialize)]
struct Lock {
    is_locked: bool,
    time: Option<DateTime<Utc>>,
}

impl Lock {
    fn new(is_locked: bool) -> Self {
        if is_locked {
            let time = Some(Utc::now());
            Self { is_locked, time }
        } else {
            Self {
                is_locked,
                time: None,
            }
        }
    }
}

#[pymethods]
impl System {
    #[new]
    pub fn new(base: &str) -> FResult<Self> {
        let path = Path::new(&base).join("interface_repo_data");
        fs::create_dir_all(&path)?;
        let db = sled::open(path).unwrap();
        let remotes = db.open_tree("remotes").unwrap();
        let lock = db.open_tree("lock").unwrap();
        Ok(Self {
            base: base.to_owned(),
            db,
            remotes,
            lock,
        })
    }

    pub fn init_repo(&self, base: &str, local: String, upstream: String) -> FResult<()> {
        let lock = Lock::new(false);
        self.lock
            .insert(local.as_bytes(), bincode::serialize(&lock).unwrap())
            .unwrap();

        self.remotes
            .insert(local.as_bytes(), upstream.as_bytes())
            .unwrap();

        Repo::new(base, local, upstream)?;
        Ok(())
    }

    pub fn with_local(&self, local: &str) -> FResult<Option<Repo>> {
        if let Ok(Some(upstream)) = self.remotes.get(local) {
            let repo = Repo::new(
                &self.base,
                local.to_owned(),
                str::from_utf8(&*upstream).unwrap().to_owned(),
            )?;
            Ok(Some(repo))
        } else {
            Ok(None)
        }
    }

    pub fn with_upstream(&self, upstream: &str) -> FResult<Option<Repo>> {
        let upstream_bytes = upstream.as_bytes();
        let config = self.remotes.iter().find(|rec| {
            if let Ok((_k, v)) = rec {
                v == upstream_bytes
            } else {
                false
            }
        });

        if let Some(Ok((local, _upstream))) = config {
            let local = str::from_utf8(&*local).unwrap().to_owned();
            let repo = Repo::new(&self.base, local, upstream.to_owned())?;
            Ok(Some(repo))
        } else {
            Ok(None)
        }
    }

    pub fn fetch_upstream(&self, repo: &Repo) -> FResult<()> {
        let cb = || repo.fetch_upstream();
        run_with_repo(&self, repo, cb)
    }

    pub fn process_patch(
        &self,
        repo: &Repo,
        patch: String,
        branch_name: String,
    ) -> FResult<String> {
        let cb = move || repo.process_patch(patch, branch_name);
        run_with_repo(&self, repo, cb)
    }

    pub fn apply_patch(
        &self,
        repo: &Repo,
        patch: Patch,
        admin: &InterfaceAdmin,
        branch_name: String,
    ) -> FResult<()> {
        let cb = move || repo.apply_patch(patch, admin, branch_name);
        run_with_repo(&self, repo, cb)
    }

    pub fn push_local(&self, repo: &Repo, branch: &str) -> FResult<()> {
        let cb = || repo.push_local(branch);
        run_with_repo(&self, repo, cb)
    }

    pub fn add_remote(&self, repo: &Repo, name: &str, url: &str) -> FResult<()> {
        let cb = || repo.add_remote(name, url);
        run_with_repo(&self, repo, cb)
    }
}

fn run_with_repo<T, F: FnOnce() -> T>(sys: &System, repo: &Repo, f: F) -> T {
    let local_bytes = &repo.local.as_bytes();
    let lock = sys.lock.get(&local_bytes).unwrap().unwrap();
    let de_lock: Lock = bincode::deserialize(&lock).unwrap();
    if !de_lock.is_locked {
        let new_lock = bincode::serialize(&Lock::new(true)).unwrap();
        let new_lock = new_lock.as_slice();
        sys.lock
            .compare_and_swap(&local_bytes, Some(lock.as_ref()), Some(new_lock))
            .unwrap()
            .unwrap();
        let resp = (f)();
        sys.lock
            .compare_and_swap(&local_bytes, Some(new_lock), Some(lock.as_ref()))
            .unwrap()
            .unwrap();
        resp
    } else {
        // One possible solution is implementing backoff loop which checks if repository is
        // available. But that could mess state up with actions that are sequential.
        //
        // For example:
        // A patch arrives for a repository. Repository is unavailable so it's blocked.
        // While being blocked, second patch arrives. It is possible that second patch detects
        // that the repository is available before the first one does, causing a race
        // condition.
        unimplemented!("When repo is locked")
    }
}
