from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock

from subprocess import Popen, PIPE
import os
import shutil
import uuid
import xk
import random
# print(os.path.dirname(os.path.abspath(__file__)))

class MainView(Widget):

    def get_images(self):
    #     process = Popen(['python', 'xk.py'], stdout = PIPE, stderr = PIPE)
    #     stdout, stderr = process.communicate()
    #     if len(stdout) > 0:
    #         print('[Out]:\n' + stdout.decode('utf8'))
    #     if len(stderr) > 0:
    #         print('[Error]:\n' + stderr.decode('utf8'))
        xk.get_captcha()
        # print(repr(xk.S.cookies))
        for key in self.ids:
            if key.startswith('img'):
                self.ids[key].reload()

    def re_focus(self, *args):
        self.ids.text_input.focus = True

    def is_valid_input(self):
        text = self.ids.text_input.text
        if text == '' or len(text) != 4:
            return False
        return xk.check_captcha(text)
        # return True
        # return False

    def save_input(self):
        for i,d in enumerate(self.ids.text_input.text):
            src = 'split_%d.png' % i
            dst = 'training/%s/%s.png' % (d, uuid.uuid4())
            shutil.copyfile(src, dst)

    def on_enter(self, text):
        print(text)
        self.ids.result.color = (random.random(), random.random(), random.random(), random.random() * 0.4 + 0.6)
        self.ids.result.text = 'CHECKING'
        if self.is_valid_input():
            print('CORRECT')
            self.ids.result.text = 'CORRECT'
            self.save_input()
        else:
            print('WRONG!!!!!')
            self.ids.result.text = 'WRONG!'
        print('*'*80)
        Clock.schedule_once(self.re_focus)
        self.get_images()
        self.ids.text_input.text = ''

class TrainApp(App):
    kv_directory = 'kv_template'
    def build(self):
        main_view = MainView()
        main_view.get_images()
        return main_view


TrainApp().run()
