from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# ── Database Configuration ──────────────────────────────────────────────────
# Change these values to match your MySQL setup
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',   # <-- Change this
    'database': 'expense_tracker'
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ── Home Page ────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get filter values from URL
    filter_category = request.args.get('category', '')
    filter_date     = request.args.get('date', '')

    # Build query based on filters
    query  = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if filter_category:
        query += " AND category = %s"
        params.append(filter_category)

    if filter_date:
        query += " AND date = %s"
        params.append(filter_date)

    query += " ORDER BY date DESC"

    cursor.execute(query, params)
    expenses = cursor.fetchall()

    # Total spending (filtered)
    total = sum(e['amount'] for e in expenses)

    # Category totals for chart
    cursor.execute(
        "SELECT category, SUM(amount) as total FROM expenses GROUP BY category"
    )
    category_totals = cursor.fetchall()

    # All categories for filter dropdown
    cursor.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
    categories = [row['category'] for row in cursor.fetchall()]

    # Monthly summary
    cursor.execute("""
        SELECT DATE_FORMAT(date, '%b %Y') as month, SUM(amount) as total
        FROM expenses
        GROUP BY DATE_FORMAT(date, '%Y-%m')
        ORDER BY MIN(date) DESC
        LIMIT 6
    """)
    monthly = cursor.fetchall()

    db.close()

    return render_template('index.html',
        expenses        = expenses,
        total           = total,
        category_totals = category_totals,
        categories      = categories,
        monthly         = monthly,
        filter_category = filter_category,
        filter_date     = filter_date
    )


# ── Add Expense ──────────────────────────────────────────────────────────────
@app.route('/add', methods=['POST'])
def add_expense():
    title    = request.form['title']
    amount   = request.form['amount']
    category = request.form['category']
    date     = request.form['date']
    note     = request.form.get('note', '')

    db     = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO expenses (title, amount, category, date, note) VALUES (%s, %s, %s, %s, %s)",
        (title, amount, category, date, note)
    )
    db.commit()
    db.close()

    return redirect(url_for('index'))


# ── Delete Expense ───────────────────────────────────────────────────────────
@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    db     = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    db.commit()
    db.close()

    return redirect(url_for('index'))


# ── Edit Expense (load data) ─────────────────────────────────────────────────
@app.route('/get/<int:expense_id>')
def get_expense(expense_id):
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
    expense = cursor.fetchone()
    db.close()

    if expense:
        expense['date'] = str(expense['date'])
        expense['amount'] = float(expense['amount'])
        return jsonify(expense)
    return jsonify({'error': 'Not found'}), 404


# ── Update Expense ───────────────────────────────────────────────────────────
@app.route('/update', methods=['POST'])
def update_expense():
    expense_id = request.form['id']
    title      = request.form['title']
    amount     = request.form['amount']
    category   = request.form['category']
    date       = request.form['date']
    note       = request.form.get('note', '')

    db     = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE expenses SET title=%s, amount=%s, category=%s, date=%s, note=%s WHERE id=%s",
        (title, amount, category, date, note, expense_id)
    )
    db.commit()
    db.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)