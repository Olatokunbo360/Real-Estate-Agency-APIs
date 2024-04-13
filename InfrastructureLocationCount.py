# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 11:05:16 2024

@author: Yusuf Sanni

This is a Python API  for getting the count of the different infrastructure as they exist from the database
The ID of the infrastructire is used in another API called InfrastructureEnumeration.
This is a GET action.
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify, request
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

# API Endpoint for fetching data from infrastructure_location_count table
@app.route('/api/infrastructure_location_count', methods=['GET'])
def get_infrastructure_location_count():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /api/infrastructure_location_count - Activity Type: request - Request ID: %s - Message: Request received", request_id)
    
    # Extract data from request
    agency_id = request.args.get('AgencyId')
    loc_id = request.args.get('LocId')

    if not agency_id or not loc_id:
        return jsonify({'error': 'AgencyId and LocId are required parameters'}), 400

    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Fetch data from infrastructure_location_count table
            query = "SELECT * FROM infrastructure_location_count WHERE AgencyId = %s AND LocId = %s"
            cursor.execute(query, (agency_id, loc_id))
            data = cursor.fetchone()

            if data:
                # Log the response
                logging.info("Endpoint: /api/infrastructure_location_count - Activity Type: response - Request ID: %s - Message: Data retrieval successful", request_id)
                
                # Close cursor and connection
                cursor.close()
                db_connection.close()
                
                # Return data in JSON format
                return jsonify({
                    'AgencyId': data['AgencyId'],
                    'LocId': data['LocId'],
                    'infralocId': data['infralocId'],
                    'totalCount': data['totalCount'],
                    'occupiedCount': data['occupiedCount'],
                    'vacantCount': data['vacantCount']
                }), 200
            else:
                # Log the response
                logging.info("Endpoint: /api/infrastructure_location_count - Activity Type: response - Request ID: %s - Message: Data not found", request_id)
                return jsonify({'error': 'Data not found'}), 404
        except mysql.connector.Error as error:
            logging.error("Endpoint: /api/infrastructure_location_count - Activity Type: response - Request ID: %s - Message: Data retrieval failed - Error: %s", request_id, error)
            cursor.close()
            db_connection.close()
            return jsonify({'error': 'Data retrieval failed'}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
