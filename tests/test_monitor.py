from monitor import should_attempt_restart


def test_restart_attempted_at_threshold_multiples():
    # At the very first failure, we should NOT attempt a restart yet
    assert should_attempt_restart(failure_count=1, threshold=3, restart_attempts=0, max_restart_attempts=3) is False
    assert should_attempt_restart(failure_count=2, threshold=3, restart_attempts=0, max_restart_attempts=3) is False

    # At failure #3 (a multiple of the threshold), a restart SHOULD be attempted
    assert should_attempt_restart(failure_count=3, threshold=3, restart_attempts=0, max_restart_attempts=3) is True

    # This is the exact regression check for the original bug:
    # the old buggy code used `==` instead of `%`, so it could only ever
    # trigger once, at failure_count == threshold, and never again afterward.
    # failure_count=6 is a LATER multiple of the threshold (3), and must ALSO trigger.
    assert should_attempt_restart(failure_count=6, threshold=3, restart_attempts=1, max_restart_attempts=3) is True


def test_restart_not_attempted_once_max_attempts_reached():
    # Even at a valid threshold multiple, if restart_attempts already
    # equals max_restart_attempts, no further restart should be attempted.
    assert should_attempt_restart(failure_count=9, threshold=3, restart_attempts=3, max_restart_attempts=3) is False