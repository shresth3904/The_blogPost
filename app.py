from flask import Flask, request, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_a_secret key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.id)
    

@login_manager.user_loader
def load_user(user_id): 
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], password=user_data['password'])
    return None

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT id, url FROM img")
    imgs = cur.fetchall()
    img_dict = {img[0]: img[1] for img in imgs}
    cur.execute("SELECT id, title, content, author FROM blog ORDER BY created_at DESC")
    blogs = cur.fetchall() 
    all_ids = [blog[0] for blog in blogs]
    cur.execute("""
                SELECT t.tag, bt.blog_id
                FROM blog_tags bt
                JOIN tags t ON bt.tag_id = t.id
                ORDER BY t.tag, bt.blog_id;
                """)
    tags = cur.fetchall()
    
    cur.execute("SELECT blog_tags.blog_id, tags.tag FROM blog_tags JOIN tags ON blog_tags.tag_id = tags.id")
    blog_tags = cur.fetchall()
    blog_tags_dict = defaultdict(list)
    for blog_id, tag in blog_tags:
        blog_tags_dict[blog_id].append(tag)
    con.close()

    tags_dict = defaultdict(list)
    for tag, blog_id in tags:
        tags_dict[tag].append(blog_id)
    html = render_template("index.html", blogs = blogs, tags_dict = tags_dict, all_ids = all_ids, img_dict = img_dict, blog_tags_dict = blog_tags_dict, current_user = current_user)
    return html

@app.route("/blog", methods = ["GET"])
def blog():
    blog_id = request.args.get("id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT id, url FROM img")
    imgs = cur.fetchall()
    img_dict = {img[0]: img[1] for img in imgs}
    cur.execute("SELECT title, content, created_at, author FROM blog WHERE id = ?", (blog_id,))
    blog = cur.fetchone()
    cur.execute("SELECT name, comment FROM comments WHERE id = ?", (blog_id, ))
    comments = cur.fetchall()
    con.close()
    html = render_template("blog.html", blog = blog, img_dict = img_dict, blog_id = int(blog_id), comments = comments, current_user = current_user)
    return html

@app.route("/comment", methods = ["POST"])
def comment():
    blog_id = request.form.get("id")
    comment = request.form.get("comment")
    name = request.form.get("name")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO comments (id, comment, name) VALUES (?, ?, ?)", (blog_id, comment, name))
    con.commit()
    con.close()
    return redirect(url_for("blog") + f"?id={blog_id}")

@app.route("/submit", methods = ["GET", "POST"])
@login_required
def submit():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        author = request.form.get("author")
        img_url = request.form.get("img_url")
        tags = request.form.get("tags").split(",")
        tags = [tag.strip() for tag in tags if tag.strip()]
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("INSERT INTO blog (title, content, author, user_id) VALUES (?, ?, ?, ?)", (title, content, author, current_user.id))
        blog_id = cur.lastrowid
        cur.execute("INSERT INTO img (id, url) VALUES (?, ?)", (blog_id, img_url))
        for tag in tags:
            cur.execute("SELECT id FROM tags WHERE tag = ?", (tag,))
            tag_row = cur.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                cur.execute("INSERT INTO tags (tag) VALUES (?)", (tag,))
                tag_id = cur.lastrowid
            cur.execute("INSERT INTO blog_tags (blog_id, tag_id) VALUES (?, ?)", (blog_id, tag_id))
        con.commit()
        con.close()
        return render_template('sucess.html', status="published")
    else:
        html = render_template("submit.html")
        return html
    
@app.route("/dashboard")
@login_required
def dashboard():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT id, title,author, created_at FROM blog WHERE user_id = ? ORDER BY created_at DESC", (current_user.id,))
    blogs = cur.fetchall()
    con.close()
    html = render_template("dash_board.html", blogs = blogs, current_user = current_user)
    return html

