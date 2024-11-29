from flask import Flask, jsonify, render_template
from nse import NSE
from pathlib import Path
from datetime import datetime, timedelta
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = Path(os.getenv('DOWNLOAD_FOLDER', 'nse_downloads'))
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

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

if __name__ == '__main__':
    app.run(debug=True)