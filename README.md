# CMPUT404-Project-BetterSocial
CMPUT 404 Fall 2021 Group Project

## Initial Setup

NOTE: Python 3.9.x is recommended.

### Virtual Environment (`virtualenv`)

Create your Python3 virtual environment:
```console
virtualenv ./venv
```

Activate it:
```console
. venv/bin/activate
```

Install requirements:
```console
python3 -m pip install -r requirements.txt
```

### Pipenv Install

For those using pipenv, create a virtual environment in the current directory:
```console
pipenv install
```

Active the pipenv shell:
```console
pipenv shell
```

Install the requirements:
```console
pipenv install -r requirements.txt
```

## Running Django

Change into the project directory:
```console
cd socialdistribution/
```

Run any pending migrations:

```console
python3 manage.py migrate
```

Start the development server:

```console
python3 manage.py runserver
```

## External Sources

- Button CSS for the fiends list page: [https://codepen.io/jacobberglund/pen/AKiBf]()

## Collaboration
