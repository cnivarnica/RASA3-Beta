from typing import Any, Text, Dict, List, Union
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet, EventType

class AskForOutdoorsActivitiesForm(Action):
    def name(self) -> Text:
        return "outdoors_activities_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return [
            "hiking_camping_biking",
            "single_use_items",
            "waste_management",
            "transport",
            "protection_activities_involvment",
            "biodegradable_products_usage",
            "environment_wildlife_knowledge",
            "natural_habitats_impact",
            "changes_made"
        ]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "hiking_camping_biking": self.from_text(),
            "single_use_items": [
                self.from_intent(intent="affirm", value=True),
                self.from_intent(intent="deny", value=False)
            ],
            "waste_management": self.from_text(),
            "transport": self.from_text(),
            "protection_activities_involvment": [
                self.from_intent(intent="affirm", value=True),
                self.from_intent(intent="deny", value=False)
            ],
            "biodegradable_products_usage": [
                self.from_intent(intent="affirm", value=True),
                self.from_intent(intent="deny", value=False)
            ],
            "environment_wildlife_knowledge": self.from_text(),
            "natural_habitats_impact": self.from_text(),
            "changes_made": self.from_text()
        }

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[EventType]:
        for slot in self.required_slots(tracker):
            if tracker.get_slot(slot) is None:
                dispatcher.utter_message(response=f"utter_ask_{slot}")
                return [SlotSet("requested_slot", slot)]
        return [SlotSet("requested_slot", None)]

class ValidateOutdoorsActivitiesForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_outdoors_activities_form"

    def validate_hiking_camping_biking(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value.lower() in ["yes", "no"]:
            return {"hiking_camping_biking": value.lower()}
        return {"hiking_camping_biking": None}

    def validate_single_use_items(
        self,
        value: bool,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if isinstance(value, bool):
            return {"single_use_items": value}
        return {"single_use_items": None}

    def validate_waste_management(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value:
            return {"waste_management": value}
        return {"waste_management": None}

    def validate_transport(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value:
            return {"transport": value}
        return {"transport": None}

    def validate_protection_activities_involvment(
        self,
        value: bool,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if isinstance(value, bool):
            return {"protection_activities_involvment": value}
        return {"protection_activities_involvment": None}

    def validate_biodegradable_products_usage(
        self,
        value: bool,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if isinstance(value, bool):
            return {"biodegradable_products_usage": value}
        return {"biodegradable_products_usage": None}

    def validate_environment_wildlife_knowledge(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value:
            return {"environment_wildlife_knowledge": value}
        return {"environment_wildlife_knowledge": None}

    def validate_natural_habitats_impact(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if value:
            return {"natural_habitats_impact": value}
        return {"natural_habitats_impact": None}

    def validate_changes_made(
        self,
        value: bool,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if isinstance(value, bool):
            return {"changes_made": value}
        return {"changes_made": None}

class SubmitOutdoorsActivitiesForm(Action):
    def name(self) -> Text:
        return "submit_outdoors_activities_form"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        hiking_camping_biking = tracker.get_slot("hiking_camping_biking")
        single_use_items = tracker.get_slot("single_use_items")
        waste_management = tracker.get_slot("waste_management")
        transport = tracker.get_slot("transport")
        protection_activities_involvment = tracker.get_slot("protection_activities_involvment")
        biodegradable_products_usage = tracker.get_slot("biodegradable_products_usage")
        environment_wildlife_knowledge = tracker.get_slot("environment_wildlife_knowledge")
        natural_habitats_impact = tracker.get_slot("natural_habitats_impact")
        changes_made = tracker.get_slot("changes_made")

        dispatcher.utter_message(
            text=f"Thank you for sharing your activities and environmental habits:\n"
                 f"Hiking/Camping/Biking: {hiking_camping_biking}\n"
                 f"Single-use items: {single_use_items}\n"
                 f"Waste management: {waste_management}\n"
                 f"Transport: {transport}\n"
                 f"Protection activities involvement: {protection_activities_involvment}\n"
                 f"Biodegradable products usage: {biodegradable_products_usage}\n"
                 f"Environment/Wildlife knowledge: {environment_wildlife_knowledge}\n"
                 f"Impact on natural habitats: {natural_habitats_impact}\n"
                 f"Changes made: {changes_made}"
        )

        return [SlotSet(slot, None) for slot in [
            "hiking_camping_biking", "single_use_items",
            "waste_management", "transport", "protection_activities_involvment",
            "biodegradable_products_usage", "environment_wildlife_knowledge",
            "natural_habitats_impact", "changes_made"
        ]]