# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 12:49:45 2024

@author: Yusuf Sanni

This is a Python API  for listing the locations based on the userId or agencyId
provided in the Login API.This is a GET action.
All requests and responses are in JSON format. It gets infpormaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify # Flask creates the API, jsonify serialises the given argument as JSON
import mysql.connector # mySQL cdriver written in Python to connect to a MySQL DB
import logging # For creating log messages
import requests # Used for the GET or POST requests from or to an HTTP library
import uuid # Provide Universal Unique Identifiers for Logging

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

# Function to fetch data from Login API
def fetch_data_from_login_api():
    try:
        response = requests.get('http://127.0.0.1:5000/login')
        data = response.json()
        return data
    except Exception as e:
        logging.error("Error fetching data from Login API: %s", str(e))
        return None

# API Endpoint for fetching data from LocationList table
@app.route('/LocationList', methods=['GET'])
def get_location_list():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /LocationList - Activity Type: request - Request ID: %s - Message: Request received", request_id)
    
    # Fetch data from Login API
    login_data = fetch_data_from_login_api()
    if login_data is None:
        return jsonify({'error': 'Failed to fetch data from Login API'}), 500

    agency_id = login_data.get('AgencyId')
    user_id = login_data.get('userId')

    if not (agency_id and user_id):
        return jsonify({'error': 'Missing AgencyId or userId from Login API'}), 400

    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Fetch data from infrastructure_location_lookup table
            query = "SELECT LocId, LocName, Locations FROM infrastructure_location_lookup WHERE AgencyId = %s"
            cursor.execute(query, (agency_id,))
            data = cursor.fetchall()

            # Log the response
            logging.info("Endpoint: /LocationList - Activity Type: response - Request ID: %s - Message: Data retrieval successful", request_id)
            
            # Close cursor and connection
            cursor.close()
            db_connection.close()
            
            # Return data in JSON format
            return jsonify({'LocationList': data}), 200
        except mysql.connector.Error as error:
            logging.error("Endpoint: /LocationList - Activity Type: response - Request ID: %s - Message: Data retrieval failed - Error: %s", request_id, error)
            cursor.close()
            db_connection.close()
            return jsonify({'error': 'Data retrieval failed'}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
