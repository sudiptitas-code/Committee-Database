import os
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL not set in environment variables")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS committees (
            id SERIAL PRIMARY KEY,
            subject TEXT,
            reference_no TEXT,
            date TEXT,
            convener TEXT,
            member1 TEXT,
            member2 TEXT,
            member3 TEXT,
            secretary TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

with app.app_context():
    init_db()

# ================= DASHBOARD =================

@app.route('/')
def dashboard():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM committees")
    rows = cur.fetchall()

    total_committees = len(rows)

    members = []
    growth_data = {}

    for row in rows:
        members.extend([
            row['member1'],
            row['member2'],
            row['member3'],
            row['secretary']
        ])

        if row['date']:
            month = row['date'][:7]
            growth_data[month] = growth_data.get(month, 0) + 1

    total_members = len(set([m for m in members if m]))

    sorted_growth = dict(sorted(growth_data.items()))

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_committees=total_committees,
        total_members=total_members,
        growth_labels=list(sorted_growth.keys()),
        growth_values=list(sorted_growth.values())
    )

# ================= MEMBER ANALYTICS =================

@app.route('/members')
def member_analytics():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT member1, member2, member3, secretary FROM committees")
    rows = cur.fetchall()

    member_count = {}

    for row in rows:
        for member in [row['member1'], row['member2'], row['member3'], row['secretary']]:
            if member:
                member_count[member] = member_count.get(member, 0) + 1

    sorted_members = dict(sorted(member_count.items(), key=lambda x: x[1], reverse=True))

    cur.close()
    conn.close()

    return render_template("members.html", members=sorted_members)

# ================= ADD =================

@app.route('/add', methods=['GET','POST'])
def add():
    if request.method == 'POST':
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO committees
            (subject, reference_no, date, convener, member1, member2, member3, secretary)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form.get('subject',''),
            request.form.get('reference_no',''),
            request.form.get('date',''),
            request.form.get('convener',''),
            request.form.get('member1',''),
            request.form.get('member2',''),
            request.form.get('member3',''),
            request.form.get('secretary','')
        ))

        conn.commit()
        cur.close()
        conn.close()

        flash("Committee added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template("add.html")

# ================= SEARCH =================

@app.route('/search')
def search():
    return render_template("search.html")

@app.route('/api/search')
def api_search():
    query = request.args.get('q','')

    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT * FROM committees
        WHERE subject ILIKE %s
        OR reference_no ILIKE %s
        OR convener ILIKE %s
        OR member1 ILIKE %s
        OR member2 ILIKE %s
        OR member3 ILIKE %s
        OR secretary ILIKE %s
        ORDER BY id DESC
    """, tuple(['%'+query+'%']*7))

    results = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(results)

# ================= EDIT =================

@app.route('/edit/<int:id>')
def edit(id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM committees WHERE id=%s",(id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        flash("Record not found","danger")
        return redirect(url_for('search'))

    return render_template("edit.html", data=row)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE committees SET
            subject=%s,
            reference_no=%s,
            date=%s,
            convener=%s,
            member1=%s,
            member2=%s,
            member3=%s,
            secretary=%s
        WHERE id=%s
    """,(
        request.form.get('subject',''),
        request.form.get('reference_no',''),
        request.form.get('date',''),
        request.form.get('convener',''),
        request.form.get('member1',''),
        request.form.get('member2',''),
        request.form.get('member3',''),
        request.form.get('secretary',''),
        id
    ))

    conn.commit()
    cur.close()
    conn.close()

    flash("Updated successfully!","success")
    return redirect(url_for('search'))

# ================= DELETE =================

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM committees WHERE id=%s",(id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Deleted successfully!","warning")
    return redirect(url_for('search'))

# ================= EXPORT =================

@app.route('/export')
def export_excel():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM committees", conn)
    conn.close()

    output = BytesIO()
    df.to_excel(output,index=False)
    output.seek(0)

    return send_file(output,download_name="committees.xlsx",as_attachment=True)

# ================= IMPORT =================

@app.route('/import', methods=['GET','POST'])
def import_excel():
    if request.method == 'POST':
        file = request.files.get('file')
        df = pd.read_excel(file)

        conn = get_connection()
        cur = conn.cursor()

        for _,row in df.iterrows():
            cur.execute("""
                INSERT INTO committees
                (subject, reference_no, date, convener, member1, member2, member3, secretary)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,(
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
        cur.close()
        conn.close()

        flash("Excel imported successfully!","success")
        return redirect(url_for('dashboard'))

    return render_template("import.html")

if __name__ == "__main__":
    app.run(debug=True)