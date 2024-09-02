import boto3
import json

client = boto3.client('events')
sns_client = boto3.client('sns')

def handle_book_added(event):
    """Handle the book added event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'BookAdded',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )

    # Publish to SNS
    sns_client.publish(
        TopicArn='arn:aws:sns:us-east-1:your-account-id:BookHubNotifications',  
        Message=json.dumps(event),
        Subject='Book Added'
    )

    print(f"Book added event published: {response}")

def handle_book_deleted(event):
    """Handle the book deleted event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'BookDeleted',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"Book deleted event published: {response}")

def handle_book_borrowed(event):
    """Handle the book borrowed event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'BookBorrowed',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"Book borrowed event published: {response}")

def handle_book_returned(event):
    """Handle the book returned event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'BookReturned',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"Book returned event published: {response}")