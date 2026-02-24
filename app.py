import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =====================================
# DATABASE CONFIGURATION
# =====================================

# If using Render Persistent Disk:
# Set environment variable DATABASE_URL = /data/committee.db
DATABASE = os.environ.get("DATABASE_URL", "committee.db")


# =====================================
# DATABASE INITIALIZATION
# =====================================

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
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


# 🔥 IMPORTANT: Run DB creation when app starts (for Render)
with app.app_context():
    init_db()


# =====================================
# DASHBOARD
# =====================================

@app.route('/')
def dashboard():
    conn = get_connection()
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


# =====================================
# ADD COMMITTEE
# =====================================

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO committees 
                (subject, reference_no, date, convener, member1, member2, member3, secretary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form.get('subject'),
                request.form.get('reference_no'),
                request.form.get('date'),
                request.form.get('convener'),
                request.form.get('member1'),
                request.form.get('member2'),
                request.form.get('member3'),
                request.form.get('secretary')
            ))

            conn.commit()
            conn.close()

            flash("Committee added successfully!")
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for('add'))

    return render_template('add.html')


# =====================================
# SEARCH PAGE
# =====================================

@app.route('/search')
def search():
    return render_template('search.html')


# =====================================
# LIVE SEARCH API
# =====================================

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()

    conn = get_connection()
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT * FROM committees
            WHERE subject LIKE ?
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

    return jsonify({"results": results})


# =====================================
# EDIT
# =====================================

@app.route('/edit/<int:id>')
def edit(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM committees WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Record not found!")
        return redirect(url_for('search'))

    return render_template('edit.html', data=dict(row))


# =====================================
# UPDATE
# =====================================

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    conn = get_connection()
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
        request.form.get('subject'),
        request.form.get('reference_no'),
        request.form.get('date'),
        request.form.get('convener'),
        request.form.get('member1'),
        request.form.get('member2'),
        request.form.get('member3'),
        request.form.get('secretary'),
        id
    ))

    conn.commit()
    conn.close()

    flash("Record updated successfully!")
    return redirect(url_for('search'))


# =====================================
# DELETE
# =====================================

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM committees WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Record deleted successfully!")
    return redirect(url_for('search'))


# =====================================
# EXPORT TO EXCEL
# =====================================

@app.route('/export')
def export_excel():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM committees", conn)
    conn.close()

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name="committees.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =====================================
# IMPORT EXCEL
# =====================================

@app.route('/import', methods=['GET', 'POST'])
def import_excel():
    if request.method == 'POST':

        file = request.files.get('file')

        if not file:
            flash("No file selected!")
            return redirect(url_for('import_excel'))

        try:
            df = pd.read_excel(file)

            conn = get_connection()
            cursor = conn.cursor()

            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO committees
                    (subject, reference_no, date, convener, member1, member2, member3, secretary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('subject', ''),
                    row.get('reference_no', ''),
                    row.get('date', ''),
                    row.get('convener', ''),
                    row.get('member1', ''),
                    row.get('member2', ''),
                    row.get('member3', ''),
                    row.get('secretary', '')
                ))

            conn.commit()
            conn.close()

            flash("Excel imported successfully!")
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f"Import error: {str(e)}")
            return redirect(url_for('import_excel'))

    return render_template('import.html')