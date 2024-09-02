import boto3
import json

client = boto3.client('events')
sns_client = boto3.client('sns')

def handle_collection_created(event):
    """Handle the collection created event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'CollectionCreated',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )

    # Publish to SNS
    sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:your-account-id:BookHubNotifications',  # Replace with your actual topic ARN
        Message=json.dumps(event),
        Subject='Collection Created'
    )

    print(f"Collection created event published: {response}")

def handle_collection_deleted(event):
    """Handle the collection deleted event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'CollectionDeleted',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )

    # Publish to SNS
    sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:your-account-id:BookHubNotifications',  # Replace with your actual topic ARN
        Message=json.dumps(event),
        Subject='Collection Deleted'
    )

    print(f"Collection deleted event published: {response}")