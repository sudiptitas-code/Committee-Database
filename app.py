import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ===============================
# DATABASE CONFIGURATION
# ===============================
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
    total_committees = cursor.fetchone()[0]

    cursor.execute("SELECT member1, member2, member3, secretary FROM committees")
    rows = cursor.fetchall()
    members = []
    for row in rows:
        members.extend([row['member1'], row['member2'], row['member3'], row['secretary']])
    total_members = len(set([m for m in members if m]))

    current_datetime = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    conn.close()

    return render_template(
        'dashboard.html',
        total_committees=total_committees,
        total_members=total_members,
        current_datetime=current_datetime
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
            request.form.get('member1',''),
            request.form.get('member2',''),
            request.form.get('member3',''),
            request.form.get('secretary','')
        ))

        conn.commit()
        conn.close()
        flash("Committee added successfully!")
        return redirect(url_for('dashboard'))

    return render_template('index.html')


# ===============================
# SEARCH PAGE
# ===============================
@app.route('/search')
def search_page():
    return render_template('search.html')


# ===============================
# LIVE SEARCH API
# ===============================
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT * FROM committees
            WHERE 
                subject LIKE ? OR
                reference_no LIKE ? OR
                convener LIKE ? OR
                member1 LIKE ? OR
                member2 LIKE ? OR
                member3 LIKE ? OR
                secretary LIKE ?
        """, tuple(['%' + query + '%'] * 7))
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
    else:
        results = []

    conn.close()
    return jsonify(results)


# ===============================
# EDIT
# ===============================
@app.route('/edit/<int:id>', methods=['GET'])
def edit(id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM committees WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Record not found!")
        return redirect(url_for('search_page'))

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
        request.form.get('member1',''),
        request.form.get('member2',''),
        request.form.get('member3',''),
        request.form.get('secretary',''),
        id
    ))

    conn.commit()
    conn.close()
    flash("Record updated successfully!")
    return redirect(url_for('search_page'))


# ===============================
# DELETE
# ===============================
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM committees WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Record deleted successfully!")
    return redirect(url_for('search_page'))


# ===============================
# EXPORT DATABASE TO EXCEL
# ===============================
@app.route('/export')
def export_excel():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM committees", conn)
    conn.close()

    file_path = "committee_export.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)


# ===============================
# IMPORT EXCEL TO DATABASE
# ===============================
@app.route('/import', methods=['POST'])
def import_excel():
    file = request.files.get('file')
    if not file:
        flash("No file selected!")
        return redirect(url_for('dashboard'))

    df = pd.read_excel(file)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO committees
            (subject, reference_no, date, convener, member1, member2, member3, secretary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get('subject',''),
            row.get('reference_no',''),
            row.get('date',''),
            row.get('convener',''),
            row.get('member1',''),
            row.get('member2',''),
            row.get('member3',''),
            row.get('secretary','')
        ))

    conn.commit()
    conn.close()
    flash("Excel data imported successfully!")
    return redirect(url_for('dashboard'))


# ===============================
# MAIN
# ===============================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)