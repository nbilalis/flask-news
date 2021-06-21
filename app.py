from datetime import datetime
from os import environ, path, listdir
from flask import Flask, g, render_template, redirect, request, url_for, make_response, abort, flash

import sqlite3

from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

# Use the following line to generate a proper key
# python -c "import os; print(os.urandom(24).hex())"
app.secret_key = environ.get('SECRET_KEY', '1234')
toolbar = DebugToolbarExtension(app)

BASE_PATH = path.dirname(path.abspath(__file__))
DATABASE_PATH = path.join(BASE_PATH, 'data/flask-news.db')


def make_dicts(cursor, row):
    '''
    Use this as a "row factory" function in order to
    get DB records as a list of dictionaries
    '''
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def get_con():
    '''
    Call `get_con()` to get a connection for the DB.
    It stores the connection in the `g` object,
    so that a single connection is used for each request.
    '''
    con = getattr(g, 'con', None)   # con = g.con
    if con is None:
        con = sqlite3.connect(DATABASE_PATH)
        con.row_factory = sqlite3.Row
        # Alternatively
        # con.row_factory = make_dicts
        setattr(g, 'con', con)      # g.con = con

    return con


@app.teardown_appcontext
def close_connection(err):
    '''
    Close the connection to the DB.
    The `teardown_appcontext` decorator with ensure
    that this function gets called at the end of each request,
    even when an exception is raised.
    '''
    """ if request.endpoint != 'static':
        app.logger.debug('...') """
    if (con := g.pop('con', None)) is not None:
        con.close()

    if err is not None:
        app.logger.error(err)


@app.get('/')
def home():
    '''
    Just render the Home Page.
    Also, set a cookie with a timestamp,
    if one doesn't exist already
    '''
    res = make_response(render_template('home.html'))
    if request.cookies.get('timestamp') is None:
        res.set_cookie('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return res
    # Alternatively
    # return render_template('home.html'), {'Set-Cookie': 'foo=bar'}


@app.get('/articles/')
def article_list():
    '''
    Show an article list, using pagination.
    Page is passed as a query string param.
    '''
    PAGE_SIZE = 5

    try:
        page = int(request.args.get('page', 1))    # /articles/?page=2
    except (TypeError, ValueError):  # as err:
        page = 1

    cur = get_con().cursor()
    articles = cur.execute(
        '''
        SELECT "id", "title", "publish_date"
        FROM "article"
        ORDER BY "publish_date" DESC, "title"
        LIMIT :page_size OFFSET :offset
        ''',
        {'page_size': PAGE_SIZE, 'offset': (page-1) * PAGE_SIZE}
    ).fetchall()

    if len(articles) == 0:
        abort(404)

    # Log fetched rows as dictionaries, for readability
    app.logger.debug([dict(a) for a in articles])

    return render_template('/articles/list.html', articles=articles)


@app.get('/articles/<int:id>')
def article_details(id):
    '''
    Show details of a single article
    '''
    cur = get_con().cursor()
    article = cur.execute(
        '''
        SELECT "id", "title", "body", "publish_date"
        FROM "article"
        WHERE "id" = :id
        ''',
        {'id': id}
    ).fetchone()

    if article is None:
        abort(404)

    # Log fetched row as a dictionary, for readability
    app.logger.debug(dict(article))

    return render_template('articles/details.html', article=article)


@app.get('/articles/new')
def new_article():
    '''
    New article form
    '''
    return render_template('articles/new.html')


@app.get('/articles/edit/<int:id>')
def edit_article(id):
    '''
    Edit article form
    '''
    cur = get_con().cursor()
    article = cur.execute(
        '''
        SELECT "id", "title", "body", "publish_date"
        FROM "article"
        WHERE "id" = :id
        ''',
        {'id': id}
    ).fetchone()

    if article is None:
        abort(404)

    return render_template('articles/edit.html', article=article)


@app.post('/articles/save')
def save_article():
    '''
    This view function that will save an article's data,
    whether it's a new article on an existing one.
    In case the article already exists, `id` will have a value.
    '''

    id = request.form.get('id')  # Will return None if `id` was not posted
    title = request.form.get('title').strip()
    body = request.form.get('body').strip()
    publish_date = request.form.get('publish_date')

    # This should probably be the `id` of the logged-in user
    AUTHOR_ID = 1

    con = get_con()
    cur = con.cursor()

    # Insert a new article in DB
    if id is None:
        try:
            # Context manager usage (`with`) won't close the connection,
            # but it will auto-commit on success / rollback on exception.
            # Still need to manually catch errors though.
            with get_con() as con:
                # Insert new article
                cur.execute(
                    '''
                    INSERT INTO "article" ("title", "body", "publish_date", "author_id")
                    VALUES (:title, :body, :publish_date, :author_id)
                    ''',
                    {'title': title, 'body': body, 'publish_date': publish_date, 'author_id': AUTHOR_ID}
                )
                flash('Article saved successfully!', category='success')
                id = cur.lastrowid

        except Exception as err:
            app.logger.error(err)
            flash('Something went wrong...', 'error')
            return render_template('articles/new.html')

        finally:
            con.close()
    # Edit existing article's details
    else:
        # Edit existing article
        cur.execute(
            '''
            UPDATE "article"
            SET "title" = :title, "body" = :body, "publish_date" = :publish_date
            WHERE "id" = :id
            ''',
            {'title': title, 'body': body, 'publish_date': publish_date, 'id': id}
        )
        if cur.rowcount == 1:
            con.commit()
        else:
            con.rollback()

    flash('Article saved successfully', category='success')
    return redirect(url_for('article_details', id=id))


@app.cli.command('create-db')
# @click.argument('name')
def init_db():
    '''
    A CLI command to create the DB, running `flask create-db`,
    by executing the scripts in the "migrations" folder
    '''
    migrations_path = path.join(BASE_PATH, '_migrations')
    for file in listdir(migrations_path):
        file_path = path.join(migrations_path, file)
        with app.app_context():
            with get_con() as con:
                with app.open_resource(file_path, mode='r') as f:
                    contents = f.read()
                    con.cursor().executescript(contents)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(environ.get('SERVER_PORT', 8081)))
