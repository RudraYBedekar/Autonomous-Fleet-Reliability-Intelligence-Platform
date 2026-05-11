import sys
import selectors

def apply_kafka_python_312_fix():
    if sys.version_info >= (3, 12):
        for selector_name in dir(selectors):
            if selector_name.endswith('Selector') and selector_name != 'BaseSelector':
                selector_class = getattr(selectors, selector_name)
                if hasattr(selector_class, 'unregister'):
                    original_unregister = selector_class.unregister
                    def make_patched(orig):
                        def patched(self, fileobj):
                            try:
                                return orig(self, fileobj)
                            except (ValueError, KeyError):
                                pass
                        return patched
                    setattr(selector_class, 'unregister', make_patched(original_unregister))

apply_kafka_python_312_fix()
