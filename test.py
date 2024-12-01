import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file (optional, if not directly in system env)
load_dotenv()

# Fetch credentials from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

def test_smtp_connection():
    try:
        # Create an SMTP object and establish a connection to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            # Login to the server using credentials
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            # Create a simple message
            msg = MIMEText('SMTP connection test successful!')
            msg['Subject'] = 'Test Email'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS  # Sending to self for testing

            # Send the email
            smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())
        
        print("Email sent successfully. SMTP connection is working.")

    except Exception as e:
        print(f"Failed to send email: {e}")

# Test the SMTP connection
if __name__ == '__main__':
    test_smtp_connection()
