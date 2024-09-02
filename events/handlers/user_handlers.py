import boto3
import json

client = boto3.client('events')

def handle_user_created(event):
    """Handle the user created event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'UserCreated',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'  
            }
        ]
    )
    print(f"User created event published: {response}")

def handle_user_updated(event):
    """Handle the user updated event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'UserUpdated',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"User updated event published: {response}")

def handle_user_logged_in(event):
    """Handle the user logged in event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'UserLoggedIn',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"User logged in event published: {response}")

def handle_password_reset(event):
    """Handle the password reset event."""
    response = client.put_events(
        Entries=[
            {
                'Source': 'com.bookhub',
                'DetailType': 'PasswordReset',
                'Detail': json.dumps(event),
                'EventBusName': 'BookhubEventBus'
            }
        ]
    )
    print(f"Password reset event published: {response}")