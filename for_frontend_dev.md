# Frontend Developer Guide (Next.js)

Welcome! This backend provides the API endpoints needed to build the Yale Radiology Policies chat interface. You'll primarily interact with the authentication endpoint to log users in and the chat endpoints to manage conversations, stream responses, and maintain chat history.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Users log in with their email and password to get a short-lived access token, which must be sent with subsequent requests.

### Login Endpoint:

- **Path**: `/auth/token`
- **Method**: `POST`
- **Request Body Type**: `application/x-www-form-urlencoded` (standard for OAuth2 password flow)
- **Form Fields**:
  - `username`: The user's email address.
  - `password`: The user's plain text password.
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiI...", // The JWT token string
    "token_type": "bearer"
  }
  ```
- **Error Response (401 Unauthorized)**:
  ```json
  {
    "detail": "Incorrect email or password"
  }
  ```

**Action**: Store the `access_token` securely (e.g., in memory, session storage - consider security implications). Store the `token_type` (it will always be "bearer").

### Making Authenticated Requests:

For all subsequent requests to protected endpoints (anything under `/chat`, `/auth/users/me`), you must include the Authorization header:

```
Authorization: Bearer <access_token>
```

Replace `<access_token>` with the actual token string you received from `/auth/token`.

## Chat Interaction & History

All real-time chat happens via a single streaming endpoint. Separate endpoints are provided to list past chats and retrieve their message history.

### Listing User's Chats:

- **Path**: `/chat`
- **Method**: `GET`
- **Authentication**: Required (send `Authorization: Bearer <token>` header).
- **Query Parameters**:
  - `archived` (boolean, optional, default=false): Set to true to list archived chats. If false or omitted, lists active (non-archived) chats.
  - `skip` (integer, optional, default=0): For pagination.
  - `limit` (integer, optional, default=100): For pagination.
- **Success Response (200 OK)**: An array of ChatSummary objects, ordered by most recently updated:
  ```json
  [
    {
      "id": 123,
      "title": "MRI Contrast Policy Discussion",
      "created_at": "2023-10-27T10:00:00Z",
      "updated_at": "2023-10-27T10:05:30Z",
      "is_archived": false // Indicates if the chat is archived
    }
    // ... more chat summaries
  ]
  ```

**Purpose**: To display a list of the user's active or archived conversations in the UI. Use the `archived` parameter to control which list is shown.

### Getting Messages for a Specific Chat:

- **Path**: `/chat/{chat_id}/messages` (replace `{chat_id}` with the actual ID)
- **Method**: `GET`
- **Authentication**: Required. The backend also checks if the `chat_id` belongs to the authenticated user.
- **Query Parameters**:
  - `skip` (integer, optional, default=0): For pagination.
  - `limit` (integer, optional, default=100): For pagination.
- **Success Response (200 OK)**: An array of MessageSummary objects, ordered chronologically (oldest first):
  ```json
  [
    {
      "id": 501,
      "role": "user",
      "content": "What is the policy for MRI contrast?",
      "created_at": "2023-10-27T10:05:00Z"
    },
    {
      "id": 502,
      "role": "assistant",
      "content": "Based on Policy ID 5 (MRI Contrast Guidelines), ...",
      "created_at": "2023-10-27T10:05:30Z"
    }
    // ... more messages
  ]
  ```
- **Error Responses**: 404 Not Found (if chat doesn't exist or belong to user), 401 Unauthorized.

**Purpose**: To load the message history when a user selects a past conversation (active or archived).

### Sending a Message & Streaming Response:

- **Path**: `/chat/stream`
- **Method**: `POST`
- **Authentication**: Required.
- **Request Body (JSON)**:
  ```json
  {
    "user_id": integer, // ID of the authenticated user (must match token)
    "message": string,  // The user's new message
    "chat_id": integer | null // ID of chat to continue, or null/0 for new chat
  }
  ```
- **Response**: `text/event-stream` (Server-Sent Events).

#### Handling the /chat/stream SSE Response

You need to use a client-side library or method capable of handling SSE streams from a POST request (native EventSource only supports GET). `@microsoft/fetch-event-source` is recommended.

1. **Connection**: Establish the connection to `/chat/stream` with the POST method, appropriate headers (`Content-Type: application/json`, `Authorization: Bearer <token>`), and the JSON request body.
2. **Events**: Listen for `message` events.
3. **Data Parsing**: Parse `event.data` as JSON. It will be a StreamChunk object: `{ "type": "...", "data": {...} }`.
4. **Handling type**:
   - `chat_info`: Contains `data: { "chat_id": number, "title": string|null }`. Store the `chat_id` if this is a new conversation. Use it for subsequent requests in this chat. Update UI title if desired.
   - `text_delta`: Contains `data: { "delta": string }`. Append this delta to the currently displayed assistant message in the UI.
   - `tool_call`: Contains `data: { "id": string, "name": string, "input": object }`. Optionally display a "Searching policies..." indicator.
   - `tool_output`: Contains `data: { "tool_call_id": string, "output": any }`. Optionally hide the "Searching..." indicator.
   - `error`: Contains `data: { "message": string }`. Display the error message to the user. The stream might terminate.
   - `status`: Contains `data: { "status": "complete" | "error", "chat_id": number }`. Indicates the end of the response stream for this user message. Use this to re-enable the user input field and finalize the assistant's message in the history.

## Chat Management

Endpoints for renaming, archiving, and unarchiving chat sessions.

### Rename a Chat:

- **Path**: `/chat/{chat_id}/rename`
- **Method**: `PATCH`
- **Authentication**: Required.
- **Request Body (JSON)**:
  ```json
  {
    "new_title": "Your Concise New Chat Title" // Max 255 characters
  }
  ```
- **Success Response (200 OK)**: The updated ChatSummary object for the renamed chat:
  ```json
  {
    "id": 123,
    "title": "Your Concise New Chat Title",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T11:15:00Z", // Note updated_at timestamp
    "is_archived": false
  }
  ```
- **Error Responses**: 404 Not Found (if chat doesn't exist or belong to user), 401 Unauthorized, 422 Unprocessable Entity (if title is invalid).

**Purpose**: Allows the user to rename a chat session listed in the UI.

### Archive a Chat:

- **Path**: `/chat/{chat_id}/archive`
- **Method**: `PATCH`
- **Authentication**: Required.
- **Request Body**: None
- **Success Response (200 OK)**: The updated ChatSummary object for the archived chat:
  ```json
  {
    "id": 123,
    "title": "Your Concise New Chat Title", // Title remains
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T11:20:00Z", // Note updated_at timestamp
    "is_archived": true // Flag is now true
  }
  ```
- **Error Responses**: 404 Not Found, 401 Unauthorized.

**Purpose**: To move a chat from the active list to the archived list. After calling this, refresh the active chat list (using `GET /chat?archived=false`).

### Unarchive a Chat:

- **Path**: `/chat/{chat_id}/unarchive`
- **Method**: `PATCH`
- **Authentication**: Required.
- **Request Body**: None
- **Success Response (200 OK)**: The updated ChatSummary object for the unarchived chat:
  ```json
  {
    "id": 123,
    "title": "Your Concise New Chat Title",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T11:25:00Z", // Note updated_at timestamp
    "is_archived": false // Flag is now false
  }
  ```
- **Error Responses**: 404 Not Found, 401 Unauthorized.

**Purpose**: To move a chat from the archived list back to the active list. After calling this, refresh the archived chat list (using `GET /chat?archived=true`) and potentially the active list.

### Archive All Active Chats:

- **Path**: `/chat/archive-all`
- **Method**: `POST`
- **Authentication**: Required.
- **Request Body**: None
- **Success Response (200 OK)**: Confirmation message and count:
  ```json
  {
    "message": "Successfully archived 5 active chat session(s).",
    "count": 5 // Number of chats that were actually archived
  }
  ```
- **Error Responses**: 401 Unauthorized, 500 Internal Server Error.

**Purpose**: Provides a bulk action to archive all currently active chats for the user. After calling this, refresh the active chat list (it should become empty).

## Frontend State Considerations

- **Authentication Token**: Store the JWT securely and refresh it as needed (implement token refresh logic if backend supports it later).
- **Current chat_id**: Keep track of the ID for the currently active conversation. Reset to null when starting a new chat.
- **Displayed Messages**: Maintain an array of message objects for the current chat to render in the UI. Append user messages immediately, and build assistant messages progressively using `text_delta` events.
- **Chat Lists (Active/Archived)**: Maintain separate states or filter the fetched list based on the `is_archived` flag and the current view (Active vs. Archived). Refresh these lists after relevant management actions (rename, archive, unarchive, archive-all).
- **Loading/Busy State**: Track when the backend is processing a request to disable input and show indicators. Use the `status` event to know when processing is finished. Track loading states for list refreshes and management actions.

## CORS

For local development, ensure the backend `config.py` has `http://localhost:3000` (or your Next.js dev port) in `API.CORS_ORIGINS`. Update this for deployed environments.
