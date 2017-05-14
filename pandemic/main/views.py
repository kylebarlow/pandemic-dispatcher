import os
import cStringIO

from collections import defaultdict, Counter

from flask import g, session, render_template, redirect, url_for, flash

from . import main
from .. import db
from .. import constants as c
from ..models import Game, City, Turn, PlayerSession, Character

from .forms import BeginForm, DrawForm, InfectForm, ReplayForm


@main.app_template_filter('to_percent')
def to_percent(v):
    return u'{:.1f}%'.format(v * 100.0) if v > 0 else u'-'


@main.app_template_filter('danger_level')
def to_percent(v):
    if v > 0.66:
        return u'bg-danger'
    elif v > 0.33:
        return u'bg-warning'
    else:
        return u''


def get_game_state(game, draw_phase=True):
    turns = (Turn.query.filter_by(game_id=game.id)
             .filter(Turn.turn_num <= game.turn_num)
             .order_by(Turn.turn_num).all())

    # deck size after dealing the initial hands
    post_setup_deck_size = (len(c.CITIES) + c.EPIDEMICS
                            + game.funding_rate + game.extra_cards
                            - c.NUM_PLAYERS * c.INITIAL_HAND_SIZE[c.NUM_PLAYERS])
    # number of post-setup cards drawn so far
    if game.turn_num == -1:
        ps_cards_drawn = 0
    else:
        ps_cards_drawn = (len(turns) - 1 - draw_phase) * c.DRAW
    # how many cards are left
    deck_size = post_setup_deck_size - ps_cards_drawn

    stack = {city_name:1 for city_name in c.CITIES}

    drawn_cards = set() # only for COdA cards
    epidemics = 0
    vaccines = 0
    for turn in turns:
        drawn_cards.update(city.name for city in turn.draws)

        if turn.epidemic:
            epidemics += 1
            stack[turn.epidemic[0].name] = 0
            stack = {city_name:(stack[city_name] + 1) for city_name in stack}
            if len(turn.epidemic) == 2:
                epidemics += 1
                stack[turn.epidemic[1].name] = 0
                stack = {city_name: (stack[city_name] + 1) for city_name in stack}

        if turn.x_vaccine:
            vaccines += 1

        for city in sorted(turn.infections, key=lambda city: stack[city.name]):
            assert stack[city.name] == 1 # if a city is infected too early
            stack[city.name] = 0

            if not any(stack[city_name] == 1 for city_name in stack):
                stack = {city_name:(s - (s > 0)) for city_name,s in stack.items()}

    epi_cards_seen = epidemics + vaccines

    epidemic_stacks = Counter((i % c.EPIDEMICS) for i in range(post_setup_deck_size))
    epidemic_blocks = list(epidemic_stacks.elements())

    i_block = epidemic_blocks[ps_cards_drawn]
    j_block = epidemic_blocks[ps_cards_drawn + 1]

    for i in epidemic_blocks[:ps_cards_drawn]:
        epidemic_stacks[i] -= 1

    if game.turn_num > -1:
        if i_block < epi_cards_seen:
            if j_block < epi_cards_seen:
                # this epidemic has already been drawn
                epidemic_risk = 0.0
            else:
                # the second card could be one
                epidemic_risk = 1.0 / epidemic_stacks[j_block]
        elif i_block == j_block:
            # both are same block, and it hasn't been drawn yet
            epidemic_risk = 2.0 / epidemic_stacks[i_block]
        else:
            # first card is definitely an epidemic, second one might be!
            assert epidemic_stacks[i_block] == 1
            epidemic_risk = 1.0 + 1.0 / epidemic_stacks[j_block]
    else:
        epidemic_risk = 0.0

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
            'turns': turns, 'deck_size': deck_size, 'epi_risk': epidemic_risk,
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

        for player_data in form.players.data:
            player_char = Character.query.filter_by(name=player_data['character']).one()
            player = PlayerSession(player_name=player_data['player_name'],
                                   turn_num=int(player_data['turn_num']),
                                   color_index=int(player_data['color_index']),
                                   game_id=game.id, char_id=player_char.id)
            db.session.add(player)

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

    game_id = session['game_id']
    game = Game.query.filter_by(id=game_id).one_or_none()
    if game is None:
        flash(u'No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('.begin'))

    turn = Turn.query.filter_by(game_id=game.id, turn_num=game.turn_num).one_or_none()
    if turn is None:
        turn = Turn(game_id=game.id, turn_num=game.turn_num, x_vaccine=False)
        db.session.add(turn)
    else:
        turn.infections = [] # this could break the game state otherwise
        turn.draws = []

    db.session.commit()

    game_state = get_game_state(game)

    form = DrawForm(game_state, game.characters)

    if form.validate_on_submit():
        if game.turn_num > -1:
            turn.x_vaccine = len(form.vaccine.data) == c.NUM_PLAYERS
            if form.epidemic.data:
                turn.epidemic = [City.query.filter_by(name=form.epidemic.data).first()]
                if 'second_epidemic' in form and form.second_epidemic.data:
                    turn.epidemic.append(City.query.filter_by(name=form.second_epidemic.data).first())

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

    game_id = session['game_id']
    game = Game.query.filter_by(id=game_id).first()
    if game is None:
        flash(u'No game with that ID', 'error')
        session['game_id'] = None
        return redirect(url_for('.begin'))

    this_turn = Turn.query.filter_by(game_id=game.id, turn_num=game.turn_num).one_or_none()
    if this_turn is None:
        flash(u'Not on the infection step right now', 'error')
        return redirect(url_for('.draw'))

    game_state = get_game_state(game, False)

    form = InfectForm(game_state)

    if form.validate_on_submit():
        if form.game.data != game_id:
            flash(u'Game ID did not match session', 'error')
            return redirect(url_for('.begin'))

        if form.cities.data:
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

    form = ReplayForm(game_id, game.characters)

    if form.validate_on_submit():
        if len(form.authorize.data) == c.NUM_PLAYERS:
            session['game_id'] = game_id
            game.turn_num = turn_num
            db.session.commit()

            return redirect(url_for('.draw'))
        else:
            flash(u'A replay was not authorized')
            return redirect(url_for('.game_history', game_id=form.game.data))

    return render_template("replay.html", form=form)
