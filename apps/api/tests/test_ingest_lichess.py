import httpx
from knightwise_api.ingest.lichess import LichessClient, fetch_lichess_games


def _transport(body: str) -> httpx.MockTransport:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body.encode("utf-8"), headers={"content-type": "application/x-ndjson"})

    return httpx.MockTransport(handler)


NDJSON_ONE_WIN_WHITE = (
    '{"id":"abc123","createdAt":1700000000000,"speed":"blitz","perf":"blitz","winner":"white",'
    '"players":{"white":{"user":{"name":"mike-bear"},"rating":1500},"black":{"user":{"name":"opp"},"rating":1550}},'
    '"pgn":"1. e4 e5"}\n'
)

NDJSON_MULTI = (
    NDJSON_ONE_WIN_WHITE
    + '{"id":"def456","createdAt":1700000100000,"speed":"rapid","winner":"black",'
    '"players":{"white":{"user":{"name":"opp2"},"rating":1600},"black":{"user":{"name":"mike-bear"},"rating":1510}},'
    '"pgn":"1. d4 d5"}\n'
)


def test_lichess_normalizes_single_game():
    http = httpx.Client(transport=_transport(NDJSON_ONE_WIN_WHITE), timeout=5.0)
    with LichessClient(client=http) as client:
        games = fetch_lichess_games("mike-bear", max_games=10, client=client)
    assert len(games) == 1
    g = games[0]
    assert g.source == "lichess"
    assert g.external_id == "abc123"
    assert g.played_as == "white"
    assert g.result == "win"
    assert g.user_rating == 1500
    assert g.opponent_rating == 1550
    assert g.pgn.startswith("1. e4")


def test_lichess_handles_black_and_loss():
    http = httpx.Client(transport=_transport(NDJSON_MULTI), timeout=5.0)
    with LichessClient(client=http) as client:
        games = fetch_lichess_games("mike-bear", max_games=10, client=client)
    assert len(games) == 2
    black_game = games[1]
    assert black_game.played_as == "black"
    assert black_game.result == "win"


def test_lichess_draw_when_no_winner():
    draw_line = (
        '{"id":"xyz789","createdAt":1700000200000,"speed":"blitz",'
        '"players":{"white":{"user":{"name":"mike-bear"},"rating":1500},"black":{"user":{"name":"opp"},"rating":1550}},'
        '"pgn":"1. e4 e5 1/2-1/2"}\n'
    )
    http = httpx.Client(transport=_transport(draw_line), timeout=5.0)
    with LichessClient(client=http) as client:
        games = fetch_lichess_games("mike-bear", max_games=10, client=client)
    assert games[0].result == "draw"
