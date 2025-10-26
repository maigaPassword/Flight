from  amadeus import amadeus 
from flask import Flask, render_template

app = Flask(__name__)

# --- Home ---
@app.route('/')
def home():
    return render_template('base.html')

# --- Search Flights ---
@app.route('/search')
def search():
    return render_template('search.html')

# --- About Page ---
@app.route('/about')
def about():
    return render_template('about.html')

# --- Contact Page ---
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)