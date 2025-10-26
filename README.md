YouTube WebSub (PubSubHubbub) Proof of Concept
This project provides a simple Python Flask server to demonstrate how to receive real-time push notifications from YouTube when a channel uploads a new video.

How It Works
The WebSub protocol involves three parties:

Publisher (YouTube): Publishes content updates to a feed.

Hub (Google): A service that sits between the publisher and subscriber. It fetches the feed and pushes updates to subscribers.

Subscriber (This App): Our Python server that tells the Hub it wants to be notified of updates.

The flow is as follows:

Our server sends a subscribe request to the Hub, telling it which YouTube channel feed (hub.topic) we're interested in and where to send notifications (hub.callback).

The Hub immediately sends a GET request back to our callback URL with a unique hub.challenge token.

Our server must respond with that exact token to prove we own the callback URL.

Once verified, the subscription is active. When the YouTube channel posts a new video, the Hub sends a POST request to our callback URL with the video details in an XML (Atom feed) format.

Setup and Usage Guide
Step 1: Install Prerequisites
First, install the necessary Python packages.

pip install -r requirements.txt

Step 2: Find the YouTube Channel ID
You need the ID of the channel you want to subscribe to.

Go to the YouTube channel's main page (e.g., https://www.youtube.com/@GoogleDevelopers).

Right-click on the page and select "View Page Source".

Search (Ctrl+F or Cmd+F) for the text "channelId".

You will find a string like "channelId":"UCBJycsmduvYEL83R_U4JriQ". The value is the Channel ID.

Open websub_server.py and replace the value of YOUTUBE_CHANNEL_ID with the one you found.

Step 3: Expose Your Server with Tailscale Funnel
Your local server needs to be accessible from the public internet for the Hub to reach it. As you mentioned, Tailscale Funnel is a perfect tool for this.

Make sure you have Tailscale installed and running.

Run the Flask server in one terminal (see next step). It will run on port 5000.

In a separate terminal, run the following command to expose port 5000:

tailscale funnel 5000

Tailscale will output your public HTTPS URL, which will look something like https://your-machine-name.your-tailnet.ts.net. This is your callback URL base.

Step 4: Configure and Run the Server
Open the websub_server.py script.

Set the YOUTUBE_CHANNEL_ID you found in Step 2.

Set the CALLBACK_URL_BASE to the public URL you got from Tailscale in Step 3. You can either edit the script directly or set it as an environment variable:

# For Linux/macOS
export CALLBACK_URL_BASE="[https://your-machine-name.your-tailnet.ts.net](https://your-machine-name.your-tailnet.ts.net)"
python websub_server.py

# For Windows (Command Prompt)
set CALLBACK_URL_BASE="[https://your-machine-name.your-tailnet.ts.net](https://your-machine-name.your-tailnet.ts.net)"
python websub_server.py

Step 5: Watch the Magic Happen
When you run the script, you should see the following sequence in your console:

The Flask server starts.

After 2 seconds, the script sends the subscription request to the Google Hub.

Almost immediately, you will see a Received GET request from Hub for verification. message, followed by the server responding with the challenge token.

Your subscription is now active!

To test it, the target channel needs to upload a new video (or change an existing unlisted video to public). When that happens, you will see a Received POST request message in your console, along with the parsed details of the new video.