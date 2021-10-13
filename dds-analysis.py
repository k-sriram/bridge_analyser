from ddstable import ddstable
import itertools
import random
import os.path
import json
# ddstable.get_ddstable(PBN)

def ptwise_add(a, b):
    return (i+j for i, j in zip(a, b))
def ptwise_or(a, b):
    return (i or j for i, j in zip(a, b))

TRUMPS = ddstable.dcardSuit
SUITS = ['S', 'H', 'D', 'C']
PL_INDEX = {'N':0, 'E':1, 'S':2, 'W':3}
PL_TEAM = {'N':'NS', 'E':'EW', 'S':'NS', 'W':'EW'}
PL_PARTNER = {'N':'S', 'E':'W', 'S':'N', 'W':'E'}
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
DECK = [s+r for s in SUITS for r in RANKS]
total_pts = 40
pbnfile = 'games.pbn'
datfile = 'results.json'

def isblocked(cards):
    return (('A' in cards and len(cards)>=2) or
            (('K' in cards or 'Q' in cards) and len(cards)>=3) or
            ('K' in cards and 'Q' in cards) or
            (len(cards)>=4)
           )

class Hand(dict):
    def __init__(self, S = None, H = None, D = None, C = None, PBN=None, cards=None):
        """ Hand(S=None, H=None, D=None, C=None, PBN=None, cards=None)
        Acceptable formats for suits are S=['A', '9'] and S="A9".
        Can accept PBN format as well as a list of cards"""
        if S is None: S=[]
        if H is None: H=[]
        if D is None: D=[]
        if C is None: C=[]
        dict.__init__(self, S=list(S), H=list(H), D=list(D), C=list(C))
        if PBN is not None: self.from_PBN(PBN)
        if cards is not None: self.add_cards(cards)

    def add_card(self, card):
        """ Adds a single card. Input should be like ST for 10 of spades."""
        suit, rank = card
        if suit not in SUITS or rank not in RANKS:
            raise ValueError
        self[suit].append(rank)

    def add_cards(self, cards):
        for card in cards:
            self.add_card(card)
    def add_suit(self, suit, cards):
        if suit not in SUITS: raise ValueError
        self[suit].extend(list(cards))

    def remove_card(self, card):
        suit, rank = card
        if suit not in SUITS or rank not in RANKS:
            raise ValueError
        self[suit].remove(rank)

    def sort(self):
        """ Sorts the suits from highest to lowest."""
        for suit in self.values():
            suit.sort(key = RANKS.index)

    def PBN(self):
        return '.'.join([''.join(self['S']), ''.join(self['H']), ''.join(self['D']), ''.join(self['C'])])
    def from_PBN(self, PBN):
        suits = PBN.split('.')
        for suit, cards in zip(SUITS, suits):
            self.add_suit(suit, cards)

    def HCP(self, points_table={r:max(4-i,0) for i,r in enumerate(RANKS)}):
        return sum(sum(points_table[card] for card in suit) for suit in self.values())
    def shape(self):
        return tuple(len(self[suit]) for suit in SUITS)
    def blocker(self):
        """ Returns the blocker status for SHDC suits as a tuple of bools."""
        return tuple(isblocked(self[suit]) for suit in SUITS)

class Deal():
    def __init__(self, north=None, east=None, south=None, west=None, PBN=None):
        self.north = Hand() if north is None else north
        self.east = Hand() if east is None else east
        self.south = Hand() if south is None else south
        self.west = Hand() if west is None else west
        self.hands = [self.north, self.east, self.south, self.west]
        if PBN is not None: self.from_PBN(PBN)
    def from_PBN(self, PBN):
        start, hands = PBN.split(':')
        start = PL_INDEX[start]
        hands = hands.split()
        for i, hand in enumerate(hands):
            i = (i+start)%4
            self.hands[i].from_PBN(hand)
    def PBN(self, first='N'):
        index = PL_INDEX[first]
        return first+':'+' '.join(hand.PBN() for hand in self.hands[index:] + self.hands[:index])

    def sort(self):
        for hand in self.hands:
            hand.sort()

    def HCP(self, players=None):
        """ HCP(players=None)
        Returns a tuple of HCP in NESW order.
        Use players='N' for specific players HCP.
        Use players='NS' for team HCP."""
        if players is None:
            return tuple(hand.HCP() for hand in self.hands)
        else:
            return sum(self.hands[PL_INDEX[player]].HCP() for player in players)
    def shape(self, players=None):
        """ shape(players=None)
        Returns a tuple of (S,H,D,C)-shape in NESW order.
        Use players='N' for specific players shape.
        Use players='NS' for team shape."""
        if players is None:
            return tuple(hand.shape() for hand in self.hands)
        else:
            return tuple(list(itertools.accumulate((self.hands[PL_INDEX[player]].shape() for player in players), ptwise_add, initial=(0, 0, 0, 0)))[-1])
    def blocker(self, players=None):
        if players is None:
            return tuple(hand.blocker() for hand in self.hands)
        else:
            return tuple(list(itertools.accumulate((self.hands[PL_INDEX[player]].blocker() for player in players), ptwise_or, initial=(False, False, False, False)))[-1])



if __name__ == '__main__':
    if os.path.exists(datfile):
        with open(datfile) as file:
            data = json.load(file)
    else:
        data = {suit:[[[[0]*14 for smaller in range(fit//2+1)] for fit in range(14)] for pt in range(total_pts+1)] for suit in SUITS}
        # data[trump][points][fitsize][smallersize][tricks]
        data['NT'] = [[[0]*14, [0]*14] for pt in range(total_pts+1)]
        # data['NT'][points][blocker][tricks]
    with open(pbnfile, 'a') as file:
        for trial in range(1000):
            new_deck = DECK[:]
            random.shuffle(new_deck)
            new_deal = Deal(Hand(cards=new_deck[:13]), Hand(cards=new_deck[13:26]), Hand(cards=new_deck[26:39]), Hand(cards=new_deck[39:]))
            dds_analysis = ddstable.get_ddstable(bytes(new_deal.PBN(),'utf-8'))
            for player in "NSEW":
                team = PL_TEAM[player]
                points = new_deal.HCP(team)
                blocker = int(all(new_deal.blocker(team)))
                team_shape = new_deal.shape(team)
                player_shape = new_deal.shape(player)
                smaller_shape = tuple(min(ps, ts-ps) for ps, ts in zip(player_shape, team_shape))
                for trump in TRUMPS:
                    tricks = dds_analysis[player][trump]
                    if trump == 'NT':
                        data['NT'][points][blocker][tricks] += 1
                    else:
                        fitsize = team_shape[SUITS.index(trump)]
                        smallersize = smaller_shape[SUITS.index(trump)]
                        data[trump][points][fitsize][smallersize][tricks] += 1
            file.write(new_deal.PBN())
            file.write('\n')
            if trial%10 == 9: print('.', end='')

    with open(datfile, 'w') as file:
        json.dump(data, file)
    
