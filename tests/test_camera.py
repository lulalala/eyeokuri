from eyeokuri.sources.camera import ReconnectingCamera


class FakeCapture:
    """Delivers frames until it runs out of `good_reads`, then fails forever."""

    def __init__(self, good_reads: int = 10**9, opened: bool = True) -> None:
        self.good_reads = good_reads
        self.opened = opened
        self.released = False

    def isOpened(self) -> bool:
        return self.opened and not self.released

    def read(self) -> tuple[bool, object]:
        if not self.isOpened() or self.good_reads <= 0:
            return False, None
        self.good_reads -= 1
        return True, "frame"

    def release(self) -> None:
        self.released = True


def make_camera(captures: list[FakeCapture]) -> tuple[ReconnectingCamera, list[FakeCapture], list[str]]:
    pending = list(captures)
    opened: list[FakeCapture] = []
    messages: list[str] = []

    def open_capture() -> FakeCapture:
        cap = pending.pop(0)
        opened.append(cap)
        return cap

    return ReconnectingCamera(open_capture, 1.0, messages.append), opened, messages


def test_reads_frames_without_reopening():
    camera, opened, messages = make_camera([FakeCapture()])
    assert all(camera.read(t * 0.1) == "frame" for t in range(30))
    assert len(opened) == 1
    assert messages == []


def test_dead_capture_is_replaced_after_reconnect_interval():
    camera, opened, messages = make_camera([FakeCapture(good_reads=2), FakeCapture()])
    assert camera.read(0.0) == "frame"
    assert camera.read(0.1) == "frame"
    assert camera.read(0.2) is None
    assert camera.read(0.7) is None
    assert len(opened) == 1  # too soon to reopen
    assert camera.read(1.3) is None
    assert len(opened) == 2
    assert opened[0].released
    assert camera.read(1.4) == "frame"
    assert messages[-1] == "camera: frames are back after 1.20s"


def test_keeps_retrying_while_device_is_missing():
    camera, opened, _ = make_camera([
        FakeCapture(good_reads=0),
        FakeCapture(opened=False),
        FakeCapture(opened=False),
        FakeCapture(),
    ])
    assert camera.read(0.0) is None
    assert camera.read(1.0) is None  # reopen fails: device not back yet
    assert camera.read(2.0) is None  # fails again
    assert camera.read(3.0) is None  # this attempt gets a working capture
    assert camera.read(3.1) == "frame"
    assert len(opened) == 4
    assert all(cap.released for cap in opened[:3])


def test_reports_unopened_camera():
    camera, _, _ = make_camera([FakeCapture(opened=False)])
    assert not camera.opened


def test_camera_missing_at_start_is_picked_up_when_plugged_in():
    camera, opened, messages = make_camera([
        FakeCapture(opened=False),
        FakeCapture(opened=False),
        FakeCapture(),
    ])
    assert camera.read(0.0) is None
    assert camera.read(1.0) is None  # still unplugged
    assert camera.read(2.0) is None  # this attempt gets a working capture
    assert camera.read(2.1) == "frame"
    assert len(opened) == 3
    assert all(cap.released for cap in opened[:2])
    assert messages[0] == "camera: reopening"  # not "frame grab failed": it never worked
    assert messages[-1] == "camera: frames are back after 2.10s"


def test_reopen_is_logged_once_in_a_while_not_every_attempt():
    captures = [FakeCapture(opened=False) for _ in range(70)]
    camera, _, messages = make_camera(captures)
    for t in range(65):
        camera.read(float(t))
    assert messages.count("camera: reopening") == 3  # at 1 s, 31 s and 61 s
