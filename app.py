from  amadeus import amadeus 

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