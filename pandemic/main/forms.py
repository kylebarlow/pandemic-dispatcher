from collections import OrderedDict

from flask_wtf import FlaskForm

from wtforms import (Form, Field, StringField, IntegerField, BooleanField, SelectField, RadioField,
                     FieldList, FormField, SelectMultipleField, SubmitField, HiddenField, ValidationError)
from wtforms.validators import InputRequired, NumberRange, AnyOf

from .. import constants as c
from ..models import Game, City, Turn

import widgets as wdg


def order_fields(fields, order):
    return OrderedDict((k,fields[k]) for k in order)


class PlayerField(Form):
    player_name = StringField(u'Name', validators=[InputRequired()])
    turn_num = HiddenField(u'num', validators=[InputRequired()])
    character = HiddenField(u'char', validators=[InputRequired(), AnyOf(c.CHARACTERS)])
    color_index = HiddenField(u'oolor', validators=[InputRequired()])


class BeginForm(FlaskForm):
    month = SelectField(u'Current Month', choices=zip(c.MONTHS, c.MONTHS), validators=[InputRequired()],
                        widget=wdg.select_month, description=u'The month for this game')
    players = FieldList(FormField(PlayerField, widget=wdg.player_widget, label=u'Player name'), label=u'',
                        widget=wdg.PlayerListWidget(), min_entries=c.NUM_PLAYERS, max_entries=c.NUM_PLAYERS)
    funding_rate = IntegerField(u'Funding Rate', default=0, validators=[InputRequired(), NumberRange(0, 10)],
                                description=u'How many R01s we have')
    extra_cards = IntegerField(u'Bonus Cards', default=0, validators=[InputRequired(), NumberRange(0)],
                               description=u'Number of other cards (e.g. experimental vaccines) in the deck')
    submit = SubmitField(u'Submit')

    def validate_players(self, field):
        if len(field.data) == c.NUM_PLAYERS and any(ch['character'] == u'TRAITOR' for ch in field.data):
            raise ValidationError(u"Error: The Dispatcher is dead to us now")


class DrawForm(FlaskForm):
    epidemic = SelectField(u'Epidemic', description=u'If an epidemic was drawn, select the city affected')
    second_epidemic = SelectField(u'Epidemic', description=u'If a second epidemic was drawn')
    vaccine = SelectMultipleField(u'Experimental Vaccine', widget=wdg.authorize_vaccine,
                                  description=u'Authorization required for experimental vaccine')
    cards = SelectMultipleField(u'COdA-403b Player Cards', widget=wdg.select_cities,
                                description=u'{} city cards drawn'.format(c.CODA_COLOR.capitalize()))
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_state, characters, *args, **kwargs):
        super(DrawForm, self).__init__(*args, **kwargs)

        self.game.data = game_state['game_id']

        self.turn_num = game_state['turn_num']
        if self.turn_num == -1:
            self.cards.description = u'{} city cards in initial hands'.format(c.CODA_COLOR.capitalize())

        if game_state['epi_risk'] == 0.0 or self.turn_num == -1:
            del self.epidemic
            del self.second_epidemic
            del self.vaccine
        else:
            max_stack = max(city['stack'] for city in game_state['city_data'])
            epidemic_cities = [(u'', u'')] + [(city['name'], city['name']) for city in game_state['city_data']
                                              if city['stack'] == max_stack]
            self.epidemic.choices = epidemic_cities

            if game_state['epi_risk'] > 1.0:
                self.second_epidemic.choices = epidemic_cities
            else:
                del self.second_epidemic

            self.vaccine.choices = [(ch.character.name,(u'Yes', ch.color_index)) for ch in characters]

        cards = [(city['name'], city['name']) for city in game_state['city_data']
                 if city['color'] == c.CODA_COLOR and not city['drawn']]
        self.cards.choices = cards

    def validate_cards(self, field):
        if self.turn_num == -1 and len(field.data) > (c.DRAW * c.NUM_PLAYERS):
            field.data = []
            raise ValidationError(u"You drew too many cards")

        if self.turn_num > -1 and (len(field.data) + bool(self.epidemic and self.epidemic.data)) > c.DRAW:
            field.data = []
            raise ValidationError(u"You drew too many cards")

    def validate_vaccine(self, field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError(u"All players must authorize an experimental vaccine")

    def validate_second_epidemic(self, field):
        if field.data and not self.epidemic.data:
            raise ValidationError(u"For one epidemic, use the other selector")
        elif field.data and field.data == self.epidemic.data:
            raise ValidationError(u"The second epidemic can't be the same city")


class SetupInfectForm(FlaskForm):
    cities = SelectMultipleField(u'Infected Cities', widget=wdg.select_cities,
                                 description=u'Cities infected during setup')
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_state, *args, **kwargs):
        super(SetupInfectForm, self).__init__(*args, **kwargs)

        self.game.data = game_state['game_id']
        self.epidemics = -1
        self.cities.choices = [(city['name'], city['name']) for city in game_state['city_data']]

    def validate_cities(self, field):
        if len(field.data) != c.INFECTION_RATES[self.epidemics]:
            field.data = []
            raise ValidationError(u"You didn't infect the right number of cities")


class InfectForm(SetupInfectForm):
    skip_infection = SelectMultipleField(u'Quiet night/Sacrifice', widget=wdg.authorize_vaccine,
                                         description=u'Skip this infection step')
    resilient_population = SelectField(u'Resilient Population',
                                       description=u'If Resilient Population was played, select the city affected')

    _order = ['cities', 'skip_infection', 'resilient_population', 'submit', 'game']

    def __init__(self, game_state, characters, *args, **kwargs):
        super(InfectForm, self).__init__(game_state, *args, **kwargs)

        self.game.data = game_state['game_id']
        self.epidemics = game_state['epidemics']

        self.cities.description = u'Cities infected this turn'
        self.skip_infection.choices = [(ch.character.name,(u'Yes', ch.color_index)) for ch in characters]
        self.resilient_population.choices = [(u'', u'')]
        self.resilient_population.choices.extend((city['name'], city['name']) for city in game_state['city_data']
                                                 if city['stack'] == 0)

        choices = []
        for i in range(1, 7):
            choices.extend((city['name'], city['name']) for city in game_state['city_data']
                           if city['stack'] == i)

            if len(choices) >= c.INFECTION_RATES[self.epidemics]:
                break

        self.cities.choices = choices

        self._fields = order_fields(self._fields, self._order)

    def validate_cities(self, field):
        if len(self.skip_infection.data) == c.NUM_PLAYERS:
            if len(field.data) > 0:
                field.data = []
                self.skip_infection.data = []
                raise ValidationError(u"You shouldn't be infecting any cities")
        else:
            super(InfectForm, self).validate_cities(field)

    def validate_skip_infection(self, field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError(u"All players must authorize this decision")


class ReplayForm(FlaskForm):
    authorize = SelectMultipleField(u'Redo Turn?', widget=wdg.authorize_vaccine,
                                    description=u'Authorization required to replay this turn')
    submit = SubmitField(u'Submit')
    game = HiddenField(u'game_id', validators=[InputRequired()])

    def __init__(self, game_id, characters, *args, **kwargs):
        super(ReplayForm, self).__init__(*args, **kwargs)
        self.authorize.choices = [(ch.character.name,(u'Yes', ch.color_index)) for ch in characters]
        self.game.data = game_id

    def validate_authorize(self, field):
        if 0 < len(field.data) < c.NUM_PLAYERS:
            field.data = []
            raise ValidationError(u"All players must authorize this decision")

