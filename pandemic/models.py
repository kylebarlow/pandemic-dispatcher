from . import db


class PlayerSession(db.Model):
    __tablename__ = 'sessions'
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key=True)
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id'), primary_key=True)

    player_name = db.Column(db.String(16), nullable=False) # name of the person playing this character this game
    turn_num = db.Column(db.Integer, nullable=False) # when they go in the turn order
    color_index = db.Column(db.Integer, nullable=False) # index into the four gamepiece colors

    game = db.relationship('Game', backref='characters', lazy=True)
    character = db.relationship('Character', backref='games', lazy=True)

    def __repr__(self):
        return u'<Game {} - {} - {}'.format(self.game_id, self.player_name, self.character.name)


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(16), nullable=False) # month of the game
    funding_rate = db.Column(db.Integer, nullable=False) # funding rate
    extra_cards = db.Column(db.Integer, nullable=False) # bonus cards
    turn_num = db.Column(db.Integer, nullable=False) # the current turn
    turns = db.relationship('Turn', backref='game', lazy='subquery')

    def __repr__(self):
        return u'<Game {}, Month {}, Turn {}, FR {}>'.format(
                self.id, self.month, self.turn_num, self.funding_rate)


class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False) # character name/role
    first_name = db.Column(db.String(32), nullable=False) # first name
    middle_name = db.Column(db.String(32), nullable=False) # middle name/initial
    icon = db.Column(db.String(32), nullable=False) # glyphicon used for buttons

    def __repr__(self):
        return u'{} {} {}'.format(self.first_name, self.middle_name, self.name)


# tables for many-to-many relationships
infections = db.Table('infections',
    db.Column('city_id', db.Integer, db.ForeignKey('cities.id'), primary_key=True),
    db.Column('turn_id', db.Integer, db.ForeignKey('turns.id'), primary_key=True)
)

draws = db.Table('draws',
    db.Column('city_id', db.Integer, db.ForeignKey('cities.id'), primary_key=True),
    db.Column('turn_id', db.Integer, db.ForeignKey('turns.id'), primary_key=True)
)


class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False) # city name
    color = db.Column(db.String(32), nullable=False) # (original) color of the city

    # turns when this city was infected
    infections = db.relationship('Turn', secondary=infections, lazy=True, backref='infections')
    # turns when this city was drawn as a player card
    draws = db.relationship('Turn', secondary=draws, lazy=True, backref='draws')

    def __repr__(self):
        return self.name


class Turn(db.Model):
    __tablename__ = 'turns'
    id = db.Column(db.Integer, primary_key=True)
    turn_num = db.Column(db.Integer)  # which turn this is
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    epidemic = db.Column(db.Boolean, nullable=False) # was an epidemic drawn?
    x_vaccine = db.Column(db.Boolean, nullable=False) # was an experimental vaccine used?

    def __repr__(self):
        return u'<Turn {}: {} infected, {} drawn>'.format(self.turn_num,
            ', '.join(city.name for city in self.infections) if self.infections else 'No cities',
            ', '.join(city.name for city in self.draws) if self.draws else 'No COdA cities')
