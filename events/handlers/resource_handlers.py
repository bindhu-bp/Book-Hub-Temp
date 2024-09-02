import boto3
import json

client = boto3.client('events')
sns_client = boto3.client('sns')

def handle_resource_added(event):
    """Handle the resource added event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'ResourceAdded',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )

    # Publish to SNS
    sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:your-account-id:BookHubNotifications',  # Replace with your actual topic ARN
        Message=json.dumps(event),
        Subject='Resource Created'
    )

    print(f"Resource added event published: {response}")

def handle_resource_deleted(event):
    """Handle the resource deleted event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'ResourceDeleted',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"Resource deleted event published: {response}")