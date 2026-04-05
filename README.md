# 💰 Financial Tracker (KZT)

A professional, local desktop application for tracking personal finances and SAT tutoring business in Kazakhstani Tenge (₸). Built with Python, Streamlit, and SQLite for complete offline functionality.

## ✨ Features

### 🏠 Dashboard
- **Net Worth Overview**: Bank balances + total income + student payments - expenses
- **Bank Account Monitoring**: Real-time balances for Kaspi, Freedom, and Halyk banks
- **Pending Debt Tracking**: Real-time student debt calculations in ₸
- **Monthly Profit Chart**: Interactive bar chart showing profit trends in ₸
- **Expense Distribution**: Pie chart breakdown by category

### 🏦 Bank Accounts
- **Multi-Bank Support**: Kaspi, Freedom, and Halyk bank accounts
- **Balance Tracking**: Real-time balance updates for each bank
- **Transaction Recording**: Deposit, withdrawal, and transfer tracking
- **Transaction History**: Complete audit trail with delete functionality

### 📊 Budgets & Goals
- **Monthly Budgets**: Set spending limits by category with progress tracking
- **Budget Alerts**: Real-time notifications when approaching/over budget
- **Financial Goals**: Set savings targets with progress visualization
- **Goal Tracking**: Monitor progress towards financial objectives

### 📈 Advanced Analytics
- **Detailed Reports**: Income vs expenses analysis with date ranges
- **Category Breakdown**: Pie charts and detailed spending analysis
- **Trend Analysis**: 12-month income and expense trends
- **Search & Filtering**: Advanced search and sorting in transaction history
- **Recurring Transactions**: Automated recurring income and expenses

### 💰 Personal Finance
- **Income Tracking**: Log salary, freelance work, investments, etc.
- **Expense Management**: Categorize spending (Food, Rent, Utilities, etc.)
- **Transaction History**: View and delete entries with full history

### 🎓 Enhanced SAT Tutoring Management
- **Hourly Rate System**: Set hourly rates and agreed lesson hours instead of fixed prices
- **Lesson Tracking**: Record individual lessons with topics, duration, and notes
- **Earnings Calculation**: Automatic calculation based on actual lessons conducted
- **Advanced Debt Management**: Debt based on earnings vs payments received
- **Prepayment System**: Track advance payments and calculate remaining lesson obligations
- **Bank-Linked Payments**: Payments automatically update bank account balances (Kaspi, Freedom, Halyk)
- **Comprehensive Analytics**: Detailed payment summaries and lesson progress tracking
- **Full Edit Capability**: Edit student info, lesson details, and payment records
- **Data Integrity**: All edits maintain financial accuracy and bank balance consistency

### 💾 Data Safety
- **Local SQLite Database**: All data stored locally in `finance_vault.db`
- **Bank Account Security**: Sensitive financial data stored securely offline
- **CSV Backup**: Export all data including bank accounts and transactions to timestamped CSV files
- **Offline Operation**: No internet connection required

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download this project**
   ```bash
   cd /path/to/financial_tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run_app.py
   ```

The app will open in your default web browser at `http://localhost:8501`.

## 📱 Desktop App Usage

The app is designed to run as a desktop application with these characteristics:

- **Modern Dark Theme**: Professional, sophisticated aesthetic with a refined color palette and improved component styling.
- **Enhanced Typography**: Cleaner, more readable fonts (Inter, sans-serif) for all text and headings.
- **Visually Cohesive**: All elements, from interactive forms to Plotly charts, seamlessly integrate with the dark theme.
- **Premium Look**: Metric cards, dataframes, and alert messages have been restyled for a more polished and modern feel.
- **Responsive Layout**: Adapts beautifully to various screen sizes, ensuring a consistent and optimal user experience.
- **Local Data**: All data stored in SQLite database
- **No Internet Required**: Fully offline operation

## 🗂️ Project Structure

```
financial_tracker/
├── app.py              # Main Streamlit application
├── database.py         # SQLite database operations
├── run_app.py          # Desktop app launcher
├── requirements.txt    # Python dependencies
├── finance_vault.db    # SQLite database (created automatically)
└── backups/            # CSV backup files (created on demand)
```

## 💡 Usage Guide

### Currency
All amounts are displayed in Kazakhstani Tenge (₸) with no decimal places for cleaner display (e.g., "50,000 ₸").

### Adding Students
1. Navigate to "SAT Tutoring" → "Students" tab
2. Fill in student name, course name, total price, and start date
3. Click "Add Student"

