import json
import unittest

from oxy.apis.企微.ai_bot.msg_model import BotRequestMsg


class WecomMsgModelTestCase(unittest.TestCase):
    def test_text_message(self):
        sample_data = {
            "msgid": "CAIQ16HMjQYY/NGagIOAgAMgq4KM0AI=",
            "create_time": 12312312,
            "aibotid": "AIBOTID",
            "chatid": "CHATID",
            "chattype": "group",
            "from": {
                "userid": "USERID",
            },
            "response_url": "RESPONSEURL",
            "msgtype": "text",
            "text": {
                "content": "@RobotA hello robot",
            },
            "quote": {
                "msgtype": "text",
                "text": {
                    "content": "这是今日的测试情况",
                },
            },
        }
        event = BotRequestMsg.model_validate_json(json.dumps(sample_data))
        self.assertEqual(event.msg.msg_type, 'text')
        self.assertEqual(event.msg.msg_content.content, '@RobotA hello robot')
        self.assertEqual(event.from_.userid, 'USERID')

    def test_event_message(self):
        sample_data = {
            "msgid": "20da0b8c9f81ecd2d1462dbf17ae850e",
            "create_time": 1776302411,
            "aibotid": "AIBOTID",
            "chatid": "CHATID",
            "chattype": "group",
            "from": {
                "userid": "USERID",
            },
            "response_url": "RESPONSEURL",
            "msgtype": "event",
            "event": {
                "eventtype": "template_card_event",
                "template_card_event": {
                    "card_type": "vote_interaction",
                    "event_key": "button_replace_text",
                    "task_id": "fBmjTL7ErRCQSNA6GZKMlcFiWX1shOvg",
                    "selected_items": {
                        "selected_item": [
                            {
                                "question_key": "button_selection_key1",
                                "option_ids": {
                                    "option_id": [
                                        "button_selection_id1"
                                    ]
                                }
                            }
                        ]
                    }
                }
            },
        }
        event = BotRequestMsg.model_validate_json(json.dumps(sample_data))
        self.assertEqual(event.msg.msg_type, 'event')
        self.assertEqual(event.msg.msg_content.event_type, 'template_card_event')


if __name__ == '__main__':
    unittest.main()
