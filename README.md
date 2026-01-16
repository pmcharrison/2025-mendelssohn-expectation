# Mendelssohn Expectation Experiment

## Overview

This experiment investigates how listeners generate expectations about musical events. Participants listen to Mendelssohn pieces that have been altered according to various rules, and mark surprising events using a timed push button paradigm. The experiment uses the PsyNet framework.

## Experiment Design

- **Stimuli**: 10 Mendelssohn pieces (Op. 19, No. 5; Op. 30, No. 1; Op. 30, No. 4; Op. 53, No. 3; Op. 62, No. 6; Op. 67, No. 4; Op. 67, No. 6; Op. 85, No. 2; Op. 102, No. 1; Op. 102, No. 2)
- **Conditions**: Each piece has 5 conditions (1, 2a, 2b, 2c, 2d)
- **Task**: Participants listen to each piece and press buttons to mark surprising events. Multiple surprising moments can be marked throughout each piece.
- **Response options**: "Slightly surprising" (keyboard shortcut: S) or "Very surprising" (keyboard shortcut: V)
- **Trials per participant**: 10 (one trial per piece, with piece-condition combinations balanced across participants)
- **Training**: Participants complete a practice trial before the main experiment
- **Recognition question**: After each trial, participants are asked if they had heard the piece before

## Structure

- `experiment.py`: Main experiment definition, trial structure, and bot testing
- `control.py`: Custom timed push button control implementation
- `questionnaire.py`: Initial questionnaire (demographics: age, gender; musical experience: instrument playing history; listening habits: frequency and genre) and final questionnaire (surprise source: melody/harmony/equally/don't know; general strategy; optional feedback)
- `debrief.py`: Debriefing page explaining the experiment purpose
- `data/stimuli/`: Audio files for all piece-condition combinations

## Running the experiment

### GitHub Codespaces

The simplest way to work with this experiment is to run it in GitHub Codespaces.
To do so, navigate to the repository page in GitHub (you might be looking at it already),
and click the green "Code" button, click "Codespaces", and then click "Create a codespace on main". The codespace will take a while to start up, because it needs to install the
dependencies, but don't worry, this is a one-time process. Once the codespace is ready, you
can then launch the experiment in debug mode by running the following command in the terminal:

```bash
psynet debug local
```

Wait a moment, and then a browser window should open containing a link to the dashboard.
Click it, then enter 'admin' as both username and password, then press OK.
You'll now see the experiment dashboard.
Click 'Development', then 'New participant', to create a link to try the experiment
as a participant.

### Locally in a virtual environment

A more conventional approach is to instead run this experiment locally in a virtual environment.
This is more involved as you have to install several related dependencies like Redis and PostgreSQL.
To do so, navigate to the [PsyNet website](https://psynet.dev) and follow the 'virtual environment'
installation instructions. We recommend using Python 3.12.10 for this (or double-check the recommended
version of Python specified in the `pyproject.toml` file in the PsyNet source directory).

### Other options

It should also be possible to load this repository using Devcontainers in an IDE such as VSCode.
In theory, this should function equivalently to GitHub Codespaces. However, this hasn't worked
so reliably for us yet, and we're still figuring out how to make it work better.

## Dependencies

- `psynet`: PsyNet framework for running online experiments (installed from GitLab commit cbc7d5ae8cf5010266f89bcb4a84c68dc822e592)
- `mutagen==1.47.0`: For reading MP3 metadata (audio duration)

## Testing

The experiment includes comprehensive bot testing (using 5 bots) to verify:
- Each bot sees all 10 pieces exactly once
- Pieces are presented in randomized order (different orders across bots)
- Conditions are balanced across participants
- Stimuli are balanced across participants
- Each piece-condition combination (node) is balanced across participants