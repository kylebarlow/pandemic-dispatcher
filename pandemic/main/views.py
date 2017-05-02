import os
import cStringIO

from collections import defaultdict

from flask import g, session, render_template, redirect, url_for, flash

from . import main
from .. import db
from .. import constants as c
from ..models import City, Game

from .forms import BeginForm, DrawForm, InfectForm


# @main.before_app_request
# def before_request():
#     print Game.query.filter_by(id=int(session['game_id'])).first()
#     print
#     print u'\n'.join(unicode(city) for city in City.query.all())


def get_game_state(game):
    def to_percent(v):
        if v > 0:
            return u'{:.1f}%'.format(v * 100.0)
        else:
            return u'-'

    infection_rate = c.INFECTION_RATES[game.epidemics]

    game_cities = City.query.filter_by(game_id=game.id).all()

    stack_d = dict()

    for i in range(7):
        stack_d[i] = [city for city in game_cities if city.stack == i]

    discard = {city.name for city in stack_d[0]}

    city_probs = defaultdict(float)

    for i in range(1,7):
        n = float(len(stack_d[i]))
        for city in stack_d[i]:
            city_probs[city.name] = min(1.0, infection_rate / n)

        infection_rate -= n
        if infection_rate <= 0:
            break

    max_i = max(i for i in stack_d if stack_d[i])
    epi_probs = defaultdict(float, {city.name: 1.0 / len(stack_d[max_i]) for city in stack_d[max_i]})

    city_data = [{'name': city.name, 'color': city.color, 'discard': (city.name in discard), 'stack': city.stack,
                  'inf_risk': to_percent(city_probs[city.name]), 'epi_risk': to_percent(epi_probs[city.name])}
                 for city in game_cities]


    return {'deck_size': game.deck_size, 'epidemics': game.epidemics, 'city_data': city_data}


@main.route('/', methods=('GET', 'POST'))
def begin():
    form = BeginForm()

    if form.validate_on_submit():
        deck_size = (len(c.CITIES) + c.EPIDEMICS
                     + form.funding_rate.data + form.extra_cards.data
                     - (c.PLAYERS * c.DRAW))

        game = Game(month=form.month.data,
                    funding_rate=form.funding_rate.data,
                    deck_size=deck_size,
                    epidemics=0)

        starting_cities = set(form.cities.data)
        starting_cards = set(form.cards.data)

        db.session.add(game)
        db.session.commit()

        db.session.add_all([
            City(name=city_name, color=city_color,
                 stack=(city_name not in starting_cities),
                 player_card=(city_name in starting_cards),
                 game_id=game.id)
            for city_name,city_color in c.CITIES.items()])

        db.session.commit()

        session['game_id'] = game.id

        return redirect(url_for('main.draw'))

    return render_template("begin.html", form=form)


@main.route('/draw', methods=('GET', 'POST'))
@main.route('/draw/<int:game_id>', methods=('GET', 'POST'))
def draw(game_id=None):
    if not (game_id or session.get('game_id', None)):
        flash('No game in progress', 'error')
        return redirect(url_for('main.begin'))
    elif game_id:
        session['game_id'] = game_id

    game_id = int(session['game_id'])
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash('No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('main.begin'))

    form = DrawForm(game_id)
    form.game.data = session['game_id']

    if form.validate_on_submit():
        game_cities = City.query.filter_by(game_id=game_id)

        if form.epidemic.data and form.epidemic.data != u'Vaccine!':
            game_cities.filter_by(name=form.epidemic.data).first().stack = 0
            game_cities.update({City.stack: City.stack + 1})
            game.epidemics += 1

        if form.cards.data:
            game_cities.filter(City.name.in_(form.cards.data)).update({'player_card': True}, synchronize_session=False)

        game.deck_size -= 2

        db.session.commit()

        return redirect(url_for('main.infect'))

    game_state = get_game_state(game)

    return render_template("draw.html", game_state=game_state, form=form)


@main.route('/infect/', methods=('GET', 'POST'))
@main.route('/infect/<int:game_id>', methods=('GET', 'POST'))
def infect(game_id=None):
    if not (game_id or session.get('game_id', None)):
        flash('No game in progress', 'error')
        return redirect(url_for('main.begin'))
    elif game_id:
        session['game_id'] = game_id

    game_id = int(session['game_id'])
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash('No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('main.begin'))

    form = InfectForm(game_id)
    form.game.data = session['game_id']

    if form.validate_on_submit():
        game_cities = City.query.filter_by(game_id=game_id)
        game_cities.filter(City.name.in_(form.cities.data)).update({'stack': 0}, synchronize_session=False)

        db.session.commit()

        return redirect(url_for('main.draw'))

    game_state = get_game_state(game)

    return render_template("infect.html", game_state=game_state, form=form)


@main.route('/edit', methods=('GET', 'POST'))
@main.route('/edit/<int:game_id>', methods=('GET', 'POST'))
def edit_game(game_id=None):
    if not (game_id or session.get('game_id', None)):
        flash('No game in progress', 'error')
        return redirect(url_for('main.begin'))
    elif game_id:
        session['game_id'] = game_id

    game_id = int(session['game_id'])
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash('No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('main.begin'))

    form = EditForm(game_id)
    form.game.data = session['game_id']

    if form.validate_on_submit():
        game_cities = City.query.filter_by(game_id=game_id)
        game_cities.filter(City.name.in_(form.cities.data)).update({'stack': 0}, synchronize_session=False)

        db.session.commit()

        return redirect(url_for('main.draw'))

    game_state = get_game_state(game)

    return render_template("infect.html", game_state=game_state, form=form)



@main.route('/history')
def history():
    games = Game.query.all()
    return render_template("history.html", games=games)
