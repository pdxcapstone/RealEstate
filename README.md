[![Build Status](https://travis-ci.org/pdxcapstone/RealEstate.svg?branch=travis_ci)](https://travis-ci.org/pdxcapstone/RealEstate)
[![Requirements Status](https://requires.io/github/pdxcapstone/RealEstate/requirements.svg?branch=models_unit_tests)](https://requires.io/github/pdxcapstone/RealEstate/requirements/?branch=dev)
[![Coverage Status](https://coveralls.io/repos/pdxcapstone/RealEstate/badge.svg?branch=dev&service=github)](https://coveralls.io/github/pdxcapstone/RealEstate?branch=dev)
# Real Estate App
This is a Django-based web app for Portland State's CS Capstone. 

## Installation
The following instructions are primarily intended for Mac/Linux, but they should also work for Cygwin.

1. Install [Python](https://www.python.org/downloads/) if it's not already on your system.

2. Install [pip](https://pip.pypa.io/en/latest/installing.html), the Python package manager.

3. Install [virtualenv](https://virtualenv.pypa.io/en/latest/). 

	```[sudo] pip install virtualenv```

4. Install [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/index.html). Follow installation instructions [here](http://virtualenvwrapper.readthedocs.org/en/latest/install.html).

5. Clone this repo.

	```git clone git@github.com:pdxcapstone/RealEstate.git```

6. Create your virtual environment. This will isolate the project from any other python projects you may have running on your system.

	```mkvirtualenv -a RealEstate/ RealEstate```

7. Enter your new virtual environment. From any directory: 

	```workon RealEstate```

8. Install dependencies:

	```pip install -r requirements.txt```

9. Create/update database:

	```python manage.py migrate```

10. Run the server:

	```python manage.py runserver```

11. When you are finished and wish to exit the virtualenv, exit by the command: ```deactivate```

12. Optional: Create a superuser in order to login to the RealEstate application:

    ```python manage.py createsuperuser```

## API Document

* [REST-API](https://docs.google.com/document/d/1f06a-pnfcYQxcg2cQIeOdPtUgF2YTUOA-gWNyFvrF7o/edit)

=======


## External Documentation

* [Team Django Notes](https://drive.google.com/drive/folders/0B24lwkPmIOELNS1paFlwaHRJYnc)
* [DB Schema/Notes](https://drive.google.com/drive/folders/0BySvjEj8bWEqfnJFUDU3dW9TY3N5VUJCam5VVE9Xc0dMWlNDWVF4MnNDVjMxODlEQ1NQcnc)
* [Initial Moc-Ups](https://docs.google.com/uc?authuser=0&id=0B5P01o4Jp1ZlWkFMcDkwODUxdEExd1RxTWl1a2d5elR5TFZv&export=download)
