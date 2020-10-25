import sqlite3
import os
import imghdr
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your secret key'
# control max file size
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
# only accept these file formats
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png']
# user-uploaded images will be stored in the /uploads folder in this project directory
app.config['UPLOAD_PATH'] = 'static/uploads'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', posts=posts)

# display an individual post
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

# upload an image post
@app.route('/upload', methods=('GET', 'POST'))
def upload():
    if request.method == 'POST':
        # read from user submission
        title = request.form['title']
        content = request.form['content']
        file = request.files['file']

        filename = secure_filename(file.filename)

        if not title or not content or not file:
            flash('Fill out all upload fields!')
        else:
            # get the file extension
            file_ext = os.path.splitext(filename)[1]

            # file validation now: check correct format
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)

            # good file extension, so add it to our uploads folder
            file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            filepath = 'static/uploads/' + filename

            # now add the post to the database, with the path to the image file stored in the database
            conn = get_db_connection()
            cursor = conn.cursor()
            print('the filepath is ' + filepath)
            cursor.execute("""INSERT INTO posts (title, content, photo) VALUES (?,?,?) """, (title, content, filepath))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('uploadPage.html')

# edit an image post's title or description
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE posts SET title = ?, content = ?'
                         ' WHERE id = ?',
                         (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post=post)

# delete posts
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug = True)