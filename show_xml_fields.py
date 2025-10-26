#!/usr/bin/env python3
"""
Show all available fields in YouTube WebSub XML notifications
"""
import xml.etree.ElementTree as ET

# Sample XML from a typical YouTube WebSub notification
sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
  <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID"/>
  <title>YouTube video feed</title>
  <updated>2025-10-22T22:21:03.123456789+00:00</updated>
  <entry>
    <id>yt:video:VIDEO_ID</id>
    <yt:videoId>VIDEO_ID</yt:videoId>
    <yt:channelId>CHANNEL_ID</yt:channelId>
    <title>Video Title Here</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=VIDEO_ID"/>
    <author>
      <name>Channel Name</name>
      <uri>https://www.youtube.com/channel/CHANNEL_ID</uri>
    </author>
    <published>2025-10-22T21:20:58+00:00</published>
    <updated>2025-10-22T21:20:58+00:00</updated>
  </entry>
</feed>'''

print("=" * 80)
print("YOUTUBE WEBSUB (ATOM FEED) AVAILABLE FIELDS")
print("=" * 80)

root = ET.fromstring(sample_xml)
ns = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015'
}

print("\n📺 FEED LEVEL:")
print("-" * 80)
print(f"  title: {root.find('atom:title', ns).text}")
print(f"  updated: {root.find('atom:updated', ns).text}")
print(f"  self link: {root.find('atom:link[@rel=\"self\"]', ns).attrib['href']}")

entry = root.find('atom:entry', ns)
if entry:
    print("\n📹 ENTRY (VIDEO) LEVEL:")
    print("-" * 80)
    print(f"  yt:videoId: {entry.find('yt:videoId', ns).text}")
    print(f"  yt:channelId: {entry.find('yt:channelId', ns).text}")
    print(f"  title: {entry.find('atom:title', ns).text}")
    print(f"  link: {entry.find('atom:link', ns).attrib['href']}")
    print(f"  published: {entry.find('atom:published', ns).text}")
    print(f"  updated: {entry.find('atom:updated', ns).text}")
    
    author = entry.find('atom:author', ns)
    if author:
        print(f"  author/name: {author.find('atom:name', ns).text}")
        print(f"  author/uri: {author.find('atom:uri', ns).text}")

print("\n" + "=" * 80)
print("THAT'S IT! No other fields available in WebSub feed.")
print("=" * 80)

print("\n❌ NOT AVAILABLE in WebSub:")
print("  - Scheduled start time")
print("  - Is live stream (boolean)")
print("  - Live status")
print("  - Duration")
print("  - View count")
print("  - Thumbnail URL")
print("  - Description")
print("  - Tags")
print("  - Category")

print("\n✅ DETECTION METHODS:")
print("  1. Title contains 'LIVE' (unreliable)")
print("  2. Multiple notifications for same video_id (reliable)")
print("  3. Published time changes (indicates archive)")
print("  4. Use yt-dlp to fetch metadata (no quota!)")
print("  5. Use YouTube API (costs quota)")

print("\n💡 RECOMMENDATION:")
print("  Use yt-dlp for metadata - it's free and gets everything!")
print("=" * 80)