@app.route("/delete", methods = ["POST"])
@login_required
def delete():
    blog_id = request.form.get("id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("DELETE FROM blog WHERE id = ?", (blog_id,))
    cur.execute("DELETE FROM img WHERE id = ?", (blog_id,))
    cur.execute("DELETE FROM comments WHERE id = ?", (blog_id,))
    cur.execute("DELETE FROM blog_tags WHERE blog_id = ?", (blog_id,))
    con.commit()
    con.close()
    return redirect(url_for("dashboard"))

@app.route("/edit", methods = ["GET", "POST"])
@login_required
def edit():
    blog_id = request.args.get("id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT title, content, author FROM blog WHERE id = ?", (blog_id,))
    blog = cur.fetchone()
    cur.execute("SELECT url FROM img WHERE id = ?", (blog_id,))
    img = cur.fetchone()
    cur.execute("""
                SELECT t.tag
                FROM blog_tags bt
                JOIN tags t ON bt.tag_id = t.id
                WHERE bt.blog_id = ?
                ORDER BY t.tag;
                """, (blog_id,))
    tags = cur.fetchall()
    tags = [tag[0] for tag in tags]
    cur.execute("SELECT comment, name, comment_id FROM comments WHERE id = ?", (blog_id,))
    comments = cur.fetchall()
    con.close()
    
    html = render_template("edit.html", blog = blog, img = img[0], blog_id = blog_id, tags = ", ".join(tags), comments = comments)
    return html

@app.route("/update", methods = ["POST"])
@login_required
def update():
    blog_id = request.form.get("id")
    title = request.form.get("title")
    content = request.form.get("content")
    author = request.form.get("author")
    img_url = request.form.get("img_url")
    tags = request.form.get("tags").split(",")
    tags = [tag.strip() for tag in tags if tag.strip()]
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("UPDATE blog SET title = ?, content = ?, author = ? WHERE id = ?", (title, content, author, blog_id))
    cur.execute("UPDATE img SET url = ? WHERE id = ?", (img_url, blog_id))
    cur.execute("DELETE FROM blog_tags WHERE blog_id = ?", (blog_id,))
    for tag in tags:
        cur.execute("SELECT id FROM tags WHERE tag = ?", (tag,))
        tag_row = cur.fetchone()
        if tag_row:
            tag_id = tag_row[0]
        else:
            cur.execute("INSERT INTO tags (tag) VALUES (?)", (tag,))
            tag_id = cur.lastrowid
        cur.execute("INSERT INTO blog_tags (blog_id, tag_id) VALUES (?, ?)", (blog_id, tag_id))
    con.commit()
    con.close()
    return render_template('sucess.html', status="updated") 
    
@app.route("/delete_comment", methods = ["POST"])
@login_required
def delete_comment():
    comment_id = request.form.get("comment_id")
    blog_id = request.form.get("blog_id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("DELETE FROM comments WHERE comment_id = ?", (comment_id,))
    con.commit()
    con.close()
    return redirect(url_for("edit") + f"?id={blog_id}")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    msg = '' 

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(id=user_data['id'], username=user_data['username'], password=user_data['password'])
            login_user(user)
            return redirect(url_for('dashboard'))
        
        msg = 'Invalid username or password'
    
    return render_template('login.html', msg=msg)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Password does not match.')
            signup_msg = 'Password does not match.'
            return render_template('signup.html', signup_msg = signup_msg)
        
        if ' ' in username or ' ' in password:
            flash('Username and password must not contain spaces')
            signup_msg = 'Username and password must not contain spaces'
            return render_template('signup.html', signup_msg = signup_msg)
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Account created successfully! Please log in.')
            signup_msg = ""
            conn = get_db_connection()
            user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            if user_data and check_password_hash(user_data['password'], password):
                user = User(id=user_data['id'], username=user_data['username'], password=user_data['password'])
                login_user(user)
                return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.')
            signup_msg = 'Username already exists. Please choose a different one.'
            return render_template('signup.html', signup_msg = signup_msg)
        finally:
            conn.close()
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/search")
def search():
    q = request.args.get("q")
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    blogs = []
    if q:
        cur.execute("SELECT id, title FROM blog WHERE title LIKE ? LIMIT 5", ('%' + q + '%' , ))
        rows = cur.fetchall()
        for row in rows:
            blogs.append({'id':row['id'], 'title':row['title']})
            
    return jsonify(blogs)

@app.route("/search_blog")
def search_blog():
    q = request.args.get("q")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT id, url FROM img")
    imgs = cur.fetchall()
    img_dict = {img[0]: img[1] for img in imgs}
    cur.execute("SELECT id, title, content, author FROM blog WHERE title LIKE ? ORDER BY created_at DESC", ('%' + q + '%' , ))
    blogs = cur.fetchall() 
    all_ids = [blog[0] for blog in blogs]
    cur.execute("""
                SELECT t.tag, bt.blog_id
                FROM blog_tags bt
                JOIN tags t ON bt.tag_id = t.id
                ORDER BY t.tag, bt.blog_id;
                """)
    tags = cur.fetchall()
    
    cur.execute("SELECT blog_tags.blog_id, tags.tag FROM blog_tags JOIN tags ON blog_tags.tag_id = tags.id")
    blog_tags = cur.fetchall()
    blog_tags_dict = defaultdict(list)
    for blog_id, tag in blog_tags:
        blog_tags_dict[blog_id].append(tag)
    con.close()

    tags_dict = defaultdict(list)
    for tag, blog_id in tags:
        tags_dict[tag].append(blog_id)
    print(tags_dict)
    html = render_template("search_res.html", blogs = blogs, tags_dict = tags_dict, all_ids = all_ids, img_dict = img_dict, blog_tags_dict = blog_tags_dict, current_user = current_user)
    return html
    
if __name__ == "__main__":
    init_db()
    app.run(debug = True)