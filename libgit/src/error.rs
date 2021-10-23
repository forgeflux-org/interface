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

use std::convert::From;
use std::error::Error as StdError;
use std::io::Error as IOError;
use std::string::ToString;

use git2::Error as GError;
use pyo3::create_exception;
use pyo3::PyErr;
use thiserror::Error;
use url::ParseError as UrlParseError;

#[derive(Debug, Error)]
pub enum FError {
    #[error("{0}")]
    IOError(#[source] IOError),
    //IOError(IOError),
    #[error("To get the directory in which a repository is stored, you have to provide a valid upstream URL. {0} is not a valid URL")]
    NoDirInvalidUpstreamUrl(String),
    #[error("please provide a valid email ID. {0} is not an email")]
    NotAnEmail(String),

    #[error("please provide a valid URL. {0}")]
    NotAUrl(#[source] UrlParseError),
    //NotAUrl(UrlParseError),
    #[error("{0}")]
    GitError(#[source] GError),
    //GitError(GError),
    #[error("A remote with similar name exists, please select different name")]
    RemoteNameExists,
}

impl From<IOError> for FError {
    fn from(e: IOError) -> Self {
        FError::IOError(e)
    }
}

impl From<GError> for FError {
    fn from(e: GError) -> Self {
        FError::GitError(e)
    }
}

impl From<UrlParseError> for FError {
    #[cfg(not(tarpaulin_include))]
    fn from(e: UrlParseError) -> Self {
        FError::NotAUrl(e)
    }
}
//impl IntoPy<PyObject> for FError {
//    fn into_py(self, py: Python) -> PyObject {
//        self.into_py(py)
//    }
//}

impl std::convert::From<FError> for PyErr {
    fn from(err: FError) -> PyErr {
        match err {
            FError::IOError(e) => PyIOError::new_err(e),
            FError::NoDirInvalidUpstreamUrl(e) => InvalidUpstreamUrl::new_err(e),
            FError::GitError(e) => GitError::new_err(e.to_string()),
            FError::NotAUrl(e) => NotUrl::new_err(e.to_string()),
            FError::RemoteNameExists => RemoteNameExists::new_err(err.to_string()),
            FError::NotAnEmail(e) => NotAnEmail::new_err(FError::NotAnEmail(e).to_string()),
        }
    }
}
pub type FResult<V> = Result<V, FError>;
pub type BoxDynError = Box<dyn StdError + 'static + Send + Sync>;

create_exception!(libgit, RemoteNameExists, pyo3::exceptions::PyException);
create_exception!(libgit, GitError, pyo3::exceptions::PyException);
create_exception!(libgit, InvalidUpstreamUrl, pyo3::exceptions::PyException);
create_exception!(libgit, PyIOError, pyo3::exceptions::PyException);
create_exception!(libgit, NotUrl, pyo3::exceptions::PyException);
create_exception!(libgit, NotAnEmail, pyo3::exceptions::PyException);
