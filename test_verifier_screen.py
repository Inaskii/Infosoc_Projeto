"""Tests for resetting the news question screen."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from main import RoundedButton, VerifierScreen


class VerifierScreenTests(unittest.TestCase):
    def test_clear_resets_question_and_enables_another_question(self) -> None:
        screen = SimpleNamespace(
            text=Mock(),
            status=Mock(),
            result=Mock(),
            verify_button=Mock(),
            _request_id=4,
        )

        VerifierScreen.clear(screen)

        screen.text.delete.assert_called_once_with("1.0", "end")
        screen.status.configure.assert_called_once_with(text="")
        screen.result.grid_remove.assert_called_once_with()
        screen.verify_button.state.assert_called_once_with(["!disabled"])
        screen.text.focus_set.assert_called_once_with()
        self.assertEqual(screen._request_id, 5)

    def test_button_state_matches_disabled_and_enabled_states(self) -> None:
        button = object.__new__(RoundedButton)
        button.enabled = True
        button.normal = "#000000"
        button.configure = Mock()

        with patch.object(RoundedButton, "_draw") as draw:
            button.state(["disabled"])
            self.assertFalse(button.enabled)
            button.configure.assert_called_with(cursor="arrow")
            draw.assert_called_with("#AAB8C2")

            button.state(["!disabled"])
            self.assertTrue(button.enabled)
            button.configure.assert_called_with(cursor="hand2")
            draw.assert_called_with(button.normal)

    def test_ignores_response_from_a_question_cleared_while_processing(self) -> None:
        screen = SimpleNamespace(_request_id=5)

        VerifierScreen._show_result(screen, SimpleNamespace(), 4)


if __name__ == "__main__":
    unittest.main()
