from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from data_fetcher import OpenF1Client
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = OpenF1Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current-session')
def get_current_session():
    """Get current or most recent F1 session"""
    session = client.get_current_session()
    return jsonify(session if session else {})

@app.route('/api/meetings')
def get_meetings():
    """Get all race meetings for current year"""
    year = request.args.get('year', datetime.utcnow().year, type=int)
    meetings = client.get_meetings(year)
    return jsonify(meetings)

@app.route('/api/sessions/<int:meeting_key>')
def get_sessions(meeting_key):
    """Get all sessions for a specific meeting"""
    sessions = client.get_sessions_for_meeting(meeting_key)
    return jsonify(sessions)

@app.route('/api/race-data/<int:session_key>')
def get_race_data(session_key):
    """Get comprehensive race data"""
    data = client.get_comprehensive_race_data(session_key)
    return jsonify(data)

@app.route('/api/positions/<int:session_key>')
def get_positions(session_key):
    """Get latest driver positions"""
    positions = client.get_latest_positions(session_key)
    return jsonify(positions)

@app.route('/api/pit-stops/<int:session_key>')
def get_pit_stops(session_key):
    """Get all pit stops"""
    pit_stops = client.get_pit_stops(session_key)
    return jsonify(pit_stops)

@app.route('/api/race-control/<int:session_key>')
def get_race_control(session_key):
    """Get race control messages"""
    messages = client.get_race_control_messages(session_key)
    return jsonify(messages)

@app.route('/api/team-radio/<int:session_key>')
def get_team_radio(session_key):
    """Get team radio messages"""
    radio = client.get_team_radio(session_key)
    return jsonify(radio)

@app.route('/api/weather/<int:session_key>')
def get_weather(session_key):
    """Get weather data"""
    weather = client.get_weather(session_key)
    return jsonify(weather)

@app.route('/api/intervals/<int:session_key>')
def get_intervals(session_key):
    """Get time intervals between drivers"""
    intervals = client.get_intervals(session_key)
    return jsonify(intervals)

@app.route('/api/stints/<int:session_key>')
def get_stints(session_key):
    """Get tire stint information"""
    stints = client.get_stints(session_key)
    return jsonify(stints)

@app.route('/api/laps/<int:session_key>')
def get_laps(session_key):
    """Get lap times"""
    driver_number = request.args.get('driver_number', type=int)
    laps = client.get_lap_data(session_key, driver_number)
    return jsonify(laps)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

