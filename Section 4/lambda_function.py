import logging.handlers
import requests
import uuid
import json

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer

from ask_sdk_model import IntentRequest
from ask_sdk_model.ui import PlayBehavior

from ask_sdk_model.interfaces.custom_interface_controller import (
    StartEventHandlerDirective, EventFilter, Expiration, FilterMatchAction,
    StopEventHandlerDirective,
    SendDirectiveDirective,
    Header,
    Endpoint,
    EventsReceivedRequest,
    ExpiredRequest
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
serializer = DefaultSerializer()
skill_builder = SkillBuilder()


@skill_builder.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):
    logger.info("== Launch Intent ==")

    response_builder = handler_input.response_builder

    system = handler_input.request_envelope.context.system
    api_access_token = system.api_access_token
    api_endpoint = system.api_endpoint

    # Get connected gadget endpoint ID.
    endpoints = get_connected_endpoints(api_endpoint, api_access_token)
    logger.debug("Checking endpoint..")
    if not endpoints:
        logger.debug("No connected gadget endpoints available.")
        return (response_builder
                .speak("No gadgets found. Please try again after connecting your gadget.")
                .set_should_end_session(True)
                .response)

    endpoint_id = endpoints[0]['endpointId']

    # Store endpoint ID for using it to send custom directives later.
    logger.debug("Received endpoints. Storing Endpoint Id: %s", endpoint_id)
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr['endpointId'] = endpoint_id
    session_attr['Logged']="False"

    
    return (response_builder
            .speak("Hi! I am Alphabet Tester. " +
                   "Place the tag and I will tell you which Alphabet it is and few fascinating facts about it. Are you ready?")
            .add_directive(build_test_alphabet_directive(endpoint_id,False))
            .set_should_end_session(False)
            .response)


@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.YesIntent"))
def yes_intent_handler(handler_input: HandlerInput):
    logger.info("YesIntent received. Starting game.")

    # Retrieve the stored gadget endpoint ID from the SessionAttributes.
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']
    logged=session_attr['Logged']
    # Create a token to be assigned to the EventHandler and store it
    # in session attributes for stopping the EventHandler later.
    token = str(uuid.uuid4())
    session_attr['token'] = token
    logger.info("Enetered value"+logged)
    response_builder = handler_input.response_builder
    if (logged=="True") :
        speechoutput="Place the tag again!"
    else :
        speechoutput="Place the tag "
    return (response_builder
            .speak(speechoutput)
            .add_directive(build_test_alphabet_directive(endpoint_id, True))
            .add_directive(build_start_event_handler_directive(token, 10000,
                                                               'Custom.AlphabetTester', 'ReportAlphabet',
                                                               FilterMatchAction.SEND_AND_TERMINATE,
                                                               {'data': "You didn't place the tag. Good bye!"}))
            .response)


@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def no_intent_handler(handler_input: HandlerInput):
    logger.info("Received NoIntent..Exiting.")

    # Retrieve the stored gadget endpointId from the SessionAttributes.
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']

    response_builder = handler_input.response_builder

    return (response_builder
            .speak("Alright. Good bye!")
            .add_directive(build_stop_test_directive(endpoint_id))
            .set_should_end_session(True)
            .response)


@skill_builder.request_handler(can_handle_func=is_request_type("CustomInterfaceController.EventsReceived"))
def custom_interface_event_handler(handler_input: HandlerInput):
    logger.info("== Received Custom Event ==")

    request = handler_input.request_envelope.request
    session_attr = handler_input.attributes_manager.session_attributes
    response_builder = handler_input.response_builder

    # Validate event handler token
    if session_attr['token'] != request.token:
        logger.info("EventHandler token doesn't match. Ignoring this event.")
        return (response_builder
                .speak("EventHandler token doesn't match. Ignoring this event.")
                .response)

    custom_event = request.events[0]
    payload = custom_event.payload
    namespace = custom_event.header.namespace
    name = custom_event.header.name

    if namespace == 'Custom.AlphabetTester' and name == 'ReportAlphabet':
        
        responses="is the Alphabet!"
        logged=session_attr['Logged']
        logger.info("Entered value :"+logged)
        logger.info("Before")
        logger.info(type(payload))
        logger.info(payload)
        alphabet=str(payload['alphabet'])
        if(alphabet=="Y"):
            responses="It is Y , The switch-hitter in the alphabet, y functions as both a vowel and a consonant , The Oxford English Dictionary actually calls it a semivowel because while the letter stops your breath in words such as yell and young—making it a consonant—it also creates an open vocal sound in words such as myth or hymn.Do you want to continue?"
            logged="True"
            session_attr['Logged']=logged
    return (response_builder
                .speak(responses)
                .set_should_end_session(False)
                .response)


    return response_builder.response


