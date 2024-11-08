import boto3
import json
import os
import logging
from fastapi import HTTPException

# Initialize AWS clients
sns_client = boto3.client('sns')
eventbridge = boto3.client('events')

logger = logging.getLogger(__name__)    
logger.setLevel(logging.INFO)

# Fetch the SNS Topic ARN and Event Bus Name from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'BookHubEventBus')

def create_sns_topic():
    """Creates an SNS topic and returns its ARN."""
    response = sns_client.create_topic(Name='BookHubNotifications')
    return response['TopicArn']


def handler(event, context):
    """Main handler function for the Lambda."""
    global SNS_TOPIC_ARN
    if not SNS_TOPIC_ARN:
        SNS_TOPIC_ARN = create_sns_topic()

    # Further processing based on the event
    # For example, you could subscribe a user or publish an event here
    return {
        'statusCode': 200,
        'body': json.dumps('Handler executed successfully!')
    }

async def publish_event(event_name: str, detail: dict):
    """Publishes an event to EventBridge and SNS."""
    if not SNS_TOPIC_ARN:
        return {"message": "SNS_TOPIC_ARN environment variable is not set"}, 500

    try:
        # Publish to EventBridge (optional)
        eventbridge_response = eventbridge.put_events(
            Entries=[{
                'Source': 'com.bookhub',
                'DetailType': event_name,
                'Detail': json.dumps(detail),
                'EventBusName': EVENT_BUS_NAME
            }]
        )

        logger.info(f"EventBridge response for {event_name}: {eventbridge_response}")

        if eventbridge_response['FailedEntryCount'] > 0:
            logger.error(f"Failed to publish event to EventBridge: {eventbridge_response}")
            return {"message": "Failed to publish event to EventBridge"}, 500

        # Publish to SNS (this will notify all subscribed users)
        sns_response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(detail),  
            Subject=f'Event Notification: {event_name}'  # Subject for the notification
        )

        logger.info(f"SNS response for {event_name}: {sns_response}")
        return sns_response

    except Exception as e:
        logger.error(f"Error publishing event to SNS: {str(e)}")
        raise HTTPException(status_code=500, detail="Error publishing notification")