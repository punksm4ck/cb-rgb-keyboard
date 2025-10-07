
from .base import BaseEffect

class RippleEffect(BaseEffect):
    def start(self):
        super().start()
        # Trigger ripple from key index
        def ripple_from(index):
            for radius in range(5):
                if not self.running:
                    break
                affected = self.controller.get_keys_in_radius(index, radius)
                for key in affected:
                    self.controller.hardware.set_keys(key, [0x00FFFF])
                self.controller.root.after(100, lambda: self.controller.clear_keys(affected))
        self.controller.bind_keypress(ripple_from)
