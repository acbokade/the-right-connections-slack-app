from collections import defaultdict
import os
import logging
import time
from dotenv import load_dotenv
from pathlib import Path 
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.logger import messages
from slack_bolt.context.ack.ack import Ack
from templates.search_modal_view import SEARCH_MODAL_VIEW
from templates.home_tab_view import HOME_TAB_VIEW
from templates.test_view import TEST_VIEW
from templates.pagination_button_view import PAGINATION_VIEW, NEXT_VIEW, PREVIOUS_VIEW
from templates.pagination_channel_view import PAGINATION_CHANNEL_VIEW, NEXT_CHANNEL_VIEW, PREVIOUS_CHANNEL_VIEW

from rake_nltk import Rake
from sentence_transformers import SentenceTransformer
from numpy import dot, vectorize
from numpy.linalg import norm

import re
import pickle

model = SentenceTransformer('sentence-transformers/bert-base-nli-mean-tokens')
vectorizer = vectorizer = pickle.load(open("vectorizer", 'rb'))
question_model = pickle.load(open("interrogative_model", 'rb'))

# loading environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# logger in a global contextd
# requires importing logging
logging.basicConfig(level=logging.ERROR)

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

users_messages_count_dict = None
users_messages_dict = None
users_info_dict = None
messages_ts = None
messages_per_page = 1
start = 0
end = None
msgs_count = None
user_id = None
channel_id = None
role = None
division = None 
keyword = None
user_ids = None
# channels_per_page = 1
# channels_ts = None
# channel_page_start = 0
# channel_page_end = 0
# channels_list = None


@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        # Call views.publish with the built-in client
        client.views_publish(
            # Use the user ID associated with the event
            user_id=event["user"],
            # Home tabs must be enabled in your app configuration
            view=HOME_TAB_VIEW
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


@app.shortcut("open_search_modal")
def open_search_modal(ack, client, logger, body):
    # {'type': 'shortcut', 'token': 'sXTZ5s0dz0ozfA50F7G94v3C', 'action_ts': '1628847754.898705', 'team': {'id': 'T02AE62LK0F', 'domain': 'salesforce-5nj8917'}, 'user': {'id': 'U02AV42PDA7', 'username': 'acbokade', 'team_id': 'T02AE62LK0F'}, 'is_enterprise_install': False, 'enterprise': None, 'callback_id': 'open_search_modal', 'trigger_id': '2378137698931.2354206699015.d1793b222942ed274c201b8c7a052eb1'}
    # open a modal
    ack()
    api_response = client.views_open(
        trigger_id=body["trigger_id"],
        view=SEARCH_MODAL_VIEW
    )
    #logger.debug(api_response)


def create_results_markdown(client):
    start_time = time.time()
    global users_messages_count_dict
    global users_info_dict
    global role 
    global division
    global keyword 
    display_role = ''
    display_division = ''
    display_keyword = ''
    if len(role) > 0:
        if len(role) == 1:
            display_role += role[0]
        else:
            display_role = '['
            for idx in range(len(role)):
                if idx == len(role) - 1:
                    display_role += role[idx]
                else:
                    display_role += f"{role[idx]}, "
            display_role += ']'
    if division is not None:
        if len(display_role) > 0:
            display_division = f", {division}" 
        else:
            display_division = division
    if len(display_role) > 0 or len(display_division) > 0:
        display_keyword = f", {keyword}"
    else:
        display_keyword = f"{keyword}"
    blocks = []
    connections_count = len(users_messages_count_dict)
    # total_search_results = sum(list(users_messages_count_dict.values()))
    blocks.append(
        {
            "type": "section",
            "text": 
            {
				"type": "mrkdwn",
				"text": f"We found *{connections_count} connections* for {display_role}{display_division}{display_keyword}"
            },
        }
    )
    blocks.append(
        {
            "type": "divider"
        }
    )
    for user_id, tuple_count in users_messages_count_dict.items():
        messages_count, similarity = tuple_count
        user_messages = users_messages_dict[user_id]
        # s_time = time.time()
        # user_info = client.users_info(user=user_id)['user']
        # e_time = time.time()
        # print(f"client.users_info call inside create_results_markdown time taken: {e_time - s_time}")
        # users_info_dict[user_id] = user_info
        user_info = users_info_dict[user_id]
        # name = user_info['profile']['real_name']
        title = user_info['profile']['title']
        image = user_info['profile']['image_192']
        channel_ids = set()
        for user_message in user_messages:
            channel_id = user_message['channel']['id']
            channel_ids.add(channel_id)
        channel_counts = len(channel_ids)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<@{user_id}> | {title}"
                }
		    },
        )
        # blocks.append(
        #     {
        #         "type": "section",
        #         "text": {
        #             "type": "mrkdwn",
        #             "text": f"<@{user_id}> | {title}"
        #         },
        #         "accessory": {
        #             "type": "image",
        #             "image_url": f"{image}",
        #             "alt_text": "Display photo"
        #         }    
		#     }
        # )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://api.slack.com/img/blocks/bkb_template_images/tripAgentLocationMarker.png",
                        "alt_text": "Location Pin Icon"
                    },
                    {
                        "type": "plain_text",
                        "text": "Location: Bangalore, India"
                    }
                ]
		    }
        )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":people_holding_hands: <fakeLink.toHotelPage.com|3 Connections>"
                }            
            }
        )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":page_with_curl: <fakelink.toUrl.com|Member Enrollments Requirements> and <fakelink.toUrl.com|5 more>"
                }            
            }
        )
        blocks.append(
            {
			    "type": "section",
			    "text": {
                    "type": "mrkdwn",
                    "text": f"*{messages_count} Posts in {channel_counts} Channels*"
			    }
            }
        )
        blocks.append(
            {
                "type": "actions",
                "block_id": f"{user_id}",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "view_posts",
                        "text": {
                            "type": "plain_text",
                            "text": "View posts",
                        },
                        "style": "primary",
                        "value": "click_me_123"
                    }
                ]
		    }
        )
        blocks.append(
            {
			    "type": "divider"
		    }
        )
    end_time = time.time()
    #print(f"create_results_markdown method time taken: {end_time - start_time}")
    return blocks


@app.command("/search-right-connections")
def handle_search_command(ack, body, client):
    start_time = time.time()
    ack()
    res = client.views_open(
        trigger_id=body["trigger_id"],
        view=SEARCH_MODAL_VIEW
    )
    global channel_id
    global user_ids
    global users_info_dict
    global role
    role = None
    global division
    division = None
    users_info_dict = {}
    channel_id = body['channel_id']
    for user_id in user_ids:
        user_info = client.users_info(user=user_id)['user']
        users_info_dict[user_id] = user_info
    # logger.info(body)
    # logger.info(res)
    end_time = time.time()
    #print(f"Search command time taken: {end_time - start_time}")


@app.view("begin_search")
def submission(ack, body, client):
    #print("enter")
    ack()
    #print("ack")
    start_time = time.time()
    global messages_ts
    global division
    global role
    global keyword
    messages_ts = None

    role_block = body['view']['state']['values']['role']
    element_key = str(list(role_block.keys())[0])
    role = []
    if len(role_block[element_key]['selected_options']) != 0:
        for idx in range(len(role_block[element_key]['selected_options'])):
            role.append(role_block[element_key]['selected_options'][idx]['text']['text'])
    #print(role)
    division = body['view']['state']['values']['division']['plain_text_input-action']['value']
    keyword = body['view']['state']['values']['keyword']['plain_text_input-action']['value']
    #search_results = search_messages(client, keyword)

    rake_var = Rake(max_length=2)
    rake_var.extract_keywords_from_text(keyword)

    key_phrases = rake_var.get_ranked_phrases()

    key_phrases = [word for phrase in key_phrases for word in phrase.split() ]
    #print(key_phrases)
    search_results = [message for phrase in key_phrases for message in search_messages(client, phrase)]
    search_results = calculate_similarity(search_results, keyword)
    #print(search_results)

    users_messages_count_and_filter_by_role(search_results)
    global users_messages_count_dict
    users_messages_count_dict = dict(sorted(users_messages_count_dict.items(), key = lambda item: -item[1][1]))
    results_markdown = create_results_markdown(client)
    res = client.chat_postMessage(
        channel=channel_id,
        blocks=results_markdown,
        mrkdwn=True
    )
    end_time = time.time()
    #print(f"Begin search time taken: {end_time - start_time}")

def calculate_similarity(search_results, input_sentence):
    input_embedding = model.encode(input_sentence)
    for message in search_results:
        if message['type'] != 'message' or message['username'] == "the_right_connections" or "blocks" not in message:
            continue
        text = message['text']
        text = text.replace('\n', '')
        text = text.replace('\t', '')
        #replace emojis in text
         #TODO replace links
        text = re.sub("(?s):.*?:", "",text) 


        message['is_question']=is_interrogative([text])
        print(keyword)
        print(text)
        print(message['is_question'])
        message_embedding = model.encode(text)

        #print(input_embedding.shape)
        #print(message_embedding.shape)
        #input_embedding.reshape(-1,1)
        #message_embedding.reshape(-1,1)
        #cos_sim = dot(a, b)/(norm(a)*norm(b))
        cosine_similarity = dot(message_embedding, input_embedding)/(norm(input_embedding)*norm(message_embedding))
        print(cosine_similarity)
        #if similarity is greater than a threshold and quesion is interrogative, replace message with reply.



        # if cosine_similarity>0.7:
        #     message = get_best_reply(message['channel'], message['ts'])
            
        message['sentence_similarity'] = cosine_similarity

    return search_results


def is_interrogative(input):

    res = question_model.predict(vectorizer.transform(input))
    return (res[0]=='whQuestion' or res[0]=='ynQuestion')


# def get_best_reply(client, channel, ts):
#     replies = client.conversations_replies(token=os.environ.get("USER_TOKEN"),channel=channel, ts=ts)['messages']
#     for reply in reply['messages']:
#         reactions = client.reactions.get(channel=channel, ts=reply['ts'])



def search_messages(client, query):
    start_time = time.time()
    search_results = client.search_messages(token=os.environ.get("USER_TOKEN"), query=query)['messages']['matches']
    end_time = time.time()
    #print(f"Search messages API call time taken: {end_time - start_time}")
    # filtered_results = []
    # for search_result in search_results:
    #     if search_result['type'] == 'message' and search_result['username'] != "the_right_connections" and "blocks" in search_result:
    #         filtered_results.append(search_result)
    # return filtered_results
    return search_results


def users_messages_count_and_filter_by_role(search_results):
    start_time = time.time()
    global users_messages_count_dict
    global users_messages_dict
    global role
    users_messages_dict = {}
    users_messages_count_dict = defaultdict(lambda: (0, 0.0))
    for message in search_results:
        if message['type'] != 'message' or message['username'] == "the_right_connections" or "blocks" not in message:
            continue
        user_id = message['user']
        user_info = users_info_dict[user_id]
        profile_title = user_info['profile']['title']
        user_role = None 
        user_division = None
        #profile_title)
        if len(profile_title) != 0:
            user_role, user_division = profile_title.split(', ')
        # print(user_role, role)
        role = [r.strip() for r in role]
        user_role = user_role.strip()
        if len(role) != 0 and user_role is not None and user_role not in role:
            continue 
        if (division is not None) and user_division is not None and division != user_division:
            continue
        if user_id not in users_messages_dict:
            users_messages_dict[user_id] = [message]
        else:
            users_messages_dict[user_id].append(message)
        count, similarity = users_messages_count_dict[user_id]
        users_messages_count_dict[user_id] = (count+1, max(similarity, message['sentence_similarity']))
    end_time = time.time()
    #print(f"users_messages_count_and_filter_by_role method time taken: {end_time - start_time}")


@app.action("view_posts")
def view_posts(body, ack, say, respond, client):
    # Acknowledge the action
    ack()
    start_time = time.time()
    global users_info_dict
    global messages_ts
    global user_id
    user_id = body['actions'][0]['block_id']
    user_info = users_info_dict[user_id]
    # real_name = user_info['profile']['real_name']
    image = user_info['profile']['image_192']

    total_msgs = users_messages_dict[user_id]
    global msgs_count
    msgs_count = len(total_msgs)
    # start: start+messages_per_page
    global start
    start = 0
    global end
    global messages_per_page
    end = min(start+messages_per_page, msgs_count)
    msgs = total_msgs[start:end]
    for message in msgs:
        channel_name = message['channel']['name']
        message_text = message['text']
        message_link = message['permalink']
        message_block = []
        #print(channel_name)
        # msg = message['blocks'][0]
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Posted in # {channel_name}"
                }
            }
        )
        message_block.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": f"{image}",
                        "alt_text": "User display picture"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}>"
                    }
                ]
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{message_text}"
                }
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{message_link}|Go to message>*"
                }
            }
        )
        # message_block.append(msg)
        if start == 0 and end == msgs_count:
            pass
        elif end == msgs_count:
            message_block.append(PREVIOUS_VIEW)
        elif start == 0:
            message_block.append(NEXT_VIEW)
        else:
            message_block.append(PAGINATION_VIEW)
        if messages_ts is not None:
            res = client.chat_update(
                channel=channel_id,
                ts=messages_ts,
                blocks=message_block,
                mrkdwn=True
            )
        else:
            res = client.chat_postMessage(
                channel=channel_id,
                blocks=message_block,
                mrkdwn=True
            )
            messages_ts = res.__dict__['data']['message']['ts']
    end_time = time.time()
    #f"View posts time taken: {end_time - start_time}")


