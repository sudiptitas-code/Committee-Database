from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = "committee.db"

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS committees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            reference_no TEXT UNIQUE,
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

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Dashboard ----------
@app.route('/')
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # Total committees
    cursor.execute("SELECT COUNT(*) FROM committees")
    total_committees = cursor.fetchone()[0]

    # Collect unique members
    cursor.execute("""
        SELECT convener, member1, member2, member3, secretary FROM committees
    """)
    rows = cursor.fetchall()

    members = set()
    for row in rows:
        for member in row:
            if member and member.strip() != "":
                members.add(member.strip())

    total_members = len(members)

    conn.close()

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        "dashboard.html",
        total_committees=total_committees,
        total_members=total_members,
        current_datetime=current_datetime
    )

# ---------- Add Record ----------
@app.route('/add')
def add_page():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO committees 
            (subject, reference_no, date, convener, member1, member2, member3, secretary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['subject'],
            request.form['reference'],
            request.form['date'],
            request.form['convener'],
            request.form['member1'],
            request.form['member2'],
            request.form['member3'],
            request.form['secretary']
        ))

        conn.commit()
        flash("Record saved successfully!")

    except sqlite3.IntegrityError:
        flash("Reference number already exists!")

    conn.close()
    return redirect(url_for('dashboard'))

# ---------- Search ----------
@app.route('/search')
def search_page():
    return render_template("search.html")

@app.route('/api/search')
def search():
    query = request.args.get('q', '')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM committees
        WHERE subject LIKE ?
        OR reference_no LIKE ?
        OR convener LIKE ?
        OR member1 LIKE ?
        OR member2 LIKE ?
        OR member3 LIKE ?
        OR secretary LIKE ?
    """, tuple([f"%{query}%"] * 7))

    rows = cursor.fetchall()
    conn.close()

    results = [dict(row) for row in rows]
    return jsonify(results)

# ---------- Delete ----------
@app.route('/delete/<ref_no>')
def delete_record(ref_no):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM committees WHERE reference_no = ?", (ref_no,))
    conn.commit()
    conn.close()

    flash("Record deleted successfully!")
    return redirect(url_for('search_page'))

# ---------- Edit ----------
@app.route('/edit/<ref_no>')
def edit_record(ref_no):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM committees WHERE reference_no = ?", (ref_no,))
    record = cursor.fetchone()
    conn.close()

    if not record:
        flash("Record not found!")
        return redirect(url_for('search_page'))

    return render_template("edit.html", data=dict(record))

@app.route('/update/<ref_no>', methods=['POST'])
def update_record(ref_no):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE committees
        SET subject=?, date=?, convener=?, member1=?, member2=?, member3=?, secretary=?
        WHERE reference_no=?
    """, (
        request.form['subject'],
        request.form['date'],
        request.form['convener'],
        request.form['member1'],
        request.form['member2'],
        request.form['member3'],
        request.form['secretary'],
        ref_no
    ))

    conn.commit()
    conn.close()

    flash("Record updated successfully!")
    return redirect(url_for('search_page'))

# ---------- Run ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)