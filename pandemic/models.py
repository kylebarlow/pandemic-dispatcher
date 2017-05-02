from . import db


class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(16), nullable=False) # month of the game
    funding_rate = db.Column(db.Integer, nullable=False) # funding rate
    deck_size = db.Column(db.Integer, nullable=False) # number of cards remaining in the deck
    epidemics = db.Column(db.Integer, nullable=False) # number of epidemics drawn
    cities = db.relationship('City', backref='game', lazy=True)

    def __repr__(self):
        return u'<Game {}, Month {}, FR {}, Deck {}, Epidemics {}>'.format(self.id, self.month, self.funding_rate,
                                                                          self.deck_size, self.epidemics)


class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False) # city name
    color = db.Column(db.String(32), nullable=False) # (original) color of the city
    stack = db.Column(db.Integer, nullable=False) # what level of the epidemic stack this city is in
    player_card = db.Column(db.Boolean, nullable=False) # was the player card drawn?
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)

    def __repr__(self):
        return u'<City {} ({}): stack {}, PC {}>'.format(self.name, self.color, self.stack, self.player_card)
