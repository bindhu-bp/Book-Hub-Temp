import boto3
import json
import os

# Initialize AWS clients
sns_client = boto3.client('sns')
eventbridge = boto3.client('events')

# Fetch the SNS Topic ARN from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'BookHubEventBus')

# Helper functions for SNS
def create_sns_topic():
    """Creates an SNS topic and returns its ARN."""
    response = sns_client.create_topic(Name='BookHubNotifications')
    return response['TopicArn']


def subscribe_user(email):
    """Subscribes a user to the SNS topic."""
    if not SNS_TOPIC_ARN:
        return {"message": "SNS_TOPIC_ARN environment variable is not set"}, 500
    
    response = sns_client.subscribe(
        TopicArn=SNS_TOPIC_ARN,
        Protocol='email',
        Endpoint=email
    )
    return response

# Main handler function for the EvebtBridge and SNS
def publish_event(event_name: str, detail: dict):
    """Publishes an event to EventBridge and SNS."""
    if not SNS_TOPIC_ARN:
        return {"message": "SNS_TOPIC_ARN environment variable is not set"}, 500

    # Publish to EventBridge
    eventbridge_response = eventbridge.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': event_name,
                'Detail': json.dumps(detail),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )

    # Publish to SNS
    sns_response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps(detail),
        Subject=f'Event Notification: {event_name}'
    )

    return eventbridge_response, sns_response

def handler(event, context):
    """Main handler function for the Lambda."""
    global SNS_TOPIC_ARN
    if not SNS_TOPIC_ARN:
        SNS_TOPIC_ARN = create_sns_topic()

    return {
        'statusCode': 200,
        'body': json.dumps('Handler executed successfully!')
    }