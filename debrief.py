from psynet.page import InfoPage


def debriefing():
    return InfoPage(
        """
        The purpose of this experiment was to investigate how listeners generate expectations about musical events.
        We played you musical pieces that had been altered accorded to various rules,
        and measured the extent to which you were surprised by the alterations.
        We plan to compare your responses to computational models that simulate listener expectations.

        Thank you for participating!
        """,
        time_estimate=30,
    )
