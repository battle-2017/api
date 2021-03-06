from GroningerAPI.conversation_data import ConversationData
from GroningerAPI.dateformatter import DateFormatter
from GroningerAPI.models import Feedback
from GroningerAPI.moviefinder import MovieFinder
from GroningerAPI.parkingfinder import ParkingFinder

"""
context:
datetime
subject
genre
number
recommends
"""

class IntentParser:
    def parse(self, data, conversation):
        conversation_data = ConversationData(conversation.conversation_params)
        context = {'conversation': conversation}
        for key, value in conversation_data.__dict__.items():
            context[key] = value
        intent = '_default'
        print("intent" + intent)
        if 'entities' in data:
            for key, value in data['entities'].items():
                if type(value) is list:
                    value = value[0]
                    print(value)
                if key == 'intent':
                    intent = value['value']
                    print(intent)
                else:
                    context[key] = value['from'] if 'from' in value else value['value']
                    print(context)
        print(intent)
        # todo: misschien hier na een paar keer menselijke help inroepen?
        result, context = getattr(self, intent)(context) or ['Ik kan je niet zo goed volgen, zou je me dit nog een keer kunnen vertellen?', context]
        for key, value in context.items():
            if key != 'conversation':
                setattr(conversation_data, key, value)
        conversation.conversation_params = conversation_data.to_json()
        conversation.save()
        print(result)
        return result

    def _default(self, context):
        if 'intent' in context and context['intent'] == 'license':
            context['intent'] = 'finish_chat'
            return ['Ik heb een parkeerplaats in onze parkeerkelder voor je gereserveerd. Er is een plek voor je beschikbaar. Kan ik je verder nog ergens mee van dienst zijn?', context]
        elif 'intent' in context and context['intent'] == 'recommend_movie' and 'genre' in context:
            return self.recommend_movie(context)
        elif 'intent' in context and context['intent'] == 'card_number' and 'number' in context:
            context['intent'] = 'continue_chat'
            return ['Ik heb de kaarten naar jouw Facebook Messenger gestuurd. Kan ik je nu verder nog ergens mee helpen?', context]
        elif 'intent' in context and context['intent'] == 'reserve_movie' and 'number' in context:
            del context['intent']
            return self.reserve_movie(context)

    def messenger_channel(self, context):
        context['intent'] = 'card_number'
        return ['Ga ik regelen, mag ik je Groninger Forum kaartnummer?', context]

    def yes(self, context):
        if 'intent' in context:
            if context['intent'] == 'parking':
                return ['Zou ik dan je kenteken mogen?', {'intent': 'license'}]
            if context['intent'] == 'review':
                context['sentiment'] = 'positive'
                return self.review(context)
            elif context['intent'] == 'continue_chat':
                return ['Waarmee kan ik je nog meer van dienst zijn?', {}]
            elif context['intent'] == 'recommend_movie':
                return self.accept_recommend(context)
            elif context['intent'] == 'ticket_channel':
                return self.messenger_channel(context)
            intent = context['intent']
            del context['intent']
            return getattr(self, intent, lambda x: None)(context)

    def no(self, context):
        if 'intent' in context:
            if context['intent'] == 'finish_chat':
                return ['Dan wens ik je een prettige dag', {}]
            if context['intent'] == 'review':
                context['sentiment'] = 'negative'
                return self.review(context)
            elif context['intent'] == 'continue_chat':
                return ['Mooi. Hopelijk kon ik je van dienst zijn. Mag ik je ten slotte nog vragen of je tevreden bent over dit gesprek?', {'intent': 'review'}]
            elif context['intent'] == 'recommend_movie':
                return self.recommend_other(context)
            elif context['intent'] == 'buy_drinks':
                context['intent'] = 'ticket_channel'
                return ['Geen probleem, waar wil je jouw kaarten ontvangen?', context]
            context['intent'] = 'continue_chat'
            return ['Ok, geen probleem. Kan ik nog iets anders voor je doen?', context]

    def find_something(self, context):
        return self.find_movie(context)

    def find_movie(self, context):
        if 'subject' in context:
            finder = MovieFinder(context)
            time = finder.find_best_time()
            if not time:
                result = self.recommend_movie(context)
                result[0] = 'Helaas, ik kan ' + context['subject'] + ' niet vinden. ' + result[0]
                return result
            context['datetime'] = time
            context['intent'] = 'reserve_movie'
            return [context['subject'] + ' speelt ' + str(DateFormatter(time)) + '. Zal ik tickets voor je reserveren?', context]
        elif 'genre' in context:
            return self.recommend_movie(context)
        else:
            context['intent'] = 'recommend_movie'
            return ['Heb je een voorkeur?', context]

    def recommend_something(self, context):
        return self.recommend_movie(context)

    def recommend_movie(self, context):
        finder = MovieFinder(context)
        context['subject'], context['datetime'], location = finder.recommend_movie()
        if context['subject']:
            context['recommends'] = [context['subject']]
            s = str(DateFormatter(context['datetime']))
            return [s[0].upper() + s[1:] + ' draait in ' + location + ' de film: ‘' + context['subject'] + '’', context]
        else:
            context['intent'] = 'continue_chat'
            return ['Helaas, ik kon niets voor je vinden. Kan ik misschien wat anders voor je doen?', context]

    def reserve_something(self, context):
        return self.reserve_movie(context)

    def reserve_movie(self, context):
        if 'subject' in context:
            finder = MovieFinder(context)
            time = finder.find_best_time()
            if not time:
                result = self.recommend_movie(context)
                result[0] = 'Helaas, ik kan ' + context['subject'] + ' %(film)s niet vinden. ' + result[0]
                return result
            elif 'datetime' in context and time != context['datetime']:
                old_time = context['datetime']
                context['datetime'] = time
                context['intent'] = 'reserve_movie'
                return [context['subject'] + ' speelt niet ' + DateFormatter(old_time) + ' maar wel ' + DateFormatter(time) + '. Wil je die misschien reserveren?', context]
            elif 'datetime' not in context:
                context['datetime'] = time
                context['intent'] = 'reserve_movie'
                return [context['subject'] + ' speelt ' + DateFormatter(time) + '. Wil je die reserveren?', context]
            if 'number' in context:
                if finder.reserve(context['number'], context['conversation'].user):
                    return ['Ik heb je reservering gemaakt. Je kan je tickets tot een kwartier van te voren ophalen bij de kassa.', {'intent': 'continue_chat'}]
                else:
                    context['intent'] = 'continue_chat'
                    return ['Helaas, zo veel plaatsen zijn er niet meer beschikbaar. Kan ik misschien iets anders voor je doen?', context]
            else:
                context['intent'] = 'reserve_movie'
                return ['Voor hoeveel personen mag ik een reservering maken?', context]
        else:
            return self.recommend_movie(context)

    def recommend_other(self, context):
        if 'intent' in context and context['intent'] == 'recommend_movie':
            if 'recommends' in context and len(context['recommends']) > 1:
                context['recommends'] = context['recommends'][1:]
                context['subject'] = context['recommends'][0]
                return ['Ok, misschien is ' + context['subject'] + ' meer wat voor je?', context]
            else:
                context['intent'] = 'continue_chat'
                return ['Ik ben bang dat ik niets meer heb om je aan te raden. Kan ik misschien wat anders voor je doen?', context]

    def accept_recommend(self, context):
        if 'intent' in context and context['intent'] == 'recommend_movie':
            context['intent'] = 'buy_drinks'
            return ['Ik stuur je door: https://www.groningerforum.nl/reserveren/65b98c9a-9aa3-41af-80ca-8c2329ff8b12', context]

    def find_parking(self, context):
        return ["Ik weet dat nu niet. Ik laat mijn leraar, Sandrine, even meekijken", {"intent": "parking"}]

    def review(self, context):
        if 'sentiment' in context and 'conversation' in context:
            if context['sentiment'] == 'positive':
                feedback = Feedback.objects.create(conversation=context['conversation'], rating=8)
                feedback.save()
                return ['Bedankt voor je feedback, hopelijk tot een volgende keer!', {}]
            elif context['sentiment'] == 'negative':
                feedback = Feedback.objects.create(conversation=context['conversation'], rating=4)
                feedback.save()
                return ['Bedankt voor je feedback. Hopelijk kunnen we je een volgende keer beter van dienst zijn.', {}]

    def find_restaurant(self, context):
        return self.information(context)

    def reserve_restaurant(self, context):
        return self.information(context)

    def information(self, context):
        return ['Je kan alle informatie over het Groninger Forum vinden op onze website www.groningerforum.nl. Kan ik iets anders voor je doen?', {'intent': 'continue_chat'}]

    def price_information(self, context):
        return self.information(context)

    def greeting(self, context):
        return ["Hallo, waarmee kan ik je van dienst zijn?", context]

    def recommend_book(self, context):
        return ["Op dit moment is onze bibliotheek gesloten", context]