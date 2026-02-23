#!/usr/bin/env python3
"""
Mission Control - Production-Ready Flask App for Railway
Server-side rendered Flask app with SQLite/PostgreSQL support
"""

import os
import sys
import json
import sqlite3
import logging
import datetime
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify, g, redirect, url_for, flash

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)

# Security: Use environment variable for secret key
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    logger.warning("SECRET_KEY not set! Using fallback - NOT SECURE FOR PRODUCTION!")
    app.secret_key = 'mission-control-dev-key-change-in-production'

# Disable debug mode in production
app.debug = False

# Database configuration - support Railway PostgreSQL or SQLite fallback
def get_database_url():
    """Get database URL from environment, supporting Railway's DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Railway uses postgres:// but psycopg2 needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("Using PostgreSQL database from DATABASE_URL")
        return database_url
    
    # Fallback to SQLite for local development
    sqlite_path = os.environ.get('SQLITE_PATH', '/app/data/mission_control.db')
    logger.info(f"Using SQLite database at {sqlite_path}")
    return f"sqlite:///{sqlite_path}"

# Database type detection
def is_postgresql():
    return get_database_url().startswith('postgresql://')

def is_sqlite():
    return get_database_url().startswith('sqlite://')

# Get database path for SQLite
def get_sqlite_path():
    url = get_database_url()
    if url.startswith('sqlite:///'):
        return url[10:]
    return '/app/data/mission_control.db'

# Database connection helpers
def get_db():
    """Get database connection"""
    if 'db' not in g:
        if is_postgresql():
            import psycopg2
            from psycopg2.extras import RealDictCursor
            g.db = psycopg2.connect(get_database_url())
            g.db.cursor_factory = RealDictCursor
        else:
            g.db = sqlite3.connect(get_sqlite_path())
            g.db.row_factory = sqlite3.Row
    return g.db

def get_cursor():
    """Get database cursor"""
    db = get_db()
    if is_postgresql():
        return db.cursor()
    return db

def execute_sql(query, params=None):
    """Execute SQL with parameter substitution for both SQLite and PostgreSQL"""
    cursor = get_cursor()
    
    # Convert ? placeholders to %s for PostgreSQL
    if is_postgresql():
        query = query.replace('?', '%s')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor

def commit_db():
    """Commit database changes"""
    db = get_db()
    db.commit()

def fetchone(cursor):
    """Fetch one row from cursor"""
    result = cursor.fetchone()
    if result is None:
        return None
    if is_postgresql():
        return dict(result)
    return result

def fetchall(cursor):
    """Fetch all rows from cursor"""
    results = cursor.fetchall()
    if is_postgresql():
        return [dict(row) for row in results]
    return results

@app.teardown_appcontext
def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables"""
    db = get_db()
    cursor = get_cursor()
    
    try:
        # Agents table
        if is_postgresql():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    status TEXT DEFAULT 'idle',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    status TEXT DEFAULT 'idle',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Messages table
        if is_postgresql():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    agent_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (id)
                )
            ''')
        
        # Projects table
        if is_postgresql():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Timeline/Activity table
        if is_postgresql():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timeline (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Subagents table
        if is_postgresql():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subagents (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subagents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
        
        commit_db()
        logger.info("Database tables initialized successfully")
        
        # Insert default agents if none exist
        cursor = execute_sql('SELECT COUNT(*) as count FROM agents')
        result = fetchone(cursor)
        count = result['count'] if result else 0
        
        if count == 0:
            default_agents = [
                ('Alpha', 'Research Assistant', 'idle', 'Web research and data gathering'),
                ('Beta', 'Code Reviewer', 'idle', 'Code analysis and optimization'),
                ('Gamma', 'Content Writer', 'idle', 'Documentation and content creation'),
                ('Delta', 'Data Analyst', 'idle', 'Data processing and visualization'),
                ('Epsilon', 'DevOps Engineer', 'idle', 'Infrastructure and deployment')
            ]
            for agent in default_agents:
                execute_sql(
                    'INSERT INTO agents (name, role, status, description) VALUES (?, ?, ?, ?)',
                    agent
                )
            commit_db()
            logger.info("Default agents inserted")
        
        # Insert default projects if none exist
        cursor = execute_sql('SELECT COUNT(*) as count FROM projects')
        result = fetchone(cursor)
        count = result['count'] if result else 0
        
        if count == 0:
            default_projects = [
                ('YouTube Automation', 'youtube', 'active', 65, 'Automated video production pipeline'),
                ('Betting Analytics', 'betting', 'active', 40, 'Sports betting data analysis system'),
                ('F-Gas Compliance', 'f-gas', 'paused', 80, 'Refrigerant tracking and compliance'),
                ('Trading Bot', 'trading', 'active', 25, 'Automated cryptocurrency trading')
            ]
            for project in default_projects:
                execute_sql(
                    'INSERT INTO projects (name, category, status, progress, description) VALUES (?, ?, ?, ?, ?)',
                    project
                )
            commit_db()
            logger.info("Default projects inserted")
        
        # Insert initial timeline events if none exist
        cursor = execute_sql('SELECT COUNT(*) as count FROM timeline')
        result = fetchone(cursor)
        count = result['count'] if result else 0
        
        if count == 0:
            execute_sql('''
                INSERT INTO timeline (event_type, title, description, agent_name)
                VALUES ('system', 'Mission Control Started', 'System initialized and ready', 'System')
            ''')
            commit_db()
            logger.info("Initial timeline event inserted")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# ============== HEALTH CHECK ==============

@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        cursor = execute_sql('SELECT 1')
        fetchone(cursor)
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        # Return 200 so Railway doesn't restart, but indicate DB issue
        logger.warning(f"Health check DB issue: {e}")
        return jsonify({
            'status': 'degraded',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200

# ============== PAGE ROUTES ==============

@app.route('/')
def index():
    """Main dashboard"""
    try:
        cursor = get_cursor()
        
        # Get agent stats
        cursor.execute('SELECT * FROM agents ORDER BY name')
        agents = fetchall(cursor)
        agent_stats = {
            'total': len(agents),
            'active': sum(1 for a in agents if a['status'] == 'active'),
            'idle': sum(1 for a in agents if a['status'] == 'idle'),
            'busy': sum(1 for a in agents if a['status'] == 'busy')
        }
        
        # Get project stats
        cursor.execute('SELECT * FROM projects ORDER BY updated_at DESC')
        projects = fetchall(cursor)
        
        # Get recent timeline events
        cursor.execute('SELECT * FROM timeline ORDER BY created_at DESC LIMIT 20')
        timeline = fetchall(cursor)
        
        # Get recent messages for each agent
        recent_messages = {}
        for agent in agents:
            cursor.execute(
                '''SELECT content, created_at FROM messages 
                   WHERE agent_id = ? ORDER BY created_at DESC LIMIT 1''',
                (agent['id'],)
            )
            msg = fetchone(cursor)
            if msg:
                recent_messages[agent['id']] = msg
        
        return render_template('dashboard.html',
                             agents=agents,
                             agent_stats=agent_stats,
                             projects=projects,
                             timeline=timeline,
                             recent_messages=recent_messages)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', agents=[], agent_stats={}, projects=[], timeline=[], recent_messages={})

@app.route('/agents')
def agents():
    """Agents list page"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT * FROM agents ORDER BY name')
        agents = fetchall(cursor)
        return render_template('agents.html', agents=agents)
    except Exception as e:
        logger.error(f"Agents page error: {e}")
        flash('Error loading agents', 'error')
        return render_template('agents.html', agents=[])

@app.route('/agent/<int:agent_id>')
def agent_detail(agent_id):
    """Individual agent chat page"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        agent = fetchone(cursor)
        
        if agent is None:
            flash('Agent not found', 'error')
            return redirect(url_for('agents'))
        
        cursor.execute(
            '''SELECT * FROM messages WHERE agent_id = ? ORDER BY created_at DESC LIMIT 50''',
            (agent_id,)
        )
        messages = fetchall(cursor)
        
        return render_template('agent_chat.html', agent=agent, messages=messages)
    except Exception as e:
        logger.error(f"Agent detail error: {e}")
        flash('Error loading agent', 'error')
        return redirect(url_for('agents'))

@app.route('/projects')
def projects():
    """Projects page"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT * FROM projects ORDER BY category, name')
        projects = fetchall(cursor)
        return render_template('projects.html', projects=projects)
    except Exception as e:
        logger.error(f"Projects page error: {e}")
        flash('Error loading projects', 'error')
        return render_template('projects.html', projects=[])

@app.route('/command-center')
def command_center():
    """Command center page"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT * FROM agents ORDER BY name')
        agents = fetchall(cursor)
        
        cursor.execute('SELECT * FROM subagents ORDER BY created_at DESC LIMIT 10')
        recent_subagents = fetchall(cursor)
        
        return render_template('command_center.html', 
                             agents=agents, 
                             recent_subagents=recent_subagents)
    except Exception as e:
        logger.error(f"Command center error: {e}")
        flash('Error loading command center', 'error')
        return render_template('command_center.html', agents=[], recent_subagents=[])

@app.route('/timeline')
def timeline():
    """Timeline/Activity feed page"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT * FROM timeline ORDER BY created_at DESC LIMIT 100')
        events = fetchall(cursor)
        return render_template('timeline.html', events=events)
    except Exception as e:
        logger.error(f"Timeline error: {e}")
        flash('Error loading timeline', 'error')
        return render_template('timeline.html', events=[])

# ============== API ROUTES ==============

@app.route('/api/agent/<int:agent_id>/message', methods=['POST'])
def send_message(agent_id):
    """Send message to agent - API endpoint"""
    try:
        cursor = get_cursor()
        
        # Check if agent exists
        cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        agent = fetchone(cursor)
        
        if agent is None:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        # Get message content
        data = request.get_json() or {}
        content = data.get('message', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Store outbound message
        execute_sql(
            'INSERT INTO messages (agent_id, content, direction) VALUES (?, ?, ?)',
            (agent_id, content, 'outbound')
        )
        
        # Update agent status
        if is_postgresql():
            execute_sql(
                'UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?',
                ('busy', agent_id)
            )
        else:
            execute_sql(
                'UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?',
                ('busy', agent_id)
            )
        
        # Add to timeline
        execute_sql(
            '''INSERT INTO timeline (event_type, title, description, agent_name)
               VALUES (?, ?, ?, ?)''',
            ('message', f'Message to {agent["name"]}', content[:100], agent['name'])
        )
        
        commit_db()
        logger.info(f"Message sent to agent {agent['name']}")
        
        return jsonify({
            'success': True,
            'message': 'Message sent',
            'agent': agent['name']
        })
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/project/<int:project_id>/update', methods=['POST'])
def update_project(project_id):
    """Update project progress - API endpoint"""
    try:
        data = request.get_json() or {}
        progress = data.get('progress')
        status = data.get('status')
        
        if progress is not None:
            progress = max(0, min(100, int(progress)))
            execute_sql(
                'UPDATE projects SET progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (progress, project_id)
            )
        
        if status:
            execute_sql(
                'UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (status, project_id)
            )
        
        commit_db()
        logger.info(f"Project {project_id} updated")
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Update project error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spawn-agent', methods=['POST'])
def spawn_agent():
    """Spawn a subagent - API endpoint"""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')
        task = data.get('task', '').strip()
        
        if not agent_id:
            return jsonify({'success': False, 'error': 'No agent selected'}), 400
        
        if not task:
            return jsonify({'success': False, 'error': 'Task cannot be empty'}), 400
        
        # Get agent details
        cursor = get_cursor()
        cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
        agent = fetchone(cursor)
        
        if agent is None:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        # Generate session ID
        session_id = f"subagent-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{agent['name'].lower()}"
        
        # Record in database
        execute_sql(
            '''INSERT INTO subagents (session_id, agent_name, task, status)
               VALUES (?, ?, ?, ?)''',
            (session_id, agent['name'], task, 'running')
        )
        
        # Update agent status
        execute_sql(
            'UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?',
            ('active', agent_id)
        )
        
        # Add to timeline
        execute_sql(
            '''INSERT INTO timeline (event_type, title, description, agent_name)
               VALUES (?, ?, ?, ?)''',
            ('spawn', f'Agent {agent["name"]} Spawned', task[:100], agent['name'])
        )
        
        commit_db()
        logger.info(f"Agent {agent['name']} spawned for task: {task[:50]}...")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'agent': agent['name'],
            'message': f'Agent {agent["name"]} spawned successfully'
        })
    except Exception as e:
        logger.error(f"Spawn agent error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/timeline')
def api_timeline():
    """Get timeline events as JSON - API endpoint"""
    try:
        cursor = get_cursor()
        limit = request.args.get('limit', 50, type=int)
        cursor.execute(
            'SELECT * FROM timeline ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        events = fetchall(cursor)
        
        return jsonify({
            'success': True,
            'events': events
        })
    except Exception as e:
        logger.error(f"API timeline error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/agents/status')
def api_agents_status():
    """Get current agent statuses - API endpoint"""
    try:
        cursor = get_cursor()
        cursor.execute('SELECT id, name, status, last_active FROM agents')
        agents = fetchall(cursor)
        
        return jsonify({
            'success': True,
            'agents': agents
        })
    except Exception as e:
        logger.error(f"API agents status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return render_template('dashboard.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('dashboard.html'), 500

# ============== INITIALIZATION ==============

def init_app():
    """Initialize the application with database"""
    try:
        with app.app_context():
            init_db()
            logger.info("Mission Control initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to initialize Mission Control: {e}")
        return False

# Initialize on startup (but don't fail if DB has issues)
db_initialized = init_app()

if __name__ == '__main__':
    if not db_initialized:
        logger.warning("Starting without database initialization")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
