# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 15:48:05 2024

@author: Yusuf Sanni

This is a Python API  for  generating a list of infrastructure that is currently 
vacant. It uses the AgencyID and LocId as identifiers to know the particular locations
and agency we would like to check which properties are vacant (StatusId = 3 is the status
for vacant properties)
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify, request
import mysql.connector
import logging 
import uuid
import requests

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

# Function to get UserId from /login API
def get_user_id(agency_id):
    try:
        response = requests.post('http://localhost:5000/login', json={'agency_id': agency_id})
        data = response.json()
        user_id = data.get('user_id')
        return user_id
    except Exception as e:
        logging.error("Error getting UserId: %s", e)
        return None

# API Endpoint for fetching data from infrastructure_list
@app.route('/fetch_infrastructure_data', methods=['GET'])
def fetch_infrastructure_data():
    # Log the request
    unique_ref = str(uuid.uuid4())
    logging.info("Endpoint Name: fetch_infrastructure_data - Activity Type: request - Activity Action: API call - UniqueRef: %s - ContentDump: Request received", unique_ref)

    # Get parameters from request
    agency_id = request.args.get('agency_id')
    loc_id = request.args.get('loc_id')

    try:
        # Connect to the database
        db_connection = connect_to_database()
        if db_connection:
            cursor = db_connection.cursor(dictionary=True)
            try:
                # Fetch data from infrastructure_list where AgencyId, LocId, and statusId=3
                query = "SELECT infrastructureId, infrastructureRef, infralocId, infraName, LocDescription, ClosestLandmark FROM infrastructure_list WHERE AgencyId = %s AND LocId = %s AND statusId = 3"
                cursor.execute(query, (agency_id, loc_id))
                infrastructure_data = cursor.fetchall()

                # Log the response
                user_id = get_user_id(agency_id)
                logging.info("Endpoint Name: fetch_infrastructure_data - Activity Type: response - Activity Action: API call - UniqueRef: %s - ContentDump: Data retrieved - UserId: %s", unique_ref, user_id)

                # Close cursor and connection
                cursor.close()
                db_connection.close()

                # Return response in JSON format
                return jsonify({'status': 'success', 'data': infrastructure_data}), 200
            except mysql.connector.Error as error:
                logging.error("Endpoint Name: fetch_infrastructure_data - Activity Type: response - Activity Action: API call - UniqueRef: %s - ContentDump: Database error - Error: %s", unique_ref, error)
                cursor.close()
                db_connection.close()
                return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logging.error("Endpoint Name: fetch_infrastructure_data - Activity Type: response - Activity Action: API call - UniqueRef: %s - ContentDump: Error processing request - Error: %s", unique_ref, e)
        return jsonify({'error': 'Error processing request'}), 400

if __name__ == '__main__':
    app.run(debug=False)
