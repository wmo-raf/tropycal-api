"""Storm SERVICE """

import logging
import os
import shutil
import tempfile
from datetime import datetime

from tropycal import realtime
from tropycal.realtime import RealtimeStorm
from werkzeug.utils import secure_filename

from troapi import app, db
from troapi.errors import StormNotFound, StormHasNoForecast
from troapi.models import Storm, StormForecast, Plot, PlotFile, StormPlot

UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']


def clean_up_storm_plots(storm_id):
    db_storm = None

    try:
        db_storm = StormService.get_storm(storm_id)
    except Exception:
        pass

    if db_storm:
        for plot in db_storm.plot:
            try:
                db.session.delete(plot)
                # delete plot from disk
                os.remove(os.path.join(UPLOAD_FOLDER, plot.file_path))

                logging.info(f"Deleted plot {plot.plot_type} for storm {db_storm.id}")
            except Exception as e:
                logging.error(f"Error deleting plot {plot.id}, {e}")

        # remove storm plot directory
        shutil.rmtree(os.path.join(UPLOAD_FOLDER, f"storm_plots/{db_storm.id}"), ignore_errors=True)


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


def create_storm_plots(realtime_storm, db_storm, update_time):
    def get_file_path(storm_id, plot_type, dt):
        date_path = f"storm_plots/{storm_id}/{dt.strftime('%Y%m%d')}/{dt.strftime('%H')}"

        # make dir recursively, dont raise if exists
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], date_path), exist_ok=True)

        fn = dt.strftime("%Y_%m_%d-%H_%M_%S")

        file_path = os.path.join(date_path, f"{plot_type}_{secure_filename(fn)}.png")

        return file_path

    def create_plot(plot_type):

        file_path = None

        if plot_type == "observed_track":
            file_path = get_file_path(db_storm.id, plot_type, update_time)

            try:
                realtime_storm.plot(save_path=os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            except Exception as e:
                logging.info(f"[PLOTTING]: Error plotting {plot_type} for storm {db_storm.id}: {e}")
                return

        if plot_type == "latest_forecast":
            file_path = get_file_path(db_storm.id, plot_type, update_time)
            temp_dir = tempfile.mkdtemp()
            try:
                realtime_storm.plot_forecast_realtime(save_path=temp_dir, ssl_certificate=False)

                for filename in os.listdir(temp_dir):
                    f = os.path.join(temp_dir, filename)

                    if f.endswith("_track.png"):
                        # move temp file to file_path
                        shutil.move(f, os.path.join(app.config['UPLOAD_FOLDER'], file_path))
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    break

            except Exception as e:
                logging.info(f"[PLOTTING]: Error plotting {plot_type} for storm {db_storm.id}: {e}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

        if plot_type == "forecast_model_tracks":
            file_path = get_file_path(db_storm.id, plot_type, update_time)

            try:
                realtime_storm.plot_models(save_path=os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            except Exception as e:
                logging.info(f"[PLOTTING]: Error plotting {plot_type} for storm {db_storm.id}: {e}")
                return

        if plot_type == "forecast_gefs_density":
            file_path = get_file_path(db_storm.id, plot_type, update_time)

            try:
                realtime_storm.plot_ensembles(save_path=os.path.join(app.config['UPLOAD_FOLDER'], file_path))
            except Exception as e:
                logging.info(f"[PLOTTING]: Error plotting {plot_type} for storm {db_storm.id}: {e}")
                return

        if plot_type == "forecast_gefs_tracks":
            pass

        if file_path:
            try:
                data = {
                    "storm_id": db_storm.id,
                    "updated_on": update_time,
                    "plot_type": plot_type,
                    "file_path": file_path
                }

                storm_plot = StormPlot(**data)

                logging.info('[DB]: SAVE PLOT')
                db.session.add(storm_plot)
                db.session.commit()
                logging.info(f"Created {plot_type} plot for storm: {db_storm.id}")
            except Exception as e:
                logging.error(f"[PLOTTING]: Error saving plot {plot_type} for storm {db_storm.id} to db, {e}")
                db.session.rollback()

    # create plots
    create_plot("observed_track")
    create_plot("forecast_model_tracks")
    create_plot("forecast_gefs_density")
    create_plot("forecast_gefs_tracks")

    if not realtime_storm.invest:
        create_plot("latest_forecast")


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

            # update storm forecast
            if not realtime_storm.invest:
                create_or_update_storm_forecast(realtime_storm, db_storm)

            # create storm plots
            create_storm_plots(realtime_storm, db_storm, realtime_obj.time)

        except Exception as e:
            logging.error(f"[DB]: Error creating updating storm {e}")
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
            logging.error(f"[DB]: Error creating storm {e}")
            db.session.rollback()

        if not realtime_storm.invest:
            # update storm forecast
            create_or_update_storm_forecast(realtime_storm, db_storm)

        create_storm_plots(realtime_storm, db_storm, realtime_obj.time)


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

        logging.info(f'[SERVICE]: Fetched {len(storms)} realtime storms from DB')

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

            # get list of active storms
            realtime_storm_list = realtime_obj.list_active_storms()

            # get all existing realtime storms from database
            db_realtime_storms = StormService.get_realtime_storms()

            for db_storm in db_realtime_storms:
                if db_storm.id not in realtime_storm_list:
                    # realtime db storm not in updated realtime list, proceed to mark as not realtime
                    updated = False

                    try:
                        logging.info(
                            f"DB Storm {db_storm.id} not found in incoming realtime storms.Mark as not realtime")
                        db_storm.realtime = False
                        db_storm.update_time = realtime_obj.time
                        db.session.commit()
                        updated = True
                    except Exception as e:
                        db.session.rollback()
                        logging.error(f"Error marking DB storm {db_storm.id} as not realtime, {e}")

                    if updated:
                        # clean up plots for storms that are no longer realtime
                        clean_up_storm_plots(db_storm.id)

            # create or update incoming realtime storms
            for storm_id in realtime_storm_list:
                logging.info(f"Creating new storm {storm_id}")
                create_or_update_storm(storm_id, realtime_obj)
        except Exception as e:
            logging.error(f"[SERVICE]: Error updating realtime data {e}")

    @staticmethod
    def plot_summary(jtwc_source="jtwc"):
        logging.info(f"[SERVICE]: Ploting realtime summary")

        basins = {"all"}

        # create realtime object
        realtime_obj = realtime.Realtime(jtwc=True, jtwc_source=jtwc_source, ssl_certificate=False)

        realtime_storms = realtime_obj.list_active_storms()

        for storm_id in realtime_storms:
            storm = realtime_obj.get_storm(storm_id)
            basins.add(storm.attrs.get("basin"))

        db_plot = Plot()

        try:
            db.session.add(db_plot)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

            # generate plot for every basin
        for basin in basins:
            try:
                dt = datetime.now()

                date_path = f"summary_plots/{dt.strftime('%Y%m%d')}/{dt.strftime('%H')}"

                # make dir recursively, dont raise if exists
                os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], date_path), exist_ok=True)

                fn = dt.strftime("%Y_%m_%d-%H_%M_%S")

                file_path = os.path.join(date_path, f"{basin}_{secure_filename(fn)}.png")

                realtime_obj.plot_summary(domain=basin, ssl_certificate=False,
                                          save_path=os.path.join(app.config['UPLOAD_FOLDER'], file_path))

                data = {
                    "plot_id": db_plot.id,
                    "basin": basin,
                    "file_path": file_path
                }

                plot_file = PlotFile(**data)

                logging.info('[DB]: SAVE PLOT')
                db.session.add(plot_file)
                db.session.commit()
                logging.info(f"Created plot for basin: {plot_file.basin} ")

            except Exception as e:
                db.session.rollback()
                print(e)

    @staticmethod
    def get_recent_plot():
        logging.info('[SERVICE]: Getting recent plot')
        logging.info('[DB]: QUERY')

        plots = Plot.query.first()

        return plots
