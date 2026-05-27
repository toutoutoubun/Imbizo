"""Small in-process event dispatcher."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


EventCallback = Callable[["AppEvent"], None]


@dataclass(slots=True)
class AppEvent:
    """A typed application event with a name and payload."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Subscription:
    """A removable event subscription."""

    event_name: str
    callback: EventCallback
    bus: "EventBus"

    def unsubscribe(self) -> None:
        """Remove this subscription from the event bus."""

        self.bus.unsubscribe(self)


class EventBus:
    """In-process publish/subscribe event dispatcher."""

    def __init__(self) -> None:
        self._callbacks: dict[str, list[EventCallback]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: EventCallback) -> Subscription:
        """Subscribe to an event and return a removable subscription."""

        self._callbacks[event_name].append(callback)
        return Subscription(event_name=event_name, callback=callback, bus=self)

    def unsubscribe(self, subscription: Subscription) -> None:
        """Remove a subscription if it is still active."""

        callbacks = self._callbacks.get(subscription.event_name, [])
        if subscription.callback in callbacks:
            callbacks.remove(subscription.callback)

    def publish(self, event: AppEvent) -> None:
        """Publish an event to current subscribers."""

        for callback in list(self._callbacks.get(event.name, [])):
            callback(event)
