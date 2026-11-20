from app.api.ratelimit import TokenBucket


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_bucket_allows_burst_then_blocks():
    clock = Clock()
    b = TokenBucket(rate_per_minute=60, burst=2, clock=clock)
    assert b.allow("u") and b.allow("u")
    assert not b.allow("u")


def test_bucket_refills_over_time():
    clock = Clock()
    b = TokenBucket(rate_per_minute=60, burst=1, clock=clock)
    assert b.allow("u") and not b.allow("u")
    clock.t = 1.0
    assert b.allow("u")


def test_buckets_are_per_key():
    b = TokenBucket(rate_per_minute=60, burst=1, clock=Clock())
    assert b.allow("a") and b.allow("b")
