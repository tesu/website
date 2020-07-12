# jasonl.net
Jason Lam's personal website, available at [jasonl.net](https://jasonl.net). You're probably not interested in deploying it, but I'll include the instructions here anyway.

## Deploying a test environment
1. `git clone git@github.com:tesu/website.git`
2. `cd website`
3. `pip install -e .`
4. `cd tesu`
5. `sqlite3 app.db < schema.sql`
6. ??? (there might be some other setup I've forgotten)
7. `./tesu.py`

## Deploying a prod environment
I recommend using NGINX + uWSGI.

