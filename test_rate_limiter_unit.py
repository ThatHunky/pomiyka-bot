from bot.modules import rate_limiter
import time

def test_can_send_to_chat():
    rl = rate_limiter.RateLimiter()
    chat_id = 123
    assert rl.can_send_to_chat(chat_id, 2)
    assert rl.can_send_to_chat(chat_id, 2)
    assert not rl.can_send_to_chat(chat_id, 2)
    time.sleep(1.1)
    assert rl.can_send_to_chat(chat_id, 2)

def test_can_send_globally():
    rl = rate_limiter.RateLimiter()
    for _ in range(20):
        assert rl.can_send_globally(20)
    assert not rl.can_send_globally(20)
    time.sleep(1.1)
    assert rl.can_send_globally(20)

def test_record_error_and_suppress():
    rl = rate_limiter.RateLimiter()
    chat_id = 456
    for _ in range(3):
        rl.record_error(chat_id)
    assert rl.should_suppress_errors(chat_id)
    time.sleep(5.1)
    assert not rl.should_suppress_errors(chat_id)
