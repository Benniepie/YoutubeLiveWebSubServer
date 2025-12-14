# Postiz API Payloads v3

## Assumptions
* **Video Title:** `Global Geopolitics Update`
* **Video URL:** `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
* **Thumbnail:** `https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg`
* **Description:** `This is a description with #Ukraine #Russia and extra tags.`
* **Config:** `POSTIZ_API_TYPE` = `schedule`, `POSTIZ_API_DATE` = `2025-12-31...`

---

## 1. Facebook (Link Post)
*Note: Validated code passes `image: []` and puts URL in settings. The `original_image_obj` is computed but NOT used in the payload.*

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
          "content": "New Video: Global Geopolitics Update\n\n#Ukraine #Russia",
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

## 2. Reddit (Native Embed)
*Note: Uses `subreddit` setting with `type: link` for native embed. `image` array is empty.*

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_reddit_789" },
      "value": [
        {
          "content": "This is a description with #Ukraine #Russia and extra tags...",
          "image": []
        }
      ],
      "settings": {
        "__type": "reddit",
        "subreddit": [
          {
            "value": {
              "subreddit": "atpgeo",
              "title": "Global Geopolitics Update",
              "type": "link",
              "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
              "is_flair_required": true,
              "flair": { "id": "flair_hits_losses_123" }
            }
          }
        ]
      }
    }
  ]
}
```

## 3. Instagram (4:5 Thumbnail)
*Note: Uses the Resized Image ID.*

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_ig_456" },
      "value": [
        {
          "content": "New Video: Global Geopolitics Update\nlink in bio\n\n#Ukraine #Russia",
          "image": [
            { "id": "img_resized_45", "path": "https://uploads.postiz.com/..." }
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

## 4. X (Twitter)
*Note: Uses Original Image ID in Tweet 1.*

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_x_999" },
      "value": [
        {
          "content": "New Video: Global Geopolitics Update\n\n#Ukraine #Russia",
          "image": [
             { "id": "img_orig_12", "path": "https://uploads.postiz.com/..." }
          ]
        },
        {
          "content": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
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

## 5. Threads (Topic Tag)
*Note: No image uploaded. Topic tag sent separately.*

```json
{
  "type": "schedule",
  "date": "2025-12-31T10:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "int_th_101" },
      "value": [
        {
          "content": "New Video: Global Geopolitics Update\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ\n\n#Ukraine #Russia",
          "image": []
        }
      ],
      "settings": {
        "__type": "threads"
      }
    }
  ]
}
```
