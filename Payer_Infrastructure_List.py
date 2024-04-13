# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 11:42:14 2024

@author: Yusuf Sanni

This is a Python API that shows the mapping of a specified payer to infrastructures
i.e. it  can be a one to one or one to many relation. This is a GET action.

All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

import mysql.connector
import logging
import uuid
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)

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


def get_user_id(phone_number):
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT userId FROM user_list WHERE phoneNumber1 = %s"
        cursor.execute(query, (phone_number,))
        user_id = cursor.fetchone()[0]
        db.close()
        return user_id
    except Exception as e:
        logger.error("Error fetching user ID: %s", str(e))
        return None

# API Endpoint for retrieving payer details
@app.route('/get_payer_details', methods=['GET','POST'])
def get_payer_details():
    try:
        # Generate unique reference number
        unique_ref = generate_unique_ref()

        # Log the request
        if request.content_type == 'application/json':
            request_data = request.json
        else:
            return jsonify({'error': 'Unsupported Media Type'}), 415
        
        payer_ref = request_data.get('payerRef')
        phone_number = request_data.get('phoneNumber')

        # Get user ID from phone number if provided
        if phone_number:
           user_id = get_user_id(phone_number)
        else:
           user_id = None
           
        logger.info("Received request: %s", request_data, extra={'endpoint': '/get_payer_details', 'activity_type': 'request', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Request received', 'user_id': None})

        # Get data from request
        data = request.json
        payer_ref = data.get('payerRef')
        phone_number = data.get('phoneNumber1')
        user_id = data.get('userId')

        # Connect to the database
        db_connection = mysql.connector.connect(**db_config)
        cursor = db_connection.cursor(dictionary=True)

        # Fetch payer details from payers_list
        if payer_ref:
            query = "SELECT * FROM payers_list WHERE payerRef = %s"
            cursor.execute(query, (payer_ref,))
            payer_details = cursor.fetchone()
        elif phone_number:
            # Get userID from user_list based on phoneNumber1
            query_user_id = "SELECT userId FROM user_list WHERE phoneNumber1 = %s"
            cursor.execute(query_user_id, (phone_number,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['userId']
            else:
                user_id = None

            # Fetch payer details based on userID
            query = "SELECT * FROM payers_list WHERE userId = %s"
            cursor.execute(query, (user_id,))
            payer_details = cursor.fetchone()
        else:
            return jsonify({'error': 'Invalid request parameters'})

        # Fetch infrastructure details from payer_infrastructure_mapping
        if payer_details:
            query_infra = "SELECT infrastructureRef, Nextpaymentdue FROM payer_infrastructure_mapping WHERE payerRef = %s"
            cursor.execute(query_infra, (payer_ref,))
            infra_details = cursor.fetchone()

            if infra_details:
                infra_ref = infra_details['infrastructureRef']
                next_payment_due = infra_details['Nextpaymentdue']

                # Fetch infrastructure name from infrastructure_list
                query_infra_list = "SELECT infraName, locId, infraClassId FROM infrastructure_list WHERE infrastructureRef = %s"
                cursor.execute(query_infra_list, (infra_ref,))
                infra_list_details = cursor.fetchone()

                if infra_list_details:
                    loc_id = infra_list_details['LocId']
                    infra_class_id = infra_list_details['infraClassId']

                    # Fetch location name from infrastructure_location_lookup
                    query_loc_lookup = "SELECT LocName FROM infrastructure_location_lookup WHERE LocId = %s"
                    cursor.execute(query_loc_lookup, (loc_id,))
                    loc_details = cursor.fetchone()
                    loc_name = loc_details['LocName'] if loc_details else None

                    # Fetch infrastructure type from infrastructureclassification
                    query_infra_class = "SELECT InfrastructureType FROM infrastructureclassification WHERE infraClassId = %s"
                    cursor.execute(query_infra_class, (infra_class_id,))
                    infra_class_details = cursor.fetchone()
                    infra_type = infra_class_details['InfrastructureType'] if infra_class_details else None

                    # Prepare response
                    response_data = {
                        'payerRef': payer_details['payerRef'],
                        'fullName': payer_details['fullName'],
                        'phoneNumber': payer_details['phoneNumber'],
                        'address': payer_details['address'],
                        'infraRef': infra_ref,
                        'nextPaymentDue': next_payment_due,
                        'infraName': infra_list_details['infrastructure_name'],
                        'closestLandmark': infra_list_details['closest_landmark'],
                        'locName': loc_name,
                        'infraType': infra_type
                    }
                    logger.info("API response: %s", response_data, extra={'endpoint': '/get_payer_details', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Response sent', 'user_id': user_id})
                    return jsonify(response_data)
                else:
                    return jsonify({'error': 'Infrastructure details not found'})
            else:
                return jsonify({'error': 'Payer infrastructure mapping details not found'})
        else:
            return jsonify({'error': 'Payer details not found'})

    except Exception as e:
        logger.error("Error processing request: %s", str(e), extra={'endpoint': '/get_payer_details', 'activity_type': 'error', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': str(e), 'user_id': user_id})
        return jsonify({'error': 'Internal server error'})


if __name__ == '__main__':
    app.run()
