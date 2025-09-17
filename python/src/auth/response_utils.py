from flask import jsonify

def success_response(message=None, data=None, status_code=200):
    """Create a standardized success response."""
    response = {'status': 'success'}
    if message:
        response['message'] = message
    if data:
        response['data'] = data
    return jsonify(response), status_code

def error_response(message, status_code=400):
    """Create a standardized error response."""
    return jsonify({'status': 'error', 'message': message}), status_code

def validation_error(message):
    """Return a 400 validation error."""
    return error_response(message, 400)

def unauthorized_error(message="Unauthorized"):
    """Return a 401 unauthorized error."""
    return error_response(message, 401)

def not_found_error(message="Not found"):
    """Return a 404 not found error."""
    return error_response(message, 404)

def conflict_error(message="Resource already exists"):
    """Return a 409 conflict error."""
    return error_response(message, 409)

def server_error(message="Internal server error"):
    """Return a 500 server error."""
    return error_response(message, 500)

def created_response(message, data=None):
    """Return a 201 created response."""
    return success_response(message, data, 201)