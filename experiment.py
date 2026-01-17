"""
In this experiment participants mark and describe interesting moments in a piece of music.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring

from collections import Counter
import os
from pathlib import Path
import json
import random
from typing import List

from markupsafe import Markup
from mutagen.mp3 import MP3

from psynet.consent import NoConsent
from psynet.trial.main import GenericTrialNode
from sqlalchemy import func

from psynet.bot import Bot
import psynet.experiment
from psynet.asset import asset
from psynet.timeline import Event, FailedValidation, join, ProgressDisplay, ProgressStage, Timeline
from psynet.page import CodeBlock, InfoPage, PageMaker, VolumeCalibration, while_loop
from psynet.modular_page import CheckboxControl, ModularPage, AudioPrompt, PushButtonControl
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

from .control import TimedPushButtonControl
from .debrief import debriefing
from .questionnaire import initial_questionnaire, final_questionnaire


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


# Run the experiment with only one piece for testing by running
# MINIMAL=1 psynet debug local
# in the terminal.
if os.environ.get("MINIMAL"):
    PIECES = PIECES[:1]

TRIALS_PER_PARTICIPANT = len(PIECES)


def get_timeline():
    return Timeline(
        information_sheet_and_consent_form(),
        InfoPage(
            """
            This experiment requires you to sit in a quiet room and wear headphones.
            Please only continue once you're ready.
            """,
            time_estimate=7.5,
        ),
        VolumeCalibration("static/example_stimulus.mp3"),
        initial_questionnaire(),
        training(),
        InfoPage(
            f"""
            You will now proceed to the main experiment, where you will take {TRIALS_PER_PARTICIPANT} trials.
            Please try to take these all in one go.
            Have fun!
            """,
            time_estimate=5,
        ),
        CustomTrialMaker(
            id_="main",
            trial_class=AudioTimedButtonTrial,
            nodes=get_nodes,
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_block=1,
            # Each node corresponds to a piece-condition combination
            balance_across_nodes=True,
        ),
        InfoPage(
            """
            Congratulations, you finished the main part of the experiment!
            """,
            time_estimate=5,
        ),
        final_questionnaire(),
        debriefing(),
    )


def information_sheet_and_consent_form():
    return join(
        NoConsent(),
        PageMaker(
            lambda experiment: ModularPage(
                "consent",
                prompt=Markup(
                    f"""
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div><strong>INFORMATION SHEET AND CONSENT</strong></div>
                        <div style="text-align: right; font-style: italic;">
                            <div>Faculty of Music</div>
                            <div>University of Cambridge</div>
                        </div>
                    </div>
                    <hr style="border: 2px solid black; margin: 10px 0;">
                    <div style="margin-top: 20px;">
                        <div><strong>Project:</strong> Exploring musical expectation</div>
                        <div><strong>Researcher(s):</strong> Maddie Melville-Smith</div>
                        <div><strong>Contact email:</strong> mm2774@cam.ac.uk</div>
                    </div>
                    <p style="margin-top: 20px;">
                        Before participating in this experiment, you will be asked to fill in a short questionnaire
                        about your musical experience and listening habits. You will then be asked to listen and respond
                        to musical extracts. You will then complete a further short questionnaire.
                        In total this should take around
                        {int(round(experiment.timeline.estimated_time_credit.get_max("time") / 60, 0))}
                        minutes of your time. Please wear headphones.
                    </p>
                    <p style="margin-top: 15px;">
                        Your participation is completely voluntary. You may withdraw from the session and be paid
                        according to the amount of the study you have completed.
                    </p>
                    <p style="margin-top: 15px;">
                        All data are recorded anonymously.
                    </p>
                    <p style="margin-top: 20px;">
                        <em>Please tick in each box to confirm the following statements:</em>
                    </p>
                    """
                ),
                control=CompulsoryCheckboxControl(
                    choices=["understand", "agree"],
                    labels=[
                        "I have read and understood the information above.",
                        "I agree to take part in this research.",
                    ],
                ),
            ),
            time_estimate=15,
        ),
    )


class CompulsoryCheckboxControl(CheckboxControl):
    def validate(self, response, **kwargs):
        if not all(choice in response.answer for choice in self.choices):
            return FailedValidation("Please confirm all statements to continue.")
        return super().validate(response, **kwargs)

    def get_bot_response(self, experiment, bot, page, prompt):
        return self.choices


def training():
    return join(
        InfoPage(
            """
            This experiment is about the concept of musical 'surprise': when something happens
            that you weren't quite expecting. We will play you various musical excerpts
            and ask you to mark the moments that you found surprising.

            Don't worry if you don't know much about music, and don't worry if you don't recognise the music!
            We're just interested in your intuitive responses.
            """,
            time_estimate=15,
        ),
        InfoPage(
            """
            We'll now give you a chance to try the task.
            """,
            time_estimate=5,
        ),
        CodeBlock(lambda participant: participant.var.set("training", "Yes")),
        while_loop(
            "training",
            condition=lambda participant: participant.var.get("training") == "Yes",
            logic=join(
                administer_practice_trial(),
                ModularPage(
                    "try_again",
                    prompt="Would you like to try the practice task again?",
                    control=PushButtonControl(
                        choices=["Yes", "No"],
                    ),
                    time_estimate=5,
                    save_answer="training",
                )
            ),
            expected_repetitions=1,
            fix_time_credit=True,  # don't pay them more for repeating the training
        )
    )


def get_nodes():
    """
    Get the nodes for the trial maker.

    Each node corresponds to a piece-condition combination.
    """
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
                        "duration_seconds": get_audio_file_duration(path)
                    },
                    block=piece,
                    assets={
                        "audio": asset(path, cache=False),  # reuse the uploaded file between deployments
                    },
                )
            )
    return nodes


def get_audio_file_duration(path) -> float:
    return MP3(str(path)).info.length


class CustomTrialMaker(StaticTrialMaker):
    def choose_block_order(self, experiment, participant, blocks):
        shuffled_blocks = list(blocks)
        random.shuffle(shuffled_blocks)
        return shuffled_blocks


class AudioTimedButtonTrial(StaticTrial):
    time_estimate = 40
    accumulate_answers = True
    should_show_answer = True

    def show_trial(self, experiment, participant):
        return join(
            ModularPage(
                "events",
                prompt=AudioPrompt(
                    audio=self.audio,
                    text=Markup(
                        """
                        <p>Listen out for surprising moments. When you hear a surprising moment, mark it as follows:</p>
                        <ul>
                            <li>If it was slightly surprising, press <strong>S</strong>.</li>
                            <li>If it was very surprising, press <strong>V</strong>.</li>
                        </ul>
                        <p>There might be multiple surprising moments in the piece, so keep listening throughout.</p>
                        <p>Note that the piece might finish suddenly, don't worry about that.</p>
                        <p>If you think you messed up, you can refresh the page to try again, but try to avoid this if you can.</p>
                        """
                    ),
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
                save_answer="events",
                events={
                    "submitEnable": Event(is_triggered_by="promptEnd"),
                },
            ),
            PageMaker(self.show_answer_if_appropriate),
            ModularPage(
                "recognition",
                prompt="Do you think you'd heard that piece before?",
                control=PushButtonControl(["Yes", "No"]),
            ),
        )

    @property
    def audio(self):
        return self.assets["audio"]

    def show_answer_if_appropriate(self, participant):
        if self.should_show_answer:
            return self.show_answer(participant)
        return []

    def show_answer(self, participant):
        events = participant.var.get("events")
        n_slightly_surprising = len([e for e in events if e["choice"] == "Slightly surprising"])
        n_very_surprising = len([e for e in events if e["choice"] == "Very surprising"])
        return InfoPage(
            f"""
            You marked {n_slightly_surprising} moment(s) as slightly surprising
            and {n_very_surprising} moment(s) as very surprising.
            """,
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

    choices = ["Slightly surprising", "Very surprising"]
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


class PracticeTrial(AudioTimedButtonTrial):
    should_show_answer = True

    @property
    def audio(self):
        return "static/example_stimulus.mp3"


def administer_practice_trial():
    return PracticeTrial.cue(definition={"duration_seconds": get_audio_file_duration("static/example_stimulus.mp3")})


GenericTrialNode.check_ready_to_spawn = lambda self: None


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
