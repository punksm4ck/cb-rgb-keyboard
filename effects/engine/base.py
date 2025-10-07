
class BaseEffect:
    def __init__(self, controller):
        self.controller = controller
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self):
        pass
