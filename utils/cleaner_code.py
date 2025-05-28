from flask import jsonify

def _json_fail(message, status_code):
    """
    Helper function to return a JSON response indicating failure, using jsonify from Flask. 
    Args:
        message (str): 
        status_code (int): 
    Returns:
        out (jsonify): {'success': False, 'message': message}, status_code
    """
    return jsonify({
        'success': False,
        'message': message
    }), status_code
