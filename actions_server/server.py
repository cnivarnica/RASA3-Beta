import os
import importlib
import inspect
import logging
from sanic import Sanic
from sanic.response import json
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Sanic("rasa_actions_server")

def import_all_actions():
    actions_module_path = 'rasa_actions'
    actions = {}

    actions_dir = os.path.join(os.path.dirname(__file__), actions_module_path)
    if not os.path.exists(actions_dir):
        logger.warning(f"Actions directory not found: {actions_dir}")
        return actions

    for file in os.listdir(actions_dir):
        if file.endswith('.py') and file != '__init__.py':
            module_name = file[:-3]
            try:
                module = importlib.import_module(f'{actions_module_path}.{module_name}')
                logger.debug(f'Importing module: {module_name}')

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Action) and obj is not Action:
                        try:
                            action_instance = obj()
                            action_name = action_instance.name()
                            actions[action_name] = action_instance
                            logger.debug(f'Registered action: {action_name}')
                        except Exception as e:
                            logger.warning(f'Error instantiating action {name}: {str(e)}')
            except ImportError as e:
                logger.error(f'Error importing module {module_name}: {str(e)}')
        
    return actions

actions = import_all_actions()

@app.route("/webhook", methods=["POST"])
async def webhook(request):
    try:
        body = request.json
        logger.info(f'Received request for action: {body.get("next_action")}')

        action_name = body.get("next_action")
        if action_name in actions:
            action = actions[action_name]
            tracker = Tracker.from_dict(body.get("tracker", {}))
            dispatcher = CollectingDispatcher()

            logger.info(f'Executing action: {action_name}')
            events = action.run(dispatcher, tracker, {})

            response = {
                "events": events,
                "responses": dispatcher.messages
            }
            logger.debug(f'Action response: {response}')
            return json(response)
        else:
            logger.error(f'Action not found: {action_name}')
            return json({"error": "Action not found"}, status=404)
    except Exception as e:
        logger.error(f'Error processing webhook: {str(e)}')
        return json({"error": "Internal server error"}, status=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055)