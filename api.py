import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# The scopes define the permissions your script is requesting.
# You MUST include the correct scopes for the API you're using.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # DO NOT leave this in production code.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret.json" # Your downloaded file

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES)
    credentials = flow.run_local_server(port=0)

    # From here, you can build your service object and make API calls
    youtube_service = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # Example API call
# Replace UCtUQHzC0QmABOQERfABAhZg with the actual Channel ID
    request = youtube_service.channels().list(
        part="snippet,contentDetails,statistics",
        id="UCtUQHzC0QmABOQERfABAhZg" 
    )
    response = request.execute()

    print(response)

if __name__ == "__main__":
    main()