#!/usr/bin/env python
#
# Copyright 2014 Trey Morris
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import ConfigParser
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os


class Trello(object):
    """
    class used to fetch boards/lists/cards from trello and
    make updates to cards as necessary
    """
    def __init__(selfie, config):
        selfie.api = config['api']
        selfie.trello_date_format = '%Y-%m-%dT%H:%M:%S.000Z'
        selfie.tokens = {'key': config['key'], 'token': config['token']}

    def _get(selfie, resource):
        r = requests.get('%s/%s' % (selfie.api, resource),
                         params=selfie.tokens)
        r.raise_for_status()
        return r.json()

    def _post(selfie, resource, data):
        r = requests.post('%s/%s' % (selfie.api, resource),
                          params=selfie.tokens, data=data)
        r.raise_for_status()
        return r

    def _put(selfie, resource, data):
        r = requests.put('%s/%s' % (selfie.api, resource),
                         params=selfie.tokens, data=data)
        r.raise_for_status()
        return r

    def get_board(selfie, board_id, eager=False):
        """
        return board with board id or shortlink

        if eager is True:
            also fetch the lists on the board and then fetch the cards
            on each list
        """
        board = selfie._get('boards/%s' % board_id)
        if not eager:
            return board

        board['lists'] = selfie.get_board_lists(board_id, eager)
        return board

    def get_board_lists(selfie, board_id, eager=False):
        """
        return lists on the board with board id or shortlink

        if eager is True:
            also fetch all of the cards contained on each list

        this will result in N+1 calls, where N is the number of cards
        on each list on the board added together
        """
        lists = selfie._get('boards/%s/lists' % board_id)
        if not eager:
            return lists

        for l in lists:
            l['cards'] = selfie.get_list_cards(l['id'])

        return lists

    def get_list_cards(selfie, list_id):
        """
        get all of the cards on this list

        it also walks through the cards to find if any of them
        are labeled with labels whose names start with rr.

        if found, the card will have a card['recurs'] field set
        to the label's name after the 'rr' bit

        for example, if a card is labeled with a label named
        'rrm3', then its 'recurs' field is set to 'm3'. Otherwise
        its 'recurs' field is set to None
        """
        cards = selfie._get('lists/%s/cards' % list_id)
        for card in cards:
            for label in card['labels']:
                if label['name'][:2] == 'rr':
                    card['recurs'] = label['name'][2:]
                    break
            else:
                card['recurs'] = None

        return cards

    def update_card(selfie, card, attribute, value):
        """
        update the card on trello by setting its attribute to value
        """
        data = {'value': value}
        return selfie._put('cards/%s/%s' % (card['id'], attribute), data)

    def create_card_on_list(selfie, list_id, card):
        card['idList'] = list_id
        return selfie._post('cards', card)

    def tick_recurring_card_date(selfie, card):
        """
        all the magic is here. parse card['recurs'] and update the
        card's due date on trello based on what it finds

        for example if a card has been labeled with a label named rrd7,
        card['recurs'] will equal 'd7'. This essentially means this
        card should recur every 7 days or weekly.

        based on this label, the card's due date will be updated to be
        N days, months, or years in the future compared to its current
        due date.

        supported labeled names are:
        rrdN - recurs every N days
        rrmN - recurs every N months
        rryN - recurs every N years
        """
        if card['recurs'] is None:
            print 'card |%s| had no known recurring label' % card['name']
            return
        if card['due'] is None:
            print 'card |%s| has no due date and cannot recur' % card['name']
            return

        if card['recurs'][0] == 'd':
            delta = relativedelta(days=int(card['recurs'][1:]))
        elif card['recurs'][0] == 'm':
            delta = relativedelta(months=int(card['recurs'][1:]))
        elif card['recurs'][0] == 'y':
            delta = relativedelta(years=int(card['recurs'][1:]))
        else:
            print 'card |%s| had no known recurring label' % card['name']
            return

        due = datetime.strptime(card['due'], selfie.trello_date_format)
        new_due = due + delta
        new_due = new_due.strftime(selfie.trello_date_format)
        return selfie.update_card(card, 'due', new_due)


def get_config():
    """
    get the config from ~/.trello.conf or read from environment variables
    if that fails for any reason

    see readme for what the boards are used for and how to get
    the key and token
    """
    possible_configs = [os.path.expanduser('~/.trello.conf')]
    config = ConfigParser.RawConfigParser()
    config.read(possible_configs)
    try:
        return {
            'api': config.get('config', 'api'),
            'key': config.get('config', 'key'),
            'token': config.get('config', 'token'),
            'relevant_board_id': config.get('config', 'relevant_board_id'),
            'recurring_list_name': config.get('config', 'recurring_list_name'),
            'done_list_name': config.get('config', 'done_list_name')}
    except Exception as e:
        print e, ' -> attempting to lead environment variables'
        # NOTE(tr3buchet): attempt to read env variables instead
        return {
            'api': os.environ['TRELLO_API'],
            'key': os.environ['TRELLO_KEY'],
            'token': os.environ['TRELLO_TOKEN'],
            'relevant_board_id': os.environ['TRELLO_RELEVANT_BOARD_ID'],
            'recurring_list_name': os.environ['TRELLO_RECURRING_LIST_NAME'],
            'done_list_name': os.environ['TRELLO_DONE_LIST_NAME']}


if __name__ == '__main__':
    config = get_config()
    relevant_board_id = config.get('relevant_board_id')
    t = Trello(config)

    # NOTE(tr3buchet): eagerload the board and all lists and cards
    #                  noting the recurring list and done list
    board = t.get_board(relevant_board_id, eager=True)
    for l in board['lists']:
        if l['name'] == config.get('recurring_list_name'):
            recurring_list = l
        elif l['name'] == config.get('done_list_name'):
            done_list = l

    # NOTE(tr3buchet): if card is done and recurs, reset it by updating its
    #                  due date and moving it back to the recurring list
    for card in done_list['cards']:
        if card['recurs']:
            t.tick_recurring_card_date(card)
            t.update_card(card, 'idList', recurring_list['id'])
