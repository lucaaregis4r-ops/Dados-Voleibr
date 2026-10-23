import json
from cbv.parser.game_metadata import parse_game_metadata


def test_flight_identity_observed_sets_and_undefined_hall():
    game=dict(ChampionshipMatch_ID=12,HomeTeam='A',GuestTeam='B',WonSetHome=2,WonSetGuest=0,Set1Home=25,Set1Guest=20,Set2Home=25,Set2Guest=19,hall='$undefined')
    chunk='1:'+json.dumps(['$',dict(updatedMatch=game)])+'\n'
    html='<script>self.__next_f.push('+json.dumps([1,chunk])+')</script>'
    result=parse_game_metadata(html,12)
    assert result['sets'][0]['away_points']==20
    assert result['hall'] is None
    assert parse_game_metadata(html,13) is None
