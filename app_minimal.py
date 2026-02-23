from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Simple in-memory storage for now
agents = [
    {'id': 1, 'name': 'Kez', 'role': 'Mission Commander', 'status': 'active'},
    {'id': 2, 'name': 'Kayla', 'role': 'Research', 'status': 'standby'},
    {'id': 3, 'name': 'Barry', 'role': 'Video Production', 'status': 'standby'},
    {'id': 4, 'name': 'Alex', 'role': 'Design', 'status': 'standby'},
    {'id': 5, 'name': 'Peyton', 'role': 'Trading Analysis', 'status': 'standby'}
]

projects = [
    {'id': 1, 'name': 'YouTube Sleep Science', 'status': 'active', 'progress': 20},
    {'id': 2, 'name': 'Sports Betting', 'status': 'setup', 'progress': 30},
    {'id': 3, 'name': 'F-Gas Product', 'status': 'ready', 'progress': 95},
    {'id': 4, 'name': 'Trading Bot', 'status': 'paused', 'progress': 70}
]

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/')
def dashboard():
    return render_template('dashboard.html', agents=agents, projects=projects)

@app.route('/agents')
def agents_page():
    return render_template('agents.html', agents=agents)

@app.route('/projects')
def projects_page():
    return render_template('projects.html', projects=projects)

@app.route('/command')
def command_page():
    return render_template('command.html', agents=agents)

@app.route('/api/agents')
def api_agents():
    return jsonify(agents)

@app.route('/api/projects')
def api_projects():
    return jsonify(projects)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
