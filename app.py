from flask import Flask, jsonify, render_template
from nse import NSE
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

app = Flask(__name__)

# Configure download folder
DOWNLOAD_FOLDER = Path(os.getenv('DOWNLOAD_FOLDER', 'nse_downloads'))
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

def get_nse_client():
    """Create NSE client with context management"""
    return NSE(download_folder=DOWNLOAD_FOLDER)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime object"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    return jsonify({
        'error': str(error),
        'type': error.__class__.__name__
    }), 500

@app.route('/api/status')
def get_market_status():
    """Get NSE market status"""
    with get_nse_client() as nse:
        return jsonify(nse.status())

@app.route('/api/holidays/<type>')
def get_holidays(type):
    """Get NSE holidays by type (trading/clearing)"""
    if type not in ['trading', 'clearing']:
        return jsonify({'error': 'Invalid holiday type'}), 400
    
    with get_nse_client() as nse:
        return jsonify(nse.holidays(type=type))

@app.route('/api/block-deals')
def get_block_deals():
    """Get NSE block deals"""
    with get_nse_client() as nse:
        return jsonify(nse.blockDeals())

@app.route('/api/actions')
def get_corporate_actions():
    """Get corporate actions with optional filters"""
    from flask import request
    
    segment = request.args.get('segment', 'equities')
    if segment not in ['equities', 'sme', 'debt', 'mf']:
        return jsonify({'error': 'Invalid segment'}), 400
        
    symbol = request.args.get('symbol')
    from_date = parse_date(request.args.get('from_date'))
    to_date = parse_date(request.args.get('to_date'))
    
    with get_nse_client() as nse:
        return jsonify(nse.actions(
            segment=segment,
            symbol=symbol,
            from_date=from_date,
            to_date=to_date
        ))

@app.route('/api/announcements')
def get_announcements():
    """Get corporate announcements with optional filters"""
    from flask import request
    
    index = request.args.get('index', 'equities')
    if index not in ['equities', 'sme', 'debt', 'mf', 'invitsreits']:
        return jsonify({'error': 'Invalid index'}), 400
        
    symbol = request.args.get('symbol')
    fno = request.args.get('fno', 'false').lower() == 'true'
    from_date = parse_date(request.args.get('from_date'))
    to_date = parse_date(request.args.get('to_date'))
    
    with get_nse_client() as nse:
        return jsonify(nse.announcements(
            index=index,
            symbol=symbol,
            fno=fno,
            from_date=from_date,
            to_date=to_date
        ))

@app.route('/api/board-meetings')
def get_board_meetings():
    """Get board meetings with optional filters"""
    from flask import request
    
    index = request.args.get('index', 'equities')
    if index not in ['equities', 'sme']:
        return jsonify({'error': 'Invalid index'}), 400
        
    symbol = request.args.get('symbol')
    fno = request.args.get('fno', 'false').lower() == 'true'
    from_date = parse_date(request.args.get('from_date'))
    to_date = parse_date(request.args.get('to_date'))
    
    with get_nse_client() as nse:
        return jsonify(nse.boardMeetings(
            index=index,
            symbol=symbol,
            fno=fno,
            from_date=from_date,
            to_date=to_date
        ))

if __name__ == '__main__':
    app.run(debug=True)