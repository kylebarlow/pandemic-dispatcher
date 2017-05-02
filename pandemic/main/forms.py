from flask_wtf import FlaskForm

from wtforms import (widgets, IntegerField, BooleanField, SelectField, RadioField,
                     SelectMultipleField, SubmitField, HiddenField, ValidationError)
from wtforms.validators import InputRequired, NumberRange

from .. import constants as c
from ..models import City, Game


def select_month(field, **kwargs):
    kwargs.setdefault('type', 'radio')
    field_id = kwargs.pop('id', field.id)
    html = [u'<div %s>' % widgets.html_params(id=field_id, class_='btn-group col-sm-12', data_toggle='buttons')]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id, autocomplete='off')
        if checked:
            options['checked'] = 'checked'
        html.append(u'<div class="btn month col-sm-3"><input %s /> ' % widgets.html_params(**options))
        html.append(u'<label for="%s">%s</label></div>' % (field_id, label))
    html.append(u'</div>')
    return u''.join(html)


def select_cities(field, **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = [u'<div %s>' % widgets.html_params(id=field_id, class_='btn-group col-sm-12', data_toggle='buttons')]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id, autocomplete='off')
        if checked:
            options['checked'] = 'checked'
        html.append((u'<div class="btn city-{} col-sm-3"><input {} /> '
                     u'<label for="{}">{}</label></div>')
                    .format(c.CITIES[value], widgets.html_params(**options), field_id, label))
    html.append(u'</div>')
    return u''.join(html)


def authorize_vaccine(field, **kwargs):
    glyphs = [u'glyphicon-alert', u'glyphicon-globe', u'glyphicon-home', u'glyphicon-star']

    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = [u'<div %s>' % widgets.html_params(id=field_id, class_='btn-group col-sm-12', data_toggle='buttons')]
    for i,(value, label, checked) in enumerate(field.iter_choices()):
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id, autocomplete='off')
        if checked:
            options['checked'] = 'checked'
        html.append((u'<div class="btn player-{} col-sm-2"><input {} /> <label for="{}">'
                     u'<span class="glyphicon {}" aria-hidden="true"></span> {}</label></div>')
                    .format(i, widgets.html_params(**options), field_id, glyphs[i], label))
    html.append(u'</div>')
    return u''.join(html)


class BeginForm(FlaskForm):
    month = SelectField(u'Current Month', choices=zip(c.MONTHS, c.MONTHS), validators=[InputRequired()],
                       widget=select_month)
    funding_rate = IntegerField(u'Funding Rate', default=0, validators=[InputRequired(), NumberRange(0, 8)],
                                description=u'How many R01s we have')
    extra_cards = IntegerField(u'Bonus Cards', default=0, validators=[NumberRange(0, 8)],
                               description=u'Number of other cards (e.g. experimental vaccines) in the deck')
    cities = SelectMultipleField(u'Infected Cities', widget=select_cities,
                              description=u'The cities infected during game setup')
    cards = SelectMultipleField(u'Starting Player Cards', widget=select_cities,
                             description=u'COdA-403a city cards in starting hands (if any)')
    submit = SubmitField(u'Submit')

    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        self.cities.choices = [(city, city) for city in c.CITIES]
        self.cards.choices = [(city, city) for city in c.CITIES if c.CITIES[city] == c.CODA_COLOR]

    def validate_cities(self, field):
        if len(field.data) != c.INFECTION_SETUP:
            field.data = []
            raise ValidationError("You didn't infect the right number of cities")

    def validate_cards(self, field):
        if len(field.data) > (c.PLAYERS * c.DRAW):
            field.data = []
            raise ValidationError("You drew too many player cards")


class DrawForm(FlaskForm):
    epidemic = SelectField(u'Epidemic')
    vaccine = SelectMultipleField(u'Experimental Vaccine', widget=authorize_vaccine,
                                  choices=[('Yes', 'Yes')] * c.PLAYERS)
    cards = SelectMultipleField(u'Player Cards', widget=select_cities)
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        game_cities = City.query.filter_by(game_id=game_id)
        max_stack = max(city.stack for city in game_cities)

        epidemic_cities = [(city.name, city.name) for city in game_cities.filter_by(stack=max_stack)]
        self.epidemic.choices = [(u'', u'')] + epidemic_cities

        cards = [(city.name, city.name) for city in
                 game_cities.filter_by(color=c.CODA_COLOR).filter_by(player_card=False)]
        self.cards.choices = sorted(cards)

    def validate_cards(self, field):
        if len(field.data) + bool(self.epidemic.data) > c.DRAW:
            field.data = []
            raise ValidationError("You drew too many cards")

    def validate_epidemic(self, field):
        if field.data and Game.query.filter_by(id=int(self.game.data)).first().epidemics == c.EPIDEMICS:
            raise ValidationError("There have already been {} epidemics! Sheesh".format(c.EPIDEMICS))

    def validate_vaccine(self, field):
        if 0 < len(field.data) < c.PLAYERS:
            field.data = []
            raise ValidationError("All players must authorize an experimental vaccine")


class InfectForm(FlaskForm):
    cities = SelectMultipleField(u'Infected Cities', widget=select_cities)
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, *args, **kwargs):
        super(InfectForm, self).__init__(*args, **kwargs)

        game = Game.query.filter_by(id=game_id).first()
        game_cities = City.query.filter_by(game_id=game_id)

        choices = []
        for i in range(1, 7):
            choices.extend((city.name, city.name) for city in game_cities.filter_by(stack=i))

            if len(choices) >= c.INFECTION_RATES[game.epidemics]:
                break

        self.cities.choices = choices

    def validate_cities(self, field):
        game = Game.query.filter_by(id=int(self.game.data)).first()
        if len(field.data) != c.INFECTION_RATES[game.epidemics]:
            field.data = []
            raise ValidationError("You didn't infect the right number of cities")


class EditForm(FlaskForm):
    pass
