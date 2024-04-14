from flask import Flask, render_template, request, redirect, url_for, flash ,session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
librarian_log_indetails={"admin":"admindapunda"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/userlogin')
def userlogin():
    return render_template('user_login.html')

@app.route('/adminlogin')
def adminlogin():
    return render_template('admin_login.html')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS userinfo (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS section (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, datecreate DATE, description LONGTEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS userbooks (id INTEGER PRIMARY KEY AUTOINCREMENT ,username TEXT ,booktitle TEXT,author TEXT,issued DATE, return DATE,section_id INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS books (booktitle TEXT PRIMARY KEY,content TEXT,author TEXT,section_id INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS request (id INTEGER PRIMARY KEY AUTOINCREMENT, booktitle TEXT, username TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS admingranted (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, booktitle TEXT,issued DATE, return DATE)')

    conn.close()

def add_user(username, password):
    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def add_userinfo(username,password):
    conn = get_db_connection()
    conn.execute('INSERT INTO userinfo (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def user_exists(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    print(user)
    return user is not None

def verify_login(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return user is not None

def verify_userlogin(username,password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM userinfo WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    return user is not None

@app.route('/admin_loginfn', methods=['GET', 'POST'])
def admin_loginfn():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if request.form['action'] == 'Login':
            if verify_login(username, password):
                session[username] = username
                 #   flash('Login successful!', 'success')
                return redirect(url_for('librarian_dashboard'))
                # librarian_dashboard()
            else:
                flash('Invalid username or password. Please try again.', 'error')
                return render_template('admin_login.html')
        elif request.form['action'] == 'Register':
            add_user(username,password)
            flash('Registration Successful','success')
            
    return render_template('admin_login.html')

@app.route('/user_loginfn',methods=['GET','POST'])
def user_loginfn():
    if request.method =='POST':
        username = request.form['username']
        password = request.form['password']
        if request.form['action'] == 'Login':
            if verify_userlogin(username,password):
                return redirect(url_for('user_dashboard',username=username))
            else:
                flash('Invalid username or password. Please try again.', 'error')
                return render_template('user_login.html')
        elif request.form['action'] == 'Register':
            add_userinfo(username,password)
            flash('Registration successful', ' success')
        return render_template('user_login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('index.html')

@app.route('/stats_page')
def stats_page():
    return render_template('admin_stats.html')


@app.route('/librarian_dashboard')
def librarian_dashboard():
    conn = get_db_connection()
    sections = conn.execute('SELECT * FROM section').fetchall()
    conn.close()
    return render_template('librarian_dashboard.html', sections=sections)

@app.route('/user_dashboard')
def user_dashboard():
    username = request.args.get('username')
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('user_dashboard.html',books=books,username=username)

@app.route('/add_section', methods=['POST'])
def add_section():
    if request.method == 'POST':
        section_name = request.form['section_name']
        section_description = request.form['section_description']
        current_date = datetime.now().date().strftime('%Y-%m-%d')
        conn = get_db_connection()
        conn.execute('INSERT INTO section (name, datecreate, description) VALUES (?, ?, ?)', (section_name, current_date, section_description))
        conn.commit()
        conn.close()
        return redirect(url_for('librarian_dashboard'))

@app.route('/section_books/<int:section_id>')
def section_books(section_id):
    #print(section_id)  # Print the section_id for debugging
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books WHERE section_id = ?', (section_id,)).fetchall()
    conn.close()
    print(books)
    return render_template('section_books.html', section_id=section_id, books=books)

@app.route('/add_book', methods=['POST'])
def add_book():
    if request.method == 'POST':
        section_id = request.form['section_id']
        book_title = request.form['book_title']
        book_author = request.form['book_author']
        content = request.form['content']
        conn = get_db_connection()
        conn.execute('INSERT INTO books (section_id, booktitle, author, content) VALUES (?, ?, ?, ?)',
                     (section_id, book_title, book_author,content))
        conn.commit()
        conn.close()
        return redirect(url_for('section_books', section_id=section_id))

@app.route('/user_requests',methods=['POST','GET'])
def user_requests():
    if request.method == 'POST':
        booktitle = request.form.get('booktitle')
        username = request.form.get('username')
        conn = get_db_connection()
        conn.execute('INSERT INTO request (booktitle, username) VALUES (?, ?)', (booktitle, username))
        conn.commit()
        conn.close()
    return redirect(url_for('user_dashboard', username=username))

@app.route('/requests')
def requests():
    conn = get_db_connection()
    requests = conn.execute('SELECT * FROM request').fetchall()
    grants = conn.execute('SELECT * FROM admingranted').fetchall()
    conn.close()
    return render_template('admin_requests.html',requests=requests,grants=grants)


@app.route('/permissions', methods=['POST'])
def permissions():
    if request.method == 'POST':
        req_id = request.form.get('request_id')
        action = request.form.get('action')
        book_title = request.form.get('booktitle')
        username = request.form.get('username')
        
        print(book_title)
        print(username)
        
        conn = get_db_connection()
        
        if action == 'grant':
            # Retrieve author and section_id from the database
            author_row = conn.execute('SELECT author FROM books WHERE booktitle = ?', (book_title,)).fetchone()
            author = author_row[0] if author_row else None
            section_id_row = conn.execute('SELECT section_id FROM books WHERE booktitle = ?', (book_title,)).fetchone()
            section_id = section_id_row[0] if section_id_row else None
            
            issue_date = datetime.now().date().strftime('%Y-%m-%d')
            return_date = (datetime.now() + timedelta(days=7)).date().strftime('%Y-%m-%d')
            
            
            conn.execute('INSERT INTO userbooks (booktitle, username, author, issued, return, section_id) VALUES (?, ?, ?, ?, ?, ?)',
                         (book_title, username, author, str(issue_date), str(return_date), section_id))
            conn.commit()
            
            conn.execute('INSERT INTO admingranted (booktitle, username, issued, return) VALUES (?, ?, ?, ?)',
                         (book_title, username, str(issue_date), str(return_date)))
            conn.commit()
        
        conn.execute('DELETE FROM request WHERE id = ?', (req_id,))
        conn.commit()
        conn.close()
        
    return redirect(url_for('requests'))

@app.route('/user_books',methods=['GET','POST'])
def user_books():
    conn= get_db_connection()
    if request.method == 'POST':
        username = request.form.get('username')
    else:
        username = request.args.get('username')
    print(username)
    userbooks = conn.execute('SELECT * FROM userbooks WHERE username= ? ',(username,)).fetchall()
    conn.close()
    return render_template('user_books.html',userbooks=userbooks,username=username)

@app.route('/return_book',methods=['POST'])
def return_book():
    conn= get_db_connection()
    booktitle = request.form.get('booktitle')
    username = request.form.get('username')
    reqid= request.form.get('id')
    conn.execute('DELETE FROM userbooks where id=?',(reqid,))
    conn.commit()
    conn.execute('DELETE FROM admingranted where username=? AND booktitle=?',(username,booktitle,))
    conn.commit()
    conn.close() 
    return redirect(url_for('user_books',username=username))

@app.route('/revoke_book',methods=['POST'])
def revoke_book():
    if request.method=='POST':
        conn= get_db_connection()
        booktitle = request.form.get('booktitle')
        username = request.form.get('username')
        print(booktitle,username)
        reqid= request.form.get('id')
        conn.execute('DELETE FROM userbooks where id=?',(reqid,))
        conn.commit()
        conn.execute('DELETE FROM admingranted where username=? AND booktitle=?',(username,booktitle,))
        conn.commit()
        conn.close() 
    return redirect(url_for('requests'))


if __name__ == '__main__':
    create_table()
    app.run(debug=True)

