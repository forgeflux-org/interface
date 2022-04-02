# Webfinger

Actor discovery is not part of ActivityPub specification so
[Webfinger](http://tools.ietf.org/html/rfc7033) is used for this purpose
by most ActivityPub implementations. Interface implements Webfinger for
Forge User, Repository, Issues and Pull Requests.

ForgeFlux uses [Group
Actor](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-group) to
describe Repositories, Issues and Pull Requests and [Person
Actor](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-person) for
Users. Since all actors share the same namespace on the Instance's
hostname, ForgeFlux differentiates and guarantees collision free Actor
IDs by using a special syntax for each of the actor types:

## Resource ID syntax 

### 1. User Actor

An User Actor is assigned unique ID using the following syntax:

```
{username}@{hostname}
```

Where `username` is a valid
[UsernameCaseMapped](https://tools.ietf.org/html/rfc8265#page-7) word as
defined by the PRECIS Framework.

### 2. Repository Actor

A Repository Actor is assigned unique IDs using the following syntax:

```
{owner-username}!{repository-name}@{hostname}"
```

Where `owner-username` and `repository-name` is a valid
[UsernameCaseMapped](https://tools.ietf.org/html/rfc8265#page-7) word as
defined by the PRECIS Framework.

### 3. Issue Actor

An Issue Actor is assigned unique IDs using the following syntax:

```
{owner-username}!{repository-name}!issue!{issue-id}@{hostname}"
```

Where `owner-username` and `repository-name` is a valid
[UsernameCaseMapped](https://tools.ietf.org/html/rfc8265#page-7) word as
defined by the PRECIS Framework and `issue ID` is a unique identifier
within the scope/namespace of the repository

### 4. Pull Request Actor

A Pull Request Actor is assigned unique IDs using the following syntax:

```
{owner-username}!{repository-name}!pull!{pullrequst-id}@{hostname}"
```

Where `owner-username` and `repository-name` is a valid
[UsernameCaseMapped](https://tools.ietf.org/html/rfc8265#page-7) word as
defined by the PRECIS Framework and `pull request ID` is a unique identifier
within the scope/namespace of the repository

**NOTE: Pull request ID and Issue ID may not share the same
namespace. Using different delimiters(`issue` and `pull` for Issue and
Pull Request Actors respectively) essentially guarantees collision
free**
