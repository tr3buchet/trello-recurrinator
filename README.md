this is a little tool to enable recurrinng task functionality for cards on [trello.com](http://trello.com)

the idea is fairly straight forward and requires some labels and a couple of lists on
a particular trello board

the labels look like this and the N can be any number you like:
* rrdN
* rrmN
* rryN

these labels correspond to how often this card should recur, some examples:
* rrd1 - recurs daily
* rrd14 - recurs every other week
* rrd28 - recurs every 4 weeks
* rrm1 - recurs monthly (ie on the 3rd of every month)
* rry1 - recurs yearly (ie each year on october 2nd)

so to get started:
1. make two lists and note their names for the config
2. make some card labels with names as described above
3. create some cards labeled with yourlabels and add due dates
4. move a card from the recurring task list to the done list

when you run the script it will
1. find the card on the done list
2. update its date based on the label
3. move it back to the recurring task list ready for next time

### installation
clone the git repo and setup your config as shown below

### run
run `python trello.py`
i recommend cron once an hour or so and it'll just magically keep all of your
recurring tasks ready to go

### config
you have two options for configuration, config file located at `~/.trello.conf` or environment variables.
if reading/parsing the config file fail for any reason it falls back to environment variables and if
they don't exist, the app will error out

example ~/.trello.conf:
```
[config]
api = https://trello.com/1
key = <key>
token = <token>
todo_board_id = hifj3lS
recurring_list_name = recurring
done_list_name = done
```

and ENV VARIABLES if you choose to use them (on heroku or whatever)
```
TRELLO_API
TRELLO_KEY
TRELLO_TOKEN
TRELLO_TODO_BOARD_ID
TRELLO_RECURRING_LIST_NAME
TRELLO_DONE_LIST_NAME
```

### key and tokens from trello.com
to get your key and token go to [trello app key](https://trello.com/app-key) and note the Key.
then go to the following link, substituting the key, your app's name, and how long you want the secret to last,
using "never" if you don't want it to expire. this app needs read and write privileges.
```
https://trello.com/1/authorize?key=substitutewithyourapplicationkey&name=My+Application&expiration=1day&response_type=token&scope=read,write
```

for more information see [getting a token from a user](https://trello.com/docs/gettingstarted/index.html#getting-a-token-from-a-user)

### heroku instructions
1. clone the git repo
2. create a [heroku](https://heroku.com)
3. heroku git:remote -a appname
4. set env variables using `heroku config:set` as shown [here](https://devcenter.heroku.com/articles/config-vars#setting-up-config-vars-for-a-deployed-application)
5. test running by `heroku run worker`
6. if test went well, add the heroku scheduler addon to your app and set it to run once an hour or so

in case it matters, a single run of the app takes only a few seconds, so your app will come no where near the 750 free dyno hours
