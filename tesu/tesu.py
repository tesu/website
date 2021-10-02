#!/usr/bin/env python3

import datetime, functools, markdown, os, re, requests, sqlite3, subprocess
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config.update({
    'DATABASE': os.path.join(app.root_path,'app.db'),
    'STEAM_KEY': '',
    'LASTFM_KEY': '',
    'LASTFM_UA': '',
})
app.config.from_pyfile('settings.cfg')

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def get_api():
    if not hasattr(g, 'api'):
        db = get_db()
        g.api = {
            "games": db.execute('select name, hours    from sidebar_games order by id asc').fetchall(),
        }
        if (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime('app.db'))).total_seconds() > 10*60 or app.config['DEBUG']:
            subprocess.Popen(['python3', '-c', 'import tesu; tesu.update_api()'], shell=False)
    return g.api

def update_api():
    r = requests.get("https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={}&steamid=76561198049007182&count=3&format=json".format(app.config['STEAM_KEY'])).json()
    if "games" in r["response"]:
        games = [(x["name"], round(x["playtime_2weeks"]/60,1)) for x in r["response"]["games"][:3]]
    else:
        games = []

    db = connect_db()
    for i in range(len(games)):
        db.execute('insert or replace into sidebar_games (id, name, hours) values (?, ?, ?)',
            [i+1, games[i][0], games[i][1]])
    db.commit()

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/blog/')
@app.route('/blog/<int:page>')
@app.route('/')
def index(page=0):
    ppp = 5 # posts per page
    db = get_db()
    posts = db.execute('select timestamp, title, slug, text from posts order by id desc').fetchall()
    return render_template('index.html', api=get_api(), page='Blog', posts=posts[page*ppp:page*ppp+ppp], newer=page-1, older=page+1 if (page+1)*ppp<len(posts) else -1)

@app.route('/blog/<slug>')
def show_post(slug):
    db = get_db()
    post = db.execute('select timestamp, title, slug, text from posts where slug == ?', [slug]).fetchone()
    if post is None:
        abort(404)
    return render_template('post.html', api=False, page='Blog', title=post['title'], post=post)

@app.route('/projects')
def projects():
    db = get_db()
    projects = db.execute('select name, description, url, urlname, img from projects order by id asc').fetchall()
    return render_template('projects.html', api=get_api(), page='Projects', projects=projects)

@app.route('/about')
def about():
    return render_template('about.html', api=get_api(), page='About')

@app.route('/about/webdev')
def about_webdev():
    return render_template('about/webdev.html', api=get_api(), page='About', title='About Web Development')

@app.route('/about/code')
def about_code():
    return render_template('about/code.html', api=get_api(), page='About', title='About Programming')

@app.route('/about/gaming')
def about_gaming():
    return render_template('about/gaming.html', api=get_api(), page='About', title='About Gaming')

@app.route('/about/anime')
def about_anime():
    return render_template('about/anime.html', api=get_api(), page='About', title='About Anime')

@app.route('/contact')
def contact():
    return render_template('contact.html', api=get_api(), page='Contact')

@app.route('/misc/')
def misc():
    files = [x for x in sorted(os.listdir(os.path.join(app.root_path, 'static/misc/'))) if '.html' in x]
    return render_template('misc.html', api=get_api(), page='Misc', files=files)

@app.route('/misc/<file>')
def show_misc(file):
    return app.send_static_file('misc/{}'.format(file))

@app.route('/py/<file>')
def show_py(file):
    try:
        m = __import__('scripts.{}'.format(file), fromlist=['x'])
    except Exception:
        abort(404)
    return m.run(request.args)

@app.route('/uploads/<file>')
def show_upload(file):
    return app.send_static_file('uploads/{}'.format(file))

@app.route('/uploads/<subfolder>/<file>')
def show_uploads_subfolder(subfolder, file):
    return app.send_static_file('uploads/{}/{}'.format(subfolder,file))

@app.route('/<slug>/')
@app.route('/<slug>')
def redirect_slug(slug):
    db = get_db()
    post = db.execute('select timestamp, title, slug, text from posts where slug == ?', [slug]).fetchone()
    if post is None:
        abort(404)
    return redirect(url_for('show_post', slug=slug))

@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(500)
def page_not_found(e):
    return render_template('error.html', api=get_api(), e=e, page='Error {}'.format(e.code)), e.code

@app.template_filter('timestamp')
def timestamp_filter(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').strftime('%B %-d, %Y')

@app.template_filter('truncate')
def truncate_filter(s):
    try:
        return s[:s.index('<!--more-->')]
    except ValueError:
        return s

@app.template_filter('truncated')
def truncated_filter(s):
    return '<!--more-->' in s

@app.template_filter('markdown')
def markdown_filter(s):
    return markdown.markdown(s)

def admin_only(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['DEBUG']:
            return f(*args, **kwargs)
        abort(404)
    return decorated_function

@app.route('/blog/new', methods=['GET','POST'])
@admin_only
def new_post():
    if request.method == 'GET':
        return render_template('admin/newpost.html', api=False, page='New Post')
    slug = re.sub(r'[^a-z0-9-]','',re.sub(r'\s+','-',request.form['title'].lower()).strip('-'))
    db = get_db()
    db.execute('insert into posts (title, slug, text) values (?, ?, ?)',
            [request.form['title'], slug, request.form['text']])
    db.commit()
    return redirect(url_for('show_post', slug=slug))

@app.route('/blog/<slug>/edit', methods=['GET','POST'])
@admin_only
def edit_post(slug):
    db = get_db()
    if request.method == 'GET':
        post = db.execute('select id, timestamp, title, slug, text from posts where slug == ?', [slug]).fetchone()
        if post is None:
            abort(404)
        return render_template('admin/editpost.html', api=False, post=post, page='Edit Post')
    db.execute('update posts set (title, slug, timestamp, text) = (?, ?, ?, ?) where slug==?',
            [request.form['title'], request.form['slug'], request.form['timestamp'], request.form['text'], slug])
    db.commit()
    return redirect(url_for('show_post', slug=request.form['slug']))

@app.route('/projects/edit', methods=['GET','POST'])
@admin_only
def edit_projects():
    db = get_db()
    if request.method == 'GET':
        projects = db.execute('select id, name, description, url, urlname, img from projects order by id asc').fetchall()
        return render_template('admin/editprojects.html', api=False, page='Edit Projects', projects=projects)
    if 'id' in request.form:
        db.execute('update projects set (name, description, url, urlname, img) = (?, ?, ?, ?, ?) where id==?',
                [request.form['name'], request.form['description'], request.form['url'], request.form['urlname'], request.form['img'], request.form['id']])
    else:
        db.execute('insert into projects (name, description, url, urlname, img) values (?, ?, ?, ?, ?)',
                [request.form['name'], request.form['description'], request.form['url'], request.form['urlname'], request.form['img']])
    db.commit()
    return redirect(url_for('projects'))

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(debug=True)

