"""
In this experiment participants mark and describe interesting moments in a piece of music.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from collections import Counter
from pathlib import Path
import json
import random
from typing import List

from sqlalchemy import func

from psynet.bot import Bot
import psynet.experiment
from mutagen.mp3 import MP3

from psynet.asset import asset  # noqa
from psynet.timeline import ProgressDisplay, ProgressStage, Timeline
from psynet.page import InfoPage
from psynet.modular_page import ModularPage, AudioPrompt
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from .control import TimedPushButtonControl
from .questionnaire import questionnaire


STIMULUS_DIR = "data/stimuli"
STIMULUS_PATTERN = "*.mp3"

PIECES = [
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
assert len(PIECES) == 10

CONDITIONS = ["1", "2a", "2b", "2c", "2d"]
assert len(CONDITIONS) == 5

TRIALS_PER_PARTICIPANT = len(PIECES)



def get_timeline():
    return Timeline(
        questionnaire(),
        InfoPage("Welcome! You will listen to audio and mark interesting moments.", time_estimate=5),
        CustomTrialMaker(
            id_="main",
            trial_class=AudioTimedButtonTrial,
            nodes=get_nodes,  # not get_nodes()!
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_block=1,  # We treat each piece as a block
            balance_across_nodes=True,  # PsyNet will make sure each piece/condition combination gets a similar number of trials
        ),
        InfoPage("Thank you for participating!", time_estimate=5)
    )


def get_nodes():
    nodes = []

    for piece in PIECES:
        for condition in CONDITIONS:
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
                    block=piece,
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
                button_highlight_duration=0.75,
                bot_response=self.generate_random_response,
            ),
            progress_display=ProgressDisplay(
                stages=[ProgressStage([0.0, self.definition["duration_seconds"]])],
            ),
            scripts=[*self.keyboard_javascript],
        )

    def generate_random_response(self):
        n_events = random.randint(1, 3)
        times = sorted(random.uniform(0, self.definition["duration_seconds"]) for _ in range(n_events))
        choices = [random.choice(self.choices) for _ in range(n_events)]
        return [
            {
                "choice": choice,
                "time": time
            }
            for choice, time in zip(choices, times)
        ]

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

    # There are 5 conditions, and each bot only sees one condition per stimulus,
    # so we need 5 bots to see all the conditions for all stimuli.
    test_n_bots = 5

    def test_check_bots(self, bots: List[Bot]):
        super().test_check_bots(bots)

        assert len(bots) == self.test_n_bots

        trials_by_bot = [
            AudioTimedButtonTrial.query
            .filter_by(
                trial_maker_id="main",
                participant_id=bot.id,
            )
            .order_by(AudioTimedButtonTrial.id)
            .all()
            for bot in bots
        ]

        # Check individual bots
        for trials in trials_by_bot:
            # Check that each bot saw every piece
            assert len(trials) == len(PIECES)

            # Check that the same piece doesn't occur twice in the same bot
            pieces = [trial.definition["piece"] for trial in trials]
            assert len(pieces) == len(set(pieces))

        # Check that the bots see the pieces in different orders
        piece_orders = [
            tuple(trial.definition["piece"] for trial in trials)
            for trials in trials_by_bot
        ]
        assert len(set(piece_orders)) > 1

        # Check that each node has been seen a similar number of times
        # Returns a list of tuples: [(node_id, count), ...]
        node_counts = (
            StaticTrial.query
            .filter_by(trial_maker_id="main")
            .group_by(StaticTrial.node_id)
            .with_entities(StaticTrial.node_id, func.count(StaticTrial.id).label('count'))
            .all()
        )
        counts = [count for _, count in node_counts]
        assert len(counts) > 0, "No nodes found"
        assert max(counts) - min(counts) <= 1, f"Node counts are not balanced: min={min(counts)}, max={max(counts)}"

        # [(definition1,), (definition2,), ...] (list of 1-tuples)
        all_definitions = (
            AudioTimedButtonTrial.query
            .filter_by(trial_maker_id="main")
            .with_entities(AudioTimedButtonTrial.definition)
            .all()
        )

        # [definition1, definition2, ...] (list of dicts)
        all_definitions = [definition for definition, in all_definitions]

        # Assert that each piece has been seen a similar number of times
        piece_counts = Counter[str](definition["piece"] for definition in all_definitions)
        counts = list[int](piece_counts.values())
        assert len(counts) == len(PIECES), f"Expected {len(PIECES)} pieces, found {len(counts)}"
        assert max(counts) - min(counts) <= 1, f"Piece counts are not balanced: min={min(counts)}, max={max(counts)}"

        # Assert that each condition has been seen a similar number of times
        condition_counts = Counter[str](definition["condition"] for definition in all_definitions)
        counts = list[int](condition_counts.values())
        assert len(counts) == len(CONDITIONS), f"Expected {len(CONDITIONS)} conditions, found {len(counts)}"
        assert max(counts) - min(counts) <= 1, f"Condition counts are not balanced: min={min(counts)}, max={max(counts)}"

        # Assert that each stimulus has been seen a similar number of times
        stimulus_counts = Counter[str](definition["stimulus"] for definition in all_definitions)
        counts = list[int](stimulus_counts.values())
        expected_stimuli = len(PIECES) * len(CONDITIONS)
        assert len(counts) <= expected_stimuli, f"Found {len(counts)} unique stimuli, expected at most {expected_stimuli}"
        assert max(counts) - min(counts) <= 1, f"Stimulus counts are not balanced: min={min(counts)}, max={max(counts)}"
