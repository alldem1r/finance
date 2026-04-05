import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import FinanceDatabase
import os
import auth

# Configure page
st.set_page_config(
    page_title="Financial Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and styling - INCLUDING FULL WIDTH EXPANDERS
st.markdown("""
<style>
    .main {
        background-color: #0e1117; /* Deep charcoal */
        color: #e0e0e0; /* Soft white for readability */
        font-family: 'Inter', sans-serif; /* Modern, clean font */
    }
    .stSidebar {
        background-color: #1a1c23;
        border-right: 2px solid #2e3440;
    }
    .stSidebar [data-testid="stSidebarNav"] {
        background-color: #1a1c23;
    }
    .css-1d391kg {
        background-color: #0e1117;
    }

    /* FULL WIDTH EXPANDERS - Global rule for all edit forms */
    .st-expander {
        width: 100% !important;
        max-width: none !important;
    }
    .st-expander > div:first-child {
        width: 100% !important;
    }
    .st-expander .streamlit-expanderContent {
        width: 100% !important;
        max-width: none !important;
    }

    .stTextInput, .stNumberInput, .stSelectbox, .stDateInput {
        background-color: #2e3440;
        border: 1px solid #434c5e;
        border-radius: 5px;
        color: #ffffff;
        width: 100% !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
        background-color: #2e3440;
        color: #ffffff;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .stButton button {
        background-color: #5e81ac;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stButton button:hover {
        background-color: #81a1c1;
    }
    .css-1offfwp {
        background-color: #1a1c23;
    }
    .stDataFrame {
        background-color: #2e3440;
    }
    .stDataFrame th {
        background-color: #434c5e;
        color: #ffffff;
    }
    .stDataFrame td {
        background-color: #2e3440;
        color: #ffffff;
    }
    .metric-card {
        background-color: #2e3440;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #434c5e;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #5e81ac;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #d8dee9;
    }
    .debt-positive {
        color: #bf616a;
        font-weight: bold;
    }
    .debt-zero {
        color: #a3be8c;
        font-weight: bold;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #eceff4;
    }
    .stMarkdown {
        color: #d8dee9;
    }

    /* Ensure columns use full width */
    .stColumn {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
db = FinanceDatabase()

# Sidebar navigation
def sidebar():
    st.sidebar.title("💰 Financial Tracker")
    st.sidebar.markdown("---")

    if not auth.is_password_configured():
        st.sidebar.warning(
            "No app password configured. Set environment variable "
            "FINANCIAL_TRACKER_PASSWORD or Streamlit secret `app_password` before sharing publicly."
        )

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Bank Accounts", "Personal Finance", "SAT Tutoring", "Budgets", "Goals", "Recurring", "Reports", "Backup Data"],
        index=0
    )

    st.sidebar.markdown("---")

    # Quick stats in sidebar
    st.sidebar.subheader("Quick Stats")

    net_worth = db.get_total_net_worth()
    pending_debt = db.get_total_pending_debt()
    bank_balance = db.get_total_bank_balance()

    st.sidebar.metric("Net Worth", f"{net_worth:,.0f} ₸")
    st.sidebar.metric("Bank Balance", f"{bank_balance:,.0f} ₸")
    st.sidebar.metric("Pending Debt", f"{pending_debt:,.0f} ₸")

    # Budget alerts
    current_month = datetime.now().strftime("%Y-%m")
    budgets = db.get_budgets_for_month(current_month)
    over_budget = [b for b in budgets if b['percentage'] > 100]

    if over_budget:
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚠️ Budget Alerts")
        for budget in over_budget[:3]:  # Show top 3 alerts
            st.sidebar.error(f"{budget['category']}: {budget['percentage']:.0f}% over budget")
    elif budgets:
        st.sidebar.markdown("---")
        st.sidebar.subheader("✅ Budget Status")
        st.sidebar.success(f"All {len(budgets)} budgets on track")

    if auth.is_password_configured():
        st.sidebar.markdown("---")
        if st.sidebar.button("Sign out", use_container_width=True):
            auth.logout()
            st.rerun()

    return page

# Dashboard page
def dashboard_page():
    st.title("📊 Dashboard")
    st.markdown("High-level overview of your finances and business")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        net_worth = db.get_total_net_worth()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Net Worth</div>
            <div class="metric-value">{net_worth:,.0f} ₸</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        bank_balance = db.get_total_bank_balance()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Bank Balance</div>
            <div class="metric-value">{bank_balance:,.0f} ₸</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        pending_debt = db.get_total_pending_debt()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pending Student Debt</div>
            <div class="metric-value">{pending_debt:,.0f} ₸</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # Monthly profit for current month
        profit_data = db.get_monthly_profit()
        current_month = datetime.now().strftime("%Y-%m")
        current_profit = profit_data.get(current_month, 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">This Month's Profit</div>
            <div class="metric-value">{current_profit:,.0f} ₸</div>
        </div>
        """, unsafe_allow_html=True)

    # Bank Accounts Overview
    st.subheader("🏦 Bank Accounts")
    bank_accounts = db.get_bank_accounts()

    if bank_accounts:
        cols = st.columns(len(bank_accounts))
        for i, account in enumerate(bank_accounts):
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{account['bank_name']}</div>
                    <div class="metric-value">{account['balance']:,.0f} ₸</div>
                </div>
                """, unsafe_allow_html=True)

    # Budget Overview
    st.subheader("📊 Budget Overview")
    current_month = datetime.now().strftime("%Y-%m")
    budgets = db.get_budgets_for_month(current_month)

    if budgets:
        # Show budget progress bars
        for budget in budgets:
            progress = min(budget['percentage'] / 100, 1.0)
            status_color = "🟢" if progress < 0.8 else "🟡" if progress < 1.0 else "🔴"

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"{status_color} {budget['category']}")
            with col2:
                st.progress(progress)
            with col3:
                st.write(f"{budget['percentage']:.0f}%")

            # Show detailed breakdown
            with st.expander(f"Details for {budget['category']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Budget", f"{budget['budget_amount']:,.0f} ₸")
                with col2:
                    st.metric("Spent", f"{budget['spent_amount']:,.0f} ₸")
                with col3:
                    remaining = budget['remaining']
                    st.metric("Remaining", f"{remaining:,.0f} ₸",
                            delta=f"{remaining:,.0f} ₸" if remaining >= 0 else None,
                            delta_color="normal" if remaining >= 0 else "inverse")
    else:
        st.info("No budgets set for this month. Go to 'Budgets' page to set up your monthly budgets.")

    st.markdown("---")

    # Charts section
    st.subheader("📈 Financial Overview")

    col1, col2 = st.columns(2)

    with col1:
        # Monthly profit chart
        profit_data = db.get_monthly_profit()
        if profit_data:
            df_profit = pd.DataFrame({
                'Month': list(profit_data.keys()),
                'Profit': list(profit_data.values())
            })
            df_profit['Month'] = pd.to_datetime(df_profit['Month'])
            df_profit = df_profit.sort_values('Month')

            fig_profit = px.bar(
                df_profit,
                x='Month',
                y='Profit',
                title='Monthly Profit (Income + Payments - Expenses) in ₸',
                color='Profit',
                color_continuous_scale=['#bf616a', '#a3be8c']
            )
            fig_profit.update_layout(
                plot_bgcolor='#2e3440',
                paper_bgcolor='#2e3440',
                font_color='#d8dee9'
            )
            st.plotly_chart(fig_profit, use_container_width=True)
        else:
            st.info("No profit data available yet. Add income, expenses, or student payments to see the chart.")

    with col2:
        # Expense distribution pie chart
        expense_data = db.get_expenses_by_category()
        if expense_data:
            df_expenses = pd.DataFrame({
                'Category': list(expense_data.keys()),
                'Amount': list(expense_data.values())
            })

            fig_expenses = px.pie(
                df_expenses,
                values='Amount',
                names='Category',
                title='Expense Distribution by Category'
            )
            fig_expenses.update_layout(
                plot_bgcolor='#2e3440',
                paper_bgcolor='#2e3440',
                font_color='#d8dee9'
            )
            st.plotly_chart(fig_expenses, use_container_width=True)
        else:
            st.info("No expense data available yet. Add expenses to see the distribution chart.")

    # Recent activity
    st.markdown("---")
    st.subheader("📋 Recent Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Income")
        income_data = db.get_all_income()[:5]  # Last 5 entries
        if income_data:
            for income in income_data:
                st.write(f"💰 {income['amount']:,.0f} ₸ - {income['category']} ({income['date']})")
        else:
            st.write("No income entries yet.")

    with col2:
        st.subheader("Recent Expenses")
        expense_data = db.get_all_expenses()[:5]  # Last 5 entries
        if expense_data:
            for expense in expense_data:
                st.write(f"💸 {expense['amount']:,.0f} ₸ - {expense['category']} ({expense['date']})")
        else:
            st.write("No expense entries yet.")

# Personal Finance page
def personal_finance_page():
    st.title("💰 Personal Finance")
    st.markdown("Track your personal income and expenses")

    tab1, tab2 = st.tabs(["📈 Income", "📉 Expenses"])

    with tab1:
        st.subheader("Add New Income")

        col1, col2 = st.columns(2)
        with col1:
            income_amount = st.number_input("Amount (₸)", min_value=0.0, step=0.01, key="income_amount")
            income_category = st.selectbox(
                "Category",
                ["Salary", "Freelance", "Investment", "Other"],
                key="income_category"
            )

        with col2:
            income_date = st.date_input("Date", datetime.now().date(), key="income_date")
            income_description = st.text_input("Description (optional)", key="income_description")

        if st.button("Add Income", key="add_income"):
            if income_amount > 0:
                db.add_income(income_amount, income_category, income_date.isoformat(), income_description)
                st.success("Income added successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid amount.")

        st.markdown("---")
        st.subheader("Income History")

        # Search and filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term = st.text_input("Search description", key="income_search", placeholder="Search...")
        with col2:
            filter_category = st.selectbox("Filter by category", ["All"] + list(set([inc['category'] for inc in db.get_all_income()])), key="income_filter")
        with col3:
            sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High)", "Amount (Low)"], key="income_sort")

        income_data = db.get_all_income()

        # Apply filters
        if search_term:
            income_data = [inc for inc in income_data if search_term.lower() in (inc['description'] or '').lower()]

        if filter_category != "All":
            income_data = [inc for inc in income_data if inc['category'] == filter_category]

        # Apply sorting
        if sort_by == "Date (Newest)":
            income_data.sort(key=lambda x: x['date'], reverse=True)
        elif sort_by == "Date (Oldest)":
            income_data.sort(key=lambda x: x['date'])
        elif sort_by == "Amount (High)":
            income_data.sort(key=lambda x: x['amount'], reverse=True)
        elif sort_by == "Amount (Low)":
            income_data.sort(key=lambda x: x['amount'])
        if income_data:
            df_income = pd.DataFrame(income_data)
            df_income['date'] = pd.to_datetime(df_income['date']).dt.strftime('%Y-%m-%d')
            df_income = df_income[['id', 'date', 'category', 'amount', 'description']]

            # Add edit and delete buttons
            for idx, row in df_income.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 3, 1, 1])
                with col1:
                    st.write(row['date'])
                with col2:
                    st.write(row['category'])
                with col3:
                    st.write(f"{row['amount']:,.0f} ₸")
                with col4:
                    st.write(row['description'] or "")
                with col5:
                    # Edit button for income
                    edit_income_key = f"edit_income_{row['id']}"
                    if st.button("✏️", key=f"edit_income_btn_{row['id']}", help="Edit income entry"):
                        st.session_state[edit_income_key] = True

                    # Show edit form if edit button was clicked
                    if st.session_state.get(edit_income_key, False):
                        with st.expander(f"Edit Income Entry - {row['date']}", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_date = st.date_input("Date", value=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                                                        key=f"edit_income_date_{row['id']}")
                                edit_amount = st.number_input("Amount (₸)", min_value=0.0, value=float(row['amount']),
                                                            step=1000.0, key=f"edit_income_amount_{row['id']}")

                            with col2:
                                edit_category = st.selectbox("Category",
                                    ["Salary", "Freelance", "Investment", "Other"],
                                    index=["Salary", "Freelance", "Investment", "Other"].index(row['category']),
                                    key=f"edit_income_category_{row['id']}")
                                edit_description = st.text_input("Description",
                                    value=row['description'] or "", key=f"edit_income_desc_{row['id']}")

                            save_col, cancel_col = st.columns(2)
                            with save_col:
                                if st.button("💾 Update Income", key=f"save_income_{row['id']}"):
                                    try:
                                        # Update income entry in database
                                        with db.get_connection() as conn:
                                            cursor = conn.cursor()
                                            cursor.execute('''
                                                UPDATE income_entries
                                                SET amount = ?, category = ?, date = ?, description = ?
                                                WHERE id = ?
                                            ''', (edit_amount, edit_category, edit_date.isoformat(), edit_description, row['id']))
                                            conn.commit()

                                        st.success("Income entry updated successfully!")
                                        st.session_state[edit_income_key] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating income: {str(e)}")

                            with cancel_col:
                                if st.button("❌ Cancel", key=f"cancel_income_{row['id']}"):
                                    st.session_state[edit_income_key] = False
                                    st.rerun()

                with col6:
                    if st.button("🗑️", key=f"del_income_{row['id']}", help="Delete income entry"):
                        # Show confirmation
                        confirm_income_key = f"confirm_delete_income_{row['id']}"
                        st.session_state[confirm_income_key] = True

                    # Show confirmation if delete was clicked
                    confirm_income_key = f"confirm_delete_income_{row['id']}"
                    if st.session_state.get(confirm_income_key, False):
                        st.warning(f"Delete income entry of {row['amount']:,.0f} ₸ from {row['date']}?")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("✅ Yes, Delete", key=f"confirm_income_yes_{row['id']}"):
                                db.delete_income(row['id'])
                                st.success("Income entry deleted!")
                                st.session_state[confirm_income_key] = False
                                st.rerun()
                        with no_col:
                            if st.button("❌ No, Cancel", key=f"confirm_income_no_{row['id']}"):
                                st.session_state[confirm_income_key] = False
                                st.rerun()
        else:
            st.info("No income entries yet. Add your first income above.")

    with tab2:
        st.subheader("Add New Expense")

        col1, col2 = st.columns(2)
        with col1:
            expense_amount = st.number_input("Amount (₸)", min_value=0.0, step=0.01, key="expense_amount")
            expense_category = st.selectbox(
                "Category",
                ["Food", "Rent", "Utilities", "Transportation", "Entertainment", "Healthcare", "Shopping", "Other"],
                key="expense_category"
            )

        with col2:
            expense_date = st.date_input("Date", datetime.now().date(), key="expense_date")
            expense_description = st.text_input("Description (optional)", key="expense_description")

        if st.button("Add Expense", key="add_expense"):
            if expense_amount > 0:
                db.add_expense(expense_amount, expense_category, expense_date.isoformat(), expense_description)
                st.success("Expense added successfully!")
                st.rerun()
            else:
                st.error("Please enter a valid amount.")

        st.markdown("---")
        st.subheader("Expense History")

        # Search and filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search_term_expense = st.text_input("Search description", key="expense_search", placeholder="Search...")
        with col2:
            filter_category_expense = st.selectbox("Filter by category", ["All"] + list(set([exp['category'] for exp in db.get_all_expenses()])), key="expense_filter")
        with col3:
            sort_by_expense = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High)", "Amount (Low)"], key="expense_sort")

        expense_data = db.get_all_expenses()

        # Apply filters
        if search_term_expense:
            expense_data = [exp for exp in expense_data if search_term_expense.lower() in (exp['description'] or '').lower()]

        if filter_category_expense != "All":
            expense_data = [exp for exp in expense_data if exp['category'] == filter_category_expense]

        # Apply sorting
        if sort_by_expense == "Date (Newest)":
            expense_data.sort(key=lambda x: x['date'], reverse=True)
        elif sort_by_expense == "Date (Oldest)":
            expense_data.sort(key=lambda x: x['date'])
        elif sort_by_expense == "Amount (High)":
            expense_data.sort(key=lambda x: x['amount'], reverse=True)
        elif sort_by_expense == "Amount (Low)":
            expense_data.sort(key=lambda x: x['amount'])
        if expense_data:
            df_expenses = pd.DataFrame(expense_data)
            df_expenses['date'] = pd.to_datetime(df_expenses['date']).dt.strftime('%Y-%m-%d')
            df_expenses = df_expenses[['id', 'date', 'category', 'amount', 'description']]

            # Add edit and delete buttons
            for idx, row in df_expenses.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 3, 1, 1])
                with col1:
                    st.write(row['date'])
                with col2:
                    st.write(row['category'])
                with col3:
                    st.write(f"{row['amount']:,.0f} ₸")
                with col4:
                    st.write(row['description'] or "")
                with col5:
                    # Edit button for expense
                    edit_expense_key = f"edit_expense_{row['id']}"
                    if st.button("✏️", key=f"edit_expense_btn_{row['id']}", help="Edit expense entry"):
                        st.session_state[edit_expense_key] = True

                    # Show edit form if edit button was clicked
                    if st.session_state.get(edit_expense_key, False):
                        with st.expander(f"Edit Expense Entry - {row['date']}", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_date = st.date_input("Date", value=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                                                        key=f"edit_expense_date_{row['id']}")
                                edit_amount = st.number_input("Amount (₸)", min_value=0.0, value=float(row['amount']),
                                                            step=1000.0, key=f"edit_expense_amount_{row['id']}")

                            with col2:
                                edit_category = st.selectbox("Category",
                                    ["Food", "Rent", "Utilities", "Transportation", "Entertainment", "Healthcare", "Shopping", "Other"],
                                    index=["Food", "Rent", "Utilities", "Transportation", "Entertainment", "Healthcare", "Shopping", "Other"].index(row['category']) if row['category'] in ["Food", "Rent", "Utilities", "Transportation", "Entertainment", "Healthcare", "Shopping", "Other"] else 7,
                                    key=f"edit_expense_category_{row['id']}")
                                edit_description = st.text_input("Description",
                                    value=row['description'] or "", key=f"edit_expense_desc_{row['id']}")

                            save_col, cancel_col = st.columns(2)
                            with save_col:
                                if st.button("💾 Update Expense", key=f"save_expense_{row['id']}"):
                                    try:
                                        # Update expense entry in database
                                        with db.get_connection() as conn:
                                            cursor = conn.cursor()
                                            cursor.execute('''
                                                UPDATE expense_entries
                                                SET amount = ?, category = ?, date = ?, description = ?
                                                WHERE id = ?
                                            ''', (edit_amount, edit_category, edit_date.isoformat(), edit_description, row['id']))
                                            conn.commit()

                                        st.success("Expense entry updated successfully!")
                                        st.session_state[edit_expense_key] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating expense: {str(e)}")

                            with cancel_col:
                                if st.button("❌ Cancel", key=f"cancel_expense_{row['id']}"):
                                    st.session_state[edit_expense_key] = False
                                    st.rerun()

                with col6:
                    if st.button("🗑️", key=f"del_expense_{row['id']}", help="Delete expense entry"):
                        # Show confirmation
                        confirm_expense_key = f"confirm_delete_expense_{row['id']}"
                        st.session_state[confirm_expense_key] = True

                    # Show confirmation if delete was clicked
                    confirm_expense_key = f"confirm_delete_expense_{row['id']}"
                    if st.session_state.get(confirm_expense_key, False):
                        st.warning(f"Delete expense entry of {row['amount']:,.0f} ₸ from {row['date']}?")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("✅ Yes, Delete", key=f"confirm_expense_yes_{row['id']}"):
                                db.delete_expense(row['id'])
                                st.success("Expense entry deleted!")
                                st.session_state[confirm_expense_key] = False
                                st.rerun()
                        with no_col:
                            if st.button("❌ No, Cancel", key=f"confirm_expense_no_{row['id']}"):
                                st.session_state[confirm_expense_key] = False
                                st.rerun()
        else:
            st.info("No expense entries yet. Add your first expense above.")

# SAT Tutoring page
def sat_tutoring_page():
    st.title("🎓 SAT Tutoring")
    st.markdown("Manage your students, lessons, and payments")

    tab1, tab2, tab3 = st.tabs(["👥 Students", "📚 Lessons", "💳 Payments"])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Add New Student")

            student_name = st.text_input("Student Name", key="student_name")
            student_course = st.text_input("Course Name", key="student_course")
            student_hourly_rate = st.number_input("Hourly Rate (₸)", min_value=0.0, step=100.0, key="student_hourly_rate")
            student_agreed_hours = st.number_input("Agreed Hours", min_value=1, step=1, key="student_agreed_hours")
            student_start_date = st.date_input("Start Date", datetime.now().date(), key="student_start_date")

            # Calculate total agreed value
            total_value = student_hourly_rate * student_agreed_hours
            if total_value > 0:
                st.info(f"Total agreed value: {total_value:,.0f} ₸")

            if st.button("Add Student", key="add_student"):
                if student_name and student_course and student_hourly_rate > 0 and student_agreed_hours > 0:
                    db.add_student(student_name, student_course, student_hourly_rate, student_agreed_hours, student_start_date.isoformat())
                    st.success("Student added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields with valid values.")

        with col2:
            st.subheader("Student List")

            students = db.get_students_with_debt()
            if students:
                for student in students:
                    debt_color = "debt-positive" if student['current_debt'] > 0 else "debt-zero"
                    total_agreed = student['hourly_rate'] * student['agreed_hours']

                    st.markdown(f"""
                    <div style="background-color: #2e3440; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>{student['name']}</h4>
                        <p><strong>Course:</strong> {student['course_name']}</p>
                        <p><strong>Rate:</strong> {student['hourly_rate']:,.0f} ₸/hour | <strong>Agreed:</strong> {student['agreed_hours']} hours</p>
                        <p><strong>Lessons Done:</strong> {student['lessons_conducted']} | <strong>Remaining:</strong> {max(0, student['agreed_hours'] - student['lessons_conducted'])}</p>
                        <p><strong>Earned:</strong> {student['total_earnings']:,.0f} ₸ | <strong>Paid:</strong> {student['total_paid']:,.0f} ₸</p>
                        <p><strong>Prepayments:</strong> {student['total_prepayments']:,.0f} ₸</p>
                        <span class="{debt_color}"><strong>Current Debt: {student['current_debt']:,.0f} ₸</strong></span>
                        <br><small>Lessons from prepayment: {student['remaining_lessons_from_prepayment']:.1f}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    # Quick action buttons
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button(f"Add Lesson", key=f"quick_lesson_{student['id']}"):
                            db.add_lesson(student['id'], datetime.now().date().isoformat())
                            st.success(f"Lesson added for {student['name']}!")
                            st.rerun()

                    with col2:
                        # Undo last lesson button
                        undo_key = f"undo_lesson_{student['id']}"
                        if st.button("↶ Undo", key=f"undo_btn_{student['id']}", help="Remove last lesson added today"):
                            # Get today's lessons for this student
                            today = datetime.now().date().isoformat()
                            lessons = db.get_student_lessons(student['id'])
                            today_lessons = [l for l in lessons if l['lesson_date'] == today]

                            if today_lessons:
                                # Delete the most recent lesson from today
                                latest_lesson = max(today_lessons, key=lambda x: x['id'])
                                db.delete_lesson(latest_lesson['id'])
                                st.success(f"Removed today's latest lesson for {student['name']}!")
                                st.rerun()
                            else:
                                st.warning(f"No lessons found for {student['name']} today.")

                    with col4:
                        # Edit button - opens edit form
                        edit_key = f"edit_student_{student['id']}"
                        if st.button(f"✏️ Edit", key=f"edit_btn_{student['id']}"):
                            st.session_state[edit_key] = True

                        # Show edit form if edit button was clicked
                        if st.session_state.get(edit_key, False):
                            # Custom CSS to make edit forms FULL WIDTH and much larger
                            st.markdown(f"""
                            <style>
                            .st-expander {{
                                width: 100% !important;
                                max-width: none !important;
                            }}
                            .st-expander > div:first-child {{
                                width: 100% !important;
                            }}
                            .st-expander .streamlit-expanderContent {{
                                width: 100% !important;
                                max-width: none !important;
                            }}
                            .edit-expander {{
                                min-height: 400px !important;
                                width: 100% !important;
                            }}
                            .edit-container {{
                                background-color: #1e1e2e;
                                padding: 30px !important;
                                border-radius: 15px;
                                margin: 20px 0;
                                border: 2px solid #434c5e;
                                width: 100% !important;
                                max-width: none !important;
                                box-sizing: border-box !important;
                            }}
                            .stTextInput {{
                                width: 100% !important;
                            }}
                            .stTextInput input {{
                                font-size: 16px !important;
                                padding: 12px !important;
                                height: 20px !important;
                                width: 100% !important;
                                box-sizing: border-box !important;
                            }}
                            .stNumberInput {{
                                width: 100% !important;
                            }}
                            .stNumberInput input {{
                                font-size: 16px !important;
                                padding: 12px !important;
                                height: 20px !important;
                                width: 100% !important;
                                box-sizing: border-box !important;
                            }}
                            .stSelectbox {{
                                width: 100% !important;
                            }}
                            .stSelectbox select {{
                                font-size: 16px !important;
                                padding: 12px !important;
                                height: 20px !important;
                                width: 100% !important;
                                box-sizing: border-box !important;
                            }}
                            .stDateInput {{
                                width: 100% !important;
                            }}
                            .stDateInput input {{
                                font-size: 16px !important;
                                padding: 12px !important;
                                height: 20px !important;
                                width: 100% !important;
                                box-sizing: border-box !important;
                            }}
                            .stTextArea {{
                                width: 100% !important;
                            }}
                            .stTextArea textarea {{
                                font-size: 16px !important;
                                padding: 12px !important;
                                min-height: 80px !important;
                                width: 100% !important;
                                box-sizing: border-box !important;
                            }}
                            .edit-title {{
                                font-size: 24px;
                                font-weight: bold;
                                color: #eceff4;
                                margin-bottom: 20px;
                            }}
                            .stColumn {{
                                width: 100% !important;
                            }}
                            </style>
                            """, unsafe_allow_html=True)

                            with st.expander(f"📝 Edit {student['name']}", expanded=True):
                                st.markdown('<div class="edit-title">Edit Student Information</div>', unsafe_allow_html=True)

                                with st.container():
                                    # Full-width layout for maximum usability
                                    st.markdown("### 👤 Student Details")
                                    edit_name = st.text_input("Student Name", value=student['name'], key=f"edit_name_{student['id']}",
                                                            help="Enter the student's full name")

                                    # Two columns for course and date - full width
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        edit_course = st.text_input("Course Name", value=student['course_name'], key=f"edit_course_{student['id']}",
                                                                  help="e.g., SAT Math, SAT English")
                                    with col2:
                                        edit_date = st.date_input("Start Date", value=datetime.strptime(student['start_date'], '%Y-%m-%d').date(),
                                                                key=f"edit_date_{student['id']}")

                                    st.markdown("### 💰 Pricing Information")
                                    # Two columns for rate and hours - full width
                                    col3, col4 = st.columns(2)
                                    with col3:
                                        edit_rate = st.number_input("Hourly Rate (₸)", min_value=0.0, step=1000.0,
                                                                   value=float(student['hourly_rate']), key=f"edit_rate_{student['id']}",
                                                                   help="Rate per hour in Kazakhstani Tenge")
                                    with col4:
                                        edit_hours = st.number_input("Agreed Hours", min_value=1, step=1,
                                                                    value=int(student['agreed_hours']), key=f"edit_hours_{student['id']}",
                                                                    help="Total hours agreed for the course")

                                    # Calculate and show new total with prominent display
                                    new_total = edit_rate * edit_hours
                                    if new_total > 0:
                                        st.success(f"💰 New total agreed value: {new_total:,.0f} ₸")
                                    else:
                                        st.warning("Please set valid hourly rate and agreed hours")

                                # Save and Cancel buttons with better styling
                                st.markdown("---")
                                save_col, cancel_col = st.columns([1, 1])
                                with save_col:
                                    if st.button("💾 Save Changes", key=f"save_edit_{student['id']}"):
                                        try:
                                            db.update_student(
                                                student_id=student['id'],
                                                name=edit_name,
                                                course_name=edit_course,
                                                hourly_rate=edit_rate,
                                                agreed_hours=edit_hours,
                                                start_date=edit_date.isoformat()
                                            )
                                            st.success(f"Updated {edit_name}'s information!")
                                            st.session_state[edit_key] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating student: {str(e)}")

                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_edit_{student['id']}"):
                                        st.session_state[edit_key] = False
                                        st.rerun()

                    with st.container():
                        # Delete button in its own section
                        if st.button(f"🗑️ Delete {student['name']}", key=f"del_student_{student['id']}"):
                            # Show confirmation dialog
                            confirm_key = f"confirm_delete_{student['id']}"
                            st.session_state[confirm_key] = True

                        # Show confirmation if delete was clicked
                        confirm_key = f"confirm_delete_{student['id']}"
                        if st.session_state.get(confirm_key, False):
                            st.warning(f"Are you sure you want to delete {student['name']}? This will also delete all their lessons and payments.")

                            yes_col, no_col = st.columns(2)
                            with yes_col:
                                if st.button("✅ Yes, Delete", key=f"confirm_yes_{student['id']}"):
                                    db.delete_student(student['id'])
                                    st.success(f"Deleted student {student['name']} and all associated data")
                                    st.session_state[confirm_key] = False
                                    st.rerun()

                            with no_col:
                                if st.button("❌ No, Cancel", key=f"confirm_no_{student['id']}"):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
            else:
                st.info("No students added yet.")

    with tab2:
        st.subheader("Lesson Tracking")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Add Lesson")

            students = db.get_all_students()
            if students:
                student_options = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                selected_student = st.selectbox("Select Student", list(student_options.keys()), key="lesson_student")

                lesson_date = st.date_input("Lesson Date", datetime.now().date(), key="lesson_date")
                lesson_duration = st.number_input("Duration (hours)", min_value=0.5, max_value=8.0, value=1.0, step=0.5, key="lesson_duration")
                lesson_topic = st.text_input("Topic (optional)", key="lesson_topic")
                lesson_notes = st.text_area("Notes (optional)", key="lesson_notes")

                if st.button("Record Lesson", key="add_lesson"):
                    student_id = student_options[selected_student]
                    db.add_lesson(student_id, lesson_date.isoformat(), lesson_duration, lesson_topic, lesson_notes)
                    st.success("Lesson recorded successfully!")
                    st.rerun()
            else:
                st.warning("No students available. Add students first.")

        with col2:
            st.markdown("### All Lessons Conducted")

            # Get all lessons with student names
            all_lessons = db.get_all_lessons_with_students()
            
            if all_lessons:
                # Search functionality
                st.markdown("#### 🔍 Search Lessons")
                search_term = st.text_input("Search by student name, ID, or date (YYYY-MM-DD)", 
                                          key="lesson_search", 
                                          placeholder="e.g., John, 5, or 2024-01-15")
                
                # Filter lessons based on search
                filtered_lessons = all_lessons
                if search_term:
                    search_lower = search_term.lower()
                    filtered_lessons = [
                        lesson for lesson in all_lessons
                        if (search_lower in lesson['student_name'].lower() or
                            search_lower in str(lesson['id']) or
                            search_lower in str(lesson['student_id']) or
                            search_lower in lesson['lesson_date'])
                    ]
                
                st.markdown(f"**Total Lessons:** {len(all_lessons)} | **Showing:** {len(filtered_lessons)}")
                st.markdown("---")

                if filtered_lessons:
                    for lesson in filtered_lessons:
                        # Get student hourly rate for earnings calculation
                        student = next((s for s in students if s['id'] == lesson['student_id']), None)
                        earnings = lesson['duration_hours'] * (student['hourly_rate'] if student else 0)

                        lesson_display = f"""
                        <div style="background-color: #2e3440; padding: 12px; border-radius: 5px; margin: 8px 0; border-left: 4px solid #5e81ac;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <strong style="font-size: 16px;">📅 {lesson['lesson_date']}</strong><br>
                                    <strong>👤 Student:</strong> {lesson['student_name']} (ID: {lesson['student_id']})<br>
                                    <strong>🆔 Lesson ID:</strong> {lesson['id']}<br>
                                    <small>⏱️ {lesson['duration_hours']} hours | 💰 Earned: {earnings:,.0f} ₸</small>
                                    {f"<br><em>📖 Topic: {lesson['topic']}</em>" if lesson.get('topic') else ""}
                        </div>
                        """

                        # Edit and Delete buttons for each lesson
                        edit_lesson_key = f"edit_lesson_{lesson['id']}"
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.markdown(lesson_display, unsafe_allow_html=True)

                        with col2:
                            if st.button("✏️", key=f"edit_lesson_btn_{lesson['id']}", help="Edit lesson"):
                                st.session_state[edit_lesson_key] = True

                        # Show edit form if edit button was clicked
                        if st.session_state.get(edit_lesson_key, False):
                            # FULL WIDTH lesson edit form
                            st.markdown(f"""
                        <style>
                        .st-expander {{
                            width: 100% !important;
                            max-width: none !important;
                        }}
                        .st-expander > div:first-child {{
                            width: 100% !important;
                        }}
                        .st-expander .streamlit-expanderContent {{
                            width: 100% !important;
                            max-width: none !important;
                        }}
                        .lesson-edit-expander {{
                            min-height: 350px !important;
                            width: 100% !important;
                        }}
                        .lesson-edit-container {{
                            background-color: #1e1e2e;
                            padding: 25px !important;
                            border-radius: 12px;
                            margin: 15px 0;
                            border: 2px solid #434c5e;
                            width: 100% !important;
                            max-width: none !important;
                            box-sizing: border-box !important;
                        }}
                        .stTextInput {{
                            width: 100% !important;
                        }}
                        .stTextInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stNumberInput {{
                            width: 100% !important;
                        }}
                        .stNumberInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stDateInput {{
                            width: 100% !important;
                        }}
                        .stDateInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stTextArea {{
                            width: 100% !important;
                        }}
                        .stTextArea textarea {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            min-height: 100px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .lesson-title {{
                            font-size: 20px;
                            font-weight: bold;
                            color: #eceff4;
                            margin-bottom: 15px;
                        }}
                        .stColumn {{
                            width: 100% !important;
                        }}
                        </style>
                            """, unsafe_allow_html=True)

                            with st.expander(f"📚 Edit Lesson - {lesson['student_name']}", expanded=True):
                                st.markdown('<div class="lesson-title">Edit Lesson Details</div>', unsafe_allow_html=True)

                                with st.container():
                                    # Better layout for lesson editing - more spacious
                                    col1, col2 = st.columns([1, 2])

                                    with col1:
                                        st.markdown("### 📅 Basic Info")
                                        
                                        # Student selection
                                        student_options = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
                                        current_student_key = f"{lesson['student_name']} (ID: {lesson['student_id']})"
                                        selected_student_key = st.selectbox("Student",
                                            options=list(student_options.keys()),
                                            index=list(student_options.keys()).index(current_student_key) if current_student_key in student_options else 0,
                                            key=f"edit_lesson_student_{lesson['id']}")
                                        edit_lesson_student_id = student_options[selected_student_key]
                                        
                                        edit_lesson_date = st.date_input("Lesson Date",
                                            value=datetime.strptime(lesson['lesson_date'], '%Y-%m-%d').date(),
                                            key=f"edit_lesson_date_{lesson['id']}")

                                        edit_lesson_duration = st.number_input("Duration (hours)",
                                            min_value=0.5, max_value=8.0, value=float(lesson['duration_hours']),
                                            step=0.5, key=f"edit_lesson_duration_{lesson['id']}",
                                            help="Duration in hours (e.g., 1.5 for 1.5 hours)")

                                    with col2:
                                        st.markdown("### 📖 Lesson Content")
                                        edit_lesson_topic = st.text_input("Topic Covered",
                                            value=lesson.get('topic', ''), key=f"edit_lesson_topic_{lesson['id']}",
                                            help="What topic was covered in this lesson?")

                                        edit_lesson_notes = st.text_area("Lesson Notes",
                                            value=lesson.get('notes', ''), key=f"edit_lesson_notes_{lesson['id']}",
                                            help="Additional notes about the lesson", height=120)

                                    save_col, cancel_col = st.columns(2)
                                    with save_col:
                                        if st.button("💾 Update Lesson", key=f"save_lesson_{lesson['id']}"):
                                            try:
                                                # Update lesson in database
                                                with db.get_connection() as conn:
                                                    cursor = conn.cursor()
                                                    
                                                    old_student_id = lesson['student_id']
                                                    old_duration = lesson['duration_hours']
                                                    new_student_id = edit_lesson_student_id
                                                    new_duration = edit_lesson_duration
                                                    
                                                    # If student changed, adjust both students' lesson counts
                                                    if old_student_id != new_student_id:
                                                        # Remove duration from old student
                                                        cursor.execute('UPDATE students SET lessons_conducted = lessons_conducted - ? WHERE id = ?',
                                                                     (old_duration, old_student_id))
                                                        # Add duration to new student
                                                        cursor.execute('UPDATE students SET lessons_conducted = lessons_conducted + ? WHERE id = ?',
                                                                     (new_duration, new_student_id))
                                                    else:
                                                        # Same student, just adjust duration difference
                                                        duration_diff = new_duration - old_duration
                                                        if duration_diff != 0:
                                                            cursor.execute('UPDATE students SET lessons_conducted = lessons_conducted + ? WHERE id = ?',
                                                                         (duration_diff, old_student_id))

                                                    # Update lesson record
                                                    cursor.execute('''
                                                        UPDATE lessons_conducted
                                                        SET student_id = ?, lesson_date = ?, duration_hours = ?, topic = ?, notes = ?
                                                        WHERE id = ?
                                                    ''', (new_student_id, edit_lesson_date.isoformat(), new_duration, edit_lesson_topic, edit_lesson_notes, lesson['id']))

                                                    conn.commit()

                                                st.success("Lesson updated successfully!")
                                                st.session_state[edit_lesson_key] = False
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error updating lesson: {str(e)}")

                                    with cancel_col:
                                        if st.button("❌ Cancel", key=f"cancel_lesson_{lesson['id']}"):
                                            st.session_state[edit_lesson_key] = False
                                            st.rerun()

                            if st.button("🗑️", key=f"delete_lesson_btn_{lesson['id']}", help="Delete lesson"):
                                # Show confirmation
                                confirm_lesson_key = f"confirm_delete_lesson_{lesson['id']}"
                                st.session_state[confirm_lesson_key] = True

                            # Show confirmation if delete was clicked
                            confirm_lesson_key = f"confirm_delete_lesson_{lesson['id']}"
                            if st.session_state.get(confirm_lesson_key, False):
                                st.warning(f"Delete lesson for {lesson['student_name']} on {lesson['lesson_date']}?")

                                yes_col, no_col = st.columns(2)
                                with yes_col:
                                    if st.button("✅ Yes, Delete", key=f"confirm_lesson_yes_{lesson['id']}"):
                                        db.delete_lesson(lesson['id'])
                                        st.success("Lesson deleted successfully!")
                                        st.session_state[confirm_lesson_key] = False
                                        st.rerun()

                                with no_col:
                                    if st.button("❌ No, Cancel", key=f"confirm_lesson_no_{lesson['id']}"):
                                        st.session_state[confirm_lesson_key] = False
                                        st.rerun()
                else:
                    st.warning(f"No lessons found matching '{search_term}'. Try a different search term.")
            else:
                st.info("No lessons recorded yet.")

    with tab3:
        st.subheader("Payment Management")

        # Student selection
        students = db.get_all_students()
        if students:
            student_options = {f"{s['name']} (ID: {s['id']})": s['id'] for s in students}
            selected_student = st.selectbox("Select Student", list(student_options.keys()), key="payment_student")

            col1, col2 = st.columns(2)
            with col1:
                payment_amount = st.number_input("Payment Amount (₸)", min_value=0.0, step=1000.0, key="payment_amount")
                is_prepayment = st.checkbox("This is a prepayment", key="is_prepayment")

            with col2:
                # Get available bank accounts
                bank_accounts = db.get_bank_accounts()
                bank_options = [acc['bank_name'] for acc in bank_accounts]
                selected_bank = st.selectbox("Bank Account", bank_options, key="payment_bank")
                payment_date = st.date_input("Payment Date", datetime.now().date(), key="payment_date")

            # Show student summary
            student_id = student_options[selected_student]
            summary = db.get_student_payment_summary(student_id)

            if summary:
                st.markdown("### Student Summary")
                s = summary['summary']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Earned", f"{s['total_earned']:,.0f} ₸")
                with col2:
                    st.metric("Paid", f"{s['total_paid']:,.0f} ₸")
                with col3:
                    st.metric("Debt", f"{s['current_debt']:,.0f} ₸")
                with col4:
                    st.metric("Prepaid Lessons", f"{s['remaining_lessons_from_prepayment']:.1f}")

            if st.button("Record Payment", key="add_payment"):
                if payment_amount > 0 and selected_student and selected_bank:
                    student_id = student_options[selected_student]
                    db.add_payment(student_id, payment_amount, payment_date.isoformat(), selected_bank, is_prepayment)
                    st.success("Payment recorded successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid payment amount and select a student.")
        else:
            st.warning("No students available. Add students first before recording payments.")

        st.markdown("---")
        st.subheader("Payment History")

        # Display payments for all students
        all_payments = []
        for student in students:
            payments = db.get_student_payments(student['id'])
            for payment in payments:
                payment['student_name'] = student['name']
                all_payments.append(payment)

        if all_payments:
            # Sort payments by date descending
            all_payments.sort(key=lambda x: x['date'], reverse=True)

            st.write("### Recent Payments")

            # Display payments in a more interactive format
            for payment in all_payments[:20]:  # Show last 20 payments
                payment_type = "Prepayment" if payment.get('is_prepayment', False) else "Regular Payment"

                payment_display = f"""
                <div style="background-color: #2e3440; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong>{payment['student_name']}</strong> - {payment['date']}<br>
                    <small>{payment['amount_paid']:,.0f} ₸ via {payment.get('bank_account', 'Unknown')} | {payment_type}</small>
                </div>
                """

                # Edit and Delete buttons for each payment
                col1, col2, col3 = st.columns([8, 1, 1])

                with col1:
                    st.markdown(payment_display, unsafe_allow_html=True)

                with col2:
                    edit_payment_key = f"edit_payment_{payment['id']}"
                    if st.button("✏️", key=f"edit_payment_btn_{payment['id']}", help="Edit payment"):
                        st.session_state[edit_payment_key] = True

                    # Show edit form if edit button was clicked
                    if st.session_state.get(edit_payment_key, False):
                        # FULL WIDTH payment edit form
                        st.markdown(f"""
                        <style>
                        .st-expander {{
                            width: 100% !important;
                            max-width: none !important;
                        }}
                        .st-expander > div:first-child {{
                            width: 100% !important;
                        }}
                        .st-expander .streamlit-expanderContent {{
                            width: 100% !important;
                            max-width: none !important;
                        }}
                        .payment-edit-expander {{
                            min-height: 320px !important;
                            width: 100% !important;
                        }}
                        .payment-edit-container {{
                            background-color: #1e1e2e;
                            padding: 25px !important;
                            border-radius: 12px;
                            margin: 15px 0;
                            border: 2px solid #434c5e;
                            width: 100% !important;
                            max-width: none !important;
                            box-sizing: border-box !important;
                        }}
                        .stTextInput {{
                            width: 100% !important;
                        }}
                        .stTextInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stNumberInput {{
                            width: 100% !important;
                        }}
                        .stNumberInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stDateInput {{
                            width: 100% !important;
                        }}
                        .stDateInput input {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stSelectbox {{
                            width: 100% !important;
                        }}
                        .stSelectbox select {{
                            font-size: 16px !important;
                            padding: 12px !important;
                            height: 20px !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .payment-title {{
                            font-size: 20px;
                            font-weight: bold;
                            color: #eceff4;
                            margin-bottom: 15px;
                        }}
                        .current-payment-info {{
                            background-color: #2e3440;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                            border-left: 4px solid #5e81ac;
                            width: 100% !important;
                            box-sizing: border-box !important;
                        }}
                        .stColumn {{
                            width: 100% !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)

                        with st.expander(f"💳 Edit Payment - {payment['student_name']}", expanded=True):
                            st.markdown('<div class="payment-title">Edit Payment Details</div>', unsafe_allow_html=True)

                            # Show current payment info prominently
                            st.markdown(f"""
                            <div class="current-payment-info">
                                <strong>Current Payment:</strong> {payment['amount_paid']:,.0f} ₸ on {payment['date']}<br>
                                <strong>Bank:</strong> {payment.get('bank_account', 'Not specified')}<br>
                                <strong>Type:</strong> {"Prepayment" if payment.get('is_prepayment', False) else "Regular Payment"}
                            </div>
                            """, unsafe_allow_html=True)

                            with st.container():
                                # Better layout for payment editing - more spacious
                                col1, col2 = st.columns([1, 1])

                                with col1:
                                    st.markdown("### 📅 Payment Info")
                                    edit_payment_date = st.date_input("Payment Date",
                                        value=datetime.strptime(payment['date'], '%Y-%m-%d').date(),
                                        key=f"edit_payment_date_{payment['id']}")

                                    edit_payment_amount = st.number_input("Amount (₸)",
                                        min_value=0.0, value=float(payment['amount_paid']),
                                        step=1000.0, key=f"edit_payment_amount_{payment['id']}",
                                        help="Payment amount in Kazakhstani Tenge")

                                with col2:
                                    st.markdown("### 🏦 Bank Details")
                                    bank_accounts = db.get_bank_accounts()
                                    bank_options = [acc['bank_name'] for acc in bank_accounts]
                                    current_bank = payment.get('bank_account', bank_accounts[0]['bank_name'] if bank_accounts else 'Kaspi')
                                    edit_payment_bank = st.selectbox("Bank Account", bank_options,
                                        index=bank_options.index(current_bank) if current_bank in bank_options else 0,
                                        key=f"edit_payment_bank_{payment['id']}",
                                        help="Which bank account received this payment")

                                    st.markdown("### 📋 Payment Type")
                                    edit_is_prepayment = st.checkbox("This is a prepayment",
                                        value=bool(payment.get('is_prepayment', False)),
                                        key=f"edit_is_prepayment_{payment['id']}",
                                        help="Prepayments cover future lessons")

                                st.markdown("---")
                                save_col, cancel_col = st.columns([1, 1])
                            with save_col:
                                if st.button("💾 Update Payment", key=f"save_payment_{payment['id']}"):
                                    try:
                                        # Update payment in database
                                        with db.get_connection() as conn:
                                            cursor = conn.cursor()

                                            # Get old payment details for bank balance adjustment
                                            cursor.execute('SELECT amount_paid, bank_account FROM payments WHERE id = ?', (payment['id'],))
                                            old_payment = cursor.fetchone()

                                            if old_payment:
                                                old_amount, old_bank = old_payment

                                                # Reverse old payment from bank
                                                if old_bank:
                                                    cursor.execute('UPDATE bank_accounts SET balance = balance - ? WHERE bank_name = ?',
                                                                 (old_amount, old_bank))

                                            # Update payment record
                                            cursor.execute('''
                                                UPDATE payments
                                                SET amount_paid = ?, date = ?, bank_account = ?, is_prepayment = ?
                                                WHERE id = ?
                                            ''', (edit_payment_amount, edit_payment_date.isoformat(), edit_payment_bank, edit_is_prepayment, payment['id']))

                                            # Add new amount to new bank
                                            cursor.execute('UPDATE bank_accounts SET balance = balance + ? WHERE bank_name = ?',
                                                         (edit_payment_amount, edit_payment_bank))

                                            conn.commit()

                                        st.success("Payment updated successfully!")
                                        st.session_state[edit_payment_key] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating payment: {str(e)}")

                            with cancel_col:
                                if st.button("❌ Cancel", key=f"cancel_payment_{payment['id']}"):
                                    st.session_state[edit_payment_key] = False
                                    st.rerun()

                with col3:
                    if st.button("🗑️", key=f"del_payment_{payment['id']}", help="Delete payment"):
                        # Show confirmation
                        confirm_payment_key = f"confirm_delete_payment_{payment['id']}"
                        st.session_state[confirm_payment_key] = True

                    # Show confirmation if delete was clicked
                    confirm_payment_key = f"confirm_delete_payment_{payment['id']}"
                    if st.session_state.get(confirm_payment_key, False):
                        st.warning(f"Delete payment of {payment['amount_paid']:,.0f} ₸ from {payment['student_name']}?")

                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("✅ Yes, Delete", key=f"confirm_payment_yes_{payment['id']}"):
                                # Reverse the payment from bank balance
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute('UPDATE bank_accounts SET balance = balance - ? WHERE bank_name = ?',
                                                 (payment['amount_paid'], payment['bank_account']))

                                # Delete the payment
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute('DELETE FROM payments WHERE id = ?', (payment['id'],))
                                    conn.commit()

                                st.success("Payment deleted successfully!")
                                st.session_state[confirm_payment_key] = False
                                st.rerun()

                        with no_col:
                            if st.button("❌ No, Cancel", key=f"confirm_payment_no_{payment['id']}"):
                                st.session_state[confirm_payment_key] = False
                                st.rerun()

            if len(all_payments) > 20:
                st.info(f"Showing 20 most recent payments. Total payments: {len(all_payments)}")
        else:
            st.info("No payments recorded yet.")

# Backup page
def import_from_csv(csv_file, data_type):
    """Import data from CSV file"""
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)

        imported_count = 0
        errors = []

        if data_type == "students":
            required_cols = ['name', 'course_name', 'hourly_rate', 'agreed_hours', 'start_date']
            if all(col in df.columns for col in required_cols):
                for _, row in df.iterrows():
                    try:
                        db.add_student(
                            name=str(row['name']),
                            course_name=str(row['course_name']),
                            hourly_rate=float(row['hourly_rate']),
                            agreed_hours=int(row['agreed_hours']),
                            start_date=str(row['start_date'])
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Student {row.get('name', 'Unknown')}: {str(e)}")
            else:
                return False, "Missing required columns: name, course_name, hourly_rate, agreed_hours, start_date"

        elif data_type == "bank_accounts":
            required_cols = ['bank_name', 'balance']
            if all(col in df.columns for col in required_cols):
                for _, row in df.iterrows():
                    try:
                        db.update_bank_balance(str(row['bank_name']), float(row['balance']))
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Bank {row.get('bank_name', 'Unknown')}: {str(e)}")
            else:
                return False, "Missing required columns: bank_name, balance"

        elif data_type == "lessons":
            required_cols = ['student_id', 'lesson_date', 'duration_hours']
            if all(col in df.columns for col in required_cols):
                for _, row in df.iterrows():
                    try:
                        db.add_lesson(
                            student_id=int(row['student_id']),
                            lesson_date=str(row['lesson_date']),
                            duration_hours=float(row['duration_hours']),
                            topic=str(row.get('topic', '')),
                            notes=str(row.get('notes', ''))
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Lesson for student {row.get('student_id', 'Unknown')}: {str(e)}")
            else:
                return False, "Missing required columns: student_id, lesson_date, duration_hours"

        elif data_type == "payments":
            required_cols = ['student_id', 'amount_paid', 'date']
            if all(col in df.columns for col in required_cols):
                for _, row in df.iterrows():
                    try:
                        db.add_payment(
                            student_id=int(row['student_id']),
                            amount_paid=float(row['amount_paid']),
                            date=str(row['date']),
                            bank_account=str(row.get('bank_account', 'Kaspi')),
                            is_prepayment=bool(row.get('is_prepayment', False))
                        )
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"Payment for student {row.get('student_id', 'Unknown')}: {str(e)}")
            else:
                return False, "Missing required columns: student_id, amount_paid, date"

        success_msg = f"Successfully imported {imported_count} {data_type} records."
        if errors:
            success_msg += f" {len(errors)} errors occurred."

        return True, success_msg, errors if errors else None

    except Exception as e:
        return False, f"Error processing CSV: {str(e)}"

def backup_page():
    st.title("💾 Backup & Recovery")
    st.markdown("Export data to CSV files and import from backups")

    tab1, tab2 = st.tabs(["📤 Export Data", "📥 Import Data"])

    with tab1:
        st.subheader("Export Data to CSV")

        if st.button("📤 Create Backup", key="backup_button"):
            with st.spinner("Creating backup..."):
                try:
                    export_files = db.export_to_csv()
                    st.success("Backup created successfully!")

                    st.subheader("Backup Files Created:")
                    for data_type, file_path in export_files.items():
                        if file_path and os.path.exists(file_path):
                            st.write(f"✅ {data_type.replace('_', ' ').title()}: `{file_path}`")
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    label=f"📥 Download {data_type.replace('_', ' ').title()} CSV",
                                    data=file,
                                    file_name=os.path.basename(file_path),
                                    mime="text/csv",
                                    key=f"download_{data_type}"
                                )
                        else:
                            st.write(f"❌ {data_type.replace('_', ' ').title()}: No data to export")

                except Exception as e:
                    st.error(f"Error creating backup: {str(e)}")

        st.markdown("---")
        st.subheader("Backup Information")
        st.info("""
        - Backups are saved in a 'backups' folder in your project directory
        - Each backup includes a timestamp to avoid overwriting previous backups
        - Download buttons allow you to save files to any location
        - Keep these files safe for data recovery purposes
        """)

    with tab2:
        st.subheader("Import Data from CSV")

        st.markdown("""
        **⚠️ Important Notes:**
        - CSV files must have the correct column headers
        - Existing data will not be overwritten (imports add to existing data)
        - Check the column requirements below for each data type
        """)

        import_type = st.selectbox(
            "Select Data Type to Import",
            ["students", "bank_accounts", "lessons", "payments"],
            key="import_type"
        )

        # Show required columns for each type
        if import_type == "students":
            st.info("**Required CSV columns:** name, course_name, hourly_rate, agreed_hours, start_date")
            st.code("name,course_name,hourly_rate,agreed_hours,start_date\nAlima,SAT Math,15000,20,2024-01-01", language="csv")

        elif import_type == "bank_accounts":
            st.info("**Required CSV columns:** bank_name, balance")
            st.code("bank_name,balance\nKaspi,100000\nHalyk,50000", language="csv")

        elif import_type == "lessons":
            st.info("**Required CSV columns:** student_id, lesson_date, duration_hours")
            st.info("**Optional columns:** topic, notes")
            st.code("student_id,lesson_date,duration_hours,topic,notes\n1,2024-01-15,1.5,Algebra,Good progress", language="csv")

        elif import_type == "payments":
            st.info("**Required CSV columns:** student_id, amount_paid, date")
            st.info("**Optional columns:** bank_account, is_prepayment")
            st.code("student_id,amount_paid,date,bank_account,is_prepayment\n1,50000,2024-01-20,Kaspi,false", language="csv")

        # File uploader
        uploaded_file = st.file_uploader(
            f"Choose {import_type.replace('_', ' ')} CSV file",
            type=['csv'],
            key=f"upload_{import_type}"
        )

        if uploaded_file is not None:
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")

            # Show preview of the data
            try:
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)

                if len(df) > 10:
                    st.info(f"Showing first 10 rows of {len(df)} total rows.")

                # Import button
                if st.button(f"📥 Import {len(df)} {import_type.replace('_', ' ')} records", key=f"import_{import_type}"):
                    with st.spinner("Importing data..."):
                        # Reset file pointer
                        uploaded_file.seek(0)

                        success, message, errors = import_from_csv(uploaded_file, import_type)

                        if success:
                            st.success(message)
                            if errors:
                                st.warning("Some records had errors:")
                                for error in errors:
                                    st.write(f"• {error}")
                        else:
                            st.error(message)

                        # Rerun to refresh data
                        st.rerun()

            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.info("Make sure your CSV file has the correct format and column headers.")

        st.markdown("---")
        st.subheader("Import Guidelines")
        st.info("""
        **CSV Format Requirements:**
        - First row must contain column headers
        - Use commas (,) as separators
        - Dates should be in YYYY-MM-DD format
        - Numbers should not contain commas or currency symbols

        **Safety:**
        - Import adds data without overwriting existing records
        - Check data preview before importing
        - You can delete incorrect records after import
        """)

# Main app logic
# Bank Accounts page
def bank_accounts_page():
    st.title("🏦 Bank Accounts")
    st.markdown("Manage your bank accounts and transactions")

    tab1, tab2 = st.tabs(["📊 Account Overview", "💸 Transactions"])

    with tab1:
        st.subheader("Bank Account Balances")

        bank_accounts = db.get_bank_accounts()
        if bank_accounts:
            # Display current balances
            cols = st.columns(len(bank_accounts))
            for i, account in enumerate(bank_accounts):
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{account['bank_name']}</div>
                        <div class="metric-value">{account['balance']:,.0f} ₸</div>
                        <div style="font-size: 0.8rem; color: #d8dee9; margin-top: 5px;">
                            Updated: {account['last_updated'][:10] if account['last_updated'] else 'Never'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("Update Account Balances")

            col1, col2 = st.columns(2)
            with col1:
                selected_bank = st.selectbox(
                    "Select Bank",
                    [account['bank_name'] for account in bank_accounts],
                    key="update_bank_select"
                )
                new_balance = st.number_input(
                    "New Balance (₸)",
                    min_value=0.0,
                    step=0.01,
                    value=float(bank_accounts[[acc['bank_name'] for acc in bank_accounts].index(selected_bank)]['balance']),
                    key="new_balance"
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacer
                if st.button("Update Balance", key="update_balance"):
                    db.update_bank_balance(selected_bank, new_balance)
                    st.success(f"Updated {selected_bank} balance to {new_balance:,.0f} ₸")
                    st.rerun()
        else:
            st.warning("No bank accounts found.")

    with tab2:
        st.subheader("Add Transaction")

        bank_accounts = db.get_bank_accounts()
        if bank_accounts:
            col1, col2 = st.columns(2)
            with col1:
                transaction_bank = st.selectbox(
                    "Bank Account",
                    [account['bank_name'] for account in bank_accounts],
                    key="transaction_bank"
                )
                transaction_amount = st.number_input("Amount (₸)", min_value=0.01, step=0.01, key="transaction_amount")
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["deposit", "withdrawal", "transfer_in", "transfer_out"],
                    key="transaction_type"
                )

            with col2:
                transaction_date = st.date_input("Date", datetime.now().date(), key="transaction_date")
                transaction_description = st.text_input("Description", key="transaction_description")

            if st.button("Add Transaction", key="add_transaction"):
                if transaction_amount > 0:
                    db.add_bank_transaction(
                        transaction_bank,
                        transaction_amount,
                        transaction_type,
                        transaction_description,
                        transaction_date.isoformat()
                    )
                    st.success("Transaction added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid amount.")
        else:
            st.warning("No bank accounts available. Please add bank accounts first.")

        st.markdown("---")
        st.subheader("Transaction History")

        transactions = db.get_bank_transactions()
        if transactions:
            df_transactions = pd.DataFrame(transactions)
            df_transactions['date'] = pd.to_datetime(df_transactions['date']).dt.strftime('%Y-%m-%d')
            df_transactions['amount'] = df_transactions['amount'].apply(lambda x: f"{x:,.0f} ₸")
            df_transactions = df_transactions[['date', 'bank_name', 'transaction_type', 'amount', 'description']]

            # Add delete buttons
            for idx, row in df_transactions.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 3, 1])
                with col1:
                    st.write(row['date'])
                with col2:
                    st.write(row['bank_name'])
                with col3:
                    st.write(row['transaction_type'].replace('_', ' ').title())
                with col4:
                    st.write(row['amount'])
                with col5:
                    st.write(row['description'] or "")
                with col6:
                    # Get transaction ID from original data
                    transaction_id = transactions[idx]['id']
                    if st.button("🗑️", key=f"del_transaction_{transaction_id}"):
                        db.delete_bank_transaction(transaction_id)
                        st.success("Transaction deleted!")
                        st.rerun()
        else:
            st.info("No transactions recorded yet.")

# Budgets page
def budgets_page():
    st.title("📊 Budgets")
    st.markdown("Set and track your monthly budgets")

    tab1, tab2 = st.tabs(["📅 Monthly Budgets", "📈 Budget History"])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Set Monthly Budget")

            # Month selector
            selected_month = st.date_input(
                "Select Month",
                datetime.now().replace(day=1),
                key="budget_month"
            ).replace(day=1)

            month_year = selected_month.strftime("%Y-%m")

            # Quick budget categories
            categories = [
                "Food", "Rent", "Utilities", "Transportation", "Entertainment",
                "Healthcare", "Shopping", "Education", "Savings", "Other"
            ]

            selected_category = st.selectbox("Category", categories, key="budget_category")
            budget_amount = st.number_input("Budget Amount (₸)", min_value=0.0, step=1000.0, key="budget_amount")

            if st.button("Set Budget", key="set_budget"):
                if budget_amount > 0:
                    db.set_budget(selected_category, budget_amount, month_year)
                    st.success(f"Budget set for {selected_category}: {budget_amount:,.0f} ₸")
                    st.rerun()
                else:
                    st.error("Please enter a valid budget amount.")

        with col2:
            st.subheader(f"Current Month Budgets ({month_year})")

            budgets = db.get_budgets_for_month(month_year)
            if budgets:
                for budget in budgets:
                    status = "🟢 On Track" if budget['percentage'] < 80 else "🟡 Warning" if budget['percentage'] < 100 else "🔴 Over Budget"

                    # Display budget with edit and delete buttons
                    col1, col2, col3 = st.columns([4, 1, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="background-color: #2e3440; padding: 10px; border-radius: 5px; margin: 5px 0;">
                            <strong>{budget['category']}</strong><br>
                            Budget: {budget['budget_amount']:,.0f} ₸ | Spent: {budget['spent_amount']:,.0f} ₸<br>
                            <small>{status} ({budget['percentage']:.1f}%)</small>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        # Edit button for budget
                        edit_budget_key = f"edit_budget_{budget['id']}"
                        if st.button("✏️", key=f"edit_budget_btn_{budget['id']}", help="Edit budget"):
                            st.session_state[edit_budget_key] = True

                        # Show edit form if edit button was clicked
                        if st.session_state.get(edit_budget_key, False):
                            with st.expander(f"Edit Budget - {budget['category']}", expanded=True):
                                edit_amount = st.number_input("New Budget Amount (₸)",
                                    min_value=0.0, value=float(budget['budget_amount']),
                                    step=1000.0, key=f"edit_budget_amount_{budget['id']}")

                                save_col, cancel_col = st.columns(2)
                                with save_col:
                                    if st.button("💾 Update Budget", key=f"save_budget_{budget['id']}"):
                                        try:
                                            # Update budget in database
                                            with db.get_connection() as conn:
                                                cursor = conn.cursor()
                                                cursor.execute('''
                                                    UPDATE budgets
                                                    SET budget_amount = ?
                                                    WHERE id = ?
                                                ''', (edit_amount, budget['id']))
                                                conn.commit()

                                            st.success(f"Updated budget for {budget['category']}: {edit_amount:,.0f} ₸")
                                            st.session_state[edit_budget_key] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating budget: {str(e)}")

                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_budget_{budget['id']}"):
                                        st.session_state[edit_budget_key] = False
                                        st.rerun()

                    with col3:
                        if st.button("🗑️", key=f"del_budget_{budget['id']}", help="Delete budget"):
                            # Show confirmation
                            confirm_budget_key = f"confirm_delete_budget_{budget['id']}"
                            st.session_state[confirm_budget_key] = True

                        # Show confirmation if delete was clicked
                        confirm_budget_key = f"confirm_delete_budget_{budget['id']}"
                        if st.session_state.get(confirm_budget_key, False):
                            st.warning(f"Delete budget for {budget['category']} ({budget['budget_amount']:,.0f} ₸)?")
                            yes_col, no_col = st.columns(2)
                            with yes_col:
                                if st.button("✅ Yes, Delete", key=f"confirm_budget_yes_{budget['id']}"):
                                    db.delete_budget(budget['id'])
                                    st.success(f"Deleted budget for {budget['category']}")
                                    st.session_state[confirm_budget_key] = False
                                    st.rerun()
                            with no_col:
                                if st.button("❌ No, Cancel", key=f"confirm_budget_no_{budget['id']}"):
                                    st.session_state[confirm_budget_key] = False
                                    st.rerun()
            else:
                st.info("No budgets set for this month.")

    with tab2:
        st.subheader("Budget History")

        # Get all budget months
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT month_year FROM budgets ORDER BY month_year DESC')
            months = [row[0] for row in cursor.fetchall()]

        if months:
            selected_history_month = st.selectbox("Select Month", months, key="history_month")
            budgets = db.get_budgets_for_month(selected_history_month)

            if budgets:
                # Summary stats
                total_budget = sum(b['budget_amount'] for b in budgets)
                total_spent = sum(b['spent_amount'] for b in budgets)
                avg_percentage = sum(b['percentage'] for b in budgets) / len(budgets)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Budget", f"{total_budget:,.0f} ₸")
                with col2:
                    st.metric("Total Spent", f"{total_spent:,.0f} ₸")
                with col3:
                    st.metric("Average Usage", f"{avg_percentage:.1f}%")
                with col4:
                    remaining = total_budget - total_spent
                    st.metric("Remaining", f"{remaining:,.0f} ₸")

                # Detailed breakdown
                st.subheader("Category Breakdown")
                for budget in budgets:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(budget['category'])
                    with col2:
                        st.write(f"{budget['budget_amount']:,.0f} ₸")
                    with col3:
                        st.write(f"{budget['spent_amount']:,.0f} ₸")
                    with col4:
                        progress = min(budget['percentage'] / 100, 1.0)
                        st.progress(progress)
                        st.write(f"{budget['percentage']:.1f}%")
            else:
                st.info("No budget data for selected month.")
        else:
            st.info("No budget history available.")

# Goals page
def goals_page():
    st.title("🎯 Financial Goals")
    st.markdown("Set and track your financial goals")

    tab1, tab2 = st.tabs(["🎯 Active Goals", "✅ Completed Goals"])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Add New Goal")

            goal_name = st.text_input("Goal Name", key="goal_name")
            goal_amount = st.number_input("Target Amount (₸)", min_value=0.0, step=1000.0, key="goal_amount")
            goal_date = st.date_input("Target Date (optional)", key="goal_date")
            goal_description = st.text_area("Description (optional)", key="goal_description")

            if st.button("Add Goal", key="add_goal"):
                if goal_name and goal_amount > 0:
                    target_date = goal_date.isoformat() if goal_date else None
                    db.add_goal(goal_name, goal_amount, target_date, goal_description)
                    st.success(f"Goal '{goal_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a goal name and valid target amount.")

        with col2:
            st.subheader("Your Goals")

            goals = db.get_all_goals()
            active_goals = [g for g in goals if g['current_amount'] < g['target_amount']]

            if active_goals:
                for goal in active_goals:
                    progress = (goal['current_amount'] / goal['target_amount']) * 100

                    st.markdown(f"""
                    <div style="background-color: #2e3440; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>{goal['name']}</h4>
                        <p>{goal['description'] or 'No description'}</p>
                        <div style="margin: 10px 0;">
                            Progress: {progress:.1f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Progress bar
                    st.progress(progress / 100)

                    # Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current", f"{goal['current_amount']:,.0f} ₸")
                    with col2:
                        st.metric("Target", f"{goal['target_amount']:,.0f} ₸")
                    with col3:
                        remaining = goal['target_amount'] - goal['current_amount']
                        st.metric("Remaining", f"{remaining:,.0f} ₸")

                    # Update progress
                    new_amount = st.number_input(
                        f"Update progress for {goal['name']} (₸)",
                        min_value=0.0,
                        value=float(goal['current_amount']),
                        step=1000.0,
                        key=f"update_goal_{goal['id']}"
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Update Progress", key=f"update_btn_{goal['id']}"):
                            db.update_goal_progress(goal['id'], new_amount)
                            st.success("Goal progress updated!")
                            st.rerun()

                    with col2:
                        # Edit button for goal details
                        edit_goal_key = f"edit_goal_details_{goal['id']}"
                        if st.button("✏️ Edit Goal", key=f"edit_goal_btn_{goal['id']}"):
                            st.session_state[edit_goal_key] = True

                        # Show edit form if edit button was clicked
                        if st.session_state.get(edit_goal_key, False):
                            with st.expander(f"Edit Goal Details - {goal['name']}", expanded=True):
                                edit_goal_name = st.text_input("Goal Name",
                                    value=goal['name'], key=f"edit_goal_name_{goal['id']}")
                                edit_goal_target = st.number_input("Target Amount (₸)",
                                    min_value=0.0, value=float(goal['target_amount']),
                                    step=1000.0, key=f"edit_goal_target_{goal['id']}")
                                edit_goal_date = st.date_input("Target Date",
                                    value=datetime.strptime(goal['target_date'], '%Y-%m-%d').date() if goal['target_date'] else None,
                                    key=f"edit_goal_date_{goal['id']}")
                                edit_goal_description = st.text_area("Description",
                                    value=goal.get('description', ''), key=f"edit_goal_desc_{goal['id']}")

                                save_col, cancel_col = st.columns(2)
                                with save_col:
                                    if st.button("💾 Update Goal", key=f"save_goal_details_{goal['id']}"):
                                        try:
                                            # Update goal details in database
                                            with db.get_connection() as conn:
                                                cursor = conn.cursor()
                                                cursor.execute('''
                                                    UPDATE financial_goals
                                                    SET name = ?, target_amount = ?, target_date = ?, description = ?
                                                    WHERE id = ?
                                                ''', (edit_goal_name, edit_goal_target,
                                                     edit_goal_date.isoformat() if edit_goal_date else None,
                                                     edit_goal_description, goal['id']))
                                                conn.commit()

                                            st.success(f"Updated goal details for '{edit_goal_name}'!")
                                            st.session_state[edit_goal_key] = False
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating goal: {str(e)}")

                                with cancel_col:
                                    if st.button("❌ Cancel", key=f"cancel_goal_details_{goal['id']}"):
                                        st.session_state[edit_goal_key] = False
                                        st.rerun()

                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_goal_{goal['id']}", help="Delete goal"):
                            # Show confirmation
                            confirm_goal_key = f"confirm_delete_goal_{goal['id']}"
                            st.session_state[confirm_goal_key] = True

                        # Show confirmation if delete was clicked
                        confirm_goal_key = f"confirm_delete_goal_{goal['id']}"
                        if st.session_state.get(confirm_goal_key, False):
                            st.warning(f"Delete goal '{goal['name']}' and all its progress?")
                            yes_col, no_col = st.columns(2)
                            with yes_col:
                                if st.button("✅ Yes, Delete", key=f"confirm_goal_yes_{goal['id']}"):
                                    db.delete_goal(goal['id'])
                                    st.success("Goal deleted!")
                                    st.session_state[confirm_goal_key] = False
                                    st.rerun()
                            with no_col:
                                if st.button("❌ No, Cancel", key=f"confirm_goal_no_{goal['id']}"):
                                    st.session_state[confirm_goal_key] = False
                                    st.rerun()

                    st.markdown("---")
            else:
                st.info("No active goals. Add your first financial goal above!")

    with tab2:
        st.subheader("Completed Goals")

        goals = db.get_all_goals()
        completed_goals = [g for g in goals if g['current_amount'] >= g['target_amount']]

        if completed_goals:
            for goal in completed_goals:
                st.success(f"🎉 {goal['name']} - Completed!")
                st.write(f"Target: {goal['target_amount']:,.0f} ₸")
                st.write(f"Achieved: {goal['current_amount']:,.0f} ₸")

                if st.button(f"Delete completed goal: {goal['name']}", key=f"delete_completed_{goal['id']}"):
                    db.delete_goal(goal['id'])
                    st.success("Completed goal deleted!")
                    st.rerun()

                st.markdown("---")
        else:
                st.info("No completed goals yet. Keep working towards your targets!")

# Recurring Transactions page
def recurring_page():
    st.title("🔄 Recurring Transactions")
    st.markdown("Manage automatic income and expense transactions")

    tab1, tab2 = st.tabs(["➕ Add Recurring", "📋 Manage Recurring"])

    with tab1:
        st.subheader("Add New Recurring Transaction")

        col1, col2 = st.columns(2)
        with col1:
            trans_name = st.text_input("Transaction Name", key="recurring_name")
            trans_type = st.selectbox("Type", ["income", "expense"], key="recurring_type")
            trans_amount = st.number_input("Amount (₸)", min_value=0.0, step=1000.0, key="recurring_amount")

        with col2:
            trans_category = st.text_input("Category", key="recurring_category")
            trans_frequency = st.selectbox("Frequency",
                ["daily", "weekly", "monthly", "yearly"], key="recurring_frequency")
            trans_date = st.date_input("Next Date", datetime.now().date(), key="recurring_date")

        trans_description = st.text_area("Description (optional)", key="recurring_description")

        if st.button("➕ Add Recurring Transaction", key="add_recurring"):
            if trans_name and trans_amount > 0 and trans_category:
                db.add_recurring_transaction(
                    trans_name, trans_amount, trans_type, trans_category,
                    trans_frequency, trans_date.isoformat(), trans_description
                )
                st.success(f"Added recurring {trans_type}: {trans_name}")
                st.rerun()
            else:
                st.error("Please fill in all required fields.")

    with tab2:
        st.subheader("Active Recurring Transactions")

        recurring_transactions = db.get_active_recurring_transactions()

        if recurring_transactions:
            for transaction in recurring_transactions:
                # Display transaction with edit and delete buttons
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    type_icon = "💰" if transaction['type'] == 'income' else "💸"
                    status = "✅ Active" if transaction['is_active'] else "⏸️ Inactive"

                    st.markdown(f"""
                    <div style="background-color: #2e3440; padding: 15px; border-radius: 8px; margin: 8px 0;">
                        <h4>{type_icon} {transaction['name']}</h4>
                        <p><strong>Amount:</strong> {transaction['amount']:,.0f} ₸ | <strong>Type:</strong> {transaction['type'].title()}</p>
                        <p><strong>Category:</strong> {transaction['category']} | <strong>Frequency:</strong> {transaction['frequency']}</p>
                        <p><strong>Next Date:</strong> {transaction['next_date']} | <strong>Status:</strong> {status}</p>
                        {f"<p><em>{transaction['description']}</em></p>" if transaction['description'] else ""}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Edit button for recurring transaction
                    edit_recurring_key = f"edit_recurring_{transaction['id']}"
                    if st.button("✏️", key=f"edit_recurring_btn_{transaction['id']}", help="Edit recurring transaction"):
                        st.session_state[edit_recurring_key] = True

                    # Show edit form if edit button was clicked
                    if st.session_state.get(edit_recurring_key, False):
                        with st.expander(f"Edit Recurring - {transaction['name']}", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_name = st.text_input("Name", value=transaction['name'],
                                                        key=f"edit_recurring_name_{transaction['id']}")
                                edit_amount = st.number_input("Amount (₸)", min_value=0.0,
                                                            value=float(transaction['amount']), step=1000.0,
                                                            key=f"edit_recurring_amount_{transaction['id']}")
                                edit_category = st.text_input("Category", value=transaction['category'],
                                                            key=f"edit_recurring_category_{transaction['id']}")

                            with col2:
                                edit_type = st.selectbox("Type", ["income", "expense"],
                                                       index=["income", "expense"].index(transaction['type']),
                                                       key=f"edit_recurring_type_{transaction['id']}")
                                edit_frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "yearly"],
                                                            index=["daily", "weekly", "monthly", "yearly"].index(transaction['frequency']),
                                                            key=f"edit_recurring_frequency_{transaction['id']}")
                                edit_date = st.date_input("Next Date",
                                                        value=datetime.strptime(transaction['next_date'], '%Y-%m-%d').date(),
                                                        key=f"edit_recurring_date_{transaction['id']}")

                            edit_description = st.text_area("Description",
                                                          value=transaction.get('description', ''),
                                                          key=f"edit_recurring_desc_{transaction['id']}")

                            save_col, cancel_col = st.columns(2)
                            with save_col:
                                if st.button("💾 Update Recurring", key=f"save_recurring_{transaction['id']}"):
                                    try:
                                        db.update_recurring_transaction(
                                            transaction_id=transaction['id'],
                                            name=edit_name,
                                            amount=edit_amount,
                                            trans_type=edit_type,
                                            category=edit_category,
                                            frequency=edit_frequency,
                                            next_date=edit_date.isoformat(),
                                            description=edit_description
                                        )
                                        st.success(f"Updated recurring transaction: {edit_name}")
                                        st.session_state[edit_recurring_key] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating recurring transaction: {str(e)}")

                            with cancel_col:
                                if st.button("❌ Cancel", key=f"cancel_recurring_{transaction['id']}"):
                                    st.session_state[edit_recurring_key] = False
                                    st.rerun()

                with col3:
                    if st.button("🗑️", key=f"delete_recurring_{transaction['id']}", help="Delete recurring transaction"):
                        # Show confirmation
                        confirm_recurring_key = f"confirm_delete_recurring_{transaction['id']}"
                        st.session_state[confirm_recurring_key] = True

                    # Show confirmation if delete was clicked
                    confirm_recurring_key = f"confirm_delete_recurring_{transaction['id']}"
                    if st.session_state.get(confirm_recurring_key, False):
                        st.warning(f"Delete recurring transaction '{transaction['name']}'?")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("✅ Yes, Delete", key=f"confirm_recurring_yes_{transaction['id']}"):
                                db.delete_recurring_transaction(transaction['id'])
                                st.success("Recurring transaction deleted!")
                                st.session_state[confirm_recurring_key] = False
                                st.rerun()
                        with no_col:
                            if st.button("❌ No, Cancel", key=f"confirm_recurring_no_{transaction['id']}"):
                                st.session_state[confirm_recurring_key] = False
                                st.rerun()

                st.markdown("---")
        else:
            st.info("No recurring transactions set up yet. Add your first one in the 'Add Recurring' tab!")

def reports_page():
    st.title("📈 Financial Reports")
    st.markdown("Detailed analytics and insights")

    tab1, tab2, tab3 = st.tabs(["💰 Income vs Expenses", "📊 Category Analysis", "📅 Monthly Trends"])

    with tab1:
        st.subheader("Income vs Expenses Analysis")

        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365), key="report_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="report_end")

        if start_date <= end_date:
            # Get data for the period
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Total income
                cursor.execute('''
                    SELECT SUM(amount) FROM income_entries
                    WHERE date BETWEEN ? AND ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                total_income = cursor.fetchone()[0] or 0

                # Total expenses
                cursor.execute('''
                    SELECT SUM(amount) FROM expense_entries
                    WHERE date BETWEEN ? AND ?
                ''', (start_date.isoformat(), end_date.isoformat()))
                total_expenses = cursor.fetchone()[0] or 0

                # Net result
                net_result = total_income - total_expenses

            # Display summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Income", f"{total_income:,.0f} ₸")
            with col2:
                st.metric("Total Expenses", f"{total_expenses:,.0f} ₸")
            with col3:
                st.metric("Net Result", f"{net_result:,.0f} ₸")
            with col4:
                savings_rate = (net_result / total_income * 100) if total_income > 0 else 0
                st.metric("Savings Rate", f"{savings_rate:.1f}%")

            # Income vs Expenses chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Income',
                x=['Period'],
                y=[total_income],
                marker_color='#a3be8c'
            ))
            fig.add_trace(go.Bar(
                name='Expenses',
                x=['Period'],
                y=[total_expenses],
                marker_color='#bf616a'
            ))

            fig.update_layout(
                title='Income vs Expenses',
                barmode='group',
                plot_bgcolor='#2e3440',
                paper_bgcolor='#2e3440',
                font_color='#d8dee9'
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Start date must be before end date.")

    with tab2:
        st.subheader("Category Analysis")

        # Expense categories breakdown
        expense_categories = db.get_expenses_by_category()

        if expense_categories:
            # Pie chart
            labels = list(expense_categories.keys())
            values = list(expense_categories.values())

            fig = px.pie(
                names=labels,
                values=values,
                title='Expense Distribution by Category'
            )
            fig.update_layout(
                plot_bgcolor='#2e3440',
                paper_bgcolor='#2e3440',
                font_color='#d8dee9'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            st.subheader("Category Details")
            df_categories = pd.DataFrame({
                'Category': labels,
                'Amount': values
            })
            df_categories['Percentage'] = (df_categories['Amount'] / df_categories['Amount'].sum() * 100).round(1)
            df_categories = df_categories.sort_values('Amount', ascending=False)
            st.dataframe(df_categories, use_container_width=True)
        else:
            st.info("No expense data available for analysis.")

    with tab3:
        st.subheader("Monthly Trends")

        # Get monthly data for the last 12 months
        months = []
        income_trend = []
        expense_trend = []

        for i in range(11, -1, -1):
            month_date = datetime.now() - timedelta(days=30*i)
            month_year = month_date.strftime("%Y-%m")

            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Monthly income
                cursor.execute('''
                    SELECT SUM(amount) FROM income_entries
                    WHERE strftime('%Y-%m', date) = ?
                ''', (month_year,))
                income = cursor.fetchone()[0] or 0

                # Monthly expenses
                cursor.execute('''
                    SELECT SUM(amount) FROM expense_entries
                    WHERE strftime('%Y-%m', date) = ?
                ''', (month_year,))
                expenses = cursor.fetchone()[0] or 0

            months.append(month_year)
            income_trend.append(income)
            expense_trend.append(expenses)

        # Create trend chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=income_trend,
            mode='lines+markers',
            name='Income',
            line=dict(color='#a3be8c')
        ))
        fig.add_trace(go.Scatter(
            x=months,
            y=expense_trend,
            mode='lines+markers',
            name='Expenses',
            line=dict(color='#bf616a')
        ))

        fig.update_layout(
            title='12-Month Income vs Expenses Trend',
            xaxis_title='Month',
            yaxis_title='Amount (₸)',
            plot_bgcolor='#2e3440',
            paper_bgcolor='#2e3440',
            font_color='#d8dee9'
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    auth.ensure_authenticated()

    # Process any due recurring transactions on app start
    try:
        db.process_recurring_transactions()
    except Exception as e:
        st.sidebar.warning(f"Could not process recurring transactions: {str(e)}")

    page = sidebar()

    if page == "Dashboard":
        dashboard_page()
    elif page == "Bank Accounts":
        bank_accounts_page()
    elif page == "Personal Finance":
        personal_finance_page()
    elif page == "SAT Tutoring":
        sat_tutoring_page()
    elif page == "Budgets":
        budgets_page()
    elif page == "Goals":
        goals_page()
    elif page == "Recurring":
        recurring_page()
    elif page == "Reports":
        reports_page()
    elif page == "Backup Data":
        backup_page()

if __name__ == "__main__":
    main()