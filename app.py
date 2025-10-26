from  amadeus import amadeus 
from flask import Flask, render_template
import os

# Create Flask app
app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('base.html')

if __name__ == '__main__':
    # Run the app in debug mode for easy testing
    app.run(debug=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/results')
def results():
    # Later this will pass real flight data from Amadeus
    # Example: return render_template('results.html', flights=flights)
    return render_template('results.html')