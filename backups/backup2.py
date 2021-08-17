from collections import defaultdict
import os
import logging
from dotenv import load_dotenv
from pathlib import Path 
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from templates.search_modal_view import SEARCH_MODAL_VIEW
from templates.home_tab_view import HOME_TAB_VIEW
from templates.test_view import TEST_VIEW

# loading environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# logger in a global context
# requires importing logging
logging.basicConfig(level=logging.ERROR)

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

users_messages_count_dict = None
users_messages_dict = None
users_info_dict = None

# Listens to incoming messages that contain "hello"
@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click Me"},
                    "action_id": "button_click"
                }
            }
        ],
        text=f"Hey there <@{message['user']}>!"
    )


@app.action("button_click")
def action_button_click(body, ack, say):
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> clicked the button")


# Your listener will be called every time a block element with the action_id "approve_button" is triggered
@app.action("approve_button")
def update_message(ack):
    ack()
    # Update the message to reflect the action


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


def ack_shortcut(ack):
    ack()


@app.shortcut("open_search_modal")
def open_search_modal(ack, client, logger, body):
    # print(body)
    # {'type': 'shortcut', 'token': 'sXTZ5s0dz0ozfA50F7G94v3C', 'action_ts': '1628847754.898705', 'team': {'id': 'T02AE62LK0F', 'domain': 'salesforce-5nj8917'}, 'user': {'id': 'U02AV42PDA7', 'username': 'acbokade', 'team_id': 'T02AE62LK0F'}, 'is_enterprise_install': False, 'enterprise': None, 'callback_id': 'open_search_modal', 'trigger_id': '2378137698931.2354206699015.d1793b222942ed274c201b8c7a052eb1'}
    # open a modal
    ack()
    api_response = client.views_open(
        trigger_id=body["trigger_id"],
        view=SEARCH_MODAL_VIEW
    )
    #logger.debug(api_response)


# @app.action("begin_search")
# def button_click(logger, body, ack, respond):
#     # logger.info(body)
#     respond("respond!")
#     ack()

def search_messages(client, query):
    search_results = client.search_messages(token=os.environ.get("USER_TOKEN"), query=query)['messages']['matches']
    filtered_results = []
    for search_result in search_results:
        if search_result['type'] == 'message' and search_result['username'] != "the_right_connections" and "blocks" in search_result:
            filtered_results.append(search_result)
    return filtered_results


def users_messages_count(search_results):
    global users_messages_count_dict
    global users_messages_dict
    users_messages_dict = {}
    users_messages_count_dict = defaultdict(int)
    for message in search_results:
        user_id = message['user']
        if user_id not in users_messages_dict:
            users_messages_dict[user_id] = [message]
        else:
            users_messages_dict[user_id].append(message)
        users_messages_count_dict[user_id] += 1


def create_results_markdown(client):
    global users_messages_count_dict
    global users_info_dict
    blocks = []
    total_search_results = sum(list(users_messages_count_dict.values()))
    blocks.append(
        {
            "type": "section",
            "text": 
            {
				"type": "mrkdwn",
				"text": f"We found *{total_search_results} Connections* for Insurance, Product Management"
            },
        }
    )
    blocks.append(
        {
            "type": "divider"
        }
    )
    users_info_dict = {}
    for user_id, messages_count in users_messages_count_dict.items():
        user_messages = users_messages_dict[user_id]
        user_info = client.users_info(user=user_id)['user']
        users_info_dict[user_id] = user_info
        name = user_info['profile']['real_name']
        title = user_info['profile']['title']
        image = user_info['profile']['image_192']
        channel_ids = set()
        messages_perma_links = set()
        for user_message in user_messages:
            channel_id = user_message['channel']['id']
            channel_ids.add(channel_id)
            messages_perma_links.add(user_message['permalink'])
        channel_counts = len(channel_ids)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<fakeLink.toHotelPage.com|{name}>* | {title}"
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
                        "action_id": "posts_click",
                        "text": {
                            "type": "plain_text",
                            "text": f"{messages_count} Posts in"
                        },
                        "style": "primary",
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "action_id": "channel_click",
                        "text": {
                            "type": "plain_text",
                            "text": f"{channel_counts} Channels"
                        },
                        "style": "primary",
                        "value": "click_me_123"
                    }
                ]
		    }
        )
        # blocks.append(
        #     {
        #         "type": "section",
        #         "text": {
        #             "type": "mrkdwn",
        #             "text": f":people_holding_hands: <fakeLink.toHotelPage.com|3 Connections> :page_with_curl: <fakelink.toUrl.com|Member Enrollments Requirements> and <fakelink.toUrl.com|5 more>"
        #         }            
        #     }
        # )
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"\n\n\n:people_holding_hands: <fakeLink.toHotelPage.com|3 Connections> \n\n\n\n :page_with_curl: <fakelink.toUrl.com|Member Enrollments Requirements> and <fakelink.toUrl.com|5 more>"
                },
                "accessory": {
                    "type": "image",
                    "image_url": f"{image}",
                    "alt_text": "Display photo"
                }                
            }
        )
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
                        "text": "Location: Los Angeles, USA"
                    }
                ]
		    }
        )
        blocks.append(
            {
			    "type": "divider"
		    }
        )
    return blocks


channel_id = None


@app.action("open_posts")
def open_posts(ack, body, respond):
    ack()
    print(body)


@app.view("begin_search")
def submission(ack, body, client):
    print("inside submission before ack")
    ack()
    print("inside submission after ack")
    # print("**************")
    #print(body)
    role_block = body['view']['state']['values']['role']
    element_key = str(list(role_block.keys())[0])
    role = role_block[element_key]['selected_options'][0]['text']['text']
    division = body['view']['state']['values']['division']['plain_text_input-action']['value']
    keyword = body['view']['state']['values']['keyword']['plain_text_input-action']['value']
    print("************")
    search_results = search_messages(client, keyword)
    users_messages_count(search_results)
    # print(user_messages_dict)
    global users_messages_count_dict
    reverse_sorted_user_counts_dict = sorted(users_messages_count_dict.items(), key = lambda item: item[1])
    results_markdown = create_results_markdown(client)
    print(channel_id)
    #print(results_markdown)
    res = client.chat_postMessage(
        channel=channel_id,
        blocks=results_markdown,
        mrkdwn=True
    )
    print("########")
    print(res.__dict__)
    print("#########")


@app.command("/search-right-connections")
def handle_search_command(body, ack, respond, client, logger):
    # logger.info(body)
    global channel_id
    channel_id = body['channel_id']
    ack(
        text="Accepted!"
    )
    res = client.views_open(
        trigger_id=body["trigger_id"],
        view=SEARCH_MODAL_VIEW
    )
    # logger.info(res)


@app.action("posts_click")
def posts_button_click(body, ack, say, respond, client):
    # Acknowledge the action
    ack()
    # print(body)
    # say(f"<@{body['user']['id']}> clicked the button")
    global users_info_dict
    user_id = body['actions'][0]['block_id']
    user_info = users_info_dict[user_id]
    real_name = user_info['profile']['real_name']
    image = user_info['profile']['image_192']
    for message in users_messages_dict[user_id]:
        channel_name = message['channel']['name']
        message_text = message['text']
        message_link = message['permalink']
        # print(message)
        message_block = []
        msgs = message['blocks']
        for msg in msgs:
            message_block.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"#{channel_name}"
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
            message_block.append(msg)
        # client.views_open(
        #     trigger_id=body["trigger_id"],
        #     view={
        #         "type": "modal",
        #         "callback_id": "abc",
        #         "title": {
        #             "type": "plain_text",
        #             "text": "My App",
        #         },
        #         "submit": {
        #             "type": "plain_text",
        #             "text": "Submit",
        #         },
        #         "close": {
        #             "type": "plain_text",
        #             "text": "Cancel",
        #         },
        #         "blocks": message_block
        #     },
        # )
        res = respond(
            replace_original=False,
            blocks=message_block
        )
        print("%%%%%%%%%")
        print(res.__dict__)
        print("%%%%%%%%%%%")
    # respond(
    #     blocks=[
    #         {
    #             "type": "section",
    #             "block_id": "b",
    #             "text": {
    #                 "type": "mrkdwn",
    #                 "text": "You can add a button alongside text in your message. ",
    #             },
    #             "accessory": {
    #                 "type": "button",
    #                 "action_id": "a",
    #                 "text": {"type": "plain_text", "text": "Button"},
    #                 "value": "click_me_123",
    #             },
    #         }
    #     ]
    # )

@app.action("channel_click")
def channels_button_click(body, ack, say, respond, client):
    # Acknowledge the action
    ack()
    user_id = body['actions'][0]['block_id']
    global users_info_dict
    user_info = users_info_dict[user_id]
    real_name = user_info['profile']['real_name']
    messages = users_messages_dict[user_id]
    channel_set = set()
    channels_block = []
    for message in messages:
        channel_name = message['channel']['name']
        channel_set.add(channel_name)
    channels_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Channels where <@{user_id}> posted"
                }
            }
        )
    for channel_name in channel_set:
        channels_block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"#{channel_name}"
                }
            }
        )
    respond (
        replace_original=False,
        blocks=channels_block
    )