@skill_builder.request_handler(can_handle_func=is_request_type("CustomInterfaceController.Expired"))
def custom_interface_expiration_handler(handler_input):
    logger.info("== Custom Event Expiration Input ==")

    request = handler_input.request_envelope.request
    response_builder = handler_input.response_builder
    session_attr = handler_input.attributes_manager.session_attributes
    endpoint_id = session_attr['endpointId']

    # When the EventHandler expires, send StopLED directive to stop LED animation
    # and end skill session.
    return (response_builder
            .add_directive(build_stop_test_directive(endpoint_id))
            .speak(request.expiration_payload['data'])
            .set_should_end_session(True)
            .response)


@skill_builder.request_handler(can_handle_func=lambda handler_input:
                               is_intent_name("AMAZON.CancelIntent")(handler_input) or
                               is_intent_name("AMAZON.StopIntent")(handler_input))
def stop_and_cancel_intent_handler(handler_input):
    logger.info("Received a Stop or a Cancel Intent..")
    session_attr = handler_input.attributes_manager.session_attributes
    response_builder = handler_input.response_builder
    endpoint_id = session_attr['endpointId']

    if 'token' in session_attr.keys():
        logger.debug("Active session detected, sending stop EventHandlerDirective.")
        response_builder.add_directive(StopEventHandlerDirective(session_attr['token']))

    return (response_builder
            .speak("Alright, see you later.")
            .add_directive(build_stop_test_directive(endpoint_id))
            .set_should_end_session(True)
            .response)


@skill_builder.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    logger.info("Session ended with reason: " +
                handler_input.request_envelope.request.reason.to_str())
    return handler_input.response_builder.response


@skill_builder.exception_handler(can_handle_func=lambda i, e: True)
def error_handler(handler_input, exception):
    logger.info("==Error==")
    logger.error(exception, exc_info=True)
    return (handler_input.response_builder
            .speak("I'm sorry, something went wrong!").response)


@skill_builder.global_request_interceptor()
def log_request(handler_input):
    # Log the request for debugging purposes.
    logger.info("==Request==\r" +
                str(serializer.serialize(handler_input.request_envelope)))


@skill_builder.global_response_interceptor()
def log_response(handler_input, response):
    # Log the response for debugging purposes.
    logger.info("==Response==\r" + str(serializer.serialize(response)))
    logger.info("==Session Attributes==\r" +
                str(serializer.serialize(handler_input.attributes_manager.session_attributes)))


def get_connected_endpoints(api_endpoint, api_access_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(api_access_token)
    }

    api_url = api_endpoint + "/v1/endpoints"
    endpoints_response = requests.get(api_url, headers=headers)

    if endpoints_response.status_code == requests.codes['ok']:
        return endpoints_response.json()["endpoints"]


def build_test_alphabet_directive(endpoint_id,startGame):
    return SendDirectiveDirective(
        header=Header(namespace='Custom.AlphabetTester', name='TestTheAlphabet'),
        endpoint=Endpoint(endpoint_id=endpoint_id),
        payload={
            'startGame': startGame
        }
    )


def build_stop_test_directive(endpoint_id):
    return SendDirectiveDirective(
        header=Header(namespace='Custom.AlphabetTester', name='StopTest'),
        endpoint=Endpoint(endpoint_id=endpoint_id),
        payload={}
    )


def build_start_event_handler_directive(token, duration_ms, namespace,
                                        name, filter_match_action, expiration_payload):
    return StartEventHandlerDirective(
        token=token,
        event_filter=EventFilter(
            filter_expression={
                'and': [
                    {'==': [{'var': 'header.namespace'}, namespace]},
                    {'==': [{'var': 'header.name'}, name]}
                ]
            },
            filter_match_action=filter_match_action
        ),
        expiration=Expiration(
            duration_in_milliseconds=duration_ms,
            expiration_payload=expiration_payload))


def build_stop_event_handler_directive(token):
    return StopEventHandlerDirective(token=token)


lambda_handler = skill_builder.lambda_handler()
