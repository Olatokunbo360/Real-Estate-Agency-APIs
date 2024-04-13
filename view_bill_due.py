# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 10:08:21 2024

@author: Yusuf Sanni

Displays the details of what is due on said infrastructure(s).
The payRef is used to obtain the amount due for all properties/infrastructures 
mapped to thatpayRef and just for an infrastructure when the infrastructureRef 
is provided. A unique TransRef for each request is also generated.
This is a GET action . All the information pulled from the tables should be stored
on the "payment_request_log" table for each infrastructure before it is summed
up and returned as AmountDue.
 
All requests and responses are in JSON format. It gets information from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, request, jsonify
import mysql.connector
import logging
import datetime
import secrets
import requests
import uuid

app = Flask(__name__)


# Database connection details
# Configure database details
db_config = {
    'host': 'Enter IP address here',
    'user': 'Enter username here',
    'password': 'Enter password here',
    'database': 'Enter DB name here'
    }

# Custom log handler to insert log details into MySQL table
class MySQLHandler(logging.Handler):
    def __init__(self, db_config):
        logging.Handler.__init__(self)
        self.db_config = db_config

    def emit(self, record):
        try:
            db_connection = mysql.connector.connect(**self.db_config)
            cursor = db_connection.cursor()
            query = "INSERT INTO api_audit_log (endpointName, activityType, activityAction, UniqueRef, contentdump, userId, dated) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (record.endpoint, record.activity_type, record.activity_action, record.unique_ref, record.content_dump, record.user_id, datetime.now())
            cursor.execute(query, values)
            db_connection.commit()
            cursor.close()
            db_connection.close()
        except Exception as e:
            print("Error inserting log into database:", e)

# Generate unique reference number for each request
def generate_unique_ref():
    return str(uuid.uuid4())

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

mysql_handler = MySQLHandler(db_config)
mysql_handler.setLevel(logging.DEBUG)
mysql_handler.setFormatter(formatter)
logger.addHandler(mysql_handler)


# Helper function to fetch user ID from login API
def get_user_id(token):
    try:
        # Assuming the login API endpoint is at http://localhost:5000/login
        login_api_url = 'http://localhost:5000/login'
        
        # Set the headers with the token for authentication
        headers = {'Authorization': f'Bearer {token}'}

        # Making a GET request to the login API to fetch user details
        response = requests.get(login_api_url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Assuming the response contains user information including user ID
            user_data = response.json()
            user_id = user_data.get('userId')
            return user_id
        else:
            print(f"Error: Unable to fetch user ID. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

    return 'user_id_placeholder'

# Helper function to generate unique payment reference
def generate_payment_ref():
    return secrets.token_hex(8)

# Helper function to fetch payment channel ID
def get_payment_channel_id(payment_channel_name):
    try:

        # Create a cursor to execute SQL queries
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Prepare the SQL query to fetch the payment channel ID
        query = "SELECT paymentchannelId FROM payment_channellookup WHERE paymentChannel = %s"

        # Execute the query with the payment channel name as parameter
        cursor.execute(query, (payment_channel_name,))

        # Fetch the payment channel ID from the result
        payment_channel_id = cursor.fetchone()[0]  # Assuming paymentChannelID is the first column

        # Close cursor and database connection
        cursor.close()
        db_config.close()

        return payment_channel_id

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


@app.route('/process_payment_request', methods=['GET','POST'])
def process_payment_request():
    try:
        # Generate unique reference number for logging
        unique_ref = secrets.token_hex(16)

        # Extract data from request
        request_data = request.json
        payer_ref = request_data.get('payerRef')
        infrastructure_ref = request_data.get('infrastructureRef')

        # Connect to MySQL database
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Check if payerRef exists in payer_infrastructure_mapping table
        query = "SELECT infralocId, statusId FROM payer_infrastructure_mapping WHERE payerRef = %s"
        cursor.execute(query, (payer_ref,))
        result = cursor.fetchone()

        if result:
            infra_loc_id, status_id = result

            # Check if infraLocId exists in revenueitem_infrastructure_feelookup table
            query = "SELECT Basefee FROM revenueitem_infrastructure_feelookup WHERE infralocId = %s"
            cursor.execute(query, (infra_loc_id,))
            base_fees = cursor.fetchall()

            if base_fees:
                # Calculate total amount due
                total_amt_due = sum([fee[0] for fee in base_fees])

                # Generate unique payment reference
                payment_ref = generate_payment_ref()

                # Get payment channel ID
                payment_channel_id = get_payment_channel_id()

                # Get user ID from login API
                handled_by = get_user_id()

                # Insert payment request details into payment_request_log table
                query = "INSERT INTO payment_request_log (paymentRef, payerRef, infrastructureRef, paymentchannelID, handledby, statusId, totalAmtDue) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (payment_ref, payer_ref, infrastructure_ref, payment_channel_id, handled_by, status_id, total_amt_due))
                db.commit()

                db.close()

                return jsonify({'message': 'Payment request processed successfully', 'paymentRef': payment_ref}), 200
            else:
                db.close()
                return jsonify({'error': 'No base fees found for infraLocId'}), 404
        else:
            db.close()
            return jsonify({'error': 'PayerRef not found'}), 404

    except Exception as e:
        logger.error("Error processing payment request: %s", str(e), extra={'endpoint': '/process_payment_request', 'activity_type': 'error', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': str(e), 'user_id': None})
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run()
