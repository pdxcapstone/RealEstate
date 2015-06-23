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

11. When you are finished and wish to exit the virtualenv, exit by the command: 

	```deactivate```
 