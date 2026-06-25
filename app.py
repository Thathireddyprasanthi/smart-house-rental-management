from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import joblib
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
model = joblib.load(
    "ml/rent_model.pkl"
)

encoder = joblib.load(
    "ml/location_encoder.pkl"
)
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "house_rental_secret_key"

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )

        conn.commit()

        cur.close()
        conn.close()

        return "Registration Successful"

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email,password)
        )



        user = cur.fetchone()

        if user:

            session['user_id'] = user[0]
            session['name'] = user[1]

            return redirect('/dashboard')

        else:
            return "Invalid Email or Password"

    return render_template("login.html")


@app.route('/dashboard')
def dashboard():

    conn = get_connection()
    cur = conn.cursor()

    # Total Properties
    cur.execute("SELECT COUNT(*) FROM properties")
    total_properties = cur.fetchone()[0]

    # Total Reviews
    cur.execute("SELECT COUNT(*) FROM ratings")
    total_reviews = cur.fetchone()[0]

    # Average Rent
    cur.execute("SELECT AVG(rent) FROM properties")
    avg_rent = cur.fetchone()[0]

    # Top Rated Property
    cur.execute("""
        SELECT p.location,
               AVG(r.rating) AS avg_rating
        FROM properties p
        JOIN ratings r
        ON p.property_id = r.property_id
        GROUP BY p.property_id
        ORDER BY avg_rating DESC
        LIMIT 1
    """)

    top_property = cur.fetchone()

    cur.close()
    conn.close()

    if 'user_id' in session:
        return render_template(
            "dashboard.html",
            name=session['name'],
            total_properties=total_properties,
            total_reviews=total_reviews,
            avg_rent=avg_rent,
            top_property=top_property
        )

    return redirect('/login')
def logout():

    session.clear()

    return redirect('/')
@app.route('/add_property', methods=['GET', 'POST'])
def add_property():

    if request.method == 'POST':

        owner_name = request.form['owner_name']
        location = request.form['location']
        bhk = request.form['bhk']
        area = request.form['area']
        rent = request.form['rent']
        furnished = request.form['furnished']

        image = request.files['image']

        filename = secure_filename(image.filename)

        print("Uploaded File:", filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO properties
        (owner_name, location, bhk, area, rent, furnished, image)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            owner_name,
            location,
            bhk,
            area,
            rent,
            furnished,
            filename
        ))

        conn.commit()

        cur.close()
        conn.close()

        return "Property Added Successfully"

    return render_template('add_property.html')
@app.route('/view_properties')
def view_properties():

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("SELECT * FROM properties")

    properties = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'view_properties.html',
        properties=properties
    )
@app.route('/edit_property/<int:id>',
           methods=['GET','POST'])
def edit_property(id):

    conn = get_connection()
    cur = conn.cursor()

    if request.method == 'POST':

        owner_name = request.form['owner_name']
        location = request.form['location']
        bhk = request.form['bhk']
        area = request.form['area']
        rent = request.form['rent']
        furnished = request.form['furnished']

        cur.execute("""
        UPDATE properties
        SET owner_name=%s,
            location=%s,
            bhk=%s,
            area=%s,
            rent=%s,
            furnished=%s
        WHERE property_id=%s
        """,
        (
            owner_name,
            location,
            bhk,
            area,
            rent,
            furnished,
            id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect('/view_properties')

    cur.execute(
        "SELECT * FROM properties WHERE property_id=%s",
        (id,)
    )

    property = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        'edit_property.html',
        property=property
    )
@app.route('/delete_property/<int:id>')
def delete_property(id):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute(
        "DELETE FROM properties WHERE property_id=%s",
        (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect('/view_properties')
@app.route('/search',
methods=['GET','POST'])
def search():

    if request.method == 'POST':

        location = request.form['location']
        rent = request.form['rent']
        bhk = request.form['bhk']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM properties
        WHERE location=%s
        AND rent<=%s
        AND bhk=%s
        """,
        (location,rent,bhk))

        properties = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            'view_properties.html',
            properties=properties
        )

    return render_template('search.html')
@app.route('/predict',
methods=['GET','POST'])
def predict():

    if request.method == 'POST':

        location = request.form['location']
        bhk = int(request.form['bhk'])
        area = int(request.form['area'])
        furnished = int(
            request.form['furnished']
        )

        location = encoder.transform(
            [location]
        )[0]

        prediction = model.predict([
            [
                location,
                bhk,
                area,
                furnished
            ]
        ])

        rent = int(prediction[0])

        return render_template(
            "result.html",
            rent=rent
        )

    return render_template(
        "predict.html"
    )
@app.route('/recommend', methods=['GET','POST'])
def recommend():

    if request.method == 'POST':

        location = request.form['location']
        budget = int(request.form['budget'])
        bhk = int(request.form['bhk'])

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        SELECT *
        FROM properties
        WHERE location=%s
        """, (location,))

        houses = cur.fetchall()

        recommendations = []

        for house in houses:

            score = 0

            if house[3] == bhk:
                score += 50

            rent = int(house[5])

            score += max(
                0,
                100 - abs(budget-rent)//100
            )

            recommendations.append(
                (score, house)
            )

        recommendations.sort(
            reverse=True,
            key=lambda x:x[0]
        )

        return render_template(
            'recommend_result.html',
            recommendations=recommendations
        )

    return render_template(
        'recommend.html'
    )
@app.route('/analytics')
def analytics():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM properties")
    total_properties = cur.fetchone()[0]

    cur.execute("SELECT AVG(rent) FROM properties")
    avg_rent = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        'analytics.html',
        total_users=total_users,
        total_properties=total_properties,
        avg_rent=round(avg_rent, 2)
    )
@app.route('/rent_chart')
def rent_chart():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT location, rent FROM properties"
    )

    data = cur.fetchall()

    cur.close()
    conn.close()

    locations = []
    rents = []

    for row in data:
        locations.append(row[0])
        rents.append(row[1])

    plt.figure(figsize=(8,5))
    plt.bar(locations, rents)

    plt.title("Location Wise Rent")
    plt.xlabel("Location")
    plt.ylabel("Rent")

    plt.savefig(
        "static/charts/rent_chart.png"
    )

    plt.close()

    return render_template(
        "rent_chart.html"
    )
@app.route('/admin')
def admin():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM properties")
    total_properties = cur.fetchone()[0]

    cur.execute("SELECT MAX(rent) FROM properties")
    max_rent = cur.fetchone()[0]

    cur.execute("SELECT MIN(rent) FROM properties")
    min_rent = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        'admin.html',
        total_users=total_users,
        total_properties=total_properties,
        max_rent=max_rent,
        min_rent=min_rent
    )
@app.route('/download_report')
def download_report():

    pdf = SimpleDocTemplate("static/property_report.pdf")

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "House Rental Management Report",
            styles['Title']
        )
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT owner_name,
           location,
           bhk,
           rent
    FROM properties
    """)

    properties = cur.fetchall()

    for p in properties:

        text = f"""
        Owner: {p[0]}<br/>
        Location: {p[1]}<br/>
        BHK: {p[2]}<br/>
        Rent: {p[3]}<br/><br/>
        """

        content.append(
            Paragraph(
                text,
                styles['Normal']
            )
        )

    pdf.build(content)

    cur.close()
    conn.close()

    return redirect(
        '/static/property_report.pdf'
    )
@app.route('/rate/<int:property_id>', methods=['GET','POST'])
def rate(property_id):

    if request.method == 'POST':

        user_id = session['user_id']
        rating = request.form['rating']
        review = request.form['review']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO ratings
        (property_id, user_id, rating, review)
        VALUES(%s,%s,%s,%s)
        """,
        (
            property_id,
            user_id,
            rating,
            review
        ))

        conn.commit()

        cur.close()
        conn.close()

        return "Rating Submitted Successfully"
    return render_template(
        'rate.html',
        property_id=property_id
    )
@app.route('/reviews/<int:property_id>')
def reviews(property_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
SELECT u.name, r.rating, r.review
FROM ratings r
JOIN users u
ON r.user_id = u.id
WHERE r.property_id=%s
""", (property_id,))

    reviews = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'reviews.html',
        reviews=reviews
    )
@app.route('/property/<int:id>')
def property_details(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
SELECT p.*,
       AVG(r.rating) as avg_rating
FROM properties p
LEFT JOIN ratings r
ON p.property_id = r.property_id
WHERE p.property_id=%s
GROUP BY p.property_id
""", (id,))

    property = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        'property_details.html',
        property=property
    )
@app.route('/enquiry/<int:property_id>', methods=['GET', 'POST'])
def enquiry(property_id):

    if request.method == 'POST':

        message = request.form['message']

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO enquiries
            (property_id, user_id, message)
            VALUES(%s,%s,%s)
        """, (
            property_id,
            session['user_id'],
            message
        ))

        conn.commit()

        cur.close()
        conn.close()

        return "Enquiry Sent Successfully"

    return render_template(
        'enquiry.html'
    )
@app.route('/view_enquiries')
def view_enquiries():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.enquiry_id,
               p.owner_name,
               p.location,
               e.message
        FROM enquiries e
        JOIN properties p
        ON e.property_id = p.property_id
    """)

    enquiries = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'view_enquiries.html',
        enquiries=enquiries
    )
@app.route('/book/<int:property_id>')
def book(property_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
INSERT INTO bookings(property_id, user_name)
VALUES(%s,%s)
""", (
    property_id,
    session['name']
))

    conn.commit()

    cur.close()
    conn.close()

    return "Booking Request Sent Successfully"
@app.route('/view_bookings')
def view_bookings():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT booking_id,
               property_id,
               user_id,
               status
        FROM bookings
    """)

    bookings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'view_bookings.html',
        bookings=bookings
    )
if __name__ == "__main__":
    app.run(debug=True)