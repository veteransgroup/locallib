# Django Local Library

"Local Library" prototype website written in Django.


## Overview

This web application creates an online catalog for a small local library, where users can browse available books and manage their accounts.

The main features that have currently been implemented are:

* There are models for books, book copies, genre and authors.
* Users can view list and detail information for books and authors.
* Admin users can create and manage models. The admin has been optimised (the basic registration is present in admin.py, but commented out).
* Librarians can renew reserved books.
* Librarians can add, update and delete books, first time delete is to throw it to trash, second time delete is real delete the book.
* Librarians can add, update and delete authors, first time delete is to throw it to trash, second time delete is real delete the author.
* It support third part login like Github account (you need to register a new OAuth application on https://github.com/settings/applications/new and configure on the admin site)
* It support user use their username or email login

## Quick Start

To get this project up and running locally on your computer:
1. Set up the [Python development environment]
   I recommend using a Python virtual environment.
1. Assuming you have Python setup, run the following commands:
   ```
   pip3 install -r requirements.txt
   python3 manage.py makemigrations
   python3 manage.py migrate
   python3 manage.py createsuperuser # Create a superuser
   python3 manage.py runserver
   ```
1. Open a browser to `http://127.0.0.1:8000/admin/` to open the admin site
1. Create a few test objects of each type.
1. Open tab to `http://127.0.0.1:8000` to see the main site, with your new objects.







## Todo functions:
### add search and filter
### add Bookinstance
### deploy prod
### other permissions come from Django original 
### register redirect to add info page, add mobile phone and nickname fields
### apply to become library member to apply to loan bookinstances (anonymous can browse books but member can loan)
### impl loan borrow functions (add models show loaning histories)
### maybe add front-end