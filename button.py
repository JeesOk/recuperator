from gpiozero import Button

class MyButton(object):
    def __init__(self, pin, held, pressed, index = 0):
        Button.was_held = False
        self.index = index
        self.pin = pin
        self.btn = Button(pin)
        self.held = held
        self.pressed = pressed
        self.btn.when_held = self._held
        self.btn.when_released = self._released

    def _held(self, b):
        b.was_held = True
        if self.held:
            self.held(self)

    def _released(self, b):
        if not b.was_held:
            self._pressed()
        b.was_held = False

    def _pressed(self):
        if self.pressed:
            self.pressed(self)

