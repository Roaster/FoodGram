import sqlite3
import os
import imghdr 
import PIL
from PIL import Image
from flask import Flask, render_template, request, url_for, flash, redirect,session
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

# initialize the Flask app
app = Flask(__name__)

app.config['SECRET_KEY'] = 'Stablecoffee123'
# control max file size
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
# only accept these file formats
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png']
# user-uploaded images will be stored in the /uploads folder in this project directory
app.config['UPLOAD_PATH'] = 'static/uploads'

# keep track of session details
loggedIn = False
userProf = ""

# START HELPER FUNCTIONS
# determine if user is currently logged into a session
def isLoggedin():
    return loggedIn

# connect to the database called database.db
# as initialized by init_db.py
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# get all posts to display on home page
def get_all_posts():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    return posts

# using the post_id, get the current post that we want to look at
def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

# using the post_id, get all the comments associated with this post
def get_comments(post_id):
    conn = get_db_connection()
    comments = conn.execute('SELECT * FROM comments WHERE postid = ?', [post_id]).fetchall()
    conn.close()
    return comments

# using the post_id, get the score associated with this post
def get_score(post_id):
    conn = get_db_connection()
    score = conn.execute('SELECT * FROM posts WHERE id = ?', [post_id]).fetchone()
    conn.close()
    return score['score']

# using the post_id, increment the score by +1
def update_score(post_id, new_score):
    conn = get_db_connection()
    conn.execute('UPDATE posts SET score = ?'
                         ' WHERE id = ?',
                         (new_score, post_id))
    conn.commit()
    score = conn.execute('SELECT * FROM posts WHERE id = ?', [post_id]).fetchone()
    print('score is now ' + str(score['score']))
    conn.close()

# insert user into database after they sign up
def insert_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
    conn.commit()
    cursor.close()
    conn.close()

# insert comment into database after user posts comment
def insert_comment(comment, id, user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (message, postid, userid) VALUES (?,?,?)', (comment, id, user))
    conn.commit()
    cursor.close()
    conn.close()

# insert post into database after user posts image
def insert_post(title, content, filepath, user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO posts (title, content, photo, score, userid) VALUES (?,?,?,?,?)', (title, content, filepath, 0, user))
    conn.commit()
    cursor.close()
    conn.close()

# update post values
def update_post(title, content, id):
    conn = get_db_connection()
    conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, id))
    conn.commit()
    conn.close()

# delete post
def delete_post(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# search the users table in the database
# if the username is found and the password is correct for that username, then log in
def validate(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', [username]).fetchone()
    conn.close()
    if user is None:
        return False
    else:
        if password == user['password']:
            return True
        else:
            return False

# count number of rows currently in the users table in the database
# if there are no users in the database, return true
def num_users():
    conn = get_db_connection()
    number = conn.execute('SELECT * FROM users').fetchone()
    conn.close()
    if number is None:
        return True
    return False

# used by def edit() endpoint below
# posts can only be edited by the OP
def verify_user(id):
    conn = get_db_connection()
    get_user = conn.execute('SELECT userid FROM posts where id = ?', [id]).fetchone()
    conn.close()
    post_user = get_user['userid']
    if session['username'] == post_user:
        return True
    return False

# END HELPER FUNCTIONS

# landing page when first opened
@app.route('/')
def index():
    return render_template('index.html', logStat = loggedIn, user = userProf)

# sign-up page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # user must fill out all 3 fields of sign-up page
        if not username or not password or not email:
            flash("All fields must be filled out.")
            return redirect(url_for('signup'))

        else:
            # insert user-entered info into users table using insert_user function
            insert_user(username, password, email)
            session['logged_in'] = True
            session['username'] = username
            # now log in after signing up
            return redirect(url_for('home'))

    return render_template("signup.html")

# login page
@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # if there are no current users, force user to the sign-up page signup.html
        # ran into error otherwise
        if num_users():
            return redirect(url_for('signup'))

        # get user input
        username = request.form['username']
        password = request.form['password']

        # user must fill out both fields
        if not username or not password:
            flash("All fields must be filled out.")
            return redirect(url_for('login'))

        else:
            # check that user is in the users table in the database
            # validate(username, password) is defined above as a helper function
            validate_user = validate(username, password)

            if validate_user == False:
                flash('The username or password is incorrect.')
                return redirect(url_for('login'))

            else:
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('home'))

    return render_template('login.html')

# logout
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))

# homepage
@app.route("/home", methods=["GET"])
def home():
    # if a user tries to access the website before logging in or signing up
    # kick them out back to index.html to force them to sign in or sign up
    if session['logged_in'] == False:
        return redirect(url_for('index'))
    # once the user has already logged in, session['logged_in'] will be true...
    # thus, get all the posts and display them
    else:    
        posts = get_all_posts()
        files = os.listdir(app.config['UPLOAD_PATH'])
        return render_template('home.html', posts=posts)

# display an individual post
@app.route('/<int:id>', methods=('GET', 'POST'))
def post(id):
    post = get_post(id)
    comments = get_comments(id)

    return render_template('post.html', comments=comments, post=post)

# upvote a post
@app.route('/<int:id>/upvote', methods=('GET',))
def upvote(id):

    old_score = get_score(id)
    new_score = old_score + 1

    # update the score
    # update_score(id, new_score) is defined above as a helper function
    update_score(id, new_score)
    return redirect(url_for('post', id=id))

# add comments
@app.route('/<int:id>/addComment', methods=('GET', 'POST'))
def addComment(id):
    post = get_post(id)
    user = session['username']

    if request.method == 'POST':
        # read comment submission
        comment = request.form['comment']

        if not comment:
            flash('Please write your comment.')

        else:
            # add to comments table in database
            insert_comment(comment, id, user)
            return redirect(url_for('post', id=id))

    return render_template('addComment.html', post=post)

# upload an image post
@app.route('/upload', methods=('GET', 'POST'))
def upload():
    if request.method == 'POST':
        # read from user submission
        title = request.form['title']
        content = request.form['content']
        file = request.files['file']
        user = session['username']

        filename = secure_filename(file.filename)

        if not title or not content or not file:
            flash('Please fill out all upload fields.')

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
            insert_post(title, content, filepath, user)
            return redirect(url_for('home'))

    return render_template('uploadPage.html')

# edit an image post's title or description
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)

    if not verify_user(id):
        flash('You do not have edit permissions for this post!')
        return redirect(url_for('post', id=id))

    if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']

            if not title or not content:
                flash('Please fill out all fields.')
            else:
                # update the post
                update_post(title, content, id)
                return redirect(url_for('post', id=id))

    return render_template('edit.html', post=post)

# delete posts
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    title = post['title']
    # delete the post from the posts table in the database
    delete_post(id)
    flash('"{}" has been deleted!'.format(title))
    return redirect(url_for('home'))

@app.context_processor
def injectUser():
    return dict(user = userProf)

if __name__ == "__main__":
 app.run(debug = True)
