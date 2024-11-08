import boto3
import json

import logging

client = boto3.client('events')
sns_client = boto3.client('sns')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle_book_added(event):

    try:
    
        response = client.put_events(
            Entries=[
            {
                '   Source': 'com.bookhub',
                'DetailType': 'BookAdded',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
            ]
        )

    # Publish to SNS
        sns_response = sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:961341516655:BookHubNotifications',  
            Message=json.dumps(event),
            Subject='Book Added'
        )

        logger.info(f"Book added event published: {response}")
        return response, sns_response
    except Exception as e:
        logger.error(f"Error handling book added event: {str(e)}")
        raise

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