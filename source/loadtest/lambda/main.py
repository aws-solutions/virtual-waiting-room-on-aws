import json

from actions import create_coordinator, create_workers, destroy


allowed_actions = [
    "create_coordinator",
    "create_workers",
    "destroy"
]


def lambda_handler(event, context):
    print(event)
    action = event.get("action")
    params = event.get("params")
    
    if action not in allowed_actions:
        raise ValueError("Invalid action: %s" % action)
        
    elif action == "create_coordinator":
        response = create_coordinator(params)
        
    elif action == "create_workers":
        response = create_workers(params)
        
    elif action == "destroy":
        response = destroy(params)
        
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
