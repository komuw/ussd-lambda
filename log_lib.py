import json


def _serializer(obj):
    """
    """
    if hasattr(obj, 'isoformat'):
        # Datetime-like objects
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return str(obj, 'utf-8')
    else:
        return 'Object type {obj} with value {value} is' \
               ' not JSON serializable'.format(obj=type(obj),
                                               value=repr(obj))


class KeyValueRenderer(object):
    """
    Render event_dict as a list of Key=json.dumps(str(Value)) pairs.
    """

    def __call__(self, logger, name, event_dict):
        def serialize(v):
            """
            Try and serialize dict objects without appending extra escape charactes.
            """
            try:
                v = json.loads(v)
            except Exception:
                v = v
            return json.dumps(v, default=_serializer)

        return ', '.join('{k}={v}'.format(k=k, v=serialize(v))
                         for k, v in event_dict.items())
