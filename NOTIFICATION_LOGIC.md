# Notification Logic Flow

This document describes the logic flow for processing YouTube notifications, from the incoming Webhook request to the final Discord notification.

## Notification Process Diagram

```mermaid
flowchart TD
    %% Entry Point
    Start([Incoming Webhook POST]) --> Verify{Verify Signature?}
    Verify -- Invalid --> Resp403([403 Forbidden])
    Verify -- Valid --> ParseXML[Parse XML Body]

    %% Parsing & Initial Validation
    ParseXML -- Error --> Resp400([400 Bad Request])
    ParseXML -- Success --> CheckEntry{Has &lt;entry&gt; tag?}

    CheckEntry -- No --> LogDelete[Log: Deletion/No Entry] --> Resp200([200 OK])
    CheckEntry -- Yes --> ExtractData[Extract Video Data]

    %% Database & Concurrency
    ExtractData --> SaveDB[(Save to DB)]
    SaveDB --> Process[Process Video Event]
    Process --> Lock{Acquire Lock?}

    Lock -- Fail (Timeout) --> Skip[Skip: Concurrent Processing] --> Resp200
    Lock -- Success --> FetchAPI[Fetch YouTube Data API]

    %% Retry Logic
    FetchAPI --> CheckRetry{Is New &amp; No Start Time?}
    CheckRetry -- Yes --> ReleaseLock1[Release Lock] --> ScheduleRetry[Schedule Retry 60s] --> Resp200
    CheckRetry -- No --> UpdateDB[(Update Metadata)]

    %% Notification Rules
    UpdateDB --> CheckLive{Is Live Content?}
    CheckLive -- No --> LogSkip[Log: Not Live] --> ReleaseLock2
    CheckLive -- Yes --> Rules{Notification Rules}

    %% Rule Evaluation
    Rules -- Live Now --> NotifyLive[Send: LIVE NOW]
    Rules -- Upcoming &lt; 2h --> NotifyUpcoming[Send: UPCOMING]
    Rules -- Rescheduled --> NotifyResched[Send: RESCHEDULED]
    Rules -- Ignore/Duplicate --> LogIgnore[Log: No Notification]

    %% Action
    NotifyLive --> SendDiscord[Send to Discord]
    NotifyUpcoming --> SendDiscord
    NotifyResched --> SendDiscord

    %% Finalization
    SendDiscord --> LogDelivery[(Log Delivery Status)] --> DebugTel
    LogIgnore --> DebugTel[Send Debug Telegram]
    LogSkip --> DebugTel

    DebugTel --> ReleaseLock2[Release Lock] --> Resp200

    %% Styling
    style Start fill:#f9f,stroke:#333,stroke-width:2px
    style Resp200 fill:#9f9,stroke:#333,stroke-width:2px
    style Resp403 fill:#f99,stroke:#333,stroke-width:2px
    style Resp400 fill:#f99,stroke:#333,stroke-width:2px
    style SaveDB fill:#ccf,stroke:#333,stroke-width:2px
    style UpdateDB fill:#ccf,stroke:#333,stroke-width:2px
    style LogDelivery fill:#ccf,stroke:#333,stroke-width:2px
    style SendDiscord fill:#7289da,stroke:#333,stroke-width:2px,color:#fff
```

## detailed Steps

1.  **Webhook Verification**:
    *   The server receives a `POST` request at `/webhook`.
    *   It verifies the `X-Hub-Signature` header against the stored `SECRET_KEY`.
    *   If invalid, returns `403 Forbidden`.

2.  **XML Parsing**:
    *   The request body (XML) is parsed to extract video details (`video_id`, `title`, `published`, `link`).
    *   If the `<entry>` tag is missing, it's treated as a deletion event and ignored.

3.  **Database Persistence**:
    *   The raw notification is saved to the `notification_events` table.
    *   The `videos` table is updated or created.
    *   The system determines if this is a "new" video or an update.

4.  **Concurrency Control**:
    *   A lock is acquired for the specific `video_id`.
    *   If the lock cannot be acquired (e.g., another request for the same video is processing), the request is skipped to prevent race conditions.

5.  **Metadata Fetch & Retry**:
    *   The system queries the **YouTube Data API** for full details (`liveStreamingDetails`, `snippet`).
    *   **Retry Logic**: If it's a *new* video but the API doesn't have `scheduled_start_time` yet (common race condition), the system waits 60 seconds and retries.

6.  **Notification Rules**:
    *   The system evaluates if a notification should be sent based on:
        *   **Live Status**: Must be `is_live`, `is_upcoming`, or `was_live`.
        *   **Timing**: Upcoming streams are only notified if they start within **2 hours**.
        *   **History**: Checks the `delivery_tracking` table to prevent duplicate notifications.
        *   **Rescheduling**: Detects if a scheduled time has changed significantly.

7.  **Dispatch**:
    *   **Discord**: Sends a rich embed to the configured Webhook.
    *   **Logging**: Records the delivery status (`success`/`failed`) in the database.
    *   **Debug**: Sends a summary to the admin Telegram channel.
