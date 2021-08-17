SEARCH_MODAL_VIEW = {
	"type": "modal",
	"callback_id": "begin_search",
	"title": {
		"type": "plain_text",
		"text": "Seach Right Connections",
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
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": ":wave: Hey Ajinkya!\n\nKey in your search terms to help find the right connections!",
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "input",
			"block_id": "role",
			"optional": True,
			"label": {
				"type": "plain_text",
				"text": "Person's Role",
			},
			"element": {
				"type": "multi_external_select",
				"action_id": "role_select",
				"min_query_length": 0,
				"placeholder": {
					"type": "plain_text",
					"text": "Select your favorites",
				},
			}
		},
		{
			"type": "input",
			"block_id": "division",
			"optional": True,
			"element": {
				"type": "plain_text_input",
                "placeholder": {
					"type": "plain_text",
					"text": "Eg. Industries",
				},
				"action_id": "plain_text_input-action"
			},
			"label": {
				"type": "plain_text",
				"text": "Person's Team/Division",
			}
		},
		{
			"type": "input",
			"block_id": "keyword",
			"element": {
				"type": "plain_text_input",
                "placeholder": {
					"type": "plain_text",
					"text": "Eg. Insurance",
				},
				"action_id": "plain_text_input-action"
			},
			"label": {
				"type": "plain_text",
				"text": "Keyword / Topic",
			}
		},
	]
}