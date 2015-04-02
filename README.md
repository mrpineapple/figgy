# Steve Smith's Code Submission

I thought this was an excellent code test. Non-trivial with a nod toward the messiness of real-world development. (Wait? What? People didn't adhere to a standard?) 

I like that I was forced to think about some architectural things and had the freedom of a variety of solutions.

Perhaps my solution is quite unlike the solution Safari Books Online chose, but I think my solution tackles the issues I thought significant in an appropriate way.

## Key Concepts: Publisher Id & Conflicts

The philosophy behind my solution is this: Conflicts happen. Store the conflicted data and provide another tool to correct and/or merge conflicted data. (I have not provided the merging tool; I would be happy to provide more work if that's helpful.)

Another key idea is that we should not trust the publisher to give us primary key data for our database. Let's just store the publisher's id as another Alias.

## The Task

Let's get to the task at hand, shall we? Let's assume you've been through the Very First Time setup.

First, run the tests as originally documented:

    $ tox

Second, reset your database to get new model changes. I did not provide migrations, because it seems
this task seems to be a proof-of-concept situation:

    $ python manage.py reset_db <user@domain.com>

This will delete the existing SQLite3 database and create the new database with the appropriate model changes. It will also create the super-user `user` with the provided email address and the password set to `user`.

Obviously, this method would NEVER be used on production (and will stop if your engine isn't SQLite3). But I find it useful to have a prompt-less database reset mechanism.

You should now be able to import the updates to the book data.

    $ python manage.py process_data_file data/initial/*.xml
    $ python manage.py process_data_file data/update/*.xml

Feel free to re-run the update. We'll ignore any file that we've already processed. (We ignore duplicate updates based on the SHA1 hash of the file contents.)

**The rest of this document is as it was.**

## Setup

### System dependencies

* virtualenv (`sudo easy_install virtualenv`)

### Very first time

This setup assumes you have just cloned the git repo and are in the directory with this `README.md`.

    $ virtualenv ve --python=python2.7 --prompt="(figgy)"  # Get a set of eggs just for this
    $ . ve/bin/activate                                    # Turn on the virtualenv
    $ python setup.py develop --always-unzip               # Fill the virtualenv with Python dependencies
    $ cp figgy/local.py.example figgy/local.py             # Your local.py is your personal settings. Edit them later.
    $ python manage.py syncdb --noinput                    # Fill out the database schema
    $ python manage.py createsuperuser                     # Establish an admin so you can log in
    $ python manage.py runserver                           # Prove this works by visiting http://localhost:8000

## Running tests

I've provided decent test coverage for my solution. The tests for this project are managed by `tox`, a Python package.

First, install `tox` via `easy_install` (or `pip`).

Prior to running tox, be sure to create a `figgy/_local_tests.py` file by copying
`figgy/_local_tests.py.example` to `figgy/_local_tests.py`. 

Any modifications to the test settings should be performed in the developer's `_local_test.py`.

To run the tests:

    tox

The first run will take a while as it builds a virtualenv and installs everything in it, subsequent ones will be much faster.  To rebuild the virtualenv later with updated dependencies:

    tox -r

You normally shouldn't need to recreate the tox virtualenv, since it updates itself on each run, but it might be necessary in cases of version conflicts.

## Importing test data

Import the initial set of test data.

````
$ python manage.py process_data_file data/initial/*.xml
````

