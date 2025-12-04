# Postiz API Payload Mockups (v2)

This document outlines the JSON payloads that will be sent to the Postiz API for each platform, based on the refactored code that strictly follows the documentation.

**Assumptions for Mock Data:**
*   **Video Title:** `Global Geopolitics Update`
*   **Video ID:** `dQw4w9WgXcQ`
*   **Video URL:** `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
*   **Configuration:**
    *   `POSTIZ_API_TYPE`: `schedule`
    *   `POSTIZ_API_DATE`: `2025-12-31T10:00:00.000Z`
*   **Fetched Data:**
    *   **Integration IDs:**
        *   Facebook: `int_fb_123`
        *   Telegram: `int_tg_456`
        *   Instagram: `int_ig_789`
        *   Blue Sky: `int_bs_101`
        *   X: `int_x_202`
        *   Threads: `int_th_303`
    *   **Uploaded Image:**
        *   ID: `img_555`
        *   Path: `https://uploads.postiz.com/img_555.jpg`

---

## 1. Facebook (Link Post)
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_fb_123" },
      "value": [
        {
          "content": "A new video has been added by ATP Geopolitics",
          "image": []
        }
      ],
      "settings": {
        "__type": "facebook",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      }
    }
  ]
}
```

## 2. Telegram
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_tg_456" },
      "value": [
        {
          "content": "A new video has been added by ATP Geopolitics\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "image": [
            { "id": "img_555", "path": "https://uploads.postiz.com/img_555.jpg" }
          ]
        }
      ],
      "settings": {
        "__type": "telegram"
      }
    }
  ]
}
```

## 3. Instagram
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_ig_789" },
      "value": [
        {
          "content": "New YouTube Video: Global Geopolitics Update\nYouTube.com/@atpgeo\nlink in bio",
          "image": [
            { "id": "img_555", "path": "https://uploads.postiz.com/img_555.jpg" }
          ]
        }
      ],
      "settings": {
        "__type": "instagram",
        "post_type": "post",
        "collaborators": []
      }
    }
  ]
}
```

## 4. Blue Sky
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_bs_101" },
      "value": [
        {
          "content": "New YouTube Video: Global Geopolitics Update\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "image": [
            { "id": "img_555", "path": "https://uploads.postiz.com/img_555.jpg" }
          ]
        }
      ],
      "settings": {
        "__type": "bluesky"
      }
    }
  ]
}
```

## 5. X (Twitter) Thread
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_x_202" },
      "value": [
        {
          "content": "New YouTube Video: Global Geopolitics Update (1/2)",
          "image": [
            { "id": "img_555", "path": "https://uploads.postiz.com/img_555.jpg" }
          ]
        },
        {
          "content": "https://www.youtube.com/watch?v=dQw4w9WgXcQ (2/2)",
          "image": []
        }
      ],
      "settings": {
        "__type": "x",
        "who_can_reply_post": "everyone"
      }
    }
  ]
}
```

## 6. Threads
**Endpoint:** `POST /api/public/v1/posts`

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_th_303" },
      "value": [
        {
          "content": "New Youtube Video: Global Geopolitics Update\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "image": [
            { "id": "img_555", "path": "https://uploads.postiz.com/img_555.jpg" }
          ]
        }
      ],
      "settings": {
        "__type": "threads"
      }
    }
  ]
}
```
