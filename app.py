from flask import Flask, g, render_template, session, redirect, url_for, flash, request
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'database.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = "MyReallySecretKey"


# creates a login required area
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session: 
            flash("You need to be logged in to view this page.")
            return redirect(url_for('login')) 
        return f(*args, **kwargs)
    return decorated_function

# data base getter
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# quering database
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# clean up database connection

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# main page
@app.route("/", methods=["GET"])
def home():
    # 1. Fetch house points
    points_query = """
        SELECT south_point, north_point, west_point
        FROM house_points
        LIMIT 1;
    """
    house_points = query_db(points_query, one=True)
    if house_points is None:
        house_points = {"south_point": 0, "north_point": 0, "west_point": 0}

    # 2. Get search parameter from URL (e.g. /?search=sports)
    search_query = request.args.get("search", "").strip()

    # 3. Build SQL for events with optional filtering
    if search_query:
        events_sql = """
            SELECT id, name, points, description, time, ended
            FROM events
            WHERE name LIKE ? OR description LIKE ?;
        """
        # Pass wildcards % for SQL substring matching
        param = f"%{search_query}%"
        events_listed = query_db(events_sql, (param, param))
    else:
        events_sql = """
            SELECT id, name, points, description, time, ended
            FROM events;
        """
        events_listed = query_db(events_sql)

    return render_template(
        "home.html",
        house_points=house_points,
        event=events_listed,
        search_query=search_query
    )

# login page
@app.route('/login', methods=["GET","POST"])
def login():
    # query the points
    points = "SELECT south_point, north_point, west_point FROM house_points"
    results = query_db(points, one=True)
    # getting the data from the form
    if request.method == "POST":
        username = request.form['username'] # get the username
        password = request.form['password']# get the password
        
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(sql, args=(username,), one=True) # get database of user and find the user
        
        if user: # if there is a user
            if check_password_hash(user[2], password): # check the password to the database
                session['user'] = {
                    'id': user[0],
                    'username': user[1]
                } # create a session with the user
                flash("Logged in successfully")
                return redirect(url_for('home')) # return them back home
            else:
                flash("Incorrect password") # tell them they typed the wrong password
        else:
            flash("Username does not exist") # tell them the username doesn't exist 
            
    return render_template('login.html', house_points=results) # render the login site


@app.route('/signup', methods=["GET", "POST"])
def signup():
    # query the points
    db = get_db()
    points = "SELECT south_point, north_point, west_point FROM house_points"
    results = query_db(points, one=True)
    #getting data from the signup page
    if request.method == "POST":
        username = request.form['username'] # username data
        password = request.form['password']# password data
        
        existing_user = query_db("SELECT * FROM user WHERE username = ?", (username,), one=True) # checking if the user already exist
        if existing_user:
            flash("Username already taken!") # tell them it exist
        else:
            hashed_password = generate_password_hash(password) # generate a unreadable string 
            db.execute("INSERT INTO user (username, password) VALUES (?, ?)", (username, hashed_password)) # add this to the database
            db.commit()
            flash("Sign Up Successful!") #tell them they succeeded
            return redirect(url_for('login')) # send them to the login page
            
    return render_template('signup.html', house_points=results)

# specific event page
@app.route("/events/<int:id>")
def event_detail(id):
    # query the points and the event data
    event_query = "SELECT name, points, description, time FROM events WHERE id = ?;"
    points = "SELECT south_point, north_point, west_point FROM house_points"
    
    house_point = query_db(points, one=True)
    event = query_db(event_query, (id,), True)
    # if event doesn't exist then show error
    if event is None:
        return "Event not found", 404
    #else render the page normally
    return render_template("events_info.html", house_points=house_point, event=event)

# edit the points
@app.route("/edit", methods=['GET', 'POST'])
@login_required # prevent people without an account to do things
def editPage():
    db = get_db()
    # getting the data from the form
    if request.method == 'POST':
        south = request.form.get('south')
        north = request.form.get('north')
        west = request.form.get('west')
        # updating the data base with the data from the form
        db.execute("""
            UPDATE house_points 
            SET south_point = ?, north_point = ?, west_point = ?
        """, (south, north, west))
        db.commit()
        return redirect(url_for('home'))

    points_query = "SELECT south_point, north_point, west_point FROM house_points"
    results = query_db(points_query, one=True) # shows the current points to the user
    return render_template("edit_score.html", house_points=results) 


# adding new events to the page
@app.route("/add_events", methods=['GET', 'POST'])
@login_required # login required to access
def addNewEvent():
    # getting the database the housepoints for the layout
    points_query = "SELECT south_point, north_point, west_point FROM house_points"
    house_point = query_db(points_query, one=True)

    db = get_db()
    # getting things from the form
    if request.method == "POST":
        name = request.form.get('event_name')
        description = request.form.get('event_discription') 
        point = int(request.form.get('event_point'))
        date = request.form.get('event_date')

        # adding things to the data base
        db.execute("""
            INSERT INTO events (name, description, time, points, ended)
            VALUES (?, ?, ?, ?, ?) 
        """, (name, description, date, point, 0))

        db.commit()
        return redirect(url_for('home'))
        
    return render_template("add_events.html", house_points=house_point)


# Edditing events
@app.route("/edit_event/<int:id>", methods=['GET', 'POST']) # getting the specific id of the page and the form
@login_required
def edit_events(id):
    points_query = "SELECT south_point, north_point, west_point FROM house_points"
    house_point = query_db(points_query, one=True)
    db = get_db()
    # getting the data of the form
    if request.method == "POST": 
        name = request.form.get('event_name')
        description = request.form.get('event_discription')
        point = int(request.form.get('event_point'))
        date = request.form.get('event_date')
        ended = 1 if request.form.get('ended') else 0 # check if the event has ended 0 is not and 1 is ended
        #updates the data base
        db.execute("""
            UPDATE events
            SET name = ?, description = ?, time = ?, points = ?, ended = ?
            WHERE id = ?
        """, (name, description, date, point, ended, id))
        db.commit()
        return redirect(url_for('home'))
    #getting the data
    event_query = "SELECT * FROM events WHERE id = ?"
    event = query_db(event_query, [id], one=True)
    return render_template("edit_event.html", event=event, house_points=house_point, id=id)

#Add a logout route to test session clearing
@app.route('/logout')
def logout():
    session.pop('user', None) # remove the session
    flash("Logged out successfully")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)