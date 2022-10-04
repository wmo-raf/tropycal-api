"""Storm SERVICE """

import logging

from tropycal import realtime

from troapi import app, db
from troapi.errors import StormNotFound
from troapi.models import Storm, StormForecast


def get_realtime_storm_data(storm, realtime_obj):
    storm_vars = {}

    for var in storm.vars:
        storm_vars[var] = storm.vars[var].tolist()

    other_info = {}

    if storm_vars.get("date"):
        other_info["start_date"] = storm_vars.get("date")[0]
        other_info["end_date"] = storm_vars.get("date")[-1]

    other_info["update_time"] = realtime_obj.time

    data = {**storm_vars, **storm.attrs, **other_info}

    return data


def get_realtime_storm_forecast(storm):
    try:
        forecast_data = storm.get_forecast_realtime()
        data = {**forecast_data}
        return data
    except Exception as e:
        return None


def create_or_update_storm_forecast(realtime_storm, db_storm):
    if not realtime_storm.invest:

        forecast_data = get_realtime_storm_forecast(realtime_storm)

        if forecast_data:

            existing_storm_forecast = StormForecast.query.filter_by(storm_id=db_storm.id).first()

            if existing_storm_forecast:
                try:
                    for key in forecast_data:
                        if hasattr(existing_storm_forecast, key):
                            setattr(existing_storm_forecast, key, forecast_data[key])
                    # update
                    logging.info('[DB]: UPDATE STORM FORECAST')
                    db.session.commit()

                    logging.info(f"Updated Storm Forecast: {db_storm.id} ")
                except Exception as e:
                    print(e)
            else:
                db_storm_forecast = StormForecast(**forecast_data, storm_id=db_storm.id)

                try:
                    logging.info('[DB]: ADD STORM FORECAST')
                    db.session.add(db_storm_forecast)
                    db.session.commit()
                    logging.info(f"Created Storm Forecast for: {db_storm.id} ")
                except Exception as e:
                    print("Error", e)
                    raise e


def update_storm(db_storm, realtime_storm, realtime_obj):
    try:
        data = get_realtime_storm_data(realtime_storm, realtime_obj)
        for key in data:
            if hasattr(db_storm, key):
                setattr(db_storm, key, data[key])
        # update
        logging.info('[DB]: UPDATE STORM')
        db.session.commit()

        logging.info(f"Updated Storm: {db_storm.id} ")
    except Exception as e:
        print(e)

    if not realtime_storm.invest:
        create_or_update_storm_forecast(realtime_storm, db_storm)


def create_storm(realtime_storm, realtime_obj):
    data = get_realtime_storm_data(realtime_storm, realtime_obj)
    db_storm = Storm(**data)

    try:
        logging.info('[DB]: ADD STORM')
        db.session.add(db_storm)
        db.session.commit()
        logging.info(f"Created storm: {db_storm.id} ")
    except Exception as e:
        print("Error", e)
        raise e

    if not realtime_storm.invest:
        create_or_update_storm_forecast(realtime_storm, db_storm)


class StormService(object):
    """Storm Service Class"""

    @staticmethod
    def get_storms(page=1):
        logging.info('[SERVICE]: Getting storms')
        logging.info('[DB]: QUERY')

        per_page = app.config['ITEMS_PER_PAGE']
        query = Storm.query

        return query.paginate(page=page, per_page=per_page)

    @staticmethod
    def get_realtime_storms():
        logging.info('[SERVICE]: Getting all realtime storms')
        logging.info('[DB]: QUERY')

        storms = Storm.query.filter_by(realtime=True).all()

        return storms

    @staticmethod
    def get_storm(storm_id):
        logging.info(f"[SERVICE]: Getting storm {storm_id} ")
        logging.info('[DB]: QUERY')

        try:
            storm = Storm.query.get(storm_id)
        except Exception as error:
            raise error

        if not storm:
            raise StormNotFound(message=f"Storm with id {storm_id} does not exist")

        return storm

    @staticmethod
    def update_storms(jtwc_source="jtwc"):
        logging.info(f"[SERVICE]: Updating storms")

        try:

            # create realtime object
            realtime_obj = realtime.Realtime(jtwc=True, jtwc_source=jtwc_source, ssl_certificate=False)

            # get all active storms
            realtime_storm_list = realtime_obj.list_active_storms()

            # get storms previously added to database
            db_realtime_storms = StormService.get_realtime_storms()

            existing_storms = []

            for db_storm in db_realtime_storms:
                if db_storm.id not in realtime_storm_list:
                    # realtime db storm not in updated realtime list, proceed to mark as not realtime
                    db_storm.realtime = False
                    db.session.commit()
                else:
                    # we have new realtime, proceed to update storm
                    storm = realtime_obj.get_storm(db_storm.id)
                    update_storm(db_storm, storm, realtime_obj)
                    existing_storms.append(db_storm.id)

            # new storms not added to db
            new_storms_list = list(set(realtime_storm_list) - set(existing_storms))

            for storm_id in new_storms_list:
                # get storm
                storm = realtime_obj.get_storm(storm_id)
                # create
                create_storm(storm, realtime_obj)

        except Exception as e:
            print("Error", e)
