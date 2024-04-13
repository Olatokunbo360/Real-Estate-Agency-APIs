# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 15:04:12 2024

@author: Yusuf Sanni

This is a Python API to print a receipt for the last payment of a specific payer. 
It can be for a single infrastructure or multiple; depending on what was captured. 
This is a GET action.

All requests and responses are in JSON format. It gets information from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, request, jsonify
import mysql.connector
import logging
import json
from datetime import datetime

app = Flask(__name__)

# Configure custom logger
logger = logging.getLogger('api_logger')
logger.setLevel(logging.DEBUG)

# Configure log handler to store logs in MySQL database
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Connect to MySQL database
db_config = {
    'host': 'Enter IP address here',
    'user': 'Enter username here',
    'password': 'Enter password here',
    'database': 'Enter DB name here'
}

def get_user_id(phone_number):
    # Query user ID based on phone number
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT userId FROM user_list WHERE phoneNumber1 = %s"
        cursor.execute(query, (phone_number,))
        user_id = cursor.fetchone()[0]  # Assuming the phone number uniquely identifies a user
        cursor.close()
        db.close()
        return user_id
    except Exception as e:
        logger.error(f"Error retrieving user ID: {str(e)}")
        return None

def get_payment_details(payment_ref):
    # Query payment details based on payment reference
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT totalAmtpaid, paymentdated, payerRef FROM payment_log WHERE paymentRef = %s"
        cursor.execute(query, (payment_ref,))
        payment_data = cursor.fetchone()
        cursor.close()
        db.close()
        return payment_data
    except Exception as e:
        logger.error(f"Error retrieving payment details: {str(e)}")
        return None

def get_payer_details(payer_ref):
    # Query payer details based on payer reference
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT FullName, PhoneNumber1 FROM payers_list WHERE payerRef = %s"
        cursor.execute(query, (payer_ref,))
        payer_data = cursor.fetchone()
        cursor.close()
        db.close()
        return payer_data
    except Exception as e:
        logger.error(f"Error retrieving payer details: {str(e)}")
        return None

def get_infra_ref(payer_ref):
    # Query infrastructure reference details based on payer reference
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT infrastructureRef FROM payer_infrastructure_mapping WHERE payerRef = %s"
        cursor.execute(query, (payer_ref,))
        payer_data = cursor.fetchone()
        cursor.close()
        db.close()
        return payer_data
    except Exception as e:
        logger.error(f"Error retrieving payer details: {str(e)}")
        return None

def get_infra_names(infra_ref):
    # Query infrastructure names based on infrastructure reference
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        query = "SELECT infraName FROM infrastructure_list WHERE infrastructureRef = %s"
        cursor.execute(query, (infra_ref,))
        infra_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        db.close()
        return infra_names
    except Exception as e:
        logger.error(f"Error retrieving infrastructure names: {str(e)}")
        return []
    

@app.route('/payment-details', methods=['GET','POST'])
def get_payment_details_api():
    try:
        data = request.get_json()
        payment_ref = data.get('paymentRef')
        user_id = data.get('userId')

        # Fetch user ID based on phone number
        phone_number = get_user_id(user_id)

        if payment_ref:
            # Fetch payment details
            payment_data = get_payment_details(payment_ref)

            if payment_data:
                total_amtpaid, payment_dated, payer_ref = payment_data

                # Fetch payer details
                payer_data = get_payer_details(payer_ref)

                if payer_data:
                    payer_name, phone_number = payer_data

                    # Fetch infrastructure reference
                    infra_ref = get_infra_ref(payer_ref)

                    if infra_ref:
                        # Fetch infrastructure names
                        infra_names = get_infra_names(infra_ref)

                        # Prepare response
                        response_data = {
                            'totalAmtpaid': total_amtpaid,
                            'paymentdated': payment_dated.strftime('%Y-%m-%d'),
                            'payerName': payer_name,
                            'phoneNumber': phone_number,
                            'infraNames': infra_names
                        }

                        # Log the API request and response
                        unique_ref = datetime.now().strftime('%Y%m%d%H%M%S%f')
                        log_data = {
                            'endpointName': '/payment-details',
                            'activityType': 'API call',
                            'activityAction': 'Request received',
                            'uniqueRef': unique_ref,
                            'contentDump': 'Request received',
                            'userId': user_id
                        }
                        logger.info(json.dumps(log_data))

                        return jsonify(response_data), 200
                    else:
                        return jsonify({'error': 'Infrastructure reference not found'}), 404
                else:
                    return jsonify({'error': 'Payer details not found'}), 404
            else:
                return jsonify({'error': 'Payment details not found'}), 404
        else:
            return jsonify({'error': 'Payment reference not provided'}), 400
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False)
