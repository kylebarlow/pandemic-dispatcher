from . import db


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(16), nullable=False) # month of the game
    funding_rate = db.Column(db.Integer, nullable=False) # funding rate
    extra_cards = db.Column(db.Integer, nullable=False) # bonus cards
    turn_num = db.Column(db.Integer, nullable=False) # the current turn
    turns = db.relationship('Turn', backref='game', lazy='subquery')
    # TODO: store player information (turn order, character, color)

    def __repr__(self):
        return u'<Game {}, Month {}, FR {}, Deck {}, Epidemics {}>'.format(self.id, self.month, self.funding_rate,
                                                                           self.deck_size, self.epidemics)


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
