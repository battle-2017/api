from GroningerAPI.conversationdata import ConversationData
from GroningerAPI.models import Conversation, User


class IntentParser:
    def __int__(self):
        pass

    def yes(self, data, conversation):
        pass

    def no(self):
        pass

    def find_something(self):
        pass

    def find_movie(self):
        pass

    def recommend_something(self):
        pass

    def recommend_movie(self, data, conversation):
        parameters = ConversationData(conversation.conversation_params)
        parameters.film_subject = data.get("subject")
        parameters.film_genre = data.get("genre")
        conversation.conversation_params = parameters.to_json()
        #
        return "Hallo, hoe kan ik je helpen?"

    def recommend_other(self):
        pass

    def accept_recommend(self):
        pass

    def reserve_something(self):
        pass

    def find_parking(self):
        pass

    def review(self):
        pass

    def request_human(self):
        pass

    def find_restaurant(self):
        pass

    def reserve_restaurant(self):
        pass

    def recommend_book(self):
        pass

    def information(self):
        pass

    def price_information(self):
        pass

    @staticmethod
    def initialize_user(user_token, is_facebook):
        conversation = None
        if is_facebook:
            user = User.objects.get_or_create(session_id = user_token)
        else:
            user = User.objects.get_or_create(facebook_id = user_token)

        if not conversation:
            conversation = Conversation(user=user)
            conversation.save(force_insert=True)
        else:
            conversation = Conversation.objects.order_by("-time_stamp").first()

        return conversation

