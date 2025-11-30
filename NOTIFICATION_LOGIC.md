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

    %% API Fields
    FetchAPI --> APIFields[[Fetched Fields:<br/>scheduled_start_time<br/>actual_start_time<br/>actual_end_time<br/>live_status<br/>is_live_content]]
    APIFields --> CheckRetry{Is New &amp;<br/>Missing Start Time?}

    %% Retry Logic
    CheckRetry -- Yes --> ReleaseLock1[Release Lock] --> ScheduleRetry[Schedule Retry 60s] --> Resp200
    CheckRetry -- No --> UpdateDB[(Update Metadata)]

    %% Notification Rules - Expanded
    UpdateDB --> CheckNotLive{Status == 'not_live'?}
    CheckNotLive -- Yes --> LogSkip[Log: Not Live] --> ReleaseLock2
    CheckNotLive -- No --> CheckIsLive{Status == 'is_live'?}

    %% Live Now Path
    CheckIsLive -- Yes --> CheckLiveSent{Already sent<br/>'live_now'?}
    CheckLiveSent -- Yes --> LogDuplicate1[Log: Duplicate] --> ReleaseLock2
    CheckLiveSent -- No --> NotifyLive[Send: LIVE NOW]

    %% Upcoming/Reschedule Path
    CheckIsLive -- No --> CheckUpcoming{Status == 'is_upcoming'?}
    CheckUpcoming -- No --> LogSkip
    CheckUpcoming -- Yes --> CheckWindow{Starts in < 2h?}

    CheckWindow -- No --> LogWait[Log: > 2h Wait] --> ReleaseLock2
    CheckWindow -- Yes --> CheckResched{Time Changed?}

    CheckResched -- Yes --> NotifyResched[Send: RESCHEDULED]
    CheckResched -- No --> CheckNewUpcoming{Is New OR<br/>Not Notified?}

    CheckNewUpcoming -- Yes --> NotifyUpcoming[Send: UPCOMING]
    CheckNewUpcoming -- No --> LogDuplicate2[Log: Duplicate] --> ReleaseLock2

    %% Action
    NotifyLive --> SendDiscord[Send to Discord]
    NotifyUpcoming --> SendDiscord
    NotifyResched --> SendDiscord

    %% Finalization
    SendDiscord --> LogDelivery[(Log Delivery Status)] --> DebugTel

    DebugTel[Send Debug Telegram] --> ReleaseLock2[Release Lock] --> Resp200

    %% Styling
    style Start fill:#f9f,stroke:#333,stroke-width:2px,color:#000
    style Resp200 fill:#9f9,stroke:#333,stroke-width:2px,color:#000
    style Resp403 fill:#f99,stroke:#333,stroke-width:2px,color:#000
    style Resp400 fill:#f99,stroke:#333,stroke-width:2px,color:#000
    style SaveDB fill:#ccf,stroke:#333,stroke-width:2px,color:#000
    style UpdateDB fill:#ccf,stroke:#333,stroke-width:2px,color:#000
    style LogDelivery fill:#ccf,stroke:#333,stroke-width:2px,color:#000
    style SendDiscord fill:#7289da,stroke:#333,stroke-width:2px,color:#000
    style APIFields fill:#fff,stroke:#333,stroke-width:2px,color:#000
```

## Detailed Steps

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
    *   The system queries the **YouTube Data API** for full details.
    *   **Fields Fetched**: `scheduled_start_time`, `actual_start_time`, `actual_end_time`, `live_status`, `is_live_content`, etc.
    *   **Retry Logic**: If it's a *new* video but the API doesn't have `scheduled_start_time` yet (common race condition), the system waits 60 seconds and retries.

6.  **Notification Rules (Expanded Decision Tree)**:
    *   **Is it Live Content?** If status is `not_live`, ignore.
    *   **Is it LIVE NOW?** (`is_live`)
        *   **Already Sent?** Check DB if 'live_now' notification succeeded.
        *   **Yes** -> Ignore (Duplicate).
        *   **No** -> **Send LIVE NOW**.
    *   **Is it UPCOMING?** (`is_upcoming`)
        *   **Starts < 2 Hours?** If > 2 hours, ignore (wait for later notification).
        *   **Time Changed?** If scheduled time differs from DB -> **Send RESCHEDULED**.
        *   **Is New/Unsent?** If it's a new video OR never successfully notified -> **Send UPCOMING**.
        *   Otherwise -> Ignore (Duplicate).

7.  **Dispatch**:
    *   **Discord**: Sends a rich embed to the configured Webhook.
    *   **Logging**: Records the delivery status (`success`/`failed`) in the database.
    *   **Debug**: Sends a summary to the admin Telegram channel.
