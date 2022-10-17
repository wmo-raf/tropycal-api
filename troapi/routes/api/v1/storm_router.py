import logging
import io
from flask import send_file

from flask import jsonify, request

from troapi.errors import StormNotFound, StormHasNoForecast
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


@endpoints.route('/storms/realtime/<storm_id>', strict_slashes=False, methods=['GET'])
def get_storm(storm_id):
    try:
        storm = StormService.get_storm(storm_id)
    except StormNotFound as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')

    response = storm.serialize()

    return jsonify(**response), 200


@endpoints.route('/storms/realtime/<storm_id>/plot', strict_slashes=False, methods=['GET'])
def get_storm_plot(storm_id):
    args = request.args
    plot_forecast = False
    if "forecast" in args:
        plot_forecast = True
    try:
        storm_plot_file = StormService.plot_storm(storm_id, forecast=plot_forecast)

        if storm_plot_file:
            plot_data = io.BytesIO()
            with open(storm_plot_file.name, 'rb') as f:
                plot_data.write(f.read())
            plot_data.seek(0)

            # delete temp file
            storm_plot_file.close()

            return send_file(plot_data, mimetype='image/png')
        else:
            return error(status=500, detail='Error Plotting')
    except StormNotFound as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=404, detail=e.message)
    except StormHasNoForecast as e:
        logging.error('[ROUTER]: ' + e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')


@endpoints.route('/storms/plots/recent', strict_slashes=False, methods=['GET'])
def get_recent_plot():
    """Get recent plot"""
    logging.info('[ROUTER]: Getting recent plots')

    try:
        plot = StormService.get_recent_plot()
    except Exception as e:
        logging.error('[ROUTER]: ' + str(e))
        return error(status=500, detail='Generic Error')

    return jsonify(plot), 200
