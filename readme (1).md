1. Install pre-requisites
=========================

Virtualenv
----------
Standard installation with virtualevnwrapper.

PostgreSQL
----------
Standard installation.



# Standard project initialization
## 1. Create virtual environment


1. Clone repository: ``git clone https://bitbucket.org/razortheory/realtorx.git``
2. Create virtual environment: ``mkvirtualenv realtorx -p python3``
3. Install requirements ``pip install -r requirements/dev.txt``
4. Edit ``$VIRTUAL_ENV/bin/postactivate`` to contain the following lines:

        export DATABASE_URL=postgres://username:password@localhost/dbname
        export DEV_ADMIN_EMAIL=your@email.com

5. Deactivate and re-activate virtualenv:

        deactivate
        workon realtorx


## 2. Database

1. Create database table:

        psql -Uyour_psql_user
        CREATE DATABASE realtorx;

2. Migrations: ``./manage.py migrate``
3. Create admin: ``./manage.py createsuperuser``
4. Run the server ``./manage.py runserver``

# Create settings environment
1. Rename `env.copy` to `.env` at `config/settings/` directory.
2. Fill out the key requirements.


# Alternative project initialization

1. Clone repository: ``git clone https://bitbucket.org/razortheory/realtorx.git``
2. Create project database
3. Execute the following command to setup database credentials:

        echo DATABASE_URL=postgres://username:password@localhost/dbname >> env.config

4. **Make sure that you are not in any of existing virtual envs**
5. run ``./initproject.bash`` - will run all commands listed in standard initialization, including edition of postactivate
6. activate virtualenv ``workon realtorx``
7. run ``./manage.py runserver``


# Docker setup for local development

The local docker development setup has services for postgres, celery, rabiitmq, redis and django server.
To run the servers follow the steps:
1. Do a compose up for the `docker-compose.local.yml` file in the `docker` folder.
2. Once the containers are created navigate to `localhost:8001` on the borwser.
3. Start the `collectstatic` service which will then call `migration` and `realtorx`(the django app server) services sequentially and automatically.
4. After the `realtorx` service is up, navigate to `localhost:8002` to start the `celery`, `celery-beat` and `flower` services. You can see the flower dashboard on `localhost:5555` which will help you in debugging about the tasks.
**To update any environment variable just edit the `env.local` file in `config/settings` folder.**
**The Django app uses the `config.settings.prod` file at the path: `config/settings/prod.py` for the django app configuration.**

More configurations:
1. Supervisor configuration is in the file `local_manager.conf` at the root of the repository.
2. `Dockerfile.local` in the `docker` folder is being used by `docker-compose.local.yml` file.
3. `env.local` file is being used to inject the environment variables into the services present at  `config/settings` folder.

# Load data from files

`manage.py` provides various commands, including `City` and `Agency`, `ApplicationUser` model data import.

## City model

Loads cities from CSV file, defaults to a saved one.

```shell
python manage.py create_cities_csv -h

usage: manage.py create_cities_csv [-h] [-f FILE] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                                   [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Specify a file containing cities in a CSV format, if not specified, Zip_Code_database.csv will be chosen instead
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE
                        environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```

## ApplicationUser/Agency model

Loads users and agencies from XLSX file, links them together.

```shell
python manage.py create_users_xlsx -h

usage: manage.py create_users_xlsx [-h] -f FILE [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                                   [--force-color]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Specify a file containing users in a XLSX format
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE
                        environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
```
