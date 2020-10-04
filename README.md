# Django Public Library

"Public Library" prototype website written in Django by <a href="mailto:liubing009@gmail.com">Jeff</a>


## Overview

This web application creates an online catalog for a small public library, where users can browse available books and manage their accounts.

The main features that have currently been implemented are:

* There are models for books, book copies, genre, and authors.
* Anonymous user can browse books and authors info including list and detail
* There are three kinds of users, one is members, one is librarians, the other is admin.
* User can use their username, email, cardNo login system.
* It supports third party login like Github account (you need to register a new OAuth application on https://github.com/settings/applications/new and configure on the admin site)
* Library member can loan book instances if the book instance is the available status
* Librarian can renew book lending for member
* Librarian can update book instance info so can do payback action for member
* Librarian can add, update, and delete book, bookinstance, author and there are some business logic in it
   * can't delete book instance when it is 'on loan' by someone
   * when adding a book from the author detail page, it has author info automated
   * when 'fake' delete an author, the book detail info page can display the author's name but can't hyperlink to them
   * when an author is real deleted, the book detail page can add a new author and automated associate the book
* Admin users can create and manage models. The admin has been optimized (the basic registration is present in admin.py, but commented out).


## Quick Start

To get this project up and running locally on your computer:
1. Set up the [Python development environment]
   I recommend using a Python virtual environment.
1. Prepare PostgreSQL db
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
### add new models to impl loaning history functions
### add like and dislike function
### add member can comment book
### more business logic like how many times member can renew a book, notificatioins
### maybe divide it into front and back structure