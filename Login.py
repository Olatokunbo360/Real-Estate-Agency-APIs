""" 
This is a Python API  for login that grants all active users access to the solution. 
Unique tokens are to be generated per session with expiration period. 
This is a GET action.It requests for the username and password and once
successful, it provides a status message and a generates a unique code.
All requests and responses are in JSON format. It gets infpormaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""

from flask import Flask, jsonify, request # For creating Flask API
import mysql.connector # For connecting to the SQL DB
import logging # For creating a log file
import uuid  # For creating unique ID reference numbers 
from datetime import datetime, timedelta # For making use of the date time format

app = Flask(__name__)

# Set up logging
logging.basicConfig(filename='api_audit.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Configuration
db_config = {
    'host': 'Enter IP address here',
    'user': 'Enter username',
    'password': 'Enter password',
    'database': 'Enter DB name'
}

# Function to connect to MySQL database
def connect_to_database():
    try:
        db_connection = mysql.connector.connect(**db_config)
        return db_connection
    except mysql.connector.Error as error:
        logging.error("Error connecting to MySQL database: %s", error)
        return None

# API Endpoint for user login
@app.route('/login', methods=['GET'])
def user_login():
    # Log the request
    request_id = str(uuid.uuid4())
    logging.info("Endpoint: /login - Activity Type: request - Request ID: %s - Message: Request received", request_id)

    # Extract data from request
    username = request.args.get('username')
    password = request.args.get('password')
    

    # Connect to the database
    db_connection = connect_to_database()
    if db_connection:
        cursor = db_connection.cursor(dictionary=True)
        try:
            # Validate username/password
            query = "SELECT * FROM user_list WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                # Generate unique token
                token = str(uuid.uuid4())
                expiration_time = datetime.utcnow() + timedelta(minutes=5)

                # Get user category name
                query = "SELECT CategoryName FROM usercategories WHERE userCatId = %s"
                cursor.execute(query, (user['userCatId'],))
                user_category = cursor.fetchone()['CategoryName']

                # Get agency name
                query = "SELECT agencyName FROM agency_details WHERE agencyId = %s"
                cursor.execute(query, (user['agencyId'],))
                agency_name = cursor.fetchone()['agencyName']

                # Determine request source
                request_source = 'Mobile' if 'User-Agent' in request.headers and 'Android' in request.headers['User-Agent'] else 'Web'

                # Log the response
                logging.info("Endpoint: /login - Activity Type: response - Request ID: %s - Message: Login successful", request_id)

                # Return response in JSON format
                response = {
                    'status': 'success',
                    'token': token,
                    'expiration_time': expiration_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'username': user['username'],
                    'LastName': user['LastName'],
                    'firstName': user['firstName'],
                    'Middlename': user['Middlename'],
                    'userCatId': user['userCatId'],
                    'userCategory': user_category,
                    'agencyId': user['agencyId'],
                    'agencyName': agency_name,
                    'request_source': request_source
                }
                return jsonify(response), 200, 'application/json'
            else:
                # Log the response
                logging.info("Endpoint: /login - Activity Type: response - Request ID: %s - Message: Invalid username/password", request_id)
                return jsonify({'status': 'error', 'message': 'Invalid username/password'}), 401
        except mysql.connector.Error as error:
            logging.error("Endpoint: /login - Activity Type: response - Request ID: %s - Message: Database error - Error: %s", request_id, error)
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        finally:
            cursor.close()
            db_connection.close()
    else:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

if __name__ == '__main__':
    app.run(debug=False)
