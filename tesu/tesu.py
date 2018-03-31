#!/usr/bin/env python3

import datetime, functools, json, markdown, os, pickle, re, requests, sqlite3, subprocess, xml.etree.ElementTree as ET
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config.update({
    'DATABASE': os.path.join(app.root_path,'app.db'),
    'STEAM_KEY': '',
    'MAL_UA': '',
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
        try:
            with app.open_resource('api.pkl') as f:
                g.api = pickle.load(f)
        except FileNotFoundError:
            g.api = update_api()
        if (datetime.datetime.now() - g.api["time"]).total_seconds() > 10*60 and not app.config['DEBUG']:
            subprocess.Popen(['python3', '-c', 'import tesu; tesu.update_api()'], shell=False)
    return g.api

def update_api():
    o = {}
    r = requests.get("https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={}&steamid=76561198049007182&count=3&format=json".format(app.config['STEAM_KEY']))
    r = json.loads(r.text)
    o["steam"] = [(x["name"], round(x["playtime_2weeks"]/60,1)) for x in r["response"]["games"][:3]]
    r = requests.get("https://myanimelist.net/rss.php?type=rwe&u=420anon", headers={"user-agent":app.config['MAL_UA']})
    r = ET.fromstring(r.text)
    o["mal"] = []
    for i in r[0][3:]:
        if all([i[0].text != x[0] for x in o["mal"]]):
            m = re.findall(r'[0-9]+',i[3].text)
            o["mal"] += [(i[0].text, '{}/{}'.format(str(m[0]),str(m[1])) if len(m) > 1 else '{}/?'.format(str(m[0])))]
            if len(o["mal"]) > 2:
                break
    r = requests.get("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=jason-lam&api_key={}&format=json".format(app.config['LASTFM_KEY']), headers={"user-agent":app.config['LASTFM_UA']})
    r = json.loads(r.text)
    o["lastfm"] = [(x["artist"]["#text"], x["name"]) for x in r["recenttracks"]["track"][:5]]
    o["time"] = datetime.datetime.now()
    with open(os.path.join(app.root_path, 'api.pkl'), 'wb') as f:
        pickle.dump(o, f)
    return o

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
    projects = db.execute('select name, description, url, urlname from projects order by id asc').fetchall()
    return render_template('projects.html', api=get_api(), page='Projects', projects=projects)

@app.route('/about')
def about():
    return render_template('about.html', api=get_api(), page='About')

@app.route('/about/webdev')
def about_webdev():
    return render_template('about/webdev.html', api=get_api(), page='About')

@app.route('/about/code')
def about_code():
    return render_template('about/code.html', api=get_api(), page='About')

@app.route('/about/gaming')
def about_gaming():
    return render_template('about/gaming.html', api=get_api(), page='About')

@app.route('/about/anime')
def about_anime():
    return render_template('about/anime.html', api=get_api(), page='About')

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

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(debug=True)
