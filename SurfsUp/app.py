# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from dateutil.relativedelta import relativedelta
from datetime import datetime

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
# Create an app
app = Flask(__name__)

# Define routes

@app.route("/")
def homepage():
    """All available api routes:"""
    session = Session(engine)

    # Get max and min dates from measurement table
    max_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    max_date_unquote = max_date[0]
    min_date = session.query(Measurement.date).order_by(Measurement.date).first()
    min_date_unquote = min_date[0]

    session.close()

    return (
        f"Available Routes:<br/><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/><br/>"
        f"Valid routes where dates between:<br/>"
        f"/api/v1.0/{min_date_unquote}<br/>"
        f"and<br/>"
        f"/api/v1.0/{max_date_unquote}<br/><br/>"
        f"Valid routes with start and end dates between:<br/>"
        f"/api/v1.0/{min_date_unquote}/{max_date_unquote}<br/>"
    )

#################################################
# Flask Routes
#################################################

@app.route("/api/v1.0/precipitation")
def precip_info():

    """Return the precipitation data as json"""

    session = Session(engine)
    
    # Get max date & 12 months prior
    max_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    max_date_str = max_date[0]
    max_date_fmt = datetime.strptime(max_date_str, '%Y-%m-%d')
    date_12m_prior = max_date_fmt - relativedelta(years=1, days=1)

    precip = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date > date_12m_prior).all()

    session.close()

# Create a dictionary from the row data and append to a list of precipitation
    precipitation = []
    for date, prcp in precip:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["prcp"] = prcp
        precipitation.append(precip_dict)

    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def station_info():

    """Return a list of all station names"""

    session = Session(engine)
    # Query all stations
    total_stations = session.query(Station.station).all()

    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(total_stations))

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def temperature():

    """Return a list of all temperatures for the most active station for the past 12 months"""

    session = Session(engine)
    
    # Get most active station
    station_obs_count = (session.query(Measurement.station, func.count(Measurement.station))
                         .group_by(Measurement.station)
                         .order_by(func.count(Measurement.station).desc())
                         .all()
                        )
    active_station = station_obs_count[0][0]

    # Get max date of most active station
    max_date_active = (session.query(Measurement.date)
                     .filter(Measurement.station==active_station)
                     .order_by(Measurement.date.desc()).first()
                    )
    max_date_active_str = max_date_active[0]
    max_date_active_fmt = datetime.strptime(max_date_active_str, '%Y-%m-%d')
    
     # Get date 12 months prior of most active station
    date_12m_prior_active = max_date_active_fmt - relativedelta(years=1, days=1)

    temp_active_station = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.date > date_12m_prior_active)\
        .filter(Measurement.station==active_station).all()
               
    session.close()    
           
    # Create a dictionary from the row data and append to a list
    list_active_date_temp = []
    for date, temp in temp_active_station:
        active_temp_dict = {}
        active_temp_dict["date"] = date
        active_temp_dict["temp"] = temp
        list_active_date_temp.append(active_temp_dict)

    return jsonify(list_active_date_temp)


# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date
@app.route("/api/v1.0/<start>")
def start_date(start):
    
    """Get the TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date that matches the path variable supplied by the user"""
    session = Session(engine)

    # Get min, max, mean of dates >= user defined start date
    # https://stackoverflow.com/questions/7133007/sqlalchemy-get-max-min-avg-values-from-a-table
    min_temp_start = session.query(func.min(Measurement.tobs)).filter(Measurement.date >= start).all()    
    max_temp_start = session.query(func.max(Measurement.tobs)).filter(Measurement.date >= start).all()
    mean_temp_start = session.query(func.avg(Measurement.tobs)).filter(Measurement.date >= start).all()

    session.close() 

    list_start_temp = []   
    start_dict = {}

    start_dict["min_temp"] = np.ravel(min_temp_start)[0]
    start_dict["max_temp"] = np.ravel(max_temp_start)[0]
    start_dict["mean_temp"] = np.ravel(mean_temp_start)[0]
    list_start_temp.append(start_dict)

    return jsonify(list_start_temp)

# For a specified start and end date, calculate TMIN, TAVG, and TMAX for all the dates between start and end date

@app.route("/api/v1.0/<startdate>/<end>")
def start_end_date(startdate,end):

    """Fetch the TMIN, TAVG, and TMAX for all the dates between start and end date (inclusive) that matches the path variable supplied by the user"""
    session = Session(engine)

    # Get min, max, mean of dates between user defined start date and end date (inclusive)
    min_temp_start_end = session.query(func.min(Measurement.tobs)).filter(Measurement.date >= startdate)\
        .filter(Measurement.date <= end).all()    
    max_temp_start_end = session.query(func.max(Measurement.tobs)).filter(Measurement.date >= startdate)\
        .filter(Measurement.date <= end).all()

    mean_temp_start_end = session.query(func.avg(Measurement.tobs)).filter(Measurement.date >= startdate)\
        .filter(Measurement.date <= end).all()

    session.close()

    list_start_end_temp = []   
    start_end_dict = {}

    start_end_dict["min_temp"] = np.ravel(min_temp_start_end)[0]
    start_end_dict["max_temp"] = np.ravel(max_temp_start_end)[0]
    start_end_dict["mean_temp"] = np.ravel(mean_temp_start_end)[0]
    list_start_end_temp.append(start_end_dict)

    return jsonify(list_start_end_temp)


if __name__ == "__main__":
    app.run(debug=True)
