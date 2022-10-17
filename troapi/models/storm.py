from datetime import timedelta

from numpy import isnan
from sqlalchemy import PickleType
from sqlalchemy.ext.mutable import MutableList
from troapi.config import SETTINGS

from troapi import db

BASIN_MAPPING = {
    "north_atlantic": "NA",
    "east_pacific": "EP",
    "west_pacific": "WP",
    "north_indian": "NI",
    "south_indian": "SI",
    "australia": "AU",
    "south_pacific": "SP",
    "south_atlantic": "SA",
    "conus": "CO",
    "east_conus": "EC",
}

MEDIA_URL = SETTINGS.get("MEDIA_URL")


class Storm(db.Model):
    __tablename__ = "storm"

    id = db.Column(db.String(255), primary_key=True)
    operational_id = db.Column(db.String(255), nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    season = db.Column(db.Integer, nullable=False)
    basin = db.Column(db.String(255), nullable=False)
    source_info = db.Column(db.String(255), nullable=True)
    source_method = db.Column(db.String(255), nullable=True)
    source_url = db.Column(db.String(255), nullable=True)
    source = db.Column(db.String(255), nullable=True)
    jtwc_source = db.Column(db.String(255), nullable=True)
    ace = db.Column(db.Float, nullable=True)
    prob_2day = db.Column(db.String(255), nullable=True)
    prob_5day = db.Column(db.String(255), nullable=True)
    risk_2day = db.Column(db.String(255), nullable=True)
    risk_5day = db.Column(db.String(255), nullable=True)
    realtime = db.Column(db.Boolean, default=False, nullable=False)
    invest = db.Column(db.Boolean, default=False, nullable=False)
    update_time = db.Column(db.DateTime, nullable=False)
    date = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    type = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    lat = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    lon = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    vmax = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    mslp = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    extra_obs = db.Column(MutableList.as_mutable(PickleType), nullable=True)
    special = db.Column(MutableList.as_mutable(PickleType), nullable=True)
    wmo_basin = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    forecast = db.relationship("StormForecast", back_populates="storm", uselist=False)
    plot = db.relationship("StormPlot", back_populates="storm")

    def __init__(self, **kwargs):
        for column in kwargs:
            if hasattr(self, column):
                setattr(self, column, kwargs[column])

    def __repr__(self):
        return '<Storm %r>' % self.id

    def serialize(self, include=None):
        """Return object data in easily serializable format"""

        include = include if include else []

        track = []
        for idx, _ in enumerate(self.date):
            mslp = None if isnan(self.mslp[idx]) else self.mslp[idx]
            vmax = None if isnan(self.vmax[idx]) else self.vmax[idx]

            feature = {
                "date": self.date[idx].isoformat(),
                "lon": self.lon[idx],
                "lat": self.lat[idx],
                "wind": vmax,
                "pressure": mslp,
                "basin": BASIN_MAPPING[self.wmo_basin[idx]],
                "type": self.type[idx],
                "forecast": False,
            }

            track.append(feature)

        storm = {
            'id': self.id,
            'operational_id': self.operational_id,
            'update_time': self.update_time.isoformat(),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'name': self.name,
            'year': self.year,
            'season': self.season,
            'basin': self.basin,
            'source_info': self.source_info,
            'invest': self.invest,
            'source_method': self.source_method,
            'source_url': self.source_url,
            'source': self.source,
            'ace': self.ace,
            'prob_2day': self.prob_2day,
            'prob_5day': self.prob_5day,
            'risk_2day': self.risk_2day,
            'risk_5day': self.risk_5day,
            'realtime': self.realtime,
            "track": track
        }

        if self.forecast:
            storm["track"] = storm["track"] + self.forecast.serialize()

        storm["plots"] = {}

        for plot in self.plot:
            updated_on = plot.updated_on.isoformat()

            if storm["plots"].get(updated_on):
                storm["plots"][updated_on].append(plot.serialize())
            else:
                storm["plots"][updated_on] = [plot.serialize()]

        return storm

    @property
    def storm_object(self):
        return {
            'id': self.id,
            'operational_id': self.operational_id,
            'update_time': self.update_time,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'name': self.name,
            'year': self.year,
            'season': self.season,
            'basin': self.basin,
            'source_info': self.source_info,
            'invest': self.invest,
            'source_method': self.source_method,
            'source_url': self.source_url,
            'source': self.source,
            "jtwc_source": self.jtwc_source,
            'ace': self.ace,
            'prob_2day': self.prob_2day,
            'prob_5day': self.prob_5day,
            'risk_2day': self.risk_2day,
            'risk_5day': self.risk_5day,
            'realtime': self.realtime,
            "type": self.type,
            "date": self.date,
            "vmax": self.vmax,
            "mslp": self.mslp,
            "lon": self.lon,
            "lat": self.lat,
            "wmo_basin": self.wmo_basin
        }


class StormForecast(db.Model):
    __tablename__ = "storm_forecast"

    id = db.Column(db.Integer, primary_key=True)
    storm_id = db.Column(db.String, db.ForeignKey('storm.id'), nullable=False)
    init = db.Column(db.DateTime, nullable=False)
    fhr = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    lat = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    lon = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    vmax = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    mslp = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    type = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    windrad = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    cumulative_ace = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    cumulative_ace_fhr = db.Column(MutableList.as_mutable(PickleType), nullable=False)

    storm = db.relationship("Storm", back_populates="forecast")

    def __init__(self, **kwargs):
        for column in kwargs:
            if hasattr(self, column):
                setattr(self, column, kwargs[column])

    def __repr__(self):
        return '<StormForecast %r>' % self.id

    def serialize(self):
        """Return object data in easily serializable format"""

        track = []
        for idx, _ in enumerate(self.lat):
            mslp = None if isnan(self.mslp[idx]) else self.mslp[idx]
            vmax = None if isnan(self.vmax[idx]) else self.vmax[idx]

            forecast_datetime = (self.init + timedelta(hours=self.fhr[idx])).isoformat()

            forecast = {
                "date": forecast_datetime,
                "lat": self.lat[idx],
                "lon": self.lon[idx],
                "wind": vmax,
                "pressure": mslp,
                "type": self.type[idx],
                "forecast": True,
            }

            track.append(forecast)

        return track


class StormPlot(db.Model):
    __tablename__ = "storm_plot"

    id = db.Column(db.Integer, primary_key=True)
    storm_id = db.Column(db.String, db.ForeignKey('storm.id'), nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)
    plot_type = db.Column(db.String, nullable=False)
    file_path = db.Column(db.String, nullable=False)

    storm = db.relationship("Storm", back_populates="plot")

    def __init__(self, storm_id, updated_on, plot_type, file_path):
        self.storm_id = storm_id
        self.updated_on = updated_on
        self.plot_type = plot_type
        self.file_path = file_path

    def __repr__(self):
        return '<StormPlot %r>' % self.id

    def serialize(self):
        """Return object data in easily serializable format"""

        return {
            "updated_on": self.updated_on.isoformat(),
            "plot_type": self.plot_type,
            "url": MEDIA_URL + self.file_path
        }
