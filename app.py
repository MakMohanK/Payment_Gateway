from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import re
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# In-memory storage for demonstration (use database in production)
transactions = []

def validate_card_number(card_number):
    """Validate card number using Luhn algorithm"""
    card_number = card_number.replace(" ", "").replace("-", "")
    if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Luhn algorithm
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10
    
    return luhn_checksum(card_number) == 0

def validate_cvv(cvv):
    """Validate CVV (3 or 4 digits)"""
    return bool(re.match(r'^\d{3,4}$', cvv))

def validate_expiry(expiry_month, expiry_year):
    """Validate card expiry date"""
    try:
        month = int(expiry_month)
        year = int(expiry_year)
        
        if month < 1 or month > 12:
            return False
        
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        if year < current_year:
            return False
        if year == current_year and month < current_month:
            return False
        
        return True
    except ValueError:
        return False

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/payment')
def payment():
    """Payment gateway page"""
    return render_template('payment.html')

@app.route('/process-payment', methods=['POST'])
def process_payment():
    """Process payment request"""
    try:
        # Get form data
        card_number = request.form.get('card_number', '').strip()
        cardholder_name = request.form.get('cardholder_name', '').strip()
        expiry_month = request.form.get('expiry_month', '').strip()
        expiry_year = request.form.get('expiry_year', '').strip()
        cvv = request.form.get('cvv', '').strip()
        amount = request.form.get('amount', '').strip()
        
        # Validation
        errors = []
        
        if not cardholder_name or len(cardholder_name) < 3:
            errors.append("Cardholder name must be at least 3 characters")
        
        if not validate_card_number(card_number):
            errors.append("Invalid card number")
        
        if not validate_cvv(cvv):
            errors.append("Invalid CVV (must be 3 or 4 digits)")
        
        if not validate_expiry(expiry_month, expiry_year):
            errors.append("Invalid or expired card")
        
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                errors.append("Amount must be greater than 0")
        except ValueError:
            errors.append("Invalid amount")
        
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        # Simulate payment processing
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}"
        
        transaction = {
            'transaction_id': transaction_id,
            'cardholder_name': cardholder_name,
            'card_last_four': card_number.replace(" ", "")[-4:],
            'amount': amount_float,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        transactions.append(transaction)
        session['last_transaction'] = transaction_id
        
        return jsonify({
            'success': True,
            'message': 'Payment processed successfully',
            'transaction_id': transaction_id,
            'amount': amount_float
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'errors': [f"Server error: {str(e)}"]
        }), 500

@app.route('/success')
def success():
    """Payment success page"""
    transaction_id = session.get('last_transaction')
    transaction = None
    
    if transaction_id:
        transaction = next((t for t in transactions if t['transaction_id'] == transaction_id), None)
    
    return render_template('success.html', transaction=transaction)

@app.route('/transactions')
def view_transactions():
    """View all transactions (for testing purposes)"""
    return render_template('transactions.html', transactions=transactions)

@app.route('/api/health')
def health_check():
    """Health check endpoint for testing"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
