from psynet.bot import Bot
from psynet.modular_page import TimedPushButtonControl as BaseTimedPushButtonControl
from datetime import datetime


class TimedPushButtonControl(BaseTimedPushButtonControl):
    def __init__(self, choices, button_highlight_duration=0.75, bot_response=None):
        super().__init__(
            choices=choices,
            arrange_vertically=False,
            button_highlight_duration=button_highlight_duration,
            bot_response=bot_response,
        )

    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs["metadata"]["event_log"]
        participant = kwargs["participant"]

        if isinstance(participant, Bot):
            event_log.append({
            "eventType": "promptStart",
            "localTime": "2025-07-29T14:50:04.304Z",
            "info": None,
        })

        date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

        audio_start = [t['localTime'] for t in event_log if t['eventType'] == 'promptStart']
        audio_start_time = datetime.strptime(audio_start[0], date_format)

        push_button_events = [t for t in event_log if t['eventType'] == 'pushButtonClicked']
        push_button_choices = [t['info']['buttonId'] for t in push_button_events]

        push_button_times_absolute = [datetime.strptime(t['localTime'], date_format) for t in push_button_events]
        push_button_times_relative = [(p - audio_start_time).total_seconds() for p in push_button_times_absolute]

        return [
            {
                "choice": choice,
                "time": time
            }
            for choice, time in zip(push_button_choices, push_button_times_relative)
        ]
