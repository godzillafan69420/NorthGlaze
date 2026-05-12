from flask import Flask, g, render_template, session, redirect, url_for, request
import sqlite3


DATABASE = 'database.db'


app = Flask(__name__)



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
    points = """
        SELECT house_points.south_point,
               house_points.north_point,
               house_points.west_point
        FROM house_points;

    """
    house_point = query_db(points, one=True)

    db=get_db()
    if request.method =="POST":
        name = request.form.get('event_name')
        discription = request.form.get('event_discription')
        point = request.form.get('event_point')
        date = request.form.get('event_date')
        db.execute("""
        INSERT INTO events (name, description, time, points)
        VALUES, name = ?, description = ?,time = ?,points = ? """(name, discription, date, point))

    db.commit()
    return render_template("add_events.html",house_points=house_point)

if __name__ == "__main__":
    app.run(debug=True)