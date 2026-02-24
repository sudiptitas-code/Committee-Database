from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = "committee.db"


# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Initialize Database
# -----------------------------
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS committees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            reference_no TEXT NOT NULL,
            date TEXT NOT NULL,
            convener TEXT,
            member1 TEXT,
            member2 TEXT,
            member3 TEXT,
            secretary TEXT
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# -----------------------------
# Dashboard
# -----------------------------
@app.route('/')
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    committees = conn.execute('SELECT * FROM committees').fetchall()

    committee_count = len(committees)

    members = set()
    for row in committees:
        for key in ['convener', 'member1', 'member2', 'member3', 'secretary']:
            if row[key]:
                members.add(row[key])

    unique_members = len(members)

    conn.close()

    return render_template(
        'dashboard.html',
        total_committees=committee_count,
        total_members=unique_members,
        current_datetime=datetime.now().strftime("%d %B %Y, %I:%M %p")
    )


# -----------------------------
# Add Committee
# -----------------------------
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        subject = request.form['subject']
        reference_no = request.form['reference_no']
        date = request.form['date']
        convener = request.form['convener']
        member1 = request.form['member1']
        member2 = request.form['member2']
        member3 = request.form['member3']
        secretary = request.form['secretary']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO committees 
            (subject, reference_no, date, convener, member1, member2, member3, secretary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (subject, reference_no, date, convener, member1, member2, member3, secretary))
        conn.commit()
        conn.close()

        flash("Committee added successfully!")
        return redirect(url_for('search'))

    return render_template('index.html')


# -----------------------------
# Search
# -----------------------------
@app.route('/search')
def search():
    query = request.args.get('q', '')

    conn = get_db_connection()

    if query:
        rows = conn.execute('''
            SELECT * FROM committees
            WHERE subject LIKE ?
            OR reference_no LIKE ?
        ''', (f'%{query}%', f'%{query}%')).fetchall()
    else:
        rows = conn.execute('SELECT * FROM committees').fetchall()

    conn.close()
    return render_template('search.html', rows=rows)


# -----------------------------
# Edit
# -----------------------------
@app.route('/edit/<int:id>')
def edit(id):
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM committees WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', data=data)


# -----------------------------
# Update
# -----------------------------
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    subject = request.form['subject']
    reference_no = request.form['reference_no']
    date = request.form['date']
    convener = request.form['convener']
    member1 = request.form['member1']
    member2 = request.form['member2']
    member3 = request.form['member3']
    secretary = request.form['secretary']

    conn = get_db_connection()
    conn.execute('''
        UPDATE committees SET
            subject = ?,
            reference_no = ?,
            date = ?,
            convener = ?,
            member1 = ?,
            member2 = ?,
            member3 = ?,
            secretary = ?
        WHERE id = ?
    ''', (subject, reference_no, date, convener, member1, member2, member3, secretary, id))

    conn.commit()
    conn.close()

    flash("Record updated successfully!")
    return redirect(url_for('search'))


# -----------------------------
# Delete
# -----------------------------
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM committees WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash("Record deleted successfully!")
    return redirect(url_for('search'))


if __name__ == '__main__':
    app.run(debug=True)
