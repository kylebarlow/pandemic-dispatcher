# pandemic-dispatcher

This is an ever-so-slightly overbuilt online assistant for the board game [Pandemic Legacy](http://www.zmangames.com/store/p31/Pandemic_Legacy.html). This was built for a specific gaming group and may contain **spoilers**, so be warned!

The project is built as a Flask website, and the structure was strongly influenced by the [Flasky](https://github.com/miguelgrinberg/flasky) project to learn what I was doing. Some pieces of the code were copied wholesale and might not even work, I haven't tried them. It uses Flask, Flask-Bootstrap, Flask-SQLAlchemy, Flask-WTF, and Flask-Nav.

I've called this version 0.1, as there are a lot of things to change, but I welcome pull requests. In particular you can't really undo any mistakes which is a problem.

Also I hope this doesn't violate zman's copyright but it feels like fair use? You should definitely buy Pandemic Legacy if you haven't already, it's good.

## Update: version 0.2?

Based on the previous game session (in which the server got into a broken state due to user error and was henceforth useless), I've rewritten the data model. The new app models a Game as a series of Turns, and allows for the possibility of going back to a previous turn to change what happened. One hiccup is that this can make the app think something is broken (i.e. a city was infected when that should be impossible) and the current solution is to wipe out the turns following the edited one&emdash;that's unfortunate because it doesn't allow for minor tweaks in game state.