@app.command("/hello-bolt-python")
def handle_command(body, ack, respond, client, logger):
    logger.info(body)
    ack(
        text="Accepted!",
        blocks=[
            {
                "type": "section",
                "block_id": "b",
                "text": {
                    "type": "mrkdwn",
                    "text": ":white_check_mark: Accepted!",
                },
            }
        ],
    )

    respond(
        blocks=[
            {
                "type": "section",
                "block_id": "b",
                "text": {
                    "type": "mrkdwn",
                    "text": "You can add a button alongside text in your message. ",
                },
                "accessory": {
                    "type": "button",
                    "action_id": "a",
                    "text": {"type": "plain_text", "text": "Button"},
                    "value": "click_me_123",
                },
            }
        ]
    )

    res = client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "view-id",
            "title": {
                "type": "plain_text",
                "text": "My App",
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit",
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
            },
            "blocks": [
                {
                    "type": "input",
                    "element": {"type": "plain_text_input"},
                    "label": {
                        "type": "plain_text",
                        "text": "Label",
                    },
                },
                {
                    "type": "input",
                    "block_id": "es_b",
                    "element": {
                        "type": "external_select",
                        "action_id": "es_a",
                        "placeholder": {"type": "plain_text", "text": "Select an item"},
                        "min_query_length": 0,
                    },
                    "label": {"type": "plain_text", "text": "Search"},
                },
                {
                    "type": "input",
                    "block_id": "mes_b",
                    "element": {
                        "type": "multi_external_select",
                        "action_id": "mes_a",
                        "placeholder": {"type": "plain_text", "text": "Select an item"},
                        "min_query_length": 0,
                    },
                    "label": {"type": "plain_text", "text": "Search (multi)"},
                },
            ],
        },
    )
    logger.info(res)


@app.options("es_a")
def show_options(ack):
    ack(
        {"options": [{"text": {"type": "plain_text", "text": "Maru"}, "value": "maru"}]}
    )


@app.options("mes_a")
def show_multi_options(ack):
    ack(
        {
            "option_groups": [
                {
                    "label": {"type": "plain_text", "text": "Group 1"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Option 1"},
                            "value": "1-1",
                        },
                        {
                            "text": {"type": "plain_text", "text": "Option 2"},
                            "value": "1-2",
                        },
                    ],
                },
                {
                    "label": {"type": "plain_text", "text": "Group 2"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Option 1"},
                            "value": "2-1",
                        },
                    ],
                },
            ]
        }
    )


@app.view("view-id")
def view_submission(ack, body, logger):
    ack()
    print("*********")
    # print(body)
    print("************")
    logger.info(body["view"]["state"]["values"])


@app.action("a")
def button_click(ack, body, respond):
    ack()

    user_id = body["user"]["id"]
    # in_channel / dict
    respond(
        {
            "response_type": "in_channel",
            "replace_original": False,
            "text": f"<@{user_id}> clicked a button! (in_channel)",
        }
    )
    # ephemeral / kwargs
    respond(
        replace_original=False,
        text=":white_check_mark: Done!",
    )


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi <{user_id}>!")






@app.command("/hello-bolt-dialog")
def test_command(body, client, ack, logger):
    logger.info(body)
    ack("I got it!")
    res = client.dialog_open(
        trigger_id=body["trigger_id"],
        dialog={
            "callback_id": "dialog-callback-id",
            "title": "Request a Ride",
            "submit_label": "Request",
            "notify_on_cancel": True,
            "state": "Limo",
            "elements": [
                {"type": "text", "label": "Pickup Location", "name": "loc_origin"},
                {
                    "type": "text",
                    "label": "Dropoff Location",
                    "name": "loc_destination",
                },
                {
                    "label": "Type",
                    "name": "types",
                    "type": "select",
                    "data_source": "external",
                },
            ],
        },
    )
    logger.info(res)


@app.action("dialog-callback-id")
def dialog_submission_or_cancellation(ack, body):
    if body["type"] == "dialog_cancellation":
        # This can be sent only when notify_on_cancel is True
        ack()
        return

    errors = []
    submission = body["submission"]
    if len(submission["loc_origin"]) <= 3:
        errors = [
            {
                "name": "loc_origin",
                "error": "Pickup Location must be longer than 3 characters",
            }
        ]
    if len(errors) > 0:
        # or ack({"errors": errors})
        ack(errors=errors)
    else:
        ack()





# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()