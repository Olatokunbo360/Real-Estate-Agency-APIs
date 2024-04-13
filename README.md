# Real Estate Agency APIs
 APIs for the website of a real estate agency to monitor property under the agency


 This repository contains a collection of APIs used in the building of real estate agency's website. The APIs were used for updating and entering data as well as monitoring property under the agency. These APIs were built using Python libraries. Every time an API is called, a message is logged as regards the activity of the API (if it is a POST or A GET action) and the status of the call (failed or successful) along with a request ID. The log messages are uploaded to a table in a MySQL database (in this case, the table is called api_audit_log). The API endpoints can then be tested with the use of a tool like Postman. The APIs upload entered details into a MySQL database and when there are data requests, it accesses the same database to pull the information required.

 ** Files**

 _Login.py_: API for login to the website.

 _LocationList.py_: API for getting a list of locations for a particular agency or user. That is, the locations of the properties assigned to that agency or user.

 _Infrastructure_classification.py_: API for getting the classification of a particular property. If is residential or commercial

 _InfrastructureLocationCount.py_: API for tracking the count of properties per user or agency as they exist.

 _statusList.py_: API for getting the status of different properties. That is, if the property is vacant or occupied.

 _InfrastructureEnumeration.py_: API that handles the creation of new details for a particular property.

_infrastructure_vacant.py_: API that gets the list of properties that are vacant.

_payers_list.py_: API that gets the list of payers on the system.

_Occupant_payersEnumeration.py_: API for mapping a payer to a property or multiple properties.

_Payer_Infrastructure_List.py_: API for showing the mapping of ONE payer to a property or multiple properties.

_View_bill_due.py_: API for showing what the bill due on a particular property or properties if applicable.

_Lodge_Payment.py_: API for making a payment using either a payer reference number or infrastructure reference number.

_Print Receipt_Infrastructure.py_: API for printing a receipt of payment for a particular property/infrastructure.

_Print Receipt_Payer.py_: API for printing receipt of last payment for a particular payer.

 For all these APIs, more details about them are captured as comments and notes in their files.

 **Dependencies**

 The following Python libraries were used for this project:

 _mysql.connector_ : MySQL driver written in Python for connecting to a MySQL DB

 _logging_: logging package for Python for creating and generating log messages

 _flask_: For API creation

_jsonify_: For serializing given arguments as JSON

_request_: Used by default in Flask for remembering the matched endpoint and view arguments.

_logging.handlers_: Additional handlers for the logging package.

_RotatingFileHandler_: Handler for logging to a set of files, which switches from one file to the next when the current file reaches a certain size.

_datetime_: For accessing date/time values and other related types.

_uuid_: For creating universally unique identifiers.

_requests_: HTTP library, written in Python.

_time_delta_: For getting the difference between 2 datetime objects.

**Usage**

To run the analysis on your local machine, follow these steps:

Clone this repository to your local machine using the following command:

bash

Copy code git clone https://github.com/Olatokunbo360/Real-Estate-Agency-APIs.git

Navigate to the project directory:

bash

Copy code cd Real-Estate-Agency-APIs

Install the required dependencies. You can use the following command to install dependencies using pip:

Copy code pip install -r requirements.txt

Once the dependencies are installed, then you can begin checking the files.

