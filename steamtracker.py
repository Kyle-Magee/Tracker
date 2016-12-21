import config
import requests
import datetime


def playtime(user):
    url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&format=json'.format(
        config.steam_key, user.steam_id)
    response = requests.get(url).json()
    games = response['response']['games']
    time_played = sum([games[i]['playtime_forever'] for i in range(len(games))])
    return time_played


def minutes_played_this_session(user):
    return playtime(user) - user.start_playtime


def over_limit(user):
    if minutes_played_this_session(user) / 60 > user.time_limit:
        return True
    else:
        return False


def notify_user(user):
    return requests.post(config.mail_url, auth=config.mail_key,
                         data={"from": "Mailgun Sandbox <postmaster@sandbox5ec3142264ec408ca87618cb784f58d9.mailgun.org>",
                               "to": user.email,
                               "subject": "Limit Reached",
                               "text": "You have exceeded your Steam Limit."})


def reset_user(user):
    user.start_playtime = playtime(user)
    user.start_date = datetime.datetime.now()
    user.notified = False
    return user


def run(user, usermeta):

    user.current_playtime = minutes_played_this_session(user)

    if over_limit(user) and not user.notified:
        notify_user(usermeta)
        user.notified = True

    days_tracked_this_interval = datetime.datetime.now() - user.start_date
    if days_tracked_this_interval.days >= 7:
        reset_user(user)