### Recording Payments
1. Go to "SAT Tutoring" → "Payments" tab
2. Select student from dropdown
3. Enter payment amount, date, and method
4. Click "Record Payment"

### Tracking Personal Finances
1. Use "Personal Finance" section
2. Add income in the "Income" tab
3. Add expenses in the "Expenses" tab
4. View history and delete entries as needed

### Managing Bank Accounts
1. Navigate to "Bank Accounts" → "Account Overview" tab
2. View current balances for all banks
3. Update balances manually or record transactions
4. Use "Transactions" tab to add deposits, withdrawals, or transfers

### Setting Up Budgets
1. Go to "Budgets" → "Monthly Budgets"
2. Select month and category
3. Set budget amounts for each spending category
4. Monitor progress on dashboard and get alerts

### Managing SAT Tutoring
1. Go to "SAT Tutoring" → "Students" tab
2. Add students with hourly rates and agreed lesson hours
3. **Quick Actions**: Use "Add Lesson" or "↶ Undo" buttons for fast lesson management
4. **Edit Anytime**: Click "✏️ Edit" to modify student information with responsive forms
5. Use "Lessons" tab to record detailed lesson information
6. **Edit Lessons**: Modify lesson details (duration, topics, notes) after recording
7. Record payments in "Payments" tab, automatically linked to bank accounts
8. **Edit Payments**: Correct payment amounts, dates, or bank accounts
9. Monitor comprehensive earnings, debt, and prepayment analytics

**Enhanced Features:**
- ✏️ **Responsive Edit Forms**: Wider, adaptive forms that scale with content
- ↶ **Undo Functionality**: Quickly remove accidentally added lessons
- 💡 **Help Text**: Contextual help for all form fields
- 📊 **Real-time Calculations**: See updated totals as you edit
- 🛡️ **Confirmation Dialogs**: Prevent accidental deletions
- 🔄 **Automatic Updates**: All dependent calculations refresh instantly

### Creating Financial Goals
1. Navigate to "Goals" → "Active Goals"
2. Add goal name, target amount, and deadline
3. Update progress as you save
4. Track completion on the completed goals tab

### Using Advanced Reports
1. Go to "Reports" for detailed analytics
2. View income vs expenses analysis with custom date ranges
3. Analyze spending by category with pie charts
4. Track monthly trends over the past 12 months

### Creating Backups
1. Navigate to "Backup Data"
2. Click "Create Backup"
3. Download CSV files for all data including bank accounts and transactions

## 🔧 Technical Details

- **Database**: SQLite with automatic schema initialization and advanced data models
- **UI Framework**: Streamlit with custom dark theme CSS and a responsive design approach
- **Charts**: Plotly for interactive and visually cohesive data visualizations
- **Data Export/Import**: Robust CSV format for backups and flexible data recovery
- **Dependencies**: Minimal - Streamlit, Pandas, and Plotly

## 🔒 Data Security

- All data stored locally in SQLite database
- No data sent to external servers
- CSV backups for additional safety
- Database file: `finance_vault.db`

## 🆘 Troubleshooting

### App won't start
- Ensure Python 3.8+ is installed
- Run `pip install -r requirements.txt`
- Check that all files are in the same directory

### Database issues
- Delete `finance_vault.db` to reset (will recreate automatically)
- Check file permissions in the directory

### Browser issues
- Try a different browser (Chrome, Firefox, Safari recommended)
- Clear browser cache if charts don't display

## 📈 Future Enhancements

- [x] Budget tracking and alerts (✅ Implemented)
- [x] Financial goal setting (✅ Implemented)
- [x] Advanced reports and analytics (✅ Implemented)
- [x] Search and filtering (✅ Implemented)
- [x] Edit functionality for all data types (✅ Implemented)
- [x] Undo functionality for accidental actions (✅ Implemented)
- [x] Responsive UI with adaptive forms (✅ Implemented)
- [ ] Receipt/document attachment for expenses
- [ ] Student progress tracking beyond payments
- [ ] Invoice generation for SAT tutoring
- [ ] Tax report generation
- [ ] Investment tracking
- [ ] Password protection and security
- [ ] Bulk operations (import/export from CSV)
- [ ] Email notifications for budgets/goals
- [ ] Advanced forecasting and predictions

## 🤝 Contributing

This is a personal project, but feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests for improvements

## 📄 License

This project is for personal use. Modify and distribute as needed.