import sqlite3
import os
import imghdr
from flask import Flask, render_template, request, url_for, flash, redirect,session
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)

app.config['SECRET_KEY'] = 'Stablecoffee123'
# control max file size
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
# only accept these file formats
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png']
# user-uploaded images will be stored in the /uploads folder in this project directory
app.config['UPLOAD_PATH'] = 'static/uploads'

loggedIn = False
userProf = ""

class UserData():
    def __init__(self, user):
        self.user = user

    def set_user(user):
        self.user = user

    def get_user():
        return self.user


# START HELPER FUNCTIONS
def isLoggedin():
    return loggedIn

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

def get_comments(post_id):
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments WHERE postid = ?', [post_id]).fetchall()
    conn.close()
    return comments

def validate(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', [username])
    get_data = user.fetchall()
    user_data = get_data[0]
    conn.close()
    if user is None:
        return False
    else:
        if password == user_data['password']:
            the_user = UserData(user_data)
            return True
        else:
            return False

# END HELPER FUNCTIONS

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    files = os.listdir(app.config['UPLOAD_PATH'])
    
    return render_template('index.html', posts=posts, logStat = loggedIn, user = userProf)

# sign-up page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if not username or not password or not email:
            flash("All fields must be filled out.")
            return redirect(url_for('signup'))
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO users (username, password, email) VALUES (?, ?, ?) """, (username, password, email))
            conn.commit()
            cursor.close()
            conn.close()
            # now log in after signing up
            return redirect(url_for('login'))

    return render_template("signup.html")

# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("All fields must be filled out.")
            return redirect(url_for('login'))
        else:
            validate_user = validate(username, password)
            if validate_user == False:
                error = 'Invalid Credentials Please Try Again'
                return render_template('login.html', error=error)
            else:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))
    return render_template('login.html') 

# display an individual post
@app.route('/<int:id>', methods=('GET', 'POST'))
def post(id):
    post = get_post(id)
    comments = get_comments(id)
    print('the request method is ' + str(request.method))
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        # get the current score
        old_score = cursor.execute('SELECT score FROM posts WHERE id = ?', [id])
        # add plus one to that score
        new_score = old_score

        # insert the new score to the database entry
        cursor.execute('UPDATE posts SET score = score + 1'
                         ' WHERE id = ?',
                         (id))
        get_score = conn.execute('SELECT score FROM posts WHERE id = ?', [id])
        print('the score is ' + str(get_score))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    return render_template('post.html', comments=comments, post=post)

# add comments
@app.route('/<int:id>/addComment', methods=('GET', 'POST'))
def addComment(id):
    post = get_post(id)

    if request.method == 'POST':
        # read comment submission
        comment = request.form['comment']

        if not comment:
            flash('Fill out all upload fields!')

        else:
            # add to comments database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO comments (message, postid) VALUES (?,?) """, (comment, id))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

    return render_template('addComment.html', post=post)


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
            cursor.execute("""INSERT INTO posts (title, content, photo, score) VALUES (?,?,?,?) """, (title, content, filepath, 0))
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

@app.context_processor
def injectUser():
    return dict(user = userProf)



if __name__ == "__main__":
    app.run(debug = True)
