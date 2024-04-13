"""

@author: Yusuf Sanni

This is a Python API  for handling the creation of new space/infrastructure/property
the agency collects revenue for. This is a POST action. It posts to both tables 
listed  (infrastructure_list and infrastructure_location_count)and generates a unique reference id which is used to populate the 
infrastructureRef column. This is another column in a table in the SQL DB
This is a GET action.It gets its information from the other APIs that have populated 
this information.
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify, request
import requests
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

# Function to fetch data from API URLs
def fetch_data_from_api(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Failed to fetch data from %s - Status Code: %d", url, response.status_code)
            return None
    except Exception as e:
        logging.error("Error fetching data from %s: %s", url, str(e))
        return None

# API Endpoint for posting data to infrastructure_list table
@app.route('/InfrastructureEnumeration', methods=['GET','POST'])
def post_infrastructure_data():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /InfrastructureEnumeration - Activity Type: request - Request ID: %s - Message: Request received", request_id)
    
    # Extract data from request
    data = request.json
    
    # Fetch data from approved API URLs
    agency_data = fetch_data_from_api('http://localhost:5000/login')
    infraclass_data = fetch_data_from_api('http://localhost:5000/infrastructure_classification')
    loc_data = fetch_data_from_api('http://localhost:5000/LocationList')
    status_data = fetch_data_from_api('http://localhost:5000/status_list')
    infraloccount_data = fetch_data_from_api('http://localhost:5000/infrastructure_location_count')
    
    
    if not (agency_data and infraclass_data and loc_data and status_data):
        return jsonify({'error': 'Failed to retrieve data from API endpoints'}), 500

    # Extract relevant fields from fetched data
    agency_id = agency_data.get('agencyId')
    infraclass_id = infraclass_data.get('infraClassId')
    loc_id = loc_data.get('LocId')
    status_id = status_data.get('statusId')
    infraloc_id = infraloccount_data.get('InfralocId')
    capturedby_id = agency_data.get('UserId')
    handledby_id = agency_data.get('UserId')
    infra_name = data.get('infraName')
    LocDescription = data.get('LocDescription')
    ClosestLandMark = data.get('ClosestLandMark')
    reference_number = str(uuid.uuid4())
    

    if not (agency_id and infraclass_id and loc_id and status_id):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Check if the record already exists
            query = ("SELECT * FROM infrastructure_list WHERE infraName = %s AND LocDescription = %s AND ClosestLandMark = %s")
            cursor.execute(query, (infra_name, LocDescription, ClosestLandMark ))
            existing_record = cursor.fetchone()

            if existing_record:
                logging.info("Endpoint: /InfrastructureEnumeration - Activity Type: response - Request ID: %s - Message: Matching record already exists", request_id)
                return jsonify({'message': 'Record already exists in the database'}), 400
            else:
                # Insert new record into infrastructure_list table
                insert_query = "INSERT INTO infrastructure_list (agencyId, infralocId, LocId, infraClassId, infraName, LocDescription, ClosestLandMark, CapturedBy, handledby, statusId, infrastructureRef) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(insert_query, (agency_id, infraloc_id, loc_id, infraclass_id, infra_name, LocDescription, ClosestLandMark, capturedby_id, handledby_id, status_id, reference_number))
                
                # Update totalCount column in infrastructure_location_count table
                update_query = "UPDATE infrastructure_location_count SET totalCount = totalCount + 1 WHERE infralocId = %s"
                cursor.execute(update_query, (data['infralocId'],))
                
                # Commit changes to the database
                db_connection.commit()

                # Log the response
                logging.info("Endpoint: /InfrastructureEnumeration - Activity Type: response - Request ID: %s - Message: Data inserted successfully", request_id)

                # Close cursor and connection
                cursor.close()
                db_connection.close()
                
                return jsonify({'message': 'Data inserted successfully'}), 201
        except mysql.connector.Error as error:
            logging.error("Endpoint: /InfrastructureEnumeration - Activity Type: response - Request ID: %s - Message: Data insertion failed - Error: %s", request_id, error)
            cursor.close()
            db_connection.close()
            return jsonify({'error': 'Data insertion failed'}), 500
    else:
        return jsonify({'error': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
