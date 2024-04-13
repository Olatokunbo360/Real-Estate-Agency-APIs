# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 12:57:07 2024

@author: Yusuf Sanni

This is a Python API  for getting the list of statuses available for use from the database.
In other words, it checks the statuses of the different available infrastructure to know which
is vacant or occupied. It pulls this information from a table called status_lookup in the DB.

This is a GET action.
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify
import mysql.connector
import logging 
import json
import uuid

app = Flask(__name__)

# Set up logging 
logging.basicConfig(filename='api_audit.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration
db_config = {
   'host': 'Enter IP address here',
   'user': 'Enter username here',
   'password': 'Enter password here',
   'database': 'Enter DB name here'
}

# Function to connect to MySQL database
def connect_to_database():
    try:
        db_connection = mysql.connector.connect(**db_config)
        return db_connection
    except mysql.connector.Error as error:
        logging.error("Error connecting to MySQL database: %s", error)
        return None

# API Endpoint for fetching status list from status_lookup table
@app.route('/statusList', methods=['GET'])
def get_status_list():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /statusList - Activity Type: request - Request ID: %s - Message: Request received", request_id)
    
    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Fetch data from status_lookup table
            query = "SELECT statusId, StatusDesc FROM status_lookup"
            cursor.execute(query)
            data = cursor.fetchall()

            # Log the response
            logging.info("Endpoint: /statusList - Activity Type: response - Request ID: %s - Message: Data retrieval successful", request_id)
            
            # Close cursor and connection
            cursor.close()
            db_connection.close()
            
            # Return data in JSON format
            return jsonify({'status_list': data}), 200
        except mysql.connector.Error as error:
            logging.error("Endpoint: /statusList - Activity Type: response - Request ID: %s - Message: Data retrieval failed - Error: %s", request_id, error)
            cursor.close()
            db_connection.close()
            return jsonify({'error': 'Data retrieval failed'}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
