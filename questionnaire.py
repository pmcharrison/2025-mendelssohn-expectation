import random

from psynet.modular_page import ModularPage, SurveyJSControl


def initial_questionnaire():
    return ModularPage(
        "questionnaire",
        prompt="Please answer the following questions about your musical experience and listening habits.",
        control=SurveyJSControl(
            design={
                "pages": [
                    {
                        "name": "demographics",
                        "elements": [
                            {
                                "type": "text",
                                "name": "age",
                                "title": "What is your age?",
                                "isRequired": True,
                                "inputType": "number"
                            },
                            {
                                "type": "radiogroup",
                                "name": "gender",
                                "title": "What is your gender?",
                                "isRequired": True,
                                "choices": [
                                    {"value": "male", "text": "Male"},
                                    {"value": "female", "text": "Female"},
                                    {"value": "non_binary", "text": "Non-binary"},
                                    {"value": "prefer_not_to_say", "text": "Prefer not to say"}
                                ]
                            }
                        ]
                    },
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
                                "title": "Which genre(s) do you predominantly listen to?",
                                "isRequired": True,
                                "visibleIf": "{listen_frequency} != 'never'"
                            }
                        ]
                    }
                ]
            },
            bot_response=generate_initial_questionnaire_bot_response,
        ),
        time_estimate=60,
        save_answer="initial_questionnaire",
    )


def generate_initial_questionnaire_bot_response():
    played_instrument = random.choice(["yes", "no"])
    listen_frequency = random.choice(["never", "<1", "1-2", "3-5", ">5"])

    response = {
        "age": str(random.randint(18, 80)),
        "gender": random.choice(["male", "female", "non_binary", "prefer_not_to_say"]),
        "played_instrument": played_instrument,
        "listen_frequency": listen_frequency,
    }

    if played_instrument == "yes":
        response["instrument_duration"] = random.choice(["<1", "1-3", "4-7", "8-12", ">12"])
        response["still_play"] = random.choice(["yes", "no"])

    if listen_frequency != "never":
        response["predominant_genre"] = random.choice([
            "Rock", "Pop", "Classical", "Jazz", "Electronic", "Hip-hop", "Country", "Blues"
        ])

    return response


def final_questionnaire():
    return ModularPage(
        "final_questionnaire",
        prompt="We just have a few final questions for you before the experiment concludes.",
        control=SurveyJSControl(
            design={
                "pages": [
                    {
                        "name": "surprise_source",
                        "elements": [
                            {
                                "type": "radiogroup",
                                "name": "most_surprised_by",
                                "isRequired": True,
                                "choices": [
                                    {"value": "melody", "text": "Melody"},
                                    {"value": "harmony", "text": "Harmony"},
                                    {"value": "equally", "text": "Equally"},
                                    {"value": "dont_know", "text": "Don't know enough about music to say"},
                                ]
                            },
                            {
                                "type": "comment",
                                "name": "general_strategy",
                                "title": "Please tell us a little about your strategy for completing the task.",
                                "isRequired": True,
                            }
                        ]
                    },
                    {
                        "name": "feedback",
                        "elements": [
                            {
                                "type": "comment",
                                "name": "experiment_feedback",
                                "title": "Do you have any feedback on the experiment?",
                                "isRequired": False
                            }
                        ]
                    }
                ]
            },
            bot_response=generate_final_questionnaire_bot_response,
        ),
        time_estimate=60,
        save_answer="final_questionnaire",
    )


def generate_final_questionnaire_bot_response():
    strategy_options = [
        "I focused on listening for unexpected changes in the music.",
        "I tried to identify moments that stood out from the rest of the piece.",
        "I listened for anything that sounded unusual or surprising.",
        "I paid attention to both melody and harmony to detect surprises.",
        "I focused on the overall musical flow and marked anything that disrupted it."
    ]
    feedback_options = [
        "The experiment was interesting.",
        "I enjoyed listening to the music.",
        "Some pieces were more surprising than others.",
        "",
        None
    ]
    return {
        "most_surprised_by": random.choice(["melody", "harmony", "equally", "dont_know"]),
        "general_strategy": random.choice(strategy_options),
        "experiment_feedback": random.choice(feedback_options)
    }
