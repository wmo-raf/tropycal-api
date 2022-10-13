"""Storm SERVICE """

import logging
import os
import shutil

import tempfile

from tropycal import realtime
from tropycal.realtime import RealtimeStorm

from troapi import app, db
from troapi.errors import StormNotFound, StormHasNoForecast
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
    other_info["jtwc_source"] = realtime_obj.jtwc_source

    data = {**storm_vars, **storm.attrs, **other_info, }

    return data


def get_realtime_storm_forecast(storm):
    try:
        forecast_data = storm.get_forecast_realtime(ssl_certificate=False)
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
                    db.session.rollback()
            else:
                db_storm_forecast = StormForecast(**forecast_data, storm_id=db_storm.id)

                try:
                    logging.info('[DB]: ADD STORM FORECAST')
                    db.session.add(db_storm_forecast)
                    db.session.commit()
                    logging.info(f"Created Storm Forecast for: {db_storm.id} ")
                except Exception as e:
                    print(e)
                    db.session.rollback()


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
        db.session.rollback()
        print(e)

    if not realtime_storm.invest:
        create_or_update_storm_forecast(realtime_storm, db_storm)


def create_or_update_storm(storm_id, realtime_obj):
    realtime_storm = realtime_obj.get_storm(storm_id)

    data = get_realtime_storm_data(realtime_storm, realtime_obj)

    try:
        db_storm = StormService.get_storm(storm_id)
    except Exception as e:
        db.session.rollback()
        db_storm = None

    # update storm already in database
    if db_storm:
        # loop all data keys, check if key is in db_storm, and assign new value
        for key in data:
            if hasattr(db_storm, key):
                setattr(db_storm, key, data[key])
        # update
        try:
            logging.info('[DB]: UPDATE STORM')
            db.session.commit()
            logging.info(f"Updated Storm: {db_storm.id} ")
        except Exception as e:
            db.session.rollback()
    else:
        # create new storm
        db_storm = Storm(**data)

        try:
            logging.info('[DB]: ADD STORM')
            db.session.add(db_storm)
            db.session.commit()
            logging.info(f"Created storm: {db_storm.id} ")
        except Exception as e:
            db.session.rollback()
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
    def plot_storm(storm_id, forecast=False):
        logging.info(f"[SERVICE]: Getting storm {storm_id} ")
        logging.info('[DB]: QUERY')

        try:
            storm = Storm.query.get(storm_id)
        except Exception as error:
            raise error

        if not storm:
            raise StormNotFound(message=f"Storm with id {storm_id} does not exist")

        storm_data = storm.storm_object

        if forecast and storm.invest:
            raise StormHasNoForecast(message="Storm is invest and has no forecast")

        realtime_storm = RealtimeStorm(storm_data)

        tmp_plot_file = tempfile.NamedTemporaryFile(mode='w+b', suffix=".png")

        if not forecast:
            realtime_storm.plot(save_path=tmp_plot_file.name)
            return tmp_plot_file
        else:
            temp_dir = tempfile.mkdtemp()

            realtime_storm.plot_forecast_realtime(save_path=temp_dir, ssl_certificate=False)

            for filename in os.listdir(temp_dir):
                f = os.path.join(temp_dir, filename)

                if f.endswith("_track.png"):
                    # move to temp file
                    shutil.move(f, tmp_plot_file.name)
                    os.rmdir(temp_dir)
                break

        return tmp_plot_file

    @staticmethod
    def update_storms(jtwc_source="jtwc"):
        logging.info(f"[SERVICE]: Updating storms")

        try:

            # create realtime object
            realtime_obj = realtime.Realtime(jtwc=True, jtwc_source=jtwc_source, ssl_certificate=False)

            # get all active storms
            realtime_storm_list = realtime_obj.list_active_storms()

            # get all realtime storms from database
            db_realtime_storms = StormService.get_realtime_storms()

            # storms in db matching incoming realtime storms
            existing_storms = []

            for db_storm in db_realtime_storms:
                if db_storm.id in realtime_storm_list:
                    existing_storms.append(db_storm.id)
                else:
                    try:
                        # realtime db storm not in updated realtime list, proceed to mark as not realtime
                        db_storm.realtime = False
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        db.session.rollback()

            # get new storms not added to db
            new_storms_list = list(set(realtime_storm_list) - set(existing_storms))

            for storm_id in new_storms_list:
                # create or update storms
                create_or_update_storm(storm_id, realtime_obj)

        except Exception as e:
            print("Error", e)
