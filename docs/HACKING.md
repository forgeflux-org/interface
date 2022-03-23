# Hacking instructions

Thank you for considering to contribute to ForgeFlux. This documentation
is work-in-progress so if you feel something is missing, please feel
free to raise an issue or ping a contributor on the [ForgeFlux
development channel on Matrix!](https://matrix.to/#/#dev-forgefed:matrix.batsense.net)

## Index

1. [Setting up the environment](#1.-setting-up-the-environment)<br />
   1.1 [Development Dependencies](#1.1-development-dependencies)<br />
   1.2 [Optional Development Dependencies](#1.2-optional-development-dependencies)<br />
   1.3 [Create environment](#1.3-create-environment)<br />
2. [Task-specific instructions](#2.-task-specific-instructions)<br />
   2.1 [Linting](#2.1-linting)<br />
   2.2 [Adding new Python dependencies](#2.2-adding-new-python-dependencies)
3. [Troubleshooting](#3.-troubleshooting)<br />
   3.1 [I made changes to libgit but my interface is not picking up changes](#3.1-i-made-changes-to-libgit-but-my-interface-is-not-picking-up-changes)<br />
   3.2 [I want to discard my current database and create a new one](#3.2-i-want-to-discard-my-current-database-and-create-a-new-one)
4. [Support](#4.-support)<br />
   4.1 [Forum](#4.1-forum)<br />
   4.1 [Matrix chatrooms](#4.2-matrix-chat)

## 1. Setting up the environment

### 1.1 Development Dependencies

1. Python
2. Rust
3. python virtualenv and pip
4. GNU make

### 1.2 Optional Development Dependencies

1. [ForgeFlux Northstar](https://github.com/forgeflux-org/northstar):
   Northstar is the discovery service that ForgeFlux uses. Interface
   self-registers with Northstar on startup, so if the developer wants
   to see Interface in action, installation is recommended.

    A minimal deployment configuration is provided via
    [docker-compose.yml](../docker-compose.yml). To launch Northstar
    using `docker-compose`:

    ```bash
    docker-compose up -d
    ```

**TODO: document how to configure Interface to work with locally running Northstar instance**

### 1.3 Create environment

We have a [Makefile](../Makefile) that should setup the environment once
the above mentioned dependencies are installed.

```bash
make env
```

## 2. Task-specific instructions

### 2.1 Linting

Running the following command is recommended before committing changes
to the repository

```bash
make lint
```

Optionally, the developer can also use the `pre-commit` Git hook found
in [pre-commit](./pre-commit) To install the hook, copy
[pre-commit](./pre-commit) to `.git/hooks/pre-commit`

```bash
cp docs/pre-commit .git/hooks/pre-commit
```

### 2.2 Adding new Python dependencies

[Makefile](../Makefile) contains a subroutine to freeze all Python
dependencies:

```bash
make freeze
```

## 3. Troubleshooting

This section documents
[Interface's](https://github.com/forgeflux-org/interface) quirky
behavior

### 3.1 I made changes to [libgit](../libgit) but my [interface](../interface) is not picking up changes

Kindly delete virtual environment(found at the root of the repository in
directory named `venv`) and run `make env` to recreate the environment.

### 3.2 I want to discard my current database and create a new one

Delete `instance` directory and run `make migrate`.

```bash
rm -rf ./instance && make migrate
```

## 4. Support

### 4.1 Forum

The fine folks at [forgefriends](https://forgefriends.org), a project
with similar goals, are hosting us on their forum. Come join use there
to take part in discussions related to the project!

### 4.2 Matrix chat

Come say hi at our [Matrix space](https://matrix.to/#/#forgefedv2:matrix.batsense.net)!
