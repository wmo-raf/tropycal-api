from troapi import db

from troapi.config import SETTINGS

MEDIA_URL = SETTINGS.get("MEDIA_URL")


class Plot(db.Model):
    __tablename__ = "plot"

    id = db.Column(db.String(255), primary_key=True)
    created_on = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    files = db.relationship("PlotFile", back_populates="plot")

    def __repr__(self):
        return '<Plot %r>' % self.id

    def serialize(self):
        return {
            "id": self.id,
            "plots": self.files,
            "created_on": self.created_on,
        }


class PlotFile(db.Model):
    __tablename__ = "plot_file"

    id = db.Column(db.Integer, primary_key=True)
    plot_id = db.Column(db.String, db.ForeignKey('plot.id'), nullable=False)
    basin = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String, nullable=False)

    plot = db.relationship("Plot", back_populates="files")

    def __init__(self, plot_id, basin, file_path):
        self.plot_id = plot_id
        self.basin = basin
        self.file_path = file_path

    def __repr__(self):
        return '<PlotFile %r>' % self.id

    def serialize(self):
        return {
            "basin": self.basin,
            "url": MEDIA_URL + self.file_path
        }
