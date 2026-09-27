import json, re
from pathlib import Path
from fuzzywuzzy import fuzz
from actions import ACTIONS
from ai import AIUnavailableError, answer as ask_ai
# Simple parse_time inline to avoid circular imports
from dateutil import parser, relativedelta
from datetime import datetime
def parse_time(text):
    m = re.search(r"(\d{1,2}(:\d{2})?)\s*(am|pm)?", text, re.I)
    if not m: return None
    t = m.group(0)
    try:
        dt = parser.parse(t, fuzzy=True)
        now = datetime.now()
        dt = dt.replace(year=now.year, month=now.month, day=now.day)
        if dt <= now:
            dt = dt + relativedelta.relativedelta(days=1)
        return dt
    except:
        return None
class Assistant:
    def __init__(self, speech_engine=None):
        with (Path(__file__).resolve().parent / 'intents.json').open(encoding='utf-8') as f:
            self.intents = json.load(f)
        self.speech = speech_engine
    def match_intent(self, text):
        text = text.lower()
        best = (None, 0, None)
        for intent in self.intents['intents']:
            for utter in intent.get('utterances',[]):
                score = fuzz.partial_ratio(text, utter.lower())
                if score > best[1]:
                    best = (intent['name'], score, intent)
        return best
    def extract_entities(self, intent_name, text):
        ents = {'text':text}
        if intent_name=='set_alarm':
            when = parse_time(text)
            ents['time']=when
        if intent_name=='cancel_alarm':
            alarm_id = re.search(r'\balarm-\d+\b', text, re.I)
            if alarm_id:
                ents['alarm_id'] = alarm_id.group(0)
        if intent_name=='open_app':
            ents['app_name']=text
        if intent_name in ('take_note',):
            # extract after 'note' or 'remember'
            m = re.search(r"(?:note|remember|say) (.*)", text, re.I)
            ents['note_text'] = m.group(1) if m else text
        return ents
    def handle(self, text, ui_callback=None):
        name, score, intent = self.match_intent(text)
        if score < 35 or intent is None:
            try:
                response = ask_ai(text) or "Sorry, I didn't catch that. Could you rephrase?"
            except AIUnavailableError as exc:
                response = str(exc)
            except Exception:
                response = "I could not reach the AI service. Check your API key and connection."
            if self.speech: self.speech.speak(response)
            return {'status':'ok' if response else 'fail','say':response,'response':response}
        entities = self.extract_entities(name, text)
        func = ACTIONS.get(name)
        if func:
            result = func(entities)
            if self.speech:
                self.speech.speak(result.get('say','Done'))
            if ui_callback:
                ui_callback(result)
            return result
        try:
            response = ask_ai(text) or 'That command is not available yet.'
        except AIUnavailableError as exc:
            response = str(exc)
        except Exception:
            response = 'I could not reach the AI service. Check your API key and connection.'
        if self.speech:
            self.speech.speak(response)
        return {'status':'ok','say':response,'response':response}
