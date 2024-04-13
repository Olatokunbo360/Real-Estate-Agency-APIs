# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 14:27:57 2024

@author: Yusuf Sanni

This is a Python API for printing the receipt for payment for an infrastructure. 
This is a GET action.

All requests and responses are in JSON format. It gets information from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

import logging
import mysql.connector
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a custom logging handler to insert log details into the MySQL database
class MySQLHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        try:
            # Connect to the MySQL database
            db_connection = mysql.connector.connect(
                host='Enter IP address here',
                user='Enter username here',
                password='Enter password here',
                database='Enter DB name here'
            )
            
            # Create a cursor to execute SQL queries
            cursor = db_connection.cursor()

            # Prepare the SQL query to insert log details into the table
            query = "INSERT INTO api_audit_log (endpointName, activityType, activityAction, UniqueRef, contentdump, userId, dated) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (
                record.endpointName,
                record.activityType,
                record.activityAction,
                record.UniqueRef,
                record.contentdump,
                record.userId,
                record.dated
            )

            # Execute the query
            cursor.execute(query, values)

            # Commit the changes and close cursor and database connection
            db_connection.commit()
            cursor.close()
            db_connection.close()

        except Exception as e:
            print(f"Error inserting log into database: {e}")

# Add the custom logging handler to the logger
custom_handler = MySQLHandler()
logger.addHandler(custom_handler)

def generate_unique_ref():
    return str(uuid.uuid4())

# Define your API endpoint
@app.route('/get_infrastructure_details', methods=['POST'])
def get_infrastructure_details():
    try:
        # Extract data from the request
        data = request.json
        InfrastructureRef = data.get('InfrastructureRef')
        userId = data.get('userId')

        # Connect to the MySQL database
        db_connection = mysql.connector.connect(
            host='Enter IP address here',
            user='Enter username here',
            password='Enter password here',
            database='Enter DB name here'
        )
        

        # Create a cursor to execute SQL queries
        cursor = db_connection.cursor()

        # Get infraName, ClosestLandMark, and LocId from infrastructure_list table
        query = "SELECT infraName, ClosestLandMark, locId FROM infrastructure_list WHERE InfrastructureRef = %s"
        cursor.execute(query, (InfrastructureRef,))
        infrastructure_data = cursor.fetchone()

        # Get LocName from infrastructure_location_lookup table using LocId
        locId = infrastructure_data[0]
        query = "SELECT LocName FROM infrastructure_location_lookup WHERE locId = %s"
        cursor.execute(query, (locId,))
        LocName = cursor.fetchone()[0]

        # Get payerRef from payer_infrastructure_mapping table using InfrastructureRef
        query = "SELECT payerRef FROM payer_infrastructure_mapping WHERE InfrastructureRef = %s"
        cursor.execute(query, (InfrastructureRef,))
        payerRef = cursor.fetchone()[0]

        # Get Fullname and phoneNumber1 from payers_list table using payerRef
        query = "SELECT Fullname, phoneNumber1 FROM payers_list WHERE payerRef = %s"
        cursor.execute(query, (payerRef,))
        payer_data = cursor.fetchone()

        # Get paymentRef, totalAmtDue, and paymentdated from payment_logs table using payerRef
        query = "SELECT paymentRef, totalAmtDue, paymentdated FROM payment_logs WHERE payerRef = %s"
        cursor.execute(query, (payerRef,))
        payment_data = cursor.fetchone()

        # Close cursor and database connection
        cursor.close()
        db_connection.close()

        # Log the request and response
        unique_ref = generate_unique_ref()  # Replace with actual implementation
        logger.info("Received request: %s", data, extra={'endpointName': '/get_infrastructure_details', 'activityType': 'request', 'activityAction': 'API call', 'UniqueRef': unique_ref, 'contentdump': 'Request received', 'userId': userId})
        logger.info("Sent response: %s", {"infraName": infrastructure_data[0], "ClosestLandMark": infrastructure_data[1], "LocName": LocName, "Fullname": payer_data[0], "phoneNumber1": payer_data[1], "paymentRef": payment_data[0], "totalAmtDue": payment_data[1], "paymentdated": payment_data[2]}, extra={'endpointName': '/get_infrastructure_details', 'activityType': 'response', 'activityAction': 'API call', 'UniqueRef': unique_ref, 'contentdump': 'Response sent', 'userId': userId})

        return jsonify({"infraName": infrastructure_data[0], "ClosestLandMark": infrastructure_data[1], "LocName": LocName, "Fullname": payer_data[0], "phoneNumber1": payer_data[1], "paymentRef": payment_data[0], "totalAmtDue": payment_data[1], "paymentdated": payment_data[2]}), 200

    except Exception as e:
        logger.error("Error processing request: %s", str(e), extra={'endpointName': '/get_infrastructure_details', 'activityType': 'error', 'activityAction': 'API call', 'UniqueRef': 'generate_unique_ref()', 'contentdump': 'Error processing request', 'userId': None})
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
