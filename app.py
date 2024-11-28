from flask import Flask, render_template
from nse import NSE

# Initialize Flask app
app = Flask(__name__)

# Route to fetch and display NSE market status
@app.route("/")
def index():
    try:
        # Using the NSE API
        with NSE(download_folder=".") as nse:
            market_status = nse.status()  # Fetch market status
    except Exception as e:
        market_status = {"error": str(e)}

    # Pass market status to template
    return render_template("index.html", market_status=market_status)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
