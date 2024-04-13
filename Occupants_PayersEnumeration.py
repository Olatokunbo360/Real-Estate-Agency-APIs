# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 17:19:18 2024

@author: Yusuf Sanni

This is a Python API that can map a payer to multiple properties/infrastructure.
This is a POST action.A unique Ref for the payersRef column on successful creation
is generated. It requests for specific data and uses the information to populate the 
tables.
Two actions occur here:
1. If payerRef value provided is 0, then that means payer doesn't exist; so 
payer should be created on the payers_list table and mapped to the 
infrastructure whose ref is provided i.e. populate the payer_infrastructure_mapping 
table and the payers_list table. Also, update both the ïnfrastructure_list 
to reflect that said property is now occupied and the occupiedcount and vacantcount 
columns values should be updated too on the infrastructure_location_count table.

2. If payerRef value is not 0, then the payer exists and no need to create on 
the payers_list table; only carry out the other activities specified in 
action 1 above.

All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.


"""

from flask import Flask, jsonify, request
import mysql.connector
import logging 
from logging.handlers import RotatingFileHandler
from datetime import datetime
import uuid

app = Flask(__name__)

# Database Configuration
db_config = {
    'host': 'Enter IP address here',
    'user': 'Enter username here',
    'password': 'Enter password here',
    'database': 'Enter DB name here'
}

# Function to generate a unique reference number
def generate_unique_ref():
    return str(uuid.uuid4())

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

# API Endpoint for updating payer information
@app.route('/update_payer', methods=['GET','POST'])
def update_payer():
    try:
        # Log the request
        unique_ref = generate_unique_ref()
        logger.info("Received request: %s", request.json, extra={'endpoint': '/update_payer', 'activity_type': 'request', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Request received', 'user_id': None})

        # Get data from request
        data = request.json
        payer_ref = data.get('payerRef')
        infra_loc_id = data.get('infralocId')

        # Connect to the database
        db_connection = connect_to_database()
        if db_connection:
            cursor = db_connection.cursor()
            
            # Retrieve userID from user_list based on phoneNumber1
            phone_number = data.get('phoneNumber1')
            query = "SELECT userId FROM user_list WHERE phoneNumber1 = %s"
            cursor.execute(query, (phone_number,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row[0]
            else:
                user_id = None

            # Log the request with the retrieved user ID
            logger.info("Received request: %s", request.json, extra={'endpoint': '/update_payer', 'activity_type': 'request', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Request received', 'user_id': user_id})


            if payer_ref == 0:
                # Insert data into payers_list table
                insert_query = "INSERT INTO payers_list (payerRef, Title, FullName, phoneNumber1, phoneNumber2, email, address, area, capturedby, handledby, statusId, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                insert_values = (payer_ref, data.get('Title'), data.get('FullName'), data.get('phoneNumber1'), data.get('phoneNumber2'), data.get('email'), data.get('address'), data.get('area'), data.get('capturedby'), data.get('handledby'), data.get('statusId'), datetime.now())
                cursor.execute(insert_query, insert_values)

                # Update payer_infrastructure_mapping table
                update_mapping_query = "INSERT INTO payer_infrastructure_mapping (infrastructureRef, infralocId, paymentduration, 1stpaymentdate, lastpaymentdate, Nextpaymentdue, handledby, statusId, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                update_mapping_values = (data.get('InfrastructureRef'), infra_loc_id, data.get('paymentduration'), data.get('1stpaymentdate'), data.get('lastpaymentdate'), data.get('Nextpaymentdue'), data.get('handledby'), data.get('statusId'), datetime.now())
                cursor.execute(update_mapping_query, update_mapping_values)

                db_connection.commit()
                cursor.close()
                db_connection.close()

                logger.info("Payer information updated", extra={'endpoint': '/update_payer', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Payer information updated', 'user_id': user_id})
                return jsonify({'message': 'Payer information updated'}), 200
            else:
                # Update payer_infrastructure_mapping table for existing payerRef
                update_mapping_query = "UPDATE payer_infrastructure_mapping SET infrastructureRef = %s, infralocId = %s, paymentduration = %s, 1stpaymentdate = %s, lastpaymentdate = %s, Nextpaymentdue = %s, handledby = %s, statusId = %s, date = %s WHERE payerRef = %s"
                update_mapping_values = (data.get('InfrastructureRef'), infra_loc_id, data.get('paymentduration'), data.get('1stpaymentdate'), data.get('lastpaymentdate'), data.get('Nextpaymentdue'), data.get('handledby'), data.get('statusId'), datetime.now(), payer_ref)
                cursor.execute(update_mapping_query, update_mapping_values)

                # Update infrastructure_location_count table
                update_count_query = "UPDATE infrastructure_location_count SET vacantCount = vacantCount - 1, occupiedCount = occupiedCount + 1 WHERE infralocId = %s"
                cursor.execute(update_count_query, (infra_loc_id,))

                # Update statusId in infrastructure_list table
                update_status_query = "UPDATE infrastructure_list SET statusId = 1 WHERE InfrastructureId = %s"
                cursor.execute(update_status_query, (data.get('InfrastructureId'),))

                db_connection.commit()
                cursor.close()
                db_connection.close()

                logger.info("Payer information updated", extra={'endpoint': '/update_payer', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Payer information updated', 'user_id': user_id})
                return jsonify({'message': 'Payer information updated'}), 200
    except Exception as e:
        logger.error("Error processing request: %s", e, extra={'endpoint': '/update_payer', 'activity_type': 'response', 'activity_action': 'API call', 'unique_ref': unique_ref, 'content_dump': 'Error processing request', 'user_id': user_id})
        return jsonify({'error': 'Error processing request'}), 400

if __name__ == '__main__':
    app.run(debug=False)
