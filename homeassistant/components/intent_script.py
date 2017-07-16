"""Handle intents with scripts."""
import asyncio
import copy
import logging

import voluptuous as vol

from homeassistant.helpers import (
    intent, template, script, config_validation as cv)

DOMAIN = 'intent_script'

CONF_INTENTS = 'intents'
CONF_SPEECH = 'speech'

CONF_ACTION = 'action'
CONF_CARD = 'card'
CONF_TYPE = 'type'
CONF_TITLE = 'title'
CONF_CONTENT = 'content'
CONF_TEXT = 'text'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: {
        cv.string: {
            vol.Optional(CONF_ACTION): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_CARD): {
                vol.Optional(CONF_TYPE, default='simple'): cv.string,
                vol.Required(CONF_TITLE): cv.template,
                vol.Required(CONF_CONTENT): cv.template,
            },
            vol.Optional(CONF_SPEECH): {
                vol.Optional(CONF_TYPE, default='plain'): cv.string,
                vol.Required(CONF_TEXT): cv.template,
            }
        }
    }
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
def async_setup(hass, config):
    """Activate Alexa component."""
    intents = copy.deepcopy(config[DOMAIN])
    template.attach(hass, intents)

    for intent_type, conf in intents.items():
        if CONF_ACTION in conf:
            conf[CONF_ACTION] = script.Script(
                hass, conf[CONF_ACTION],
                "Intent Script {}".format(intent_type))
        intent.async_register(hass, ScriptIntentHandler(intent_type, conf))

    return True


class ScriptIntentHandler(intent.IntentHandler):
    """Respond to an intent with a script."""

    def __init__(self, intent_type, config):
        """Initialize the script intent handler."""
        self.intent_type = intent_type
        self.config = config

    @asyncio.coroutine
    def async_handle(self, intent_obj):
        """Handle the intent."""
        speech = self.config.get(CONF_SPEECH)
        card = self.config.get(CONF_CARD)
        action = self.config.get(CONF_ACTION)
        slots = {key: value['value'] for key, value
                 in intent_obj.slots.items()}

        if action is not None:
            yield from action.async_run(slots)

        response = intent_obj.create_response()

        if speech is not None:
            response.async_set_speech(speech[CONF_TEXT].async_render(slots),
                                      speech[CONF_TYPE])

        if card is not None:
            response.async_set_card(
                card[CONF_TITLE].async_render(slots),
                card[CONF_CONTENT].async_render(slots),
                card[CONF_TYPE])

        return response