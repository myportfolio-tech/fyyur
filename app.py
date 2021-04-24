#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from extensions import db
from models import Venue, Artist, Show
from sqlalchemy.orm import load_only

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)


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

  venue_data =[]
  
  # Select Distinct city, state where venues exist
  locations = Venue.query.distinct(Venue.city, Venue.state).options(load_only('city', 'state')).all()

  # Create Data Object organized per city
  for city in locations:
    venues = Venue.query.filter(Venue.city == city.city, Venue.state == city.state).options(load_only('id', 'name')).all()

    venue_list = []
    for venue in venues:
        venue_entry = { "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Show.query.filter(Show.venue_id == venue.id).all())}
        venue_list.append(venue_entry)

    newVenue = {"city": city.city,
    "state": city.state,
    "venues": venue_list}

    venue_data.append(newVenue)

  return render_template('pages/venues.html', areas=venue_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  today = datetime.now()
  
  search_term = request.form.get('search_term', '')
  data =[]
  
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  
  for venue in venues:

    venue_list = {
      "id": venue.id,
      "name": venue.name,
      "upcoming_shows_number": len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > today ).all())}

    data.append(venue_list)

  response={
    "count": len(data),
    "data": data}

  return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
 
  today = datetime.now()
  
  ## Queries ##
  venue = Venue.query.get(venue_id)
  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time > today ).all()
  past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time <  today ).all()


  results = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0
    }


  shows_upcoming = []
  for show in upcoming_shows:
    artist_dict = {
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.name,
      "start_time": str(show.start_time)}

    shows_upcoming.append(artist_dict)


  shows_past = []
  for show in past_shows:
    artist_dict = {
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.name,
      "start_time": str(show.start_time)}

    shows_past.append(artist_dict)

  results['past_shows'] = shows_past
  results['upcoming_shows'] = shows_upcoming
  results['past_shows_count'] = len(shows_past)
  results['upcoming_shows_count'] = len(shows_upcoming)

  return render_template('pages/show_venue.html', venue=results)   
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate():
    venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, image_link=form.image_link.data, genres=form.genres.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data)
    try:
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('Venue ' + request.form['name'] + ' did not work!')
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    flash(f'Unable to delete Venue: {venue.name}')
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = Artist.query.order_by('name').all()
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  today = datetime.now()
  
  search_term = request.form.get('search_term', '')
  data =[]
  
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  
  for artist in artists:

    artist_list = {
      "id": artist.id,
      "name": artist.name,
      "upcoming_shows_number": len(Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > today ).all())}

    data.append(artist_list)

  response={
    "count": len(data),
    "data": data}

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  today = datetime.now()
  
  ## Queries ##
  artist = Artist.query.get(artist_id)
  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time > today ).all()
  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time <  today ).all()


  results = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": [],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0
    }


  shows_upcoming = []
  for show in upcoming_shows:
    artist_dict = {
      "venue_id": show.artist.id,
      "venue_name": show.artist.name,
      "artist_image_link": show.artist.name,
      "start_time": str(show.start_time)}

    shows_upcoming.append(artist_dict)


  shows_past = []
  for show in past_shows:
    artist_dict = {
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.name,
      "start_time": str(show.start_time)}

    shows_past.append(artist_dict)

  results['past_shows'] = shows_past
  results['upcoming_shows'] = shows_upcoming
  results['past_shows_count'] = len(shows_past)
  results['upcoming_shows_count'] = len(shows_upcoming)

  return render_template('pages/show_venue.html', venue=results)  


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  form = ArtistForm(request.form, meta={'csrf': False})
  
  if form.validate():

    artist = Artist.query.get(artist_id)

    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.genres = form.genres.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    try:
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated')
    except:
      db.session.rollback()
      flash('Artist ' + request.form['name'] + ' failed to update!')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))


  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate():

    venue = Venue.query.get(venue_id)

    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.genres = form.genres.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    try:
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated')
    except:
      db.session.rollback()
      flash('Venue ' + request.form['name'] + ' failed to update!')
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
 
  form = ArtistForm(request.form, meta={'csrf': False})

  if form.validate():
    artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, image_link=form.image_link.data, genres=form.genres.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, seeking_venue=form.seeking_venue.data,   seeking_description=form.seeking_description.data)
    try:
      db.session.add(artist)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      flash('Venue ' + request.form['name'] + ' did not work!')
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = []
  today = datetime.now()
  shows = db.session.query(Show).join(Venue).join(Artist).filter(Show.start_time > today ).all()

  for show in shows:
    show_data = {"venue_id": show.venue.id,
    "venue_name": show.venue.name,
    "artist_id": show.artist.id,
    "artist_name": show.artist.name,
    "artist_image_link":show.artist.image_link,
    "start_time": str(show.start_time)}

    data.append(show_data)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  
  form = ShowForm(request.form, meta={'csrf': False})

  if form.validate():
    show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
    try:
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    except Exception as e:
      db.session.rollback()
      flash('Show did not work!')
      flash(e)
    finally:
      db.session.close()

  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

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
