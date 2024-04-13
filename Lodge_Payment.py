
"""
This is a Python API that allows payment using either PayerRef or InfrastructureRef
while also generating unique payment Ref for each request. Validation is important
 to ensure amount tied to specified TransRef (on "payment_request_log" table) is
 what is paid. This is a POST action.
  
All requests and responses are in JSON format. It gets informaton from an SQL 
db and logs all messages from the API to a custom logger in the database.
"""
import logging
import mysql.connector
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
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
                datetime.now()
            )

            # Execute the query
            cursor.execute(query, values)

            # Commit the changes and close cursor and database connection
            db_connection.commit()
            cursor.close()
            db_connection.close()

        except Exception as e:
            print(f"Error inserting log into database: {e}")

def generate_unique_ref():
    return str(uuid.uuid4())

# Add the custom logging handler to the logger
custom_handler = MySQLHandler()
logger.addHandler(custom_handler)

# Define your API endpoint
@app.route('/update_payment_log', methods=['GET','POST'])
def update_payment_log():
    try:
        # Extract data from the request
        data = request.json
        userId = data.get('userId')
        paymentRef = data.get('paymentRef')

        # Connect to the MySQL database
        db_connection = mysql.connector.connect(
            host='192.185.11.141',
            user='propeman_revcollect',
            password='y3B*352wa',
            database='propeman_revcollect'
        )

        # Create a cursor to execute SQL queries
        cursor = db_connection.cursor()

        # Get payment details from payment_request_log table
        query = "SELECT * FROM payment_request_log WHERE paymentRef = %s"
        cursor.execute(query, (paymentRef,))
        payment_data = cursor.fetchone()

        # Insert payment details into payment_log table
        query = "INSERT INTO payment_log (paymentId, payerRef, infrastructureRefs, paymentchannelId, totalAmtDue, handledby, statusId, dated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        payment_values = (
            payment_data[0],  # paymentrequestId
            payment_data[2],  # payerRef
            payment_data[3],  # infrastructureRefs
            payment_data[4],  # paymentchannelId
            payment_data[5],  # totalAmtDue
            userId,  # handledby
            payment_data[7],  # statusId
            datetime.now()
        )
        cursor.execute(query, payment_values)

        # Update payer_infrastructure_mapping table
        lastpaymentdate = datetime.strptime(payment_data[8], '%Y-%m-%d')  # Convert lastpaymentdate to datetime object
        paymentduration = payment_data[6]  # paymentduration in months
        Nextpaymentdue = lastpaymentdate + timedelta(days=30*paymentduration)  # Calculate Nextpaymentdue
        query = "UPDATE payer_infrastructure_mapping SET Nextpaymentdue = %s, lastpaymentdate = %s WHERE paymentRef = %s"
        mapping_values = (
            Nextpaymentdue.strftime('%Y-%m-%d'),  # Nextpaymentdue in string format
            datetime.now(),  # Update lastpaymentdate to current date
            paymentRef
        )
        cursor.execute(query, mapping_values)

        # Commit the changes and close cursor and database connection
        db_connection.commit()
        cursor.close()
        db_connection.close()

        # Log the request and response
        unique_ref = generate_unique_ref()  # Replace with actual implementation
        logger.info("Received request: %s", data, extra={'endpointName': '/update_payment_log', 'activityType': 'request', 'activityAction': 'API call', 'UniqueRef': unique_ref, 'contentdump': 'Request received', 'userId': userId})
        logger.info("Sent response: %s", {"message": "Payment log updated successfully"}, extra={'endpointName': '/update_payment_log', 'activityType': 'response', 'activityAction': 'API call', 'UniqueRef': unique_ref, 'contentdump': 'Response sent', 'userId': userId})

        return jsonify({"message": "Payment log updated successfully"}), 200

    except Exception as e:
        logger.error("Error processing request: %s", str(e), extra={'endpointName': '/update_payment_log', 'activityType': 'error', 'activityAction': 'API call', 'UniqueRef': 'generate_unique_ref()', 'contentdump': 'Error processing request', 'userId': None})
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
