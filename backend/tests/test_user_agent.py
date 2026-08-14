"""Unit tests for the lightweight user-agent parser."""

from app.services.user_agent import parse_user_agent

CHROME_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)
FIREFOX_MAC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5) Gecko/20100101 Firefox/128.0"
)
SAFARI_IOS = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)
CHROME_ANDROID = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
)
EDGE_WIN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
)
IPAD_SAFARI = (
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


class TestParseUserAgent:
    def test_empty(self):
        assert parse_user_agent("") == ("unknown", "Unknown", "Unknown")
        assert parse_user_agent(None) == ("unknown", "Unknown", "Unknown")

    def test_chrome_windows(self):
        device, browser, os_name = parse_user_agent(CHROME_WIN)
        assert device == "desktop"
        assert browser.startswith("Chrome")
        assert os_name == "Windows"

    def test_firefox_macos(self):
        device, browser, os_name = parse_user_agent(FIREFOX_MAC)
        assert device == "desktop"
        assert browser.startswith("Firefox")
        assert os_name == "macOS"

    def test_safari_ios(self):
        device, browser, os_name = parse_user_agent(SAFARI_IOS)
        assert device == "mobile"
        assert browser.startswith("Safari")
        assert os_name == "iOS"

    def test_chrome_android(self):
        device, browser, os_name = parse_user_agent(CHROME_ANDROID)
        assert device == "mobile"
        assert browser.startswith("Chrome")
        assert os_name == "Android"

    def test_edge_not_chrome(self):
        device, browser, os_name = parse_user_agent(EDGE_WIN)
        assert device == "desktop"
        assert browser.startswith("Edge")
        assert os_name == "Windows"

    def test_ipad_is_tablet(self):
        device, browser, os_name = parse_user_agent(IPAD_SAFARI)
        assert device == "tablet"
        assert os_name == "iOS"
