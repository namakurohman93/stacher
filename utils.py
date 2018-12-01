SUBTYPE_and_FILENAME = (
                        ('population', 'pop_ranking'),
                        ('offPoints', 'off_ranking'),
                        ('deffPoints', 'deff_ranking')
                       )
RANKING_TYPE = 'ranking_Player'

def subtypes():
    yield from SUBTYPE_and_FILENAME
    # return [x for x in SUBTYPE_and_FILENAME]
