from flask import Flask, g, render_template, session, redirect, url_for, flash,request
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'database.db'


app = Flask(__name__)

app.config['SECRET_KEY'] = "MyReallySecretKey"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()




@app.route("/")
def home():
    points = """
        SELECT house_points.south_point,
               house_points.north_point,
               house_points.west_point
        FROM house_points;

    """
    results = query_db(points, one=True)
    events = """
        SELECT events.id,
                events.name,
               events.points,
               events.description,
               events.time,
               events.ended

        FROM events;
        """
    events_listed = query_db(events)

    return render_template("home.html",
                           house_points=results,
                           event=events_listed)


@app.route('/login', methods=["GET","POST"])
def login():
    points = """
        SELECT house_points.south_point,
               house_points.north_point,
               house_points.west_point
        FROM house_points;

    """
    results = query_db(points, one=True)
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(sql,args=(username,),one=True)
        if user:
            if check_password_hash(user[2],password):
                session['user'] = user
                flash("Logged in successfully")
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
    return render_template('login.html', house_points=results)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    db = get_db()
    points = """
        SELECT house_points.south_point,
               house_points.north_point,
               house_points.west_point
        FROM house_points;

    """
    results = query_db(points, one=True)
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO user (username,password) SET (?,?)",(username,hashed_password))
        db.commit()
        flash("Sign Up Successful")
    return render_template('signup.html' ,
                           house_points=results)


@app.route("/events/<int:id>")
def event_detail(id):
    event_query = """
        SELECT name, points, description, time
        FROM events
        WHERE id = ?;
    """
    points = """
        SELECT house_points.south_point,
               house_points.north_point,
               house_points.west_point
        FROM house_points;

    """
    house_point = query_db(points, one=True)
    event = query_db(event_query, (id,), True)
    if event is None:
        return "Event not found", 404
    return render_template("events_info.html", house_points=house_point, event=event)


@app.route("/edit", methods=['GET', 'POST'])
def editPage():
    db = get_db()
    
    if request.method == 'POST':
 
        south = request.form.get('south')
        north = request.form.get('north')
        west = request.form.get('west')
        db.execute("""
            UPDATE house_points 
            SET south_point = ?, north_point = ?, west_point = ?
        """, (south, north, west))
        
        db.commit()
        
        return redirect(url_for('home'))

    points_query = "SELECT south_point, north_point, west_point FROM house_points"
    results = query_db(points_query, one=True)
    return render_template("edit_score.html", house_points=results)

@app.route("/add_events", methods=['GET', 'POST'])
def addNewEvent():
    points_query = "SELECT south_point, north_point, west_point FROM house_points"
    
    house_point = query_db(points_query, one=True)

    db=get_db()
    if request.method =="POST":
        name = request.form.get('event_name')
        discription = request.form.get('event_discription')
        point = int(request.form.get('event_point'))
        date = request.form.get('event_date')

        db.execute("""
        INSERT INTO events (name, description, time, points, ended)
        SET (?, ?, ?, ?, ?) """,(name, discription, date, point, 0))

        db.commit()
        return redirect(url_for('home'))
    return render_template("add_events.html",house_points=house_point)


@app.route("/edit_event/<int:id>" , methods=['GET', 'POST'])
def edit_events(id):
    points_query = "SELECT south_point, north_point, west_point FROM house_points"

    house_point = query_db(points_query, one=True)
    db=get_db()
    if request.method =="POST":
        name = request.form.get('event_name')
        discription = request.form.get('event_discription')
        point = int(request.form.get('event_point'))
        date = request.form.get('event_date')
        ended = 1 if request.form.get('ended') else 0

        db.execute("""
        UPDATE events
        SET  name = ?, description = ?, time = ?, points = ?, ended= ?
        WHERE id = ?""",(name, discription, date, point, ended, id))
        
        db.commit()

        return redirect(url_for('home'))
    event_query = "SELECT * FROM events WHERE id = ?"
    event = query_db(event_query, [id], one=True)
    return render_template("edit_event.html", event=event, house_points=house_point, id = id)

if __name__ == "__main__":
    app.run(debug=True)