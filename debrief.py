from markupsafe import Markup
from psynet.page import InfoPage


def debriefing():
    return InfoPage(
        Markup(
            """
            <h2>Debriefing</h2>

            <p style="font-weight: bold;">
            If you would like to learn more about the experiment, please read the debriefing below.
            Otherwise, please click 'Next' to continue.
            </p>

            <p>
            The purpose of this experiment was to investigate how listeners generate expectations about musical events.
            We played you musical pieces that had been altered accorded to various rules,
            and measured the extent to which you were surprised by the alterations.
            We plan to compare your responses to computational models that simulate listener expectations.
            </p>

            <p>
            In case you're interested, the musical excerpts were compositions by Felix Mendelssohn,
            specifically 'Songs without Words'.
            Here's a Spotify link: <a href="https://open.spotify.com/album/6kTJByn4wdXsUtdswvpxUq?si=eT1830fMSdScs0yx1X_ZbA" target="_blank" rel="noopener noreferrer">Songs without Words</a>.
            </p>

            <p>
            Thank you for participating!
            </p>
            """
        ),
        time_estimate=30,
    )
