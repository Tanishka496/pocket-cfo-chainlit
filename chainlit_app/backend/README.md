# AI Pocket CFO - Transaction Management Module

A complete, production-ready transaction management module for small business financial tracking built with **FastAPI**, **Supabase**, and **Python**.

## Features

✅ **View Transactions** - Paginated list of all transactions  
✅ **Search** - Search by keyword across description and category  
✅ **Filter** - By category, type (income/expense), and date range  
✅ **Sort** - By date, amount, or category  
✅ **CRUD Operations** - Create, read, update, delete transactions  
✅ **Personal Expense Warning** - Flag suspicious personal expenses  
✅ **Export to CSV** - Download transaction data as CSV  
✅ **Export to PDF** - Generate formatted report with summary  
✅ **Clean Error Handling** - Comprehensive error responses  
✅ **Type Safety** - Full Pydantic validation  
✅ **Async/Await** - Fast, non-blocking operations  
✅ **SQL Injection Safe** - Parameterized queries

## Project Structure

```
app/
├── main.py                          # FastAPI entry point
├── routes/
│   └── transactions.py             # Transaction endpoints
├── services/
│   └── transaction_service.py      # Business logic
├── models/
│   └── transaction_models.py       # Pydantic models
└── utils/
    ├── supabase_client.py          # Database client
    └── export_utils.py             # CSV/PDF generation
```

## Installation

### Prerequisites

- Python 3.9+
- Supabase project (with PostgreSQL database)

### Setup

1. **Clone/Create Project**

```bash
cd "module 4"
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Environment**

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SECRET_KEY=your-jwt-secret
```

5. **Database Setup**

Run this in Supabase SQL Editor to create the transactions table:

```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  amount NUMERIC(12, 2) NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL,
  transaction_date DATE NOT NULL,
  is_personal BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(id)
);

-- Create index for user_id for faster queries
CREATE INDEX transactions_user_id_idx ON transactions(user_id);
CREATE INDEX transactions_transaction_date_idx ON transactions(transaction_date);
CREATE INDEX transactions_category_idx ON transactions(category);
```

6. **Run Application**

```bash
python -m uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

## API Endpoints

### Base URL

`http://localhost:8000/transactions`

### Get All Transactions

```http
GET /transactions?page=1&page_size=10&sort_by=transaction_date&order=desc
```

**Query Parameters:**

- `page` (int, default: 1) - Page number
- `page_size` (int, default: 10, max: 100) - Results per page
- `search` (string) - Search keyword
- `category` (string) - Filter by category
- `type` (string) - Filter by type: `income` or `expense`
- `start_date` (date) - Start date filter (YYYY-MM-DD)
- `end_date` (date) - End date filter (YYYY-MM-DD)
- `sort_by` (string) - Sort field: `transaction_date`, `amount`, or `category`
- `order` (string) - Sort order: `asc` or `desc`

**Response:**

```json
{
  "success": true,
  "message": "Transactions retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-123",
      "description": "Office supplies",
      "amount": "150.50",
      "type": "expense",
      "category": "Supplies",
      "transaction_date": "2024-02-27",
      "is_personal": false,
      "created_at": "2024-02-27T10:30:00",
      "updated_at": "2024-02-27T10:30:00",
      "warning": null
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

### Get Single Transaction

```http
GET /transactions/{id}
```

### Create Transaction

```http
POST /transactions
Content-Type: application/json

{
  "description": "Monthly subscription",
  "amount": "99.99",
  "type": "expense",
  "category": "Software",
  "transaction_date": "2024-02-27",
  "is_personal": false
}
```

### Update Transaction

```http
PUT /transactions/{id}
Content-Type: application/json

