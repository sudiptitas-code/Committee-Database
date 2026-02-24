import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ===============================
# DATABASE CONFIGURATION
# ===============================

# For Render Persistent Disk use:
# DATABASE = "/data/committee.db"

DATABASE = "committee.db"


# ===============================
# DATABASE INITIALIZATION
# ===============================

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS committees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            reference_no TEXT,
            date TEXT,
            convener TEXT,
            member1 TEXT,
            member2 TEXT,
            member3 TEXT,
            secretary TEXT
        )
    """)

    conn.commit()
    conn.close()


# ===============================
# DASHBOARD
# ===============================

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM committees")
    committee_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT member1, member2, member3, secretary FROM committees
    """)
    rows = cursor.fetchall()

    members = []
    for row in rows:
        members.extend([row['member1'], row['member2'], row['member3'], row['secretary']])

    unique_members = len(set([m for m in members if m]))

    current_time = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    conn.close()

    return render_template(
        'dashboard.html',
        committee_count=committee_count,
        member_count=unique_members,
        current_time=current_time
    )


# ===============================
# ADD COMMITTEE
# ===============================

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO committees 
            (subject, reference_no, date, convener, member1, member2, member3, secretary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['subject'],
            request.form['reference_no'],
            request.form['date'],
            request.form['convener'],
            request.form['member1'],
            request.form['member2'],
            request.form['member3'],
            request.form['secretary']
        ))

        conn.commit()
        conn.close()

        flash("Committee added successfully!")
        return redirect(url_for('dashboard'))

    return render_template('add.html')


# ===============================
# SEARCH
# ===============================

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT * FROM committees
            WHERE 
                subject LIKE ?
                OR reference_no LIKE ?
                OR convener LIKE ?
                OR member1 LIKE ?
                OR member2 LIKE ?
                OR member3 LIKE ?
                OR secretary LIKE ?
        """, tuple(['%' + query + '%'] * 7))

        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
    else:
        results = []

    conn.close()

    return render_template('search.html', results=results)


# ===============================
# EDIT
# ===============================

@app.route('/edit/<int:id>')
def edit(id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM committees WHERE id=?", (id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        flash("Record not found!")
        return redirect(url_for('search'))

    return render_template('edit.html', data=dict(row))


# ===============================
# UPDATE
# ===============================

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE committees SET
            subject=?,
            reference_no=?,
            date=?,
            convener=?,
            member1=?,
            member2=?,
            member3=?,
            secretary=?
        WHERE id=?
    """, (
        request.form['subject'],
        request.form['reference_no'],
        request.form['date'],
        request.form['convener'],
        request.form['member1'],
        request.form['member2'],
        request.form['member3'],
        request.form['secretary'],
        id
    ))

    conn.commit()
    conn.close()

    flash("Record updated successfully!")
    return redirect(url_for('search'))


# ===============================
# DELETE (SAFE POST)
# ===============================

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM committees WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Record deleted successfully!")
    return redirect(url_for('search'))


# ===============================
# MAIN
# ===============================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
