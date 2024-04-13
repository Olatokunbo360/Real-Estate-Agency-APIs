# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 11:37:30 2024

@author: Yusuf Sanni

This is a Python API  for  generating a list of payers that exist on the system.
It uses a phone number as a request data and provides the corressponding information
for that phone number if it exists on the database in a table also called payers_list.

All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.

"""

from flask import Flask, jsonify, request
import mysql.connector
import logging 
from logging.handlers import RotatingFileHandler
from datetime import datetime

app = Flask(__name__)

# Database Configuration
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

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler('api.log', maxBytes=1024*1024, backupCount=10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

mysql_handler = MySQLHandler(db_config)
mysql_handler.setLevel(logging.DEBUG)
mysql_handler.setFormatter(formatter)
logger.addHandler(mysql_handler)

# Function to connect to MySQL database
def connect_to_database():
    try:
        db_connection = mysql.connector.connect(**db_config)
        return db_connection
    except mysql.connector.Error as error:
        logger.error("Error connecting to MySQL database: %s", error)
        return None

# API Endpoint for checking phone number in payers_list
@app.route('/check_phone_number', methods=['GET','POST'])
def check_phone_number():
    try:
        # Log the request
        unique_ref = request.headers.get('Request-ID')
        logger.info("Received request: %s", request.json, extra={'endpoint': '/check_phone_number', 'activity_type': 'request', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Request received', 'user_id': 'user_id_placeholder'})

        # Get phone number from request
        phone_number = request.json.get('phone_number')

        # Connect to the database
        db_connection = connect_to_database()
        if db_connection:
            cursor = db_connection.cursor(dictionary=True)
            try:
                # Check if phone number exists in payers_list
                query = "SELECT payerRef, Fullname, phoneNumber1, address FROM payers_list WHERE phoneNumber1 = %s"
                cursor.execute(query, (phone_number,))
                payer_info = cursor.fetchone()

                # Log the response
                if payer_info:
                    logger.info("Response: %s", payer_info, extra={'endpoint': '/check_phone_number', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Data retrieved', 'user_id': 'user_id_placeholder'})
                else:
                    logger.info("Phone number not found", extra={'endpoint': '/check_phone_number', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Phone number not found', 'user_id': 'user_id_placeholder'})

                # Close cursor and connection
                cursor.close()
                db_connection.close()

                if payer_info:
                    return jsonify(payer_info), 200
                else:
                    return jsonify({'message': 'Phone number not found'}), 404
            except mysql.connector.Error as error:
                logger.error("Database error: %s", error, extra={'endpoint': '/check_phone_number', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Database error', 'user_id': 'user_id_placeholder'})
                cursor.close()
                db_connection.close()
                return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error("Error processing request: %s", e, extra={'endpoint': '/check_phone_number', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Error processing request', 'user_id': 'user_id_placeholder'})
        return jsonify({'error': 'Error processing request'}), 400

if __name__ == '__main__':
    app.run(debug=False)