{
  "amount": "109.99",
  "category": "Subscriptions"
}
```

### Delete Transaction

```http
DELETE /transactions/{id}
```

### Export to CSV

```http
GET /transactions/export/csv?category=Supplies&start_date=2024-01-01
```

**Query Parameters:** Same as GET /transactions (but no pagination)

**Response:** CSV file download

**Example CSV Output:**

```csv
Transaction Date,Description,Category,Type,Amount,Is Personal
2024-02-27,Office supplies,Supplies,expense,150.50,No
2024-02-25,Client payment,Revenue,income,5000.00,No
```

### Export to PDF

```http
GET /transactions/export/pdf?type=expense&start_date=2024-01-01&end_date=2024-02-27
```

**Query Parameters:** Same as GET /transactions (but no pagination)

**Response:** PDF file download with formatted report and summary

**Report Includes:**

- Transaction details table (Date, Description, Category, Type, Amount)
- Summary section:
  - Total Income
  - Total Expense
  - Net Profit

## Features Detail

### 1. Dynamic Filtering

Combine multiple filters simultaneously:

```http
GET /transactions?category=Personal&type=expense&start_date=2024-01-01&search=medical
```

### 2. Pagination

Efficient pagination with total count:

```http
GET /transactions?page=2&page_size=25
```

### 3. Sorting

Sort by any numeric or text field:

```http
GET /transactions?sort_by=amount&order=asc
```

### 4. Personal Expense Warning

Transactions marked as personal or with "Personal" category include a warning:

```json
{
  "warning": "This expense is marked as personal and may affect business profit clarity."
}
```

### 5. Export Features

**CSV Export** - Perfect for Excel/Sheets analysis

- All filtered transactions in clean format
- Compatible with all spreadsheet applications

**PDF Export** - Professional financial report

- Formatted transaction table
- Summary with totals
- Perfect for sharing with accountants

## Database Schema

```sql
Table: transactions

Columns:
- id (UUID, PK)
- user_id (UUID, FK) - Links to auth.users
- description (TEXT) - Transaction description
- amount (NUMERIC) - Transaction amount
- type (TEXT) - 'income' or 'expense'
- category (TEXT) - Transaction category
- transaction_date (DATE) - When transaction occurred
- is_personal (BOOLEAN) - Personal expense flag
- created_at (TIMESTAMP) - Record creation time
- updated_at (TIMESTAMP) - Last update time
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "message": "Descriptive error message",
  "error_code": "ERROR_CODE"
}
```

**Common Error Codes:**

- `TRANSACTION_NOT_FOUND` - Transaction doesn't exist
- `TRANSACTION_FETCH_ERROR` - Failed to retrieve transaction
- `TRANSACTION_CREATE_ERROR` - Failed to create transaction
- `TRANSACTION_UPDATE_ERROR` - Failed to update transaction
- `TRANSACTION_DELETE_ERROR` - Failed to delete transaction
- `EXPORT_CSV_ERROR` - Failed to generate CSV
- `EXPORT_PDF_ERROR` - Failed to generate PDF
- `NO_DATA_FOR_EXPORT` - No transactions to export

## Authentication Note

⚠️ **Important:** The current implementation uses a placeholder user ID. In production, you must:

1. Implement JWT token extraction from Authorization header
2. Decode and validate JWT tokens using your SECRET_KEY
3. Extract user_id from token claims

Replace the `get_user_id()` function in `routes/transactions.py`:

```python
from fastapi import Request
from jose import jwt, JWTError

async def get_user_id(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Testing with cURL

```bash
# Get all transactions
curl http://localhost:8000/transactions

# Search transactions
curl "http://localhost:8000/transactions?search=office"

# Create transaction
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Office rent",
    "amount": "2000.00",
    "type": "expense",
    "category": "Rent",
    "transaction_date": "2024-02-27",
    "is_personal": false
  }'

# Export CSV
curl "http://localhost:8000/transactions/export/csv?category=Supplies" \
  --output transactions.csv

# Export PDF
curl "http://localhost:8000/transactions/export/pdf" \
  --output report.pdf
```

## Production Recommendations

1. **Security**
   - Change CORS origins to specific domains
   - Implement proper JWT authentication
   - Use HTTPS only
   - Add rate limiting
   - Validate and sanitize all inputs

2. **Performance**
   - Add database query caching
   - Implement request pagination limits
   - Add database indexes (included in schema)
   - Monitor API response times

3. **Logging**
   - Implement structured logging
   - Add request/response logging
   - Monitor errors and exceptions

4. **Testing**
   - Add unit tests
   - Add integration tests
   - Test export functionality
   - Load test pagination

## License

MIT

## Support

For issues or questions, contact support@aipocketcfo.com
