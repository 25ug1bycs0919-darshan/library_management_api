# Library Management API

A simple REST API for managing books, library members, and borrowing records. It
uses FastAPI, SQLAlchemy, SQLite, and Pydantic.

## Requirements

- Python 3.10 or newer
- pip

## Install and run

From the project directory, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies and start the development server:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive Swagger
documentation is at <http://127.0.0.1:8000/docs>, and ReDoc is at
<http://127.0.0.1:8000/redoc>.

The SQLite database is created automatically as `library.db` in the project
directory the first time the application starts.

## API endpoints

All endpoints are under `/api`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/books` | Add a book |
| `GET` | `/books` | List books |
| `GET` | `/books/{book_id}` | Get a book |
| `PUT` | `/books/{book_id}` | Update a book |
| `DELETE` | `/books/{book_id}` | Delete a book |
| `POST` | `/members` | Register a member |
| `GET` | `/members` | List members |
| `GET` | `/members/{member_id}` | Get a member |
| `PUT` | `/members/{member_id}` | Update a member |
| `DELETE` | `/members/{member_id}` | Delete a member |
| `POST` | `/borrowings/issue` | Issue a book |
| `POST` | `/borrowings/{borrowing_id}/return` | Return a borrowed book |
| `GET` | `/borrowings` | List currently borrowed books |
| `GET` | `/borrowings/history` | View borrowing history |

Books and members with borrowing history cannot be deleted, preserving the
history records. A member can have no more than five unreturned books at once.
Issuing an unavailable book or returning a book twice responds with `409
Conflict`; missing resources respond with `404 Not Found`.

## Sample requests and responses

Add a book (`POST /api/books`):

```json
{
  "title": "The Hobbit",
  "author": "J. R. R. Tolkien",
  "isbn": "9780547928227",
  "total_copies": 3
}
```

Example response (`201 Created`):

```json
{
  "id": 1,
  "title": "The Hobbit",
  "author": "J. R. R. Tolkien",
  "isbn": "9780547928227",
  "total_copies": 3,
  "available_copies": 3
}
```

Register a member (`POST /api/members`):

```json
{
  "name": "Avery Reader",
  "email": "avery@example.com",
  "phone": "555-0100"
}
```

Issue a book (`POST /api/borrowings/issue`):

```json
{
  "book_id": 1,
  "member_id": 1
}
```

Example response (`201 Created`):

```json
{
  "id": 1,
  "book_id": 1,
  "member_id": 1,
  "borrowed_at": "2026-10-30T06:30:00Z",
  "returned_at": null
}
```

Return it with `POST /api/borrowings/1/return`. The response contains the
borrowing record with `returned_at` set. Validation errors use FastAPI's
standard `422 Unprocessable Entity` response.
