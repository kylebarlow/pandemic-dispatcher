import os
import cStringIO

from collections import defaultdict

from flask import g, session, render_template, redirect, url_for, flash

from . import main
from .. import db
from .. import constants as c
from ..models import Game, City, Turn

from .forms import BeginForm, DrawForm, InfectForm, ReplayForm


@main.app_template_filter('to_percent')
def to_percent(v):
    return u'{:.1f}%'.format(v * 100.0) if v > 0 else u'-'


def get_game_state(game):
    turns = (Turn.query.filter_by(game_id=game.id)
             .filter(Turn.turn_num <= game.turn_num)
             .order_by(Turn.turn_num).all())
    stack = {city_name:1 for city_name in c.CITIES}

    drawn_cards = set()
    epidemics = 0
    for turn in turns:
        drawn_cards.update(city.name for city in turn.draws)

        if turn.epidemic:
            epidemics += 1
            stack = {city_name:(stack[city_name] + 1) for city_name in stack}

        for city in turn.infections:
            assert stack[city.name] == 1
            stack[city.name] = 0

    deck_size = (len(c.CITIES) + epidemics + game.funding_rate + game.extra_cards
                 - (len(turns) + (c.PLAYERS - 1)) * c.DRAW)


    infection_rate = c.INFECTION_RATES[epidemics]

    stack_d = dict()
    for i in range(7):
        stack_d[i] = {city_name for city_name in stack if stack[city_name] == i}

    city_probs = defaultdict(float)

    for i in range(1,7):
        n = float(len(stack_d[i]))
        for city in stack_d[i]:
            city_probs[city] = min(1.0, infection_rate / n)

        infection_rate -= n
        if infection_rate <= 0:
            break

    max_i = max(i for i in stack_d if stack_d[i])
    epi_probs = defaultdict(float, {city_name: 1.0 / len(stack_d[max_i]) for city_name in stack_d[max_i]})

    city_data = [dict(name=city_name, color=city_color,
                      discard=(city_name in stack_d[0]),
                      stack=stack[city_name],
                      inf_risk=city_probs[city_name],
                      epi_risk=epi_probs[city_name],
                      drawn=(city_name in drawn_cards))
                 for city_name,city_color in c.CITIES.items()]

    return {'game_id': game.id, 'turn_num': game.turn_num,
            'turns': turns, 'deck_size': deck_size,
            'epidemics': epidemics, 'city_data': city_data}


@main.route('/', methods=('GET', 'POST'))
def begin():
    form = BeginForm()

    if form.validate_on_submit():
        game = Game(month=form.month.data,
                    funding_rate=form.funding_rate.data,
                    extra_cards=form.extra_cards.data,
                    turn_num=-1)

        db.session.add(game)
        db.session.commit()

        session['game_id'] = game.id

        return redirect(url_for('.draw'))

    return render_template("begin.html", form=form)


@main.route('/draw', methods=('GET', 'POST'))
@main.route('/draw/<int:game_id>', methods=('GET', 'POST'))
def draw(game_id=None):
    if not (game_id or session.get('game_id', None)):
        flash(u'No game in progress', 'error')
        return redirect(url_for('main.begin'))
    elif game_id:
        session['game_id'] = game_id

    game_id = int(session['game_id'])
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash(u'No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('.begin'))

    turn = Turn.query.filter_by(game_id=game.id, turn_num=game.turn_num).one_or_none()
    if turn is not None:
        turn.infections = [] # this could break the game state otherwise
        db.session.commit()

    game_state = get_game_state(game)

    form = DrawForm(game_id, game_state)

    if form.validate_on_submit():
        if game.turn_num > -1:
            x_vaccine_used = len(form.vaccine.data) == c.PLAYERS
            epidemic_drawn = form.epidemic.data and not x_vaccine_used
        else:
            x_vaccine_used = False
            epidemic_drawn = False

        if turn is None:
            turn = Turn(game_id=game.id, turn_num=game.turn_num,
                        epidemic=epidemic_drawn, x_vaccine=x_vaccine_used)
            db.session.add(turn)
        else:
            turn.epidemic = epidemic_drawn
            turn.x_vaccine = x_vaccine_used
            turn.draws = []

        if form.cards.data:
            turn.draws = City.query.filter(City.name.in_(form.cards.data)).all()

        db.session.commit()

        return redirect(url_for('.infect'))

    return render_template("draw.html", game_state=game_state, form=form)


@main.route('/infect/', methods=('GET', 'POST'))
@main.route('/infect/<int:game_id>', methods=('GET', 'POST'))
def infect(game_id=None):
    if not (game_id or session.get('game_id', None)):
        flash(u'No game in progress', 'error')
        return redirect(url_for('.begin'))
    elif game_id:
        session['game_id'] = game_id

    game_id = int(session['game_id'])
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash(u'No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('.begin'))

    game_state = get_game_state(game)

    form = InfectForm(game_id, game_state)

    if form.validate_on_submit():
        this_turn = Turn.query.filter_by(game_id=game.id, turn_num=game.turn_num).one_or_none()
        if this_turn is None:
            flash(u'Not on the infection step right now', 'error')
            return redirect(url_for('.draw'))

        this_turn.infections = City.query.filter(City.name.in_(form.cities.data)).all()

        game.turn_num += 1

        db.session.commit()

        return redirect(url_for('.draw'))

    return render_template("infect.html", game_state=game_state, form=form)


@main.route('/history')
def history():
    games = Game.query.all()
    return render_template("summaries.html", games=games)


@main.route('/history/<int:game_id>')
def game_history(game_id):
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash(u'No game with that ID', 'error')
        return redirect(url_for('.history'))

    return render_template("game_history.html", game=game)


@main.route('/replay/<int:game_id>/<turn_num>', methods=('GET', 'POST'))
def replay(game_id, turn_num):
    turn_num = int(turn_num)
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash(u'No game with that ID', 'error')
        return redirect(url_for('.begin'))

    form = ReplayForm(game_id)

    if form.validate_on_submit():
        if len(form.authorize.data) == c.PLAYERS:
            session['game_id'] = game_id
            game.turn_num = turn_num
            db.session.commit()

            return redirect(url_for('.draw'))
        else:
            flash(u'A replay was not authorized')
            return redirect(url_for('.game_history', game_id=form.game.data))

    return render_template("replay.html", form=form)
