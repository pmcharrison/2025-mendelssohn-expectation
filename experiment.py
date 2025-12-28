"""
In this experiment participants mark and describe interesting moments in a piece of music.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from pathlib import Path
import json
import random

import psynet.experiment
from mutagen.mp3 import MP3

from psynet.asset import asset  # noqa
from psynet.timeline import ProgressDisplay, ProgressStage, Timeline, join, PageMaker
from psynet.page import InfoPage
from psynet.modular_page import ModularPage, AudioPrompt, SurveyJSControl, TextControl
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from markupsafe import Markup

from .control import TimedPushButtonControl


STIMULUS_DIR = "data/stimuli"
STIMULUS_PATTERN = "*.mp3"
TRIALS_PER_PARTICIPANT = 2


def get_timeline():
    return Timeline(
        questionnaire(),
        InfoPage("Welcome! You will listen to audio and mark interesting moments.", time_estimate=5),
        CustomTrialMaker(
            id_="audio_timed_button_trial",
            trial_class=AudioTimedButtonTrial,
            nodes=get_nodes,  # not get_nodes()!
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_block=1,  # We treat each piece as a block
        ),
        InfoPage("Thank you for participating!", time_estimate=5)
    )

def questionnaire():
    return ModularPage(
        "questionnaire",
        prompt="Please answer the following questions about your musical experience and listening habits.",
        control=SurveyJSControl(
            design={
                "pages": [
                    {
                        "name": "musical_experience",
                        "elements": [
                            {
                                "type": "radiogroup",
                                "name": "played_instrument",
                                "title": "Have you ever played a musical instrument?",
                                "isRequired": True,
                                "choices": [
                                    {"value": "yes", "text": "Yes"},
                                    {"value": "no", "text": "No"}
                                ]
                            }
                        ]
                    },
                    {
                        "name": "instrument_duration_page",
                        "elements": [
                            {
                                "type": "radiogroup",
                                "name": "instrument_duration",
                                "title": "For how long did you play?",
                                "isRequired": True,
                                "visibleIf": "{played_instrument} = 'yes'",
                                "choices": [
                                    {"value": "<1", "text": "<1 year"},
                                    {"value": "1-3", "text": "1-3 years"},
                                    {"value": "4-7", "text": "4-7 years"},
                                    {"value": "8-12", "text": "8-12 years"},
                                    {"value": ">12", "text": ">12 years"}
                                ],
                            },
                                                        {
                                "type": "radiogroup",
                                "name": "still_play",
                                "title": "Do you still play?",
                                "isRequired": True,
                                "visibleIf": "{played_instrument} = 'yes'",
                                "choices": [
                                    {"value": "yes", "text": "Yes"},
                                    {"value": "no", "text": "No"}
                                ]
                            },
                        ]
                    },
                    {
                        "name": "listening_habits",
                        "title": "Listening Habits",
                        "elements": [
                            {
                                "type": "radiogroup",
                                "name": "listen_frequency",
                                "title": "How regularly do you actively listen to music?",
                                "isRequired": True,
                                "choices": [
                                    {"value": "never", "text": "Never"},
                                    {"value": "<1", "text": "<1 hour per day"},
                                    {"value": "1-2", "text": "1-2 hours per day"},
                                    {"value": "3-5", "text": "3-5 hours per day"},
                                    {"value": ">5", "text": ">5 hours per day"}
                                ]
                            },
                            {
                                "type": "text",
                                "name": "predominant_genre",
                                "title": "Which genre do you predominantly listen to?",
                                "isRequired": True,
                                "visibleIf": "{listen_frequency} != 'never'"
                            }
                        ]
                    }
                ]
            },
        ),
        time_estimate=60,
    )

pieces = [
    "Op. 19, No. 5",
    "Op. 30, No. 1",
    "Op. 30, No. 4",
    "Op. 53, No. 3",
    "Op. 62, No. 6",
    "Op. 67, No. 4",
    "Op. 67, No. 6",
    "Op. 85, No. 2",
    "Op. 102, No. 1",
    "Op. 102, No. 2",
]
assert len(pieces) == 10


def get_nodes():
    nodes = []

    for piece in pieces:
        for condition in ["1", "2a", "2b", "2c", "2d"]:
            stimulus = f"{piece} condition {condition}"
            path = Path(STIMULUS_DIR) / f"{stimulus}.mp3"
            nodes.append(
                StaticNode(
                    definition={
                        "piece": piece,
                        "condition": condition,
                        "stimulus": stimulus,
                        "duration_seconds": MP3(str(path)).info.length
                    },
                    block="piece",
                    assets={
                        "audio": asset(path, cache=False),  # reuse the uploaded file between deployments
                    },
                )
            )
    return nodes


class CustomTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        shuffled_blocks = list(blocks)
        random.shuffle(shuffled_blocks)
        return shuffled_blocks


class AudioTimedButtonTrial(StaticTrial):
    time_estimate = 40
    accumulate_answers = True

    def show_trial(self, experiment, participant):
        return ModularPage(
            "event_times",
            prompt=AudioPrompt(
                audio=self.assets["audio"],
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
        return {key.lower(): choice for key, choice in zip(self.keys, self.choices)}

    @property
    def keyboard_javascript(self):
        return [
            f"const keyMap = {json.dumps(self.key_map)};",
            """
            document.addEventListener("keydown", function(event) {
                const buttonId = keyMap[event.key.toLowerCase()];
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
