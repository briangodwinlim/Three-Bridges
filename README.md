# Three-Bridges

This web app is a variant of the famous [Prisoner's Dilemma Problem](https://en.wikipedia.org/wiki/Prisoner%27s_dilemma) applied to a sailor/pirate context. The development of this app is due to the COVID-19 pandemic wherein traditional physical activities are forced to transition to online means. This app addresses this issue by allowing players to experience the thrill of the dilemma/problem through online means. The app is made using [Flask](https://flask.palletsprojects.com/en/2.1.x/) and deployed to [Heroku](https://www.heroku.com/).

To play the game, go to [three-bridges.brianlim.xyz](https://three-bridges.brianlim.xyz) and register an account. Click on the Play button to start a game. By default, you will be playing against yourself (not recommended) unless a new player joins. There will be 10 rounds per game. In each round, choose one of the three bridges available and a score will be given depending on you and your opponent's choice of bridges. The game ends after 10 rounds at which point the admin will reset the game. Due to Heroku limitations, the app can only accomodate 10 registered players at a time.

To report any bugs or submit any suggestions, open a new issue or email me at [brian@brianlim.xyz](mailto:brian@brianlim.xyz).

Credits to [Corey Schafer](https://www.youtube.com/c/Coreyms) and [Miguel Grinberg](https://www.youtube.com/c/MiguelGrinberg) for their helpful tutorials on getting started with Flask and [Turbo-Flask](https://turbo-flask.readthedocs.io/).