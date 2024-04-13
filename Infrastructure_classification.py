# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 10:12:31 2024

@author: Yusuf Sanni

This is a Python API  for getting the classification of infrastructure from the database
This is a GET action.
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify
import mysql.connector
import logging 
import uuid

app = Flask(__name__)

# Set up logging 
logging.basicConfig(filename='api_audit.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration
db_config = {
    'host': 'Enter IP Address Here',
    'user': 'Enter username here',
    'password': 'Enter password here',
    'database': 'Enter DB here'
}

# Function to connect to MySQL database
def connect_to_database():
    try:
        db_connection = mysql.connector.connect(**db_config)
        return db_connection
    except mysql.connector.Error as error:
        logging.error("Error connecting to MySQL database: %s", error)
        return None

# API Endpoint for fetching data from infrastructureclassification table
@app.route('/api/infrastructureclassification', methods=['GET'])
def get_infrastructure_classification():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /api/infrastructureclassification - Activity Type: request - Request ID: %s - Message: Request received", request_id)
    
    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Fetch data from infrastructureclassification table
            cursor.execute("SELECT * FROM infrastructureclassification")
            data = cursor.fetchall()
            
            # Log the response
            logging.info("Endpoint: /api/infrastructureclassification - Activity Type: response - Request ID: %s - Message: Data retrieval successful", request_id)
            
            # Close cursor and connection
            cursor.close()
            db_connection.close()
            
            # Return data in JSON format
            return jsonify({'data': data}), 200
        except mysql.connector.Error as error:
            logging.error("Endpoint: /api/infrastructureclassification - Activity Type: response - Request ID: %s - Message: Data retrieval failed - Error: %s", request_id, error)
            cursor.close()
            db_connection.close()
            return jsonify({'error': 'Data retrieval failed'}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
