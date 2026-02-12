# Patent Search Application

A comprehensive web-based application for searching and analyzing patent data using Apache Solr. This application provides an intuitive interface for querying patent information by various criteria including patent IDs, examiners, law firms, prosecutors, and more.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Frontend Usage](#frontend-usage)
- [Data Model](#data-model)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Patent Search Application is a full-stack solution consisting of:

- **Backend**: FastAPI-based REST API that interfaces with Apache Solr
- **Frontend**: Vanilla JavaScript web interface for intuitive search and visualization
- **Data Source**: Apache Solr database containing patent information

---

## Features

### Search Capabilities

1. **Patent ID Search**: Search for specific patents by their ID(s)
2. **Examiner Search**: Find patents handled by specific patent examiners
3. **Law Firm Search**: Query patents by representing law firms
4. **Prosecutor/Attorney Search**: Search by attorney or prosecutor names
5. **GAU (Group Art Unit) Search**: Filter patents by GAU classification
6. **Advanced Search**: Build complex queries with multiple filters

### Analytics & Statistics

- **Examiner Statistics by Date Range**: Analyze examiner activity over time
- **Multi-dimensional Stats**: Get statistics for examiners, prosecutors, law firms, GAUs, assignees, USC classes, and entity types
- **GAU Distribution**: View unique GAU counts and distribution
- **CPC Classification Analysis**: Analyze CPC (Cooperative Patent Classification) data

### Export Features

- **JSON Export**: Download search results in JSON format
- **Excel Export**: Convert results to Excel spreadsheet

### Context-Aware Search

When viewing a single patent, explore related data:

- Patents by the same examiner
- Patents from the same law firm
- Patents by the same attorney/prosecutor
- Patents in the same GAU

---

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS/CSS)  │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         │ Solr API
         │
┌────────▼────────┐
│  Apache Solr    │
│   Database      │
└─────────────────┘
```

---

## Prerequisites

- **Python**: 3.8 or higher
- **Apache Solr**: Running instance with patent data indexed
- **Node.js/npm**: Optional, for any build tools
- **Modern Web Browser**: Chrome, Firefox, Safari, or Edge

### Python Dependencies

```
fastapi
uvicorn
httpx
pandas
openpyxl
python-dotenv
pydantic
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd patent-search-app
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SOLR_BASE_URL=http://localhost:8983/solr/your_core_name
```

Replace `your_core_name` with your actual Solr core name.

### 4. Start the Backend Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 5. Open the Frontend

Open `index.html` in your web browser, or serve it using a simple HTTP server:

```bash
# Using Python
python -m http.server 3000

# Then navigate to http://localhost:3000
```

---

## Configuration

### Backend Configuration

Edit the `.env` file to configure:

```env
# Solr Configuration
SOLR_BASE_URL=http://your-solr-host:8983/solr/core_name

# Optional: Logging
LOGGING_ENABLED=true
```

### Frontend Configuration

In `app.js`, update the API URL if needed:

```javascript
const API_URL = "http://localhost:8000"; // Change if backend runs on different host/port
```

---

## API Documentation

### Base URL

```
http://localhost:8000
```

### Endpoints

#### 1. Search Endpoints

##### Search by Patent ID

```http
POST /search/patent
Content-Type: application/json

{
  "patent_ids": ["12345678", "87654321"]
}
```

##### Search by Examiner

```http
POST /search/examiner
Content-Type: application/json

{
  "examiners": ["john smith", "jane doe"],
  "search_type": "latest_filed",
  "limit": 10
}
```

**Search Types:**

- `latest_filed`: Most recently filed applications
- `latest_approved`: Most recently issued patents
- `count`: Get count only (no results)
- `last_10_years`: Applications from last 10 years
- `latest_10_approved`: Latest 10 approved patents

##### Search by Law Firm

```http
POST /build/lawfirm-query
Content-Type: application/json

{
  "lawfirms": ["wilson sonsini", "cooley llp"],
  "search_type": "latest_filed",
  "limit": 10
}
```

##### Search by Prosecutor

```http
POST /build/prosecutor-query
Content-Type: application/json

{
  "prosecutors": ["attorney name"],
  "search_type": "latest_filed",
  "limit": 10
}
```

##### Search by GAU

```http
POST /build/gau-query
Content-Type: application/json

{
  "gaus": ["3682", "3685"],
  "limit": 20,
  "sort": "app_date desc"
}
```

#### 2. Statistics Endpoints

##### Examiner Statistics by Date Range

```http
POST /stats/examiners-by-date
Content-Type: application/json

{
  "from_date": "2023-01-01",
  "to_date": "2024-01-01",
  "limit": 10
}
```

**Response includes:**

- Application count per examiner
- Unique GAU count
- GAU distribution
- CPC classification distribution

##### General Statistics by Date Range

```http
POST /stats/by-date-range
Content-Type: application/json

{
  "type": "examiner",
  "from_date": "2023-01-01",
  "to_date": "2024-01-01",
  "limit": 10,
  "sort_order": "desc"
}
```

**Supported Types:**

- `examiner`
- `prosecutor`
- `lawfirm`
- `gau`
- `assignee`
- `usc`
- `entity`
- `action`

##### Total Statistics

```http
GET /stats/total
```

Returns overall counts:

- Total patents
- Total approved
- Total pending
- Total abandoned

#### 3. Query Building Endpoints

These endpoints build Solr query URLs without executing them:

- `POST /build/patent-query`
- `POST /build/examiner-query`
- `POST /build/lawfirm-query`
- `POST /build/prosecutor-query`
- `POST /build/attorney-query`
- `POST /build/gau-query`
- `POST /build/advanced-query`

#### 4. Query Execution

##### Execute Pre-built Query

```http
POST /execute-query
Content-Type: application/json

{
  "solr_query_url": "http://solr-url/select?q=..."
}
```

#### 5. Export Endpoints

##### Download as JSON

```http
POST /download/json
Content-Type: application/json

{
  "results": [...],
  "total_found": 100
}
```

##### Download as Excel

```http
POST /download/excel
Content-Type: application/json

{
  "results": [...],
  "total_found": 100
}
```

---

## Frontend Usage

### 1. Search by Patent ID

1. Type a patent ID in the input field
2. Press **Enter** to add it as a tag
3. Add multiple IDs if needed
4. Click **Search Patent**
5. View the generated Solr query URL
6. Click **Execute Query** to fetch results

### 2. Search by Examiner

1. Enter examiner name(s) (press Enter after each)
2. Select search type:
   - All Applications
   - Latest Issued
   - Last 10 Years
   - Latest 10 Years Issued
3. Set results limit
4. Click **Search Examiner**

### 3. Search by Law Firm

1. Enter law firm name(s)
2. Choose search type
3. Set limit
4. Click **Search Law Firm**

### 4. Context-Aware Exploration

When viewing a single patent:

1. Click **Examiner Stats** to see other patents by the same examiner
2. Click **Law Firm Stats** to see other patents from the same firm
3. Click **Attorney Stats** to see other patents by the same attorney
4. Click **GAU Stats** to see other patents in the same GAU

### 5. Statistics by Date Range

1. Select date range (defaults to last 1 year)
2. Choose statistic type (Examiner, Prosecutor, Law Firm, etc.)
3. Select sort order (Top/Least)
4. Set number of results
5. Click **Get Stats**

### 6. Viewing GAU Distribution

When viewing examiner results:

- GAU buttons appear showing the count of applications per GAU
- Click any GAU button to search for all patents in that GAU

### 7. Exporting Results

After executing a search:

1. Click **Download JSON** for JSON format
2. Click **Convert to Excel** for Excel format

---

## Data Model

### Patent Document Fields

| Field                    | Type    | Description                                                 |
| ------------------------ | ------- | ----------------------------------------------------------- |
| `id`                     | String  | Unique patent application ID                                |
| `title`                  | String  | Patent title                                                |
| `app_date`               | Date    | Application date                                            |
| `app_date_year`          | Integer | Application year                                            |
| `disposal_type`          | String  | Status: `iss` (issued), `pend` (pending), `abn` (abandoned) |
| `application_status`     | String  | Current status                                              |
| `examiner`               | String  | Assigned patent examiner                                    |
| `law_firm`               | Array   | Representing law firm(s)                                    |
| `all_attorney_names`     | Array   | Attorney/prosecutor name(s)                                 |
| `gau`                    | Array   | Group Art Unit code(s)                                      |
| `cpc_classification`     | Array   | CPC classification code(s)                                  |
| `usc`                    | String  | USC classification                                          |
| `assignee_last`          | String  | Patent assignee                                             |
| `small_entity_indicator` | Boolean | Small entity status                                         |
| `first_named_inventor`   | String  | Primary inventor                                            |
| `law_firm_address`       | String  | Law firm address                                            |

---

## Troubleshooting

### Common Issues

#### 1. Cannot Connect to Backend

**Error**: `Failed to fetch` or CORS errors

**Solution**:

- Verify backend is running: `http://localhost:8000`
- Check CORS configuration in `main.py`
- Ensure frontend API_URL matches backend address

#### 2. Solr Connection Failed

**Error**: `Failed to execute Solr query`

**Solution**:

- Verify Solr is running
- Check `SOLR_BASE_URL` in `.env` file
- Test Solr directly: `http://your-solr-url/solr/admin/cores`

#### 3. No Results Found

**Possible Causes**:

- Data not indexed in Solr
- Incorrect field names in queries
- Case sensitivity issues

**Solution**:

- Verify data is indexed: Query Solr directly
- Check field mappings in `STAT_TYPE_MAP`
- Names are converted to lowercase automatically

#### 4. Date Range Returns No Results

**Solution**:

- Ensure dates are in `YYYY-MM-DD` format
- Verify data exists in the selected range
- Check Solr date field format (`app_date`)

#### 5. Statistics Not Loading

**Solution**:

- Increase timeout in `httpx.AsyncClient(timeout=120.0)`
- Check Solr faceting configuration
- Reduce date range or limit

### Performance Tips

1. **Large Result Sets**: Use pagination or limit results
2. **Date Range Queries**: Narrow the date range for faster results
3. **Statistics**: Reduce the limit parameter for complex aggregations
4. **Caching**: Consider implementing Redis for frequently accessed queries

### Logging

Enable detailed logging by setting in `.env`:

```env
LOGGING_ENABLED=true
```

Check logs in the console output for debugging.

---

## API Error Codes

| Status Code | Meaning                                     |
| ----------- | ------------------------------------------- |
| 200         | Success                                     |
| 400         | Bad Request (invalid parameters)            |
| 404         | Resource Not Found                          |
| 500         | Internal Server Error                       |
| 503         | Service Unavailable (Solr connection issue) |

---

## Development

### Project Structure

```
patent-search-app/
├── main.py                 # FastAPI backend
├── app.js                  # Frontend JavaScript
├── index.html              # Frontend HTML
├── styles.css              # Frontend styles
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
├── logger/
│   └── logger.py          # Logging configuration
└── README.md              # This file
```

### Adding New Search Types

1. **Backend**: Add new endpoint in `main.py`
2. **Frontend**: Add UI controls in `index.html`
3. **JavaScript**: Add handler function in `app.js`
4. **Mapping**: Update `STAT_TYPE_MAP` if needed

### Extending Statistics

To add a new statistic type:

1. Add to `STAT_TYPE_MAP` in `main.py`:

```python
STAT_TYPE_MAP = {
    # ...existing mappings...
    "new_type": "solr_field_name",
}
```

2. Add option in `index.html`:

```html
<option value="new_type">New Type Display Name</option>
```

---

## API Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## License

[Add your license information here]

---

## Support

For issues, questions, or contributions:

- Open an issue in the repository
- Contact the development team
- Check existing documentation

---

## Future Enhancements

Potential features for future versions:

- User authentication and saved searches
- Advanced visualization (charts, graphs)
- Bulk export functionality
- Real-time notifications
- Search history
- Collaborative features
- Mobile responsive design improvements
- API rate limiting
- Caching layer (Redis)
- Database backup and restore

---

## Version History

- **v1.0.0**: Initial release with core search and statistics functionality

---

**Last Updated**: February 2026
