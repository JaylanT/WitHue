import speech_recognition as sr
from wit import Wit
from phue import Bridge


class WitHue:

    max_bri = 254
    dim_bri = 80

    def __init__(self, wit_key, hue_ip, lights, energy_threshold=600):
        b = Bridge(hue_ip)
        b.connect()
        self.b = b

        self.client = Wit(wit_key)
        self.WIT_AI_KEY = wit_key

        self.lights = lights

        r = sr.Recognizer()
        r.dynamic_energy_threshold = False
        r.energy_threshold = energy_threshold
        self.r = r
        self.m = sr.Microphone()


    def toggle_lights(self, state, bri=None):
        if bri:
            return self.b.set_light(self.lights, {'on': True, 'bri': min(bri, self.max_bri)})
        return self.b.set_light(self.lights, 'on', state)


    @staticmethod
    def get_val(entities, entity):
        if entity not in entities:
            return None
        val = entities[entity][0]['value']
        if not val:
            return None
        return val['value'] if isinstance(val, dict) else val


    def handle_message(self, res):
        entities = res['entities']
        print(entities)
        lights_state = self.get_val(entities, 'on_off')
        if lights_state:
            if res['_text'] == 'dim lights':
                return self.toggle_lights(True, self.dim_bri)
            elif 'max' in res['_text']:
                return self.toggle_lights(True, self.max_bri)
            elif 'number' in entities:
                bri = int(entities['number'][0]['value'] * self.max_bri / 100)
                return self.toggle_lights(True, bri)
            elif lights_state == 'on':
                return self.toggle_lights(True)
            elif lights_state == 'off':
                return self.toggle_lights(False)
        return 'Invalid command'


    def listen(self):
        with self.m as source:
            try:
                audio = self.r.listen(source, 5, 3)
                print('Processing...')
                command = self.r.recognize_wit(audio, self.WIT_AI_KEY)
                if not command:
                    raise sr.UnknownValueError
                print('You said "{0}"'.format(command))
                res = self.client.message(command)
                self.handle_message(res)
            except sr.UnknownValueError: 
                print("Wit could not understand audio") 
            except sr.RequestError as e: 
                print("Could not request results from Wit service; {0}".format(e)) 
            except Exception as e:
                print('Error: {0}'.format(e))

