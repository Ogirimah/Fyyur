#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
import dateutil.parser
import babel
from flask import (Flask,
                  render_template,
                  request,
                  Response,
                  flash,
                  redirect,
                  url_for)
                  
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
import collections

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

collections.Callable = collections.abc.Callable

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref='venues', lazy=True)
    upcoming_shows_count = db.Column(db.Integer, default=0)
    past_shows_count = db.Column(db.Integer, default=0)

    def __repr__(self):
       return f'Venue ID: {self.id}, Venue name: {self.name}, City: {self.city}, State: {self.state}'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    shows = db.relationship('Show', backref='artists', lazy=True)
    upcoming_shows_count = db.Column(db.Integer, default=0)
    past_shows_count = db.Column(db.Integer, default=0)

    def __repr__(self):
       return f'Artist ID: {self.id}, Artist name: {self.name}, City: {self.city}, State: {self.state}'


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)

    def __repr__(self):
       return f'Show ID: {self.id}, Start Time: {self.start_time}, Venue-ID: {self.venue_id}, Artist-ID: {self.artist_id}'

# db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Filter venues by city and state and append them to a list
  data = []
  venue_areas = db.session.query(Venue.state, Venue.city).group_by(Venue.state, Venue.city).all()
  for area in venue_areas:
    result = {
      'city': area.city,
      'state': area.state,
      # 'venues': []
    }

    venues_result = Venue.query.filter_by(city=area.city, state=area.state).all()
    for venue in venues_result:
      venues = []
      venues.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': venue.upcoming_shows_count
      })
      result['venues'] = venues
      data.append(result)
  print (f'{data}')

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_word = request.form['search_term']
  result = Venue.query.filter(Venue.name.ilike(f'%{search_word}%')).all()
  response = {
    'count': len(result),
    'data': []
  }
  for details in result:
    response['data'].append({
      'id': details.id,
      'name': details.name,
      'num_upcoming_shows': details.upcoming_shows_count
    })

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  data = Venue.query.get(venue_id)

  setattr(data, "genres", data.genres.split(","))

  # Past shows
  past_shows = list(filter(lambda show: show.start_time < datetime.now(), data.shows))
  temp_shows = []
  for show in past_shows:
      output = {}
      output["venue_name"] = show.venues.name
      output["venue_id"] = show.venues.id
      output["artist_image_link"] = show.artists.image_link
      output["start_time"] = show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
      temp_shows.append(output)

  setattr(data, "past_shows", temp_shows)
  setattr(data,"past_shows_count", len(past_shows))

  # Future shows
  upcoming_shows = list(filter(lambda show: show.start_time > datetime.now(), data.shows))
  temp_shows = []
  for show in upcoming_shows:
      output = {}
      output["venue_name"] = show.venues.name
      output["venue_id"] = show.venues.id
      output["artist_image_link"] = show.artists.image_link
      output["start_time"] = str(show.start_time)
      temp_shows.append(output)

  setattr(data, "upcoming_shows", temp_shows)    
  setattr(data,"upcoming_shows_count", len(upcoming_shows))

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  new_venue = Venue()
  if form.validate():
      # TODO: insert form data as a new Venue record in the db, instead
      # TODO: modify data to be the data object returned from db insertion
      new_venue.name = request.form['name']
      new_venue.city = request.form['city']
      new_venue.state = request.form['state']
      new_venue.address = request.form['address']
      new_venue.phone = request.form['phone']
      new_venue.facebook_link = request.form['facebook_link']
      new_venue.genres = request.form['genres']
      new_venue.website = request.form['website_link']
      new_venue.image_link = request.form['image_link']
      try:
        db.session.add(new_venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
      except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occured. Venue' + request.form["name"] + 'could not be listed')
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      finally:
        db.session.close()
  else:
    print("\n\n", form.errors)
    print(f'Error with venue {new_venue.name}')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash("Error! Venue not deleted")
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_word = request.form['search_term']
  querry = Artist.query.filter(Artist.name.ilike(f'%{search_word}%')).all()

  response={
    "count": len(querry),
    "data": []
  }
  for artist in querry:
    response['data'].append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': artist.upcoming_shows_count
    })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = {}
  data = Artist.query.get(artist_id)

  genres = data.genres.split(',')

  # Past shows using DateTime.now as reference
  past_shows_list = list(filter(lambda show: show.start_time < datetime.now(), data.shows))
  past_shows = []
  for show in past_shows_list:
      output = {}
      output["artist_name"] = show.artists.name
      output["artist_id"] = show.artists.id
      output["artist_image_link"] = show.artists.image_link
      output["start_time"] = str(show.start_time)
      past_shows.append(output)

  # Future shows using DateTime.now as reference
  upcoming_shows_list = list(filter(lambda show: show.start_time > datetime.now(), data.shows))
  upcoming_shows = []
  for show in upcoming_shows_list:
      output = {}
      output["artist_name"] = show.artists.name
      output["artist_id"] = show.artists.id
      output["artist_image_link"] = show.artists.image_link
      output["start_time"] = str(show.start_time)
      upcoming_shows.append(output)

  artist = {
    'id': data.id,
    'name': data.name,
    'city': data.city,
    'state': data.state,
    'phone': data.phone,
    'website': data.website,
    'facebook_link': data.facebook_link,
    'past_shows': past_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows': upcoming_shows,
    'upcoming_shows_count': len(upcoming_shows),
    'genres': genres
  }
  
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  # For Artists with >1 genres
  form.genres.data = artist.genres.split(",")
 
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.facebook_link = request.form['facebook_link']
  artist.genres = request.form['genres']
  artist.image_link = request.form['image_link']
  artist.website = request.form['website_link']
  try:
    db.session.commit()
    flash(f"Artist {request.form['name']} is updated successfully".format(artist.name))
  except:
    db.session.rollback()
    flash(f"Artist {request.form['name']} isn't updated successfully".format(artist.name))
  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.genres.data = venue.genres.split(",")
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.facebook_link = request.form['facebook_link']
  venue.genres = request.form['genres']
  venue.image_link = request.form['image_link']
  venue.website = request.form['website_link']
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  new_artist = Artist()
  new_artist.name = request.form['name']
  new_artist.city = request.form['city']
  new_artist.state = request.form['state']
  new_artist.genres = request.form['genres']
  new_artist.phone = request.form['phone']
  new_artist.facebook_link = request.form['facebook_link']
  new_artist.image_link = request.form['image_link']
  try:
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
 
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  show_list = Show.query.all()
  data = []
  result = {}
  for show in show_list:
    result['venue_id'] = show.venue_id
    result['venue_name'] = show.venues.name
    result['artist_id'] = show.artist_id
    result['artist_name'] = show.artists.name
    result['artist_image_link'] = show.artists.image_link
    result['start_time'] = str(show.start_time)

  data.append(result)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  
  form = ShowForm(request.form)
  if form.validate:
    new_show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )
    try:
      db.session.add(new_show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('Error occured, show could not be listed')
    finally:
      db.session.close()
  else:
    print('Form Error')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
