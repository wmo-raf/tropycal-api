import logging

from flask import jsonify, request

from troapi.routes.api.v1 import endpoints, error
from troapi.services import StormService


@endpoints.route('/storms/realtime', strict_slashes=False, methods=['GET'])
def get_realtime_storms():
    """Get storms"""
    logging.info('[ROUTER]: Getting realtime storms')

    include = request.args.get('include')
    include = include.split(',') if include else []

    try:
        result = StormService.get_realtime_storms()
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')

    response = {
        "data": [item.serialize(include) for item in result],
        "count": len(result)
    }

    return jsonify(**response), 200
