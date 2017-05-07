# pandemic-dispatcher

This is an ever-so-slightly overbuilt online assistant for the board game [Pandemic Legacy](http://www.zmangames.com/store/p31/Pandemic_Legacy.html). This was built for a specific gaming group and may contain **spoilers**, so be warned!

The project is built as a Flask website, and the structure was strongly influenced by the [Flasky](https://github.com/miguelgrinberg/flasky) project to learn what I was doing. Some pieces of the code were copied wholesale and might not even work, I haven't tried to use them yet. It uses Flask, Flask-Bootstrap, Flask-SQLAlchemy (and SQLAlchemy), Flask-WTF (and WTForms), and Flask-Nav.

Pull requests are welcome! Please bear in mind that we haven't finished the game yet (we're currently in August), so I can't add functionality that would spoil the game (and I don't want to hear about it either).

Also I hope this doesn't violate [zmangames](http://www.zmangames.com)'s copyright, but it feels like fair use to me? You should definitely buy Pandemic Legacy if you haven't already, it's really good. You can tell because I made a thing for it.

## Update: version 0.2

Based on the previous game session (in which the server got into a broken state due to user error and was henceforth useless), I've rewritten the data model. The new app models a Game as a series of Turns, and allows for the possibility of going back to a previous turn to change what happened. One hiccup is that this can make the app think something is broken (i.e. a city was infected when that should be impossible) and the current solution is to wipe out the turns following the edited one&emdash;that's unfortunate because it doesn't allow for minor tweaks in game state.

Main TODOs:
 - Write an interface for character selection
 - Deploy to a cloud server rather than running locally (this may require some authentication though)
 - Implement some game mechanics that we aren't using right now but might come up in the future (e.g. certain funded events)
 - Possibly: customize the experience based on the game month
