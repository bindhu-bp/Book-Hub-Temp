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
    try:
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

        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:961341516655:BookHubNotifications',  # Replace with your actual topic ARN
            Message=json.dumps(event),
            Subject='Collection Deleted'
        )

        print(f"Collection deleted event published: {response}")
    except Exception as e:
        print(f"Error publishing event: {e}")
