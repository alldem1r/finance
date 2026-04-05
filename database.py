import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class FinanceDatabase:
    def __init__(self, db_path: str = "finance_vault.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Students table - updated for hourly rate system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    hourly_rate REAL NOT NULL,
                    agreed_hours INTEGER NOT NULL,
                    lessons_conducted INTEGER DEFAULT 0,
                    start_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Payments table - enhanced with bank account linking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    amount_paid REAL NOT NULL,
                    date DATE NOT NULL,
                    bank_account TEXT,
                    is_prepayment BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id),
                    FOREIGN KEY (bank_account) REFERENCES bank_accounts (bank_name)
                )
            ''')

            # Income entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS income_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Expense entries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expense_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Bank accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT NOT NULL UNIQUE,
                    balance REAL NOT NULL DEFAULT 0,
                    currency TEXT NOT NULL DEFAULT 'KZT',
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert default bank accounts if they don't exist
            cursor.execute('''
                INSERT OR IGNORE INTO bank_accounts (bank_name, balance, currency)
                VALUES
                    ('Kaspi', 0, 'KZT'),
                    ('Freedom', 0, 'KZT'),
                    ('Halyk', 0, 'KZT')
            ''')

            # Bank transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT NOT NULL, -- 'deposit', 'withdrawal', 'transfer_in', 'transfer_out'
                    description TEXT,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_name) REFERENCES bank_accounts (bank_name)
                )
            ''')

            # Budgets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    budget_amount REAL NOT NULL,
                    month_year TEXT NOT NULL, -- Format: 'YYYY-MM'
                    spent_amount REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, month_year)
                )
            ''')

            # Goals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    target_amount REAL NOT NULL,
                    current_amount REAL DEFAULT 0,
                    target_date DATE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Recurring transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL, -- 'income' or 'expense'
                    category TEXT NOT NULL,
                    frequency TEXT NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
                    next_date DATE NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Lessons conducted table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lessons_conducted (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    lesson_date DATE NOT NULL,
                    duration_hours REAL DEFAULT 1,
                    topic TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )
            ''')

            conn.commit()

    # Student operations - updated for hourly rate system
    def add_student(self, name: str, course_name: str, hourly_rate: float, agreed_hours: int, start_date: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO students (name, course_name, hourly_rate, agreed_hours, start_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, course_name, hourly_rate, agreed_hours, start_date))
            conn.commit()
            return cursor.lastrowid

    def get_all_students(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students ORDER BY created_at DESC')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_student_with_debt(self, student_id: int) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get student info
            cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
            student_row = cursor.fetchone()
            if not student_row:
                return None

            columns = [desc[0] for desc in cursor.description]
            student = dict(zip(columns, student_row))

            # Calculate total potential earnings (hourly_rate * lessons_conducted)
            total_earnings = student['hourly_rate'] * student['lessons_conducted']

            # Get total payments made
            cursor.execute('SELECT SUM(amount_paid) FROM payments WHERE student_id = ?', (student_id,))
            payment_row = cursor.fetchone()
            total_paid = payment_row[0] if payment_row[0] else 0

            # Get prepayments
            cursor.execute('SELECT SUM(amount_paid) FROM payments WHERE student_id = ? AND is_prepayment = 1', (student_id,))
            prepayment_row = cursor.fetchone()
            total_prepayments = prepayment_row[0] if prepayment_row[0] else 0

            # Calculate debt: what student owes us (earnings - payments received)
            # Positive debt means student owes us money
            # Negative debt means we owe student money (overpaid)
            student['total_earnings'] = total_earnings
            student['total_paid'] = total_paid
            student['total_prepayments'] = total_prepayments
            student['current_debt'] = total_earnings - total_paid

            # Calculate remaining lessons from prepayments
            remaining_prepayment_value = total_prepayments - total_paid + total_earnings
            student['remaining_lessons_from_prepayment'] = max(0, remaining_prepayment_value / student['hourly_rate']) if student['hourly_rate'] > 0 else 0

            return student

    def get_students_with_debt(self) -> List[Dict[str, Any]]:
        students = []
        for student in self.get_all_students():
            student_with_debt = self.get_student_with_debt(student['id'])
            if student_with_debt:
                students.append(student_with_debt)
        return students

    def update_student(self, student_id: int, name: str = None, course_name: str = None,
                      hourly_rate: float = None, agreed_hours: int = None, start_date: str = None):
        """Update student information. Only updates provided non-None values."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            values = []

            if name is not None:
                update_fields.append("name = ?")
                values.append(name)
            if course_name is not None:
                update_fields.append("course_name = ?")
                values.append(course_name)
            if hourly_rate is not None:
                update_fields.append("hourly_rate = ?")
                values.append(hourly_rate)
            if agreed_hours is not None:
                update_fields.append("agreed_hours = ?")
                values.append(agreed_hours)
            if start_date is not None:
                update_fields.append("start_date = ?")
                values.append(start_date)

            if update_fields:
                query = f"UPDATE students SET {', '.join(update_fields)} WHERE id = ?"
                values.append(student_id)
                cursor.execute(query, values)
                conn.commit()
                return True
            return False

    def delete_student(self, student_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # First delete payments for this student
            cursor.execute('DELETE FROM payments WHERE student_id = ?', (student_id,))
            # Then delete the student
            cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
            conn.commit()

    # Payment operations
    def add_payment(self, student_id: int, amount_paid: float, date: str, bank_account: str, is_prepayment: bool = False) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (student_id, amount_paid, date, bank_account, is_prepayment)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, amount_paid, date, bank_account, is_prepayment))

            # Add to bank account balance (money coming in)
            cursor.execute('UPDATE bank_accounts SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP WHERE bank_name = ?',
                         (amount_paid, bank_account))

            conn.commit()
            return cursor.lastrowid

    def get_student_payments(self, student_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payments WHERE student_id = ? ORDER BY date DESC', (student_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Income operations
    def add_income(self, amount: float, category: str, date: str, description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO income_entries (amount, category, date, description)
                VALUES (?, ?, ?, ?)
            ''', (amount, category, date, description))
            conn.commit()
            return cursor.lastrowid

    def get_all_income(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM income_entries ORDER BY date DESC')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_income_by_month_year(self) -> Dict[str, float]:
        """Returns monthly income totals as {'YYYY-MM': total}"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%Y-%m', date) as month_year, SUM(amount) as total
                FROM income_entries
                GROUP BY month_year
                ORDER BY month_year DESC
            ''')
            return {row[0]: row[1] for row in cursor.fetchall()}

    def delete_income(self, income_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM income_entries WHERE id = ?', (income_id,))
            conn.commit()

    # Expense operations
    def add_expense(self, amount: float, category: str, date: str, description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expense_entries (amount, category, date, description)
                VALUES (?, ?, ?, ?)
            ''', (amount, category, date, description))
            conn.commit()
            return cursor.lastrowid

    def get_all_expenses(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM expense_entries ORDER BY date DESC')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_expenses_by_category(self) -> Dict[str, float]:
        """Returns expense totals by category"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM expense_entries
                GROUP BY category
                ORDER BY total DESC
            ''')
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_expenses_by_month_year(self) -> Dict[str, float]:
        """Returns monthly expense totals as {'YYYY-MM': total}"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%Y-%m', date) as month_year, SUM(amount) as total
                FROM expense_entries
                GROUP BY month_year
                ORDER BY month_year DESC
            ''')
            return {row[0]: row[1] for row in cursor.fetchall()}

    def delete_expense(self, expense_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expense_entries WHERE id = ?', (expense_id,))
            conn.commit()

    # Bank account operations
    def get_bank_accounts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bank_accounts ORDER BY bank_name')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_bank_balance(self, bank_name: str, new_balance: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bank_accounts
                SET balance = ?, last_updated = CURRENT_TIMESTAMP
                WHERE bank_name = ?
            ''', (new_balance, bank_name))
            conn.commit()

    def add_bank_transaction(self, bank_name: str, amount: float, transaction_type: str, description: str, date: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Add transaction
            cursor.execute('''
                INSERT INTO bank_transactions (bank_name, amount, transaction_type, description, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (bank_name, amount, transaction_type, description, date))

            # Update bank balance based on transaction type
            if transaction_type in ['deposit', 'transfer_in']:
                cursor.execute('UPDATE bank_accounts SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP WHERE bank_name = ?',
                             (amount, bank_name))
            elif transaction_type in ['withdrawal', 'transfer_out']:
                cursor.execute('UPDATE bank_accounts SET balance = balance - ?, last_updated = CURRENT_TIMESTAMP WHERE bank_name = ?',
                             (amount, bank_name))

            conn.commit()
            return cursor.lastrowid

    def get_bank_transactions(self, bank_name: str = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if bank_name:
                cursor.execute('SELECT * FROM bank_transactions WHERE bank_name = ? ORDER BY date DESC', (bank_name,))
            else:
                cursor.execute('SELECT * FROM bank_transactions ORDER BY date DESC')

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_total_bank_balance(self) -> float:
        """Get total balance across all bank accounts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(balance) FROM bank_accounts')
            result = cursor.fetchone()
            return result[0] if result[0] else 0

    def delete_bank_transaction(self, transaction_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get transaction details first
            cursor.execute('SELECT bank_name, amount, transaction_type FROM bank_transactions WHERE id = ?', (transaction_id,))
            transaction = cursor.fetchone()

            if transaction:
                bank_name, amount, transaction_type = transaction

                # Reverse the transaction effect on balance
                if transaction_type in ['deposit', 'transfer_in']:
                    cursor.execute('UPDATE bank_accounts SET balance = balance - ?, last_updated = CURRENT_TIMESTAMP WHERE bank_name = ?',
                                 (amount, bank_name))
                elif transaction_type in ['withdrawal', 'transfer_out']:
                    cursor.execute('UPDATE bank_accounts SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP WHERE bank_name = ?',
                                 (amount, bank_name))

            # Delete the transaction
            cursor.execute('DELETE FROM bank_transactions WHERE id = ?', (transaction_id,))
            conn.commit()

    # Budget methods
    def set_budget(self, category: str, budget_amount: float, month_year: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (category, budget_amount, month_year, spent_amount)
                VALUES (?, ?, ?, COALESCE((SELECT spent_amount FROM budgets WHERE category = ? AND month_year = ?), 0))
            ''', (category, budget_amount, month_year, category, month_year))
            conn.commit()
            return cursor.lastrowid

    def get_budgets_for_month(self, month_year: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM budgets WHERE month_year = ? ORDER BY category', (month_year,))
            columns = [desc[0] for desc in cursor.description]
            budgets = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Calculate spent amounts from actual transactions
            for budget in budgets:
                if budget['category'] in ['Income', 'All Income']:
                    # For income budgets, calculate from income entries
                    cursor.execute('''
                        SELECT SUM(amount) FROM income_entries
                        WHERE strftime('%Y-%m', date) = ?
                    ''', (month_year,))
                else:
                    # For expense budgets, calculate from expense entries
                    cursor.execute('''
                        SELECT SUM(amount) FROM expense_entries
                        WHERE category = ? AND strftime('%Y-%m', date) = ?
                    ''', (budget['category'], month_year))

                spent = cursor.fetchone()[0] or 0
                budget['spent_amount'] = spent
                budget['remaining'] = budget['budget_amount'] - spent
                budget['percentage'] = (spent / budget['budget_amount'] * 100) if budget['budget_amount'] > 0 else 0

                # Update the database with current spent amount
                cursor.execute('UPDATE budgets SET spent_amount = ? WHERE id = ?', (spent, budget['id']))

            conn.commit()
            return budgets

    def get_all_budget_categories(self) -> List[str]:
        """Get unique categories that have budgets"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM budgets ORDER BY category')
            return [row[0] for row in cursor.fetchall()]

    def delete_budget(self, budget_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
            conn.commit()

    # Goals methods
    def add_goal(self, name: str, target_amount: float, target_date: str = None, description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO financial_goals (name, target_amount, target_date, description)
                VALUES (?, ?, ?, ?)
            ''', (name, target_amount, target_date, description))
            conn.commit()
            return cursor.lastrowid

    def get_all_goals(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM financial_goals ORDER BY created_at DESC')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def update_goal_progress(self, goal_id: int, current_amount: float):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE financial_goals SET current_amount = ? WHERE id = ?', (current_amount, goal_id))
            conn.commit()

    def delete_goal(self, goal_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM financial_goals WHERE id = ?', (goal_id,))
            conn.commit()

    # Recurring transactions methods
    def add_recurring_transaction(self, name: str, amount: float, trans_type: str, category: str,
                                frequency: str, next_date: str, description: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recurring_transactions (name, amount, type, category, frequency, next_date, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, amount, trans_type, category, frequency, next_date, description))
            conn.commit()
            return cursor.lastrowid

    def get_active_recurring_transactions(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM recurring_transactions WHERE is_active = 1 ORDER BY next_date')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def process_recurring_transactions(self):
        """Process due recurring transactions and create actual transactions"""
        from datetime import datetime, timedelta
        import calendar

        with self.get_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now().date()

            # Get due recurring transactions
            cursor.execute('SELECT * FROM recurring_transactions WHERE is_active = 1 AND next_date <= ?',
                         (today.isoformat(),))

            due_transactions = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            for row in due_transactions:
                transaction = dict(zip(columns, row))

                # Add the transaction
                if transaction['type'] == 'income':
                    self.add_income(transaction['amount'], transaction['category'],
                                  transaction['next_date'], f"Recurring: {transaction['name']}")
                elif transaction['type'] == 'expense':
                    self.add_expense(transaction['amount'], transaction['category'],
                                   transaction['next_date'], f"Recurring: {transaction['name']}")

                # Calculate next date
                current_date = datetime.strptime(transaction['next_date'], '%Y-%m-%d').date()

                if transaction['frequency'] == 'daily':
                    next_date = current_date + timedelta(days=1)
                elif transaction['frequency'] == 'weekly':
                    next_date = current_date + timedelta(weeks=1)
                elif transaction['frequency'] == 'monthly':
                    # Add one month
                    year = current_date.year
                    month = current_date.month + 1
                    if month > 12:
                        month = 1
                        year += 1
                    # Handle month end dates
                    _, last_day = calendar.monthrange(year, month)
                    day = min(current_date.day, last_day)
                    next_date = current_date.replace(year=year, month=month, day=day)
                elif transaction['frequency'] == 'yearly':
                    next_date = current_date.replace(year=current_date.year + 1)
                else:
                    next_date = current_date + timedelta(days=1)  # Default to daily

                # Update next_date in database
                cursor.execute('UPDATE recurring_transactions SET next_date = ? WHERE id = ?',
                             (next_date.isoformat(), transaction['id']))

            conn.commit()

    def update_recurring_transaction(self, transaction_id: int, name: str = None, amount: float = None,
                                    trans_type: str = None, category: str = None, frequency: str = None,
                                    next_date: str = None, description: str = None, is_active: bool = None):
        """Update recurring transaction. Only updates provided non-None values."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            update_fields = []
            values = []

            if name is not None:
                update_fields.append("name = ?")
                values.append(name)
            if amount is not None:
                update_fields.append("amount = ?")
                values.append(amount)
            if trans_type is not None:
                update_fields.append("type = ?")
                values.append(trans_type)
            if category is not None:
                update_fields.append("category = ?")
                values.append(category)
            if frequency is not None:
                update_fields.append("frequency = ?")
                values.append(frequency)
            if next_date is not None:
                update_fields.append("next_date = ?")
                values.append(next_date)
            if description is not None:
                update_fields.append("description = ?")
                values.append(description)
            if is_active is not None:
                update_fields.append("is_active = ?")
                values.append(is_active)

            if update_fields:
                query = f"UPDATE recurring_transactions SET {', '.join(update_fields)} WHERE id = ?"
                values.append(transaction_id)
                cursor.execute(query, values)
                conn.commit()
                return True
            return False

    def delete_recurring_transaction(self, transaction_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM recurring_transactions WHERE id = ?', (transaction_id,))
            conn.commit()

    # Enhanced tutoring methods
    def add_lesson(self, student_id: int, lesson_date: str, duration_hours: float = 1.0, topic: str = "", notes: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lessons_conducted (student_id, lesson_date, duration_hours, topic, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, lesson_date, duration_hours, topic, notes))

            # Update student's lessons_conducted count
            cursor.execute('UPDATE students SET lessons_conducted = lessons_conducted + ? WHERE id = ?',
                         (duration_hours, student_id))

            conn.commit()
            return cursor.lastrowid

    def get_student_lessons(self, student_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lessons_conducted WHERE student_id = ? ORDER BY lesson_date DESC', (student_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_all_lessons_with_students(self) -> List[Dict[str, Any]]:
        """Get all lessons with student names joined"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    l.id,
                    l.student_id,
                    l.lesson_date,
                    l.duration_hours,
                    l.topic,
                    l.notes,
                    l.created_at,
                    s.name as student_name
                FROM lessons_conducted l
                JOIN students s ON l.student_id = s.id
                ORDER BY l.lesson_date DESC, l.id DESC
            ''')
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_student_payment_summary(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive payment and earnings summary for a student"""
        student = self.get_student_with_debt(student_id)
        if not student:
            return None

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get detailed payment history
            cursor.execute('''
                SELECT date, amount_paid, bank_account, is_prepayment
                FROM payments
                WHERE student_id = ?
                ORDER BY date DESC
            ''', (student_id,))

            payments = []
            for row in cursor.fetchall():
                payments.append({
                    'date': row[0],
                    'amount': row[1],
                    'bank_account': row[2],
                    'is_prepayment': bool(row[3])
                })

            # Calculate totals
            total_agreed_value = student['hourly_rate'] * student['agreed_hours']
            total_earned = student['hourly_rate'] * student['lessons_conducted']

            return {
                'student_info': student,
                'payments': payments,
                'summary': {
                    'total_agreed_value': total_agreed_value,
                    'total_earned': total_earned,
                    'total_paid': student['total_paid'],
                    'total_prepayments': student['total_prepayments'],
                    'current_debt': student['current_debt'],
                    'remaining_lessons_from_prepayment': student['remaining_lessons_from_prepayment'],
                    'lessons_remaining': max(0, student['agreed_hours'] - student['lessons_conducted'])
                }
            }

    def delete_lesson(self, lesson_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get lesson details first
            cursor.execute('SELECT student_id, duration_hours FROM lessons_conducted WHERE id = ?', (lesson_id,))
            lesson = cursor.fetchone()

            if lesson:
                student_id, duration = lesson

                # Remove the lesson
                cursor.execute('DELETE FROM lessons_conducted WHERE id = ?', (lesson_id,))

                # Update student's lessons_conducted count
                cursor.execute('UPDATE students SET lessons_conducted = lessons_conducted - ? WHERE id = ?',
                             (duration, student_id))

            conn.commit()

    # Analytics
    def get_monthly_profit(self) -> Dict[str, float]:
        """Returns monthly profit: (personal income + student payments - expenses)"""
        income_by_month = self.get_income_by_month_year()
        expense_by_month = self.get_expenses_by_month_year()

        # Get student payments by month
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%Y-%m', date) as month_year, SUM(amount_paid) as total
                FROM payments
                GROUP BY month_year
                ORDER BY month_year DESC
            ''')
            payment_by_month = {row[0]: row[1] for row in cursor.fetchall()}

        # Combine all months
        all_months = set(income_by_month.keys()) | set(expense_by_month.keys()) | set(payment_by_month.keys())

        profit_data = {}
        for month in sorted(all_months, reverse=True):
            income = income_by_month.get(month, 0)
            expenses = expense_by_month.get(month, 0)
            payments = payment_by_month.get(month, 0)
            profit_data[month] = income + payments - expenses

        return profit_data

    def get_total_net_worth(self) -> float:
        """Calculate total net worth: bank balances + total income + total payments - total expenses"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total bank balance
            total_bank_balance = self.get_total_bank_balance()

            # Total income
            cursor.execute('SELECT SUM(amount) FROM income_entries')
            total_income = cursor.fetchone()[0] or 0

            # Total expenses
            cursor.execute('SELECT SUM(amount) FROM expense_entries')
            total_expenses = cursor.fetchone()[0] or 0

            # Total student payments
            cursor.execute('SELECT SUM(amount_paid) FROM payments')
            total_payments = cursor.fetchone()[0] or 0

            return total_bank_balance + total_income + total_payments - total_expenses

    def get_total_pending_debt(self) -> float:
        """Calculate total pending student debt (positive debt = students owe us)"""
        students = self.get_students_with_debt()
        return sum(student['current_debt'] for student in students if student['current_debt'] > 0)

    # Backup functionality
    def export_to_csv(self, export_dir: str = "backups"):
        """Export all data to CSV files"""
        import csv
        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export students
        students_file = os.path.join(export_dir, f"students_{timestamp}.csv")
        students = self.get_all_students()
        if students:
            with open(students_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=students[0].keys())
                writer.writeheader()
                writer.writerows(students)

        # Export payments
        payments_file = os.path.join(export_dir, f"payments_{timestamp}.csv")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payments ORDER BY date DESC')
            payments = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
            if payments:
                with open(payments_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=payments[0].keys())
                    writer.writeheader()
                    writer.writerows(payments)

        # Export income
        income_file = os.path.join(export_dir, f"income_{timestamp}.csv")
        income = self.get_all_income()
        if income:
            with open(income_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=income[0].keys())
                writer.writeheader()
                writer.writerows(income)

        # Export expenses
        expenses_file = os.path.join(export_dir, f"expenses_{timestamp}.csv")
        expenses = self.get_all_expenses()
        if expenses:
            with open(expenses_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=expenses[0].keys())
                writer.writeheader()
                writer.writerows(expenses)

        # Export bank accounts
        bank_accounts_file = os.path.join(export_dir, f"bank_accounts_{timestamp}.csv")
        bank_accounts = self.get_bank_accounts()
        if bank_accounts:
            with open(bank_accounts_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=bank_accounts[0].keys())
                writer.writeheader()
                writer.writerows(bank_accounts)

        # Export bank transactions
        bank_transactions_file = os.path.join(export_dir, f"bank_transactions_{timestamp}.csv")
        bank_transactions = self.get_bank_transactions()
        if bank_transactions:
            with open(bank_transactions_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=bank_transactions[0].keys())
                writer.writeheader()
                writer.writerows(bank_transactions)

        # Export budgets
        budgets_file = os.path.join(export_dir, f"budgets_{timestamp}.csv")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM budgets ORDER BY month_year DESC, category')
            budgets = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
            if budgets:
                with open(budgets_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=budgets[0].keys())
                    writer.writeheader()
                    writer.writerows(budgets)

        # Export goals
        goals_file = os.path.join(export_dir, f"goals_{timestamp}.csv")
        goals = self.get_all_goals()
        if goals:
            with open(goals_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=goals[0].keys())
                writer.writeheader()
                writer.writerows(goals)

        # Export recurring transactions
        recurring_file = os.path.join(export_dir, f"recurring_transactions_{timestamp}.csv")
        recurring = self.get_active_recurring_transactions()
        if recurring:
            with open(recurring_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=recurring[0].keys())
                writer.writeheader()
                writer.writerows(recurring)

        # Export lessons conducted
        lessons_file = os.path.join(export_dir, f"lessons_conducted_{timestamp}.csv")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM lessons_conducted ORDER BY lesson_date DESC')
            lessons = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
            if lessons:
                with open(lessons_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=lessons[0].keys())
                    writer.writeheader()
                    writer.writerows(lessons)

        return {
            "students": students_file if students else None,
            "payments": payments_file if payments else None,
            "income": income_file if income else None,
            "expenses": expenses_file if expenses else None,
            "bank_accounts": bank_accounts_file if bank_accounts else None,
            "bank_transactions": bank_transactions_file if bank_transactions else None,
            "budgets": budgets_file if budgets else None,
            "goals": goals_file if goals else None,
            "recurring_transactions": recurring_file if recurring else None,
            "lessons_conducted": lessons_file if lessons else None
        }