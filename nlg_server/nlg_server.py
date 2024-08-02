from sanic import Sanic, response
import yaml
import os
import random

app = Sanic("nlg_server")

RESPONSES_DIR = "responses"

def load_responses(directory):
    responses = {}
    for filename in os.listdir(directory):
        if filename.endswith(".yml"):
            with open(os.path.join(directory, filename), "r") as file:
                file_responses = yaml.safe_load(file)
                for template_name, template_variations in file_responses.items():
                    if template_name in responses:
                        responses[template_name].extend(template_variations)
                    else:
                        responses[template_name] = template_variations
    print("Loaded templates:", list(responses.keys()))
    return responses

responses = load_responses(RESPONSES_DIR)

@app.route("/nlg", methods=["POST"])
async def nlg(request):
    data = request.json
    print("Received request:", data)
    template_name = data.get("response")
    variables = data.get("arguments", {})
    
    if "tracker" in data:
        tracker = data["tracker"]
        sender_id = tracker.get("sender_id")
        variables["name"] = sender_id
    
    print(f"Available templates: {list(responses.keys())}")
    print(f"Requested template: {template_name}")
    
    if template_name in responses:
        template_options = responses[template_name]
        template = random.choice(template_options)
        response_text = template.format(**variables)
        print(f"Responding with: {response_text}")
        return response.json({"text": response_text})
    else:
        print(f"Template '{template_name}' not found")
        return response.json({"error": "Template not found"}, status=404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)