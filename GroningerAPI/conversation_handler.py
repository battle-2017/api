from datetime import timedelta, datetime

from GroningerAPI.intentparser import IntentParser
from GroningerAPI.models import Message, Conversation, User
from GroningerAPI.wit_parser import WitParser

class ConversationHandler:
    def receive_message(self, message_text, user_data):
        try:
            if 'first_name' not in user_data:
                user, created = User.objects.get_or_create(session_id=user_data['id'])
            else:
                user, created = User.objects.get_or_create(facebook_id=user_data['id'], name=user_data['first_name'], surname=user_data['last_name'])
            print(user)

            #yesterday = datetime.today() - timedelta(days=1)
            #conversation = Conversation.objects.get_or_create(sender=user, time_stamp__range=(yesterday, datetime.today()))
            conversation = Conversation.objects.filter(user=user).order_by("-time_stamp").first()
            print(conversation)
            if not conversation:
                conversation = Conversation(user=user)
                conversation.save(force_insert=True)

            Message.objects.create(conversation=conversation, type="message", sender="user", data=message_text)

            wit_parser = WitParser()
            parsed_intent = wit_parser.parse(message_text)
            intent_parser = IntentParser()
            result = intent_parser.parse(parsed_intent, conversation)

            Message.objects.create(conversation=conversation, type="message", sender="bot", data=result)

            return result
        except Exception as e:
            print(e)
            raise e
