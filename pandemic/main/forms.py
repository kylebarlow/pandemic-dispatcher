from flask_wtf import FlaskForm

from wtforms import (widgets, IntegerField, BooleanField, SelectField, RadioField,
                     SelectMultipleField, SubmitField, HiddenField, ValidationError)
from wtforms.validators import InputRequired, NumberRange

from .. import constants as c
from ..models import Game, City, Turn


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
                       widget=select_month, description=u'The month for this game')
    funding_rate = IntegerField(u'Funding Rate', default=0, validators=[InputRequired(), NumberRange(0, 10)],
                                description=u'How many R01s we have')
    extra_cards = IntegerField(u'Bonus Cards', default=0, validators=[InputRequired(), NumberRange(0)],
                               description=u'Number of other cards (e.g. experimental vaccines) in the deck')
    submit = SubmitField(u'Submit')


class DrawForm(FlaskForm):
    epidemic = SelectField(u'Epidemic', description=u'The city affected by the epidemic')
    vaccine = SelectMultipleField(u'Experimental Vaccine', widget=authorize_vaccine,
                                  choices=[(u'Yes', u'Yes')] * c.PLAYERS,
                                  description=u'Authorization required for experimental vaccine')
    cards = SelectMultipleField(u'Player Cards', widget=select_cities,
                                description=u'COdA-403b cards drawn')
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, game_state, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        self.game.data = game_id

        self.turn_num = game_state['turn_num']
        if self.turn_num == -1:
            self.cards.description = u'COdA-403b cards in initial hands'

        if game_state['epidemics'] == c.EPIDEMICS or self.turn_num == -1:
            del self.epidemic
            del self.vaccine
        else:
            max_stack = max(city['stack'] for city in game_state['city_data'])
            epidemic_cities = [(city['name'], city['name']) for city in game_state['city_data']
                               if city['stack'] == max_stack]
            self.epidemic.choices = [(u'', u'')] + epidemic_cities

        cards = [(city['name'], city['name']) for city in game_state['city_data']
                 if city['color'] == c.CODA_COLOR and not city['drawn']]
        self.cards.choices = cards

    def validate_cards(self, field):
        if (self.turn_num == -1 and len(field.data) > (c.DRAW * c.PLAYERS)
            or (self.turn_num > -1 and len(field.data) + bool(self.epidemic.data) > c.DRAW)):
            field.data = []
            raise ValidationError(u"You drew too many cards")

    def validate_vaccine(self, field):
        if 0 < len(field.data) < c.PLAYERS:
            field.data = []
            raise ValidationError(u"All players must authorize an experimental vaccine")


class InfectForm(FlaskForm):
    cities = SelectMultipleField(u'Infected Cities', widget=select_cities,
                                 description=u'Cities infected this turn')
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, game_state, *args, **kwargs):
        super(InfectForm, self).__init__(*args, **kwargs)

        self.game.data = game_id

        if game_state['turn_num'] == -1:
            self.epidemics = -1
            self.cities.description = u'Cities infected during setup'
        else:
            self.epidemics = game_state['epidemics']

        choices = []
        for i in range(1, 7):
            choices.extend((city['name'], city['name']) for city in game_state['city_data']
                           if city['stack'] == i)

            if len(choices) >= c.INFECTION_RATES[self.epidemics]:
                break

        self.cities.choices = choices

    def validate_cities(self, field):
        if len(field.data) != c.INFECTION_RATES[self.epidemics]:
            field.data = []
            raise ValidationError(u"You didn't infect the right number of cities")


class ReplayForm(FlaskForm):
    authorize = SelectMultipleField(u'Redo Turn?', widget=authorize_vaccine,
                                    choices=[(u'Yes', u'Yes')] * c.PLAYERS,
                                    description=u'Authorization required to replay this turn')
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, *args, **kwargs):
        super(ReplayForm, self).__init__(*args, **kwargs)
        self.game.data = game_id

    def validate_authorize(self, field):
        if 0 < len(field.data) < c.PLAYERS:
            field.data = []
            raise ValidationError(u"All players must authorize this decision")

