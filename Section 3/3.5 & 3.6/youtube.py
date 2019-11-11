import boto3

access_key = ""
access_secret = ""
region ="us-east-1"
queue_url = ""
client = boto3.client('sqs', aws_access_key_id = access_key, aws_secret_access_key = access_secret, region_name = region)
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def post_message(client, message_body, url):
     response = client.send_message(QueueUrl = url, MessageBody= message_body)

def lambda_handler(event, context):
    
    if event['session']['new']:
        on_start()
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event)
    elif event['request']['type'] == "IntentRequest":
        return intent_scheme(event)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_end()
    
def on_start():
    print("Session Started.")
def on_launch(event):
    onlaunch_MSG = "Hi welcome to the smart mirror"
    reprompt_MSG = "welcome to  vaishu's mirror!What can I help you with?"
    card_TEXT = "Mirror Mirror,what all can you do?."
    card_TITLE = "The Smart Mirror."
    return output_json_builder_with_reprompt_and_card(onlaunch_MSG, card_TEXT, card_TITLE, reprompt_MSG, False)
def on_end():
    print("Session Ended.")
def intent_scheme(event):
    
    intent_name = event['request']['intent']['name']
    
    if intent_name in ["AMAZON.NoIntent", "AMAZON.StopIntent", "AMAZON.CancelIntent"]:
        return stop_the_skill(event)
    elif intent_name == "take_a_picture":
        post_message(client, 'say cheese!', queue_url)
        message = "say cheese"
        speechlet = build_speechlet_response("Mirror Status", message, "Picture taken!", "false")
        return build_response({}, speechlet)
    elif intent_name == "play_breakfast_beats":
        post_message(client, 'BB', queue_url) 
        message = "Playing your Morning Playlist!"
        speechlet = build_speechlet_response("Mirror Status", message, "Playing Songs", "false")
        return build_response({}, speechlet)
def stop_the_skill(event):
    stop_MSG = "Thank you. Bye!"
    reprompt_MSG = ""
    card_TEXT = "Bye."
    card_TITLE = "Bye Bye."
    return output_json_builder_with_reprompt_and_card(stop_MSG, card_TEXT, card_TITLE, reprompt_MSG, True)

def plain_text_builder(text_body):
    text_dict = {}
    text_dict['type'] = 'PlainText'
    text_dict['text'] = text_body
    return text_dict
def reprompt_builder(repr_text):
    reprompt_dict = {}
    reprompt_dict['outputSpeech'] = plain_text_builder(repr_text)
    return reprompt_dict
    
def card_builder(c_text, c_title):
    card_dict = {}
    card_dict['type'] = "Simple"
    card_dict['title'] = c_title
    card_dict['content'] = c_text
    return card_dict
def response_field_builder_with_reprompt_and_card(outputSpeach_text, card_text, card_title, reprompt_text, value):
    speech_dict = {}
    speech_dict['outputSpeech'] = plain_text_builder(outputSpeach_text)
    speech_dict['card'] = card_builder(card_text, card_title)
    speech_dict['reprompt'] = reprompt_builder(reprompt_text)
    speech_dict['shouldEndSession'] = value
    return speech_dict
def output_json_builder_with_reprompt_and_card(outputSpeach_text, card_text, card_title, reprompt_text, value):
    response_dict = {}
    response_dict['version'] = '1.0'
    response_dict['response'] = response_field_builder_with_reprompt_and_card(outputSpeach_text, card_text, card_title, reprompt_text, value)
    return response_dict
