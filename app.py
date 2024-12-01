from flask import Flask, jsonify, render_template
from nse import NSE
from pathlib import Path
from datetime import datetime, timedelta
import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta
app = Flask(__name__)

DOWNLOAD_FOLDER = Path(os.getenv('DOWNLOAD_FOLDER', 'nse_downloads'))
DOWNLOAD_FOLDER.mkdir(exist_ok=True)
# Add these configurations to your existing Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscription.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv('GMAIL_USERNAME')  # Set this in environment variables
SMTP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')  # Set this in environment variables
SENDER_EMAIL = os.getenv('GMAIL_USERNAME')

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.email} - {self.symbol}>'

def send_email(recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"Email sent successfully to {recipient} for {subject}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def check_and_send_alerts():
    try:
        with get_nse_client() as nse:
            # Get all subscriptions
            subscriptions = Subscription.query.all()
            
            for sub in subscriptions:
                # Check announcements
                announcements = nse.announcements(
                    symbol=sub.symbol,
                    from_date=datetime.now() - timedelta(days=1),
                    to_date=datetime.now()
                )
                
                # Check corporate actions
                actions = nse.actions(
                    symbol=sub.symbol,
                    from_date=datetime.now() - timedelta(days=1),
                    to_date=datetime.now()
                )
                
                # Check board meetings
                meetings = nse.boardMeetings(
                    symbol=sub.symbol,
                    from_date=datetime.now() - timedelta(days=1),
                    to_date=datetime.now()
                )
                
                # Prepare and send alerts if there's any new information
                if announcements or actions or meetings:
                    subject = f"Stock Alert: Updates for {sub.symbol}"
                    body = f"""
                    <h2>Updates for {sub.symbol}</h2>
                    """
                    
                    if announcements:
                        body += """
                        <h3>Latest Announcements:</h3>
                        <ul>
                        """
                        for ann in announcements:
                            body += f"<li>{ann.get('desc', 'N/A')} - {ann.get('an_dt', 'N/A')}</li>"
                        body += "</ul>"
                    
                    if actions:
                        body += """
                        <h3>Corporate Actions:</h3>
                        <ul>
                        """
                        for action in actions:
                            body += f"<li>{action.get('subject', 'N/A')} - {action.get('exDate', 'N/A')}</li>"
                        body += "</ul>"
                    
                    if meetings:
                        body += """
                        <h3>Board Meetings:</h3>
                        <ul>
                        """
                        for meeting in meetings:
                            body += f"<li>{meeting.get('purpose', 'N/A')} - {meeting.get('meetingDate', 'N/A')}</li>"
                        body += "</ul>"
                    
                    send_email(sub.email, subject, body)
                    
    except Exception as e:
        print(f"Error in alert system: {str(e)}")

# Add these new routes to your Flask app
@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    try:
        data = request.json
        email = data.get('email')
        symbol = data.get('symbol')
        
        if not email or not symbol:
            return jsonify({'error': 'Email and symbol are required'}), 400
            
        # Check if subscription already exists
        existing = Subscription.query.filter_by(email=email, symbol=symbol).first()
        if existing:
            return jsonify({'error': 'Subscription already exists'}), 400
            
        # Create new subscription
        subscription = Subscription(email=email, symbol=symbol)
        db.session.add(subscription)
        db.session.commit()
        
        # Send confirmation email
        subject = f"Subscription Confirmed: {symbol}"
        body = f"""
        <h2>Subscription Confirmed</h2>
        <p>You have successfully subscribed to alerts for {symbol}.</p>
        <p>You will receive notifications for:</p>
        <ul>
            <li>Company Announcements</li>
            <li>Corporate Actions</li>
            <li>Board Meetings</li>
        </ul>
        """
        send_email(email, subject, body)
        
        return jsonify({'message': 'Subscription successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe():
    try:
        data = request.json
        email = data.get('email')
        symbol = data.get('symbol')
        
        if not email or not symbol:
            return jsonify({'error': 'Email and symbol are required'}), 400
            
        subscription = Subscription.query.filter_by(email=email, symbol=symbol).first()
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
            return jsonify({'message': 'Unsubscribed successfully'}), 200
        else:
            return jsonify({'error': 'Subscription not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database
with app.app_context():
    db.create_all()

# Schedule alert checks (you can use APScheduler or a similar library)

def get_nse_client():
    return NSE(download_folder=DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('stocks.html')

@app.route('/api/stock/<symbol>')
def stock_info(symbol):
    with get_nse_client() as nse:
        try:
            meta = nse.equityMetaInfo(symbol)
            quote = nse.quote(symbol, section='trade_info')
            return jsonify({
                'meta': meta,
                'quote': quote
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/quote/<symbol>')
def equity_quote(symbol):
    with get_nse_client() as nse:
        try:
            return jsonify(nse.equityQuote(symbol))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/market/advance-decline')
def advance_decline():
    try:
        with get_nse_client() as nse:
            data = nse.advanceDecline()
            return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/gainers/<index_type>')
def top_gainers(index_type):
    with get_nse_client() as nse:
        try:
            if index_type == 'fno':
                data = nse.listFnoStocks()
            elif index_type == 'sme':
                data = nse.listSME()
            else:
                data = nse.listIndexStocks('NIFTY 50')
            return jsonify(nse.gainers(data, count=10))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/market/losers/<index_type>')
def top_losers(index_type):
    with get_nse_client() as nse:
        try:
            if index_type == 'fno':
                data = nse.listFnoStocks()
            elif index_type == 'sme':
                data = nse.listSME()
            else:
                data = nse.listIndexStocks('NIFTY 50')
            return jsonify(nse.losers(data, count=10))
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/corporate/actions')
def get_corporate_actions():
    from flask import request
    try:
        segment = request.args.get('segment', 'equities')
        symbol = request.args.get('symbol')
        from_date = datetime.strptime(request.args.get('from_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')), '%Y-%m-%d')
        to_date = datetime.strptime(request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')

        with get_nse_client() as nse:
            return jsonify(nse.actions(
                segment=segment,
                symbol=symbol,
                from_date=from_date,
                to_date=to_date
            ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/corporate/announcements')
def get_announcements():
    from flask import request
    try:
        index = request.args.get('index', 'equities')
        symbol = request.args.get('symbol')
        fno = request.args.get('fno', '').lower() == 'true'
        from_date = datetime.strptime(request.args.get('from_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')), '%Y-%m-%d')
        to_date = datetime.strptime(request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')

        with get_nse_client() as nse:
            return jsonify(nse.announcements(
                index=index,
                symbol=symbol,
                fno=fno,
                from_date=from_date,
                to_date=to_date
            ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/corporate/board-meetings')
def get_board_meetings():
    from flask import request
    try:
        index = request.args.get('index', 'equities')
        symbol = request.args.get('symbol')
        fno = request.args.get('fno', '').lower() == 'true'
        from_date = datetime.strptime(request.args.get('from_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')), '%Y-%m-%d')
        to_date = datetime.strptime(request.args.get('to_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')

        with get_nse_client() as nse:
            return jsonify(nse.boardMeetings(
                index=index,
                symbol=symbol,
                fno=fno,
                from_date=from_date,
                to_date=to_date
            ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_send_alerts, trigger="interval", hours=1)
scheduler.start()
if __name__ == '__main__':
    app.run(debug=True)