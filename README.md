## About Ratings

This is a Flask app that loads anonymized user and movie ratings into a Postgres database. The user can log in, save ratings on movies, and see their predicted ratings for other movies based on similar users. The user's ratings are also compared to the ratings of a built-in third party user.

## Getting Started

```
$ pip install requirements.txt
$ createdb ratings
$ python seed.py
$ python server.py 
```