@app.action("next_page")
def message_next_page(body, ack, say, respond, client):
    # Acknowledge the action
    ack()
    global messages_ts
    global start
    global end
    global messages_per_page
    global user_id
    global users_messages_dict
    user_info = users_info_dict[user_id]
    image = user_info['profile']['image_192']

    total_msgs = users_messages_dict[user_id]
    msgs_count = len(total_msgs)
    # start: start+messages_per_page
    start = end
    end = min(start+messages_per_page, msgs_count)
    msgs = total_msgs[start:end]
    for message in msgs:
        channel_name = message['channel']['name']
        message_text = message['text']
        message_link = message['permalink']
        # print(message)
        message_block = []
        msg = message['blocks'][0]
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Posted in # {channel_name}"
                }
            }
        )
        message_block.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": f"{image}",
                        "alt_text": "User display picture"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}>"
                    }
                ]
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{message_text}"
                }
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{message_link}|Go to message>*"
                }
            }
        )
        # message_block.append(msg)
        if start == 0 and end == msgs_count:
            pass
        elif end == msgs_count:
            message_block.append(PREVIOUS_VIEW)
        elif start == 0:
            message_block.append(NEXT_VIEW)
        else:
            message_block.append(PAGINATION_VIEW)
        res = client.chat_update(
            channel=channel_id,
            ts=messages_ts,
            blocks=message_block,
            mrkdwn=True
        )


@app.action("previous_page")
def message_previous_page(body, ack, say, respond, client):
    # Acknowledge the action
    ack()
    global messages_ts
    global start
    global end
    global messages_per_page
    global user_id
    global users_messages_dict
    user_info = users_info_dict[user_id]
    image = user_info['profile']['image_192']

    total_msgs = users_messages_dict[user_id]
    msgs_count = len(total_msgs)
    # start: start+messages_per_page
    end = start
    start = max(0, end-messages_per_page)
    msgs = total_msgs[start:end]
    for message in msgs:
        channel_name = message['channel']['name']
        message_text = message['text']
        message_link = message['permalink']
        # print(message)
        message_block = []
        # msg = message['blocks'][0]
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Posted in # {channel_name}"
                }
            }
        )
        message_block.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": f"{image}",
                        "alt_text": "User display picture"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}>"
                    }
                ]
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{message_text}"
                }
            }
        )
        message_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{message_link}|Go to message>*"
                }
            }
        )
        # message_block.append(msg)
        if start == 0 and end == msgs_count:
            pass
        elif end == msgs_count:
            message_block.append(PREVIOUS_VIEW)
        elif start == 0:
            message_block.append(NEXT_VIEW)
        else:
            message_block.append(PAGINATION_VIEW)
        res = client.chat_update(
            channel=channel_id,
            ts=messages_ts,
            blocks=message_block,
            mrkdwn=True
        )


# @app.action("channel_click")
# def channels_button_click(body, ack, say, respond, client):
#     # Acknowledge the action
#     ack()
#     global user_id
#     user_id = body['actions'][0]['block_id']
#     global users_info_dict
#     global channels_ts
#     global channels_list
#     global channel_start
#     global channel_end
#     global channels_per_page
#     user_info = users_info_dict[user_id]
#     real_name = user_info['profile']['real_name']
#     messages = users_messages_dict[user_id]
#     channel_set = set()
#     channels_block = []
#     for message in messages:
#         channel_name = message['channel']['name']
#         channel_set.add(channel_name)
#     channels_list = list(channel_set)
#     total_channels_count = len(channels_list)
#     channel_start = 0
#     channel_end = min(total_channels_count, channel_start+channels_per_page)
#     cur_channels = channels_list[channel_start:channel_end]
#     channels_block.append(
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": f"Channels where <@{user_id}> posted"
#             }
#         }
#     )
#     for channel_name in cur_channels:
#         channels_block.append(
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": f"#{channel_name}"
#                 }
#             }
#         )
#     if start == 0 and end == total_channels_count:
#         pass
#     elif end == total_channels_count:
#         channels_block.append(PREVIOUS_CHANNEL_VIEW)
#     elif start == 0:
#         channels_block.append(NEXT_CHANNEL_VIEW)
#     else:
#         channels_block.append(PAGINATION_CHANNEL_VIEW)
#     # respond (
#     #     replace_original=False,
#     #     blocks=channels_block
#     # )
#     if channels_ts is not None:
#         res = client.chat_update(
#             channel=channel_id,
#             ts=channels_ts,
#             blocks=channels_block,
#             mrkdwn=True
#         )
#     else:
#         res = client.chat_postMessage(
#             channel=channel_id,
#             blocks=channels_block,
#             mrkdwn=True
#         )
#         # print("%%%%%%%%%")
#         # print(res.__dict__)
#         # print("%%%%%%%%%%%")
#         channels_ts = res.__dict__['data']['message']['ts']


