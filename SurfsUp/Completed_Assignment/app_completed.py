# Import Dependencies.
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
# Welcome users to the page and provide them with a list of selectable routes
@app.route("/")
def welcome():
    """List all available routes."""
    return(
        f"Welcome to the Honolulu, Hawaii Weather API!<br/><br>"
        f"Available Routes:<br/>"
        f"-- Daily Precipitation Totals (Aug2016 - Aug2017): <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"-- Active Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"-- Daily Temperature Observations for Station USC00519281 (Aug2016 - Aug2017): <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"-- To retrieve the minimum, average, and maximum temperatures for a specific start date, use /api/v1.0/'start' (replace 'start' with a date in yyyy-mm-dd format)<br/>"
        f"-- To retrieve the minimum, average, and maximum temperatures for a specific date range, use /api/v1.0/'start'/'end' (replace 'start' and 'end' with dates in yyyy-mm-dd format)<br/>"
        f"PLEASE NOTE: If no end-date is provided, the api will use 23Aug2017 as the end date.<br>" 
    )


# Define what will happen when the user clicks on the "/api/v1.0/precipitation" link.
# Query the database and display the daily precipitation amounts
# for only the last 12 months of data (23Aug2016 - 23Aug2017)
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set and
    # Calculate the date one year prior to the most recent date. 
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    one_year_prior = (dt.datetime.strptime(most_recent_date[0], "%Y-%m-%d") - dt.timedelta(days = 365)).strftime("%Y-%m-%d")
    
    # Perform the query to retrieve the precipitation scores (23Aug2016 - 23Aug2017)
    measurement_cols = (measurement.date, measurement.prcp)
    prcp_scores = session.query(*measurement_cols).filter(measurement.date >= one_year_prior).all()

    # Close the session
    session.close()
    
    # Create a dictionary from the query data
    prcp_list = []
    for date, prcp in prcp_scores:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        prcp_list.append(prcp_dict)

    # Return a list of jsonified precipitation scores (23Aug2016 - 23Aug2017) 
    return jsonify(prcp_list)


# Define what will happen when the user clicks on the "/api/v1.0/stations" link.
# Query the database and display the active stations
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to retrieve the stations
    stations = session.query(station.station).all()
    
    # Close the session
    session.close()

    # Convert the resulting list of tuples into a normal list
    station_listing = list(np.ravel(stations))

    # Return a jsonified version of the station listing
    return jsonify(station_listing)


# Define what will happen when the user clicks on the "/api/v1.0/tobs" link.
# Query the dates and temperature observations of the most-active station
# for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in the data set and
    # Calculate the date one year prior to the most recent date. 
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    one_year_prior = (dt.datetime.strptime(most_recent_date[0], "%Y-%m-%d") - dt.timedelta(days = 365)).strftime("%Y-%m-%d")
    
    # Perform the query to retrieve the dates and temperature obsevations(tobs) from Station USC00519281
    dates_temps = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == "USC00519281").\
        filter(measurement.date >= one_year_prior).order_by(measurement.date).all()

    # Close the session
    session.close()

    # Create a dictionary from the query data
    tobs_list = []
    for date, tobs in dates_temps:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        tobs_list.append(tobs_dict)

    # Return a list of jsonified tobs data for the previous 12 months
    return jsonify(tobs_list)


# Define what will happen when the user appends a start date to /api/v1.0/
@app.route("/api/v1.0/<start>")
def temp_stats_start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Create an empty list to hold the query results
    return_list = []

    results = session.query(measurement.date,\
                            func.min(measurement.tobs),\
                            func.avg(measurement.tobs),\
                            func.max(measurement.tobs)).\
                            filter(measurement.date >= start).\
                            group_by(measurement.date).all()
    
    for date, min, avg, max in results:
        new_dict = {}
        new_dict["Date"] = date
        new_dict["TMIN"] = min
        new_dict["TAVG"] = avg
        new_dict["TMAX"] = max
        return_list.append(new_dict)
    
    # Close the session
    session.close()

    # Return the query results jsonified
    return jsonify(return_list)


# Define what will happen when the user appends a start date and an end date to /api/v1.0/
@app.route("/api/v1.0/<start>/<end>")
def temp_stats_start_end(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Create an empty list to hold the query results
    return_list = []

    results = session.query(measurement.date,\
                            func.min(measurement.tobs),\
                            func.avg(measurement.tobs),\
                            func.max(measurement.tobs)).\
                            filter(measurement.date >= start).\
                            filter(measurement.date <= end).\
                            group_by(measurement.date).all()
    
    for date, min, avg, max in results:
        new_dict = {}
        new_dict["Date"] = date
        new_dict["TMIN"] = min
        new_dict["TAVG"] = avg
        new_dict["TMAX"] = max
        return_list.append(new_dict)
    
    # Close the session
    session.close()

    # Return the query results jsonified
    return jsonify(return_list)


if __name__ == '__main__':
    app.run(debug=True)