import asyncio
import json
import logging

from collections.abc import MutableMapping

from functools import wraps


log = logging.getLogger(__name__)

## A function to map a reading to a value in a range
def map_reading(in_val, output_values, raw_readings=[4,20], ignore_below=3):

    if in_val < ignore_below:
        return None

    ## Choose the value set to map between
    lower_val_ind = 0
    found = False
    for i in range(0, len(raw_readings)):
        if in_val <= raw_readings[i]:
            lower_val_ind = i-1
            found = True
            break

    if not found:
        lower_val_ind = len(raw_readings)-2

    # Figure out how 'wide' each range is
    inSpan = raw_readings[lower_val_ind + 1] - raw_readings[lower_val_ind]
    outSpan = output_values[lower_val_ind + 1] - output_values[lower_val_ind]

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(in_val - raw_readings[lower_val_ind]) / float(inSpan)

    # Convert the 0-1 range into a value in the right range.
    return output_values[lower_val_ind] + (valueScaled * outSpan)


def find_object_with_key(obj, key_to_find):
    stack = [obj]

    while stack:
        current = stack.pop()

        if isinstance(current, dict):
            if key_to_find in current:
                return current[key_to_find]

            for key in current:
                stack.append(current[key])

    return None


def find_path_to_key(obj, key_to_find):
    stack = [{'current': obj, 'path': ''}]

    while stack:
        current_entry = stack.pop()
        current = current_entry['current']
        path = current_entry['path']

        if isinstance(current, dict):
            if key_to_find in current:
                return f"{path}.{key_to_find}" if path else key_to_find

            for key in current:
                new_path = f"{path}.{key}" if path else key
                stack.append({'current': current[key], 'path': new_path})

    return None


def get_is_async(is_async: bool = None):
    if is_async is not None:
        return is_async

    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def maybe_async():
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            # args[0] is self
            is_async_context = getattr(args[0], "_is_async", False)
            # allow them to specify if they want to run the sync version of the function (default very much not)
            force_sync = kwargs.pop("run_sync", False)

            if is_async_context is True and force_sync is False:
                # we're in an async context, check if we have an async variety of the function to run...
                try:
                    alternative = getattr(args[0], f"{func.__name__}_async")
                    return alternative(*args[1:], **kwargs)
                except AttributeError:
                    # we don't have a corresponding async method, just use the sync one.
                    pass
            return func(*args, **kwargs)
        return inner
    return wrapper


def wrap_try_except(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log.exception(f"Error in {func.__name__}: {e}", exc_info=e)

async def wrap_try_except_async(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        log.exception(f"Error in {func.__name__}: {e}", exc_info=e)

async def call_maybe_async(func, *args, as_task: bool = False, in_executor: bool = True, **kwargs):
    # print(f"call_maybe_async: func={func}, as_task={as_task}, in_executor={in_executor is True and not asyncio.iscoroutinefunction(func)}")
    if asyncio.iscoroutinefunction(func):
        coro = wrap_try_except_async(func, *args, **kwargs)
        if as_task:
            # assign it to a variable for weak ref
            task = asyncio.create_task(coro)
            return task
        else:
            await coro
            return
    elif in_executor:
        loop = asyncio.get_running_loop()
        # run_in_executor doesn't support kwargs
        if kwargs:
            log.warning("kwargs are not supported when calling via executor")

        # this is a little bit of a hack, but essentially we're creating an async function that
        # is called with await func to allow for both running as a task and in an executor.
        future = loop.run_in_executor(None, wrap_try_except, func, *args)
        if as_task:
            return future

        await future
        return
    else:
        wrap_try_except(func, *args, **kwargs)
        return


class CaseInsensitiveDict(MutableMapping):
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def copy(self):
        return CaseInsensitiveDict(self._store)

    def to_dict(self):
        return {k: v.to_dict() if isinstance(v, CaseInsensitiveDict) else v for k, v in self.items()}

    @classmethod
    def from_dict(cls, data):
        t = {k: CaseInsensitiveDict.from_dict(v) if isinstance(v, dict) else v for k, v in data.items()}
        return cls(t)

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return iter(self._store)

    def __setitem__(self, key, value):
        self._store[key.lower()] = value

    def __getitem__(self, key):
        return self._store[key.lower()]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._store)


class CaseInsensitiveDictEncoder(json.JSONEncoder):
    # might not need this
    def default(self, obj):
        if isinstance(obj, CaseInsensitiveDict):
            return obj.to_dict()
        # Let the base class default method raise the TypeError
        return super().default(obj)
