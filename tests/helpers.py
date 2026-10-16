"""실제로 기다리지 않고 시간 경과를 검증하는 보조 도구."""


class ManualClock:
    """호출하면 현재 시각을 반환하고, advance로만 시간을 진행한다."""

    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds
