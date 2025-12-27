"""
In this experiment participants mark and describe interesting moments in a piece of music.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from pathlib import Path
import json

import psynet.experiment
from mutagen.mp3 import MP3

from psynet.asset import asset  # noqa
from psynet.timeline import ProgressDisplay, ProgressStage, Timeline, join, PageMaker
from psynet.page import InfoPage
from psynet.modular_page import ModularPage, AudioPrompt, TextControl
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from markupsafe import Markup

from .control import TimedPushButtonControl


STIMULUS_DIR = "data/stimuli"
STIMULUS_PATTERN = "*.mp3"
TRIALS_PER_PARTICIPANT = 2


def get_timeline():
    return Timeline(
        InfoPage("Welcome! You will listen to audio and mark interesting moments.", time_estimate=5),
        # CodeBlock(lambda participant: participant.var.set("event", [1])),
        StaticTrialMaker(
            id_="audio_timed_button_trial",
            trial_class=AudioTimedButtonTrial,
            nodes=get_nodes,  # not get_nodes()!
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
        ),
        InfoPage("Thank you for participating!", time_estimate=5)
    )


def get_nodes():
    return [
        StaticNode(
            definition={
                "stimulus_name": path.stem,
                "duration_seconds": MP3(str(path)).info.length
            },
            assets={
                "stimulus_audio": asset(path, cache=False),  # reuse the uploaded file between deployments
            },
        )
        for path in Path(STIMULUS_DIR).glob(STIMULUS_PATTERN)
    ]


class AudioTimedButtonTrial(StaticTrial):
    time_estimate = 40
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return ModularPage(
            "event_times",
            prompt=AudioPrompt(
                audio=self.assets["stimulus_audio"],
                text="Listen to the music and press the button when you hear a surprising event.",
                controls=False
            ),
            control=TimedPushButtonControl(
                choices=self.choices,
                button_highlight_duration=0.75
            ),
            progress_display=ProgressDisplay(
                stages=[ProgressStage([0.0, self.definition["duration_seconds"]])],
            ),
            scripts=[*self.keyboard_javascript],
        )

    def show_feedback(self, experiment, participant):
        return InfoPage(f"Your response: {participant.answer}")

    choices = ["Slightly expected", "Very unexpected"]
    keys = ['S', 'V']

    @property
    def key_map(self):
        result = {}
        for key, choice in zip(self.keys, self.choices):
            result[key] = choice
            result[key.lower()] = choice
        return result

    @property
    def keyboard_javascript(self):
        return [
            f"const keyMap = {json.dumps(self.key_map)};",
            """
            document.addEventListener("keydown", function(event) {
                const buttonId = keyMap[event.key];
                if (buttonId) {
                    const button = document.getElementById(buttonId);
                    if (!button) {
                        throw new Error("Button '" + buttonId + "' not found");
                    }
                    button.click();
                }
            });
            """
        ]


class Experiment(psynet.experiment.Experiment):
    timeline = get_timeline()