# @app.action("next_channel")
# def channel_next_page(body, ack, say, respond, client):
#     # Acknowledge the action
#     ack()
#     global user_id
#     global users_info_dict
#     global channels_ts
#     global channels_list
#     global channel_start
#     global channel_end
#     global channels_per_page
#     user_info = users_info_dict[user_id]
#     real_name = user_info['profile']['real_name']
#     total_channels_count = len(channels_list)
#     channel_start = channel_end
#     channel_end = min(total_channels_count, channel_start+channels_per_page)
#     cur_channels = channels_list[channel_start:channel_end]
#     channels_block = []
#     channels_block.append(
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": f"Channels where <@{user_id}> posted"
#             }
#         }
#     )
#     for channel_name in cur_channels:
#         channels_block.append(
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": f"#{channel_name}"
#                 }
#             }
#         )
#     if channel_start == 0 and channel_end == total_channels_count:
#         pass
#     elif channel_end == total_channels_count:
#         channels_block.append(PREVIOUS_CHANNEL_VIEW)
#     elif channel_start == 0:
#         channels_block.append(NEXT_CHANNEL_VIEW)
#     else:
#         channels_block.append(PAGINATION_CHANNEL_VIEW)
#     # respond (
#     #     replace_original=False,
#     #     blocks=channels_block
#     # )
#     res = client.chat_update(
#         channel=channel_id,
#         ts=channels_ts,
#         blocks=channels_block,
#         mrkdwn=True
#     )
#     # print("%%%%%%%%%")
#     # print(res.__dict__)
#     # print("%%%%%%%%%%%")
#     # channels_ts = res.__dict__['data']['message']['ts']


# @app.action("previous_channel")
# def channel_previous_page(body, ack, say, respond, client):
#     # Acknowledge the action
#     ack()
#     global user_id
#     global users_info_dict
#     global channels_ts
#     global channels_list
#     global channel_start
#     global channel_end
#     global channels_per_page
#     user_info = users_info_dict[user_id]
#     real_name = user_info['profile']['real_name']
#     total_channels_count = len(channels_list)
#     channel_end = channel_start
#     channel_start = max(0, channel_end-channels_per_page)
#     cur_channels = channels_list[channel_start:channel_end]
#     channels_block = []
#     channels_block.append(
#         {
#             "type": "section",
#             "text": {
#                 "type": "mrkdwn",
#                 "text": f"Channels where <@{user_id}> posted"
#             }
#         }
#     )
#     for channel_name in cur_channels:
#         channels_block.append(
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": f"#{channel_name}"
#                 }
#             }
#         )
#     if channel_start == 0 and channel_end == total_channels_count:
#         pass
#     elif channel_end == total_channels_count:
#         channels_block.append(PREVIOUS_CHANNEL_VIEW)
#     elif channel_start == 0:
#         channels_block.append(NEXT_CHANNEL_VIEW)
#     else:
#         channels_block.append(PAGINATION_CHANNEL_VIEW)
#     # respond (
#     #     replace_original=False,
#     #     blocks=channels_block
#     # )
#     res = client.chat_update(
#         channel=channel_id,
#         ts=channels_ts,
#         blocks=channels_block,
#         mrkdwn=True
#     )
#     # print("%%%%%%%%%")
#     # print(res.__dict__)
#     # print("%%%%%%%%%%%")
#     # channels_ts = res.__dict__['data']['message']['ts']


# @app.options("role_select")
# def role_options_select(ack, body):
#     keyword = body.get("value")
#     print(keyword)
#     if keyword is not None and len(keyword) > 0:
#         options = [o for o in all_options if keyword in o["text"]["text"]]
#         ack(options=options)
#     else:
#         print("all")
#         ack(options=all_options)


all_options = [
    {
        "text": {
            "type": "plain_text",
            "text": "Product Manager ",
        },
        "value": "value-0"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Developer",
        },
        "value": "value-1"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "UX Designer",
        },
        "value": "value-2"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Architect",
        },
        "value": "value-3"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Manager",
        },
        "value": "value-4"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Technical Writer",
        },
        "value": "value-5"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Consultant",
        },
        "value": "value-6"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "Sales",
        },
        "value": "value-7"
    }
]

# Start your app
if __name__ == "__main__":
    user_ids = ['U02AV42PDA7', 'U02ART4DY85', "U02AUTXK8LS", "U02AE6D8G07"]
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()