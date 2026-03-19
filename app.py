from flask import Flask, g, render_template
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
    sql = """SELECT house_points.south_point, house_points.north_point," 
    house_points.west_point FROM house_points;"""
    results = query_db(sql)
    return render_template("layout.html", house_points=results)

if __name__ == "__main__":
    app.run(debug=True)