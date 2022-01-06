/* git interface for forgefedv2 interface
 * Bridges software forges to create a distributed software development environment
 * Copyright © 2022 Aravinth Manivannan <realaravinth@batsense.net>
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

#[pyclass(name = "System", module = "libgit")]
#[derive(Debug, Clone)]
pub struct System {
    #[allow(dead_code)]
    db: Db,
    pub remotes: Tree,
    pub lock: Tree,
    pub base: String,
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

    pub fn init_repo(&self, local: String, upstream: String) -> FResult<Repo> {
        let lock = Lock::new(false);
        self.lock
            .insert(local.as_bytes(), bincode::serialize(&lock).unwrap())
            .unwrap();

        self.remotes
            .insert(local.as_bytes(), upstream.as_bytes())
            .unwrap();

        Ok(Repo::new(&self.base, local, upstream)?)
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tests::*;
    use crate::*;

    use std::env;

    #[test]
    fn system_works() {
        const NAME: &str = "SYSTEM_WORKS";
        const UPSTREAM: &str = "https://github.com/realaravinth/actix-auth-middleware";
        let tmp = env::temp_dir();
        let base_dir = tmp.join(NAME);
        let local = base_dir.join("local");
        let _ = fs::remove_dir_all(&base_dir);
        fs::create_dir_all(&local).unwrap();

        let local_bare_repo = Repository::init_bare(&local).unwrap();
        let sys = System::new(base_dir.as_os_str().to_str().unwrap()).unwrap();
        let local_repo = sys
            .init_repo(
                local.as_os_str().to_str().unwrap().to_owned(),
                UPSTREAM.into(),
            )
            .unwrap();

        {
            let check_equal = |repo: &Repo| {
                assert_eq!(repo.path, local_repo.path);
                assert_eq!(repo.upstream, local_repo.upstream);
                assert_eq!(repo.local, local_repo.local);
            };
            let with_local = sys
                .with_local(local.as_os_str().to_str().unwrap())
                .unwrap()
                .unwrap();
            check_equal(&with_local);

            let with_upstream = sys.with_upstream(UPSTREAM).unwrap().unwrap();
            check_equal(&with_upstream);

            assert!(sys.with_upstream(NAME).unwrap().is_none());
            assert!(sys.with_local(UPSTREAM).unwrap().is_none());
        }

        sys.fetch_upstream(&local_repo).unwrap();

        let default_branch = local_repo.default_branch().unwrap();
        sys.push_local(&local_repo, &default_branch).unwrap();

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
        let processed_patch = sys.process_patch(&local_repo, patch, NAME.into()).unwrap();
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

        sys.apply_patch(&local_repo, patch, &admin, NAME.into())
            .unwrap();
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
}
