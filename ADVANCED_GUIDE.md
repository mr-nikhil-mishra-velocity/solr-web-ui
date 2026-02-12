# Advanced Flexible Search - Complete Guide

## Overview

The **Advanced Search** interface provides complete flexibility to search, filter, group, and sort on **ANY field** in your Solr index.

Unlike the simple UI (which has 6 predefined search types), this advanced interface lets you:

✅ Search on **any field** (examiner_name, GAU, art_unit, whatever you have)
✅ **Group by** (facet on) any field  
✅ **Order by** (sort) any field
✅ Use **multiple filters** simultaneously
✅ Use full **Solr query syntax**
✅ Combine multiple operations in one query

---

## Quick Examples

### Example 1: Search by Examiner Name

**What you want**: Find all applications examined by "JOHN DOE"

**Simple Search Tab:**
```
Field Name: examiner_name
Search Value: JOHN DOE
Match Type: Exact Match
```

**Generated Solr Query:**
```
q=examiner_name:"JOHN DOE"&rows=10&wt=json
```

---

### Example 2: Group by GAU (Group Art Unit)

**What you want**: Count how many applications per GAU

**Group By Tab:**
```
Group By Field: gau
Max Groups: 20
```

**Generated Solr Query:**
```
q=*:*&rows=0&facet=true&facet.field=gau&facet.limit=20&wt=json
```

---

### Example 3: Complex Search with Multiple Filters

**What you want**: Find applications:
- From 2020
- That are pending
- Sorted by application date
- Show only id, title, and examiner

**Advanced Query Tab:**
```
Main Query: *:*
Filter Queries:
  app_date_year:2020
  disposal_type:pend
Sort: app_date desc
Fields to Return: id,title,examiner_name
Rows: 20
```

**Generated Solr Query:**
```
q=*:*
&fq=app_date_year:2020
&fq=disposal_type:pend
&sort=app_date desc
&fl=id,title,examiner_name
&rows=20
&wt=json
```

---

### Example 4: Group by Status for Specific Examiner

**What you want**: For examiner "JOHN DOE", how many applications are pending vs granted vs abandoned?

**Group By Tab:**
```
Group By Field: disposal_type
Filter Field: examiner_name
Filter Value: JOHN DOE
```

**Generated Solr Query:**
```
q=examiner_name:"JOHN DOE"
&rows=0
&facet=true
&facet.field=disposal_type
&wt=json
```

**Result:**
```json
{
  "groups": [
    {"value": "pend", "count": 45},
    {"value": "patented", "count": 23},
    {"value": "abandoned", "count": 8}
  ]
}
```

---

## Three Search Modes

### Mode 1: Simple Search

**Use Case:** Quick field-value searches

**Perfect for:**
- Search by examiner: `examiner_name = "JOHN DOE"`
- Search by GAU: `gau = "2100"`
- Search by art unit: `art_unit = "2155"`
- Search by any single field

**Features:**
- Exact or partial matching
- Optional sorting
- Results limit control

**API Endpoint:** `POST /search`

---

### Mode 2: Advanced Query

**Use Case:** Complex searches with multiple conditions

**Perfect for:**
- Multiple filters (year AND status AND examiner)
- Wildcard searches (`title:*battery*`)
- Boolean logic (`examiner_name:JOHN OR examiner_name:JANE`)
- Faceting on multiple fields simultaneously
- Pagination
- Custom field selection

**Features:**
- Full Solr syntax support
- Multiple filter queries (fq)
- Faceting on multiple fields
- Sort by any field
- Field list (fl) to control returned fields
- Pagination (start, rows)

**API Endpoint:** `POST /advanced`

---

### Mode 3: Group By

**Use Case:** Analytics and counting

**Perfect for:**
- Count applications per examiner
- Count applications per GAU
- Status distribution for a law firm
- Year-over-year statistics
- Any field aggregation

**Features:**
- Group by any field
- Optional filtering
- Configurable group limit
- Returns counts only (no documents)

**API Endpoint:** `POST /group-by`

---

## API Reference

### 1. Simple Search

**Endpoint:** `POST /search`

**Request:**
```json
{
  "field": "examiner_name",
  "value": "JOHN DOE",
  "exact_match": true,
  "limit": 10,
  "sort_by": "app_date desc"
}
```

**Response:**
```json
{
  "query": "examiner_name:\"JOHN DOE\"",
  "total_found": 45,
  "results": [
    {
      "id": "US123",
      "title": "Some invention",
      "examiner_name": "JOHN DOE",
      ...
    }
  ],
  "solr_url": "http://localhost:8983/solr/patents/select?..."
}
```

---

### 2. Advanced Query

**Endpoint:** `POST /advanced`

**Request:**
```json
{
  "q": "title:battery",
  "fq": ["app_date_year:2020", "disposal_type:pend"],
  "rows": 20,
  "start": 0,
  "sort": "app_date desc",
  "fl": "id,title,app_date",
  "facet": true,
  "facet_field": ["disposal_type", "examiner_name"],
  "facet_limit": 10
}
```

**Response:**
```json
{
  "query_params": {...},
  "total_found": 234,
  "start": 0,
  "results": [...],
  "facets": {
    "disposal_type": [
      {"value": "pend", "count": 150},
      {"value": "patented", "count": 60}
    ],
    "examiner_name": [
      {"value": "JOHN DOE", "count": 45},
      {"value": "JANE SMITH", "count": 38}
    ]
  },
  "solr_url": "..."
}
```

---

### 3. Group By

**Endpoint:** `POST /group-by`

**Request:**
```json
{
  "group_by_field": "gau",
  "filter_field": "app_date_year",
  "filter_value": "2020",
  "limit": 20
}
```

**Response:**
```json
{
  "group_by_field": "gau",
  "filter_applied": "app_date_year:2020",
  "total_documents": 5432,
  "groups": [
    {"value": "2100", "count": 234},
    {"value": "2600", "count": 189},
    {"value": "3600", "count": 156}
  ]
}
```

---

## Real-World Use Cases

### Use Case 1: Examiner Analysis

**Question:** Which examiners have the most pending applications?

**Solution:**
```
Group By Tab:
  Group By Field: examiner_name
  Filter Field: disposal_type
  Filter Value: pend
  Max Groups: 50
```

**Result:** Top 50 examiners by pending application count

---

### Use Case 2: GAU Performance

**Question:** For GAU 2100, what's the distribution of statuses?

**Solution:**
```
Group By Tab:
  Group By Field: disposal_type
  Filter Field: gau
  Filter Value: 2100
```

**Result:**
```
Pending: 245
Granted: 123
Abandoned: 45
```

---

### Use Case 3: Recent Applications by Attorney in Specific Tech Area

**Question:** Show me recent applications by attorney "JOHN DOE" in technology class 700

**Solution:**
```
Advanced Tab:
  Main Query: all_attorney_names:"JOHN DOE"
  Filter Queries:
    uspc_class:700
  Sort: app_date desc
  Rows: 20
```

---

### Use Case 4: Year-over-Year Application Trends

**Question:** How many applications per year for law firm "ABC Law"?

**Solution:**
```
Group By Tab:
  Group By Field: app_date_year
  Filter Field: law_firm
  Filter Value: abc law
  Max Groups: 20
```

**Result:**
```
2024: 145
2023: 167
2022: 189
2021: 203
```

---

## Solr Query Syntax Guide

### Basic Queries

```
*:*                          → All documents
title:battery                → Title contains "battery"
title:"lithium battery"      → Exact phrase
title:battery AND status:pend → Boolean AND
title:battery OR title:solar  → Boolean OR
title:batt*                  → Wildcard
title:[A TO C]               → Range
```

### Filter Queries (fq)

Multiple filters are ANDed together:
```
fq: app_date_year:2020
fq: disposal_type:pend
fq: examiner_name:"JOHN DOE"

Result: Documents matching ALL three conditions
```

### Sorting

```
app_date desc                → Newest first
id asc                       → Oldest first (by ID)
examiner_name asc            → Alphabetical
app_date desc, id asc        → Multi-field sort
```

### Field List (fl)

```
fl: *                        → All fields
fl: id,title,app_date        → Only these fields
fl: id,title,_score          → Include relevance score
```

---

## Common Field Names (USPTO Data)

Based on your Solr schema, here are commonly available fields:

### Identification
- `id` - Application ID (e.g., US61708978)
- `app_type` - Application type (provsnl, nonprov, etc.)

### Dates
- `app_date` - Application date
- `app_date_year` - Application year
- `app_status_date` - Status date

### People & Organizations
- `first_named_inventor` - Primary inventor
- `all_applicants` - All applicants
- `law_firm` - Law firm name
- `all_attorney_names` - All attorney names
- `all_attorney_registration_numbers` - Attorney registration numbers
- `examiner_name` - Patent examiner (if available)

### Classification
- `gau` - Group Art Unit
- `art_unit` - Art unit
- `uspc_class` - US Patent Classification
- `cpc_class` - Cooperative Patent Classification

### Status
- `disposal_type` - Status (pend, patented, abandoned)
- `application_status` - Detailed status

### Content
- `title` - Application title
- `abstract` - Abstract text
- `claims` - Claims text

### Administrative
- `customer_number` - Customer number
- `small_entity_indicator` - Entity size
- `confirm_number` - Confirmation number

**To see ALL fields in your Solr:**
- Use the API: `GET http://localhost:8000/fields`
- Or check Solr Admin UI: `http://localhost:8983/solr/#/patents/schema`

---

## Getting Started

### 1. Install and Run

```bash
# Backend (Advanced)
cd backend
pip install -r requirements.txt
python app_advanced.py

# Frontend
# Open frontend/advanced.html in browser
```

### 2. Try Simple Searches

Start with the **Simple Search** tab:
- Field: `law_firm`
- Value: Your law firm name
- Click Search

### 3. Experiment with Grouping

Try the **Group By** tab:
- Group By: `disposal_type`
- See the distribution

### 4. Master Advanced Queries

Move to **Advanced Query** tab:
- Start with `q=*:*`
- Add one filter at a time
- Enable faceting to see distributions

---

## Tips & Best Practices

### 1. Finding Field Names

**Not sure what fields exist?**
```bash
# Use the /fields endpoint
curl http://localhost:8000/fields
```

**Or check one document:**
```
Advanced Tab:
  Main Query: *:*
  Rows: 1
  
Look at the returned fields
```

### 2. Testing Queries

**Always test incrementally:**
1. Start with simple query: `field:value`
2. Add one filter
3. Add another filter
4. Add sorting
5. Add faceting

### 3. Performance

**For large result sets:**
- Use `fl` to limit returned fields
- Use filters (`fq`) instead of query (`q`) when possible (better caching)
- Set appropriate `rows` limit
- Use faceting instead of retrieving all documents

**Fast:**
```json
{
  "q": "*:*",
  "fq": ["app_date_year:2020", "disposal_type:pend"],
  "fl": "id,title",
  "rows": 10
}
```

**Slow:**
```json
{
  "q": "app_date_year:2020 AND disposal_type:pend",
  "fl": "*",
  "rows": 1000
}
```

### 4. Exact Matches

**For exact phrase matching, always use quotes:**
```
Good: law_firm:"smith and jones llp"
Bad:  law_firm:smith and jones llp  (searches for "smith" anywhere!)
```

### 5. Wildcard Searches

**Wildcards work but can be slow:**
```
Fast:   title:battery
Slower: title:*battery*
Faster: title:battery*  (prefix wildcard is faster)
```

---

## Troubleshooting

### "Field does not exist"

**Problem:** Error says field doesn't exist

**Solution:**
1. Check spelling
2. Get list of fields: `GET /fields`
3. Verify field is indexed in Solr schema

### "No results found"

**Problem:** Query returns 0 results

**Solution:**
1. Try broader query: `*:*`
2. Remove filters one by one
3. Check if data exists for that field value
4. Verify exact match vs partial match

### "Query syntax error"

**Problem:** Solr rejects query

**Solution:**
1. Check for special characters (escape or use quotes)
2. Verify boolean operators are UPPERCASE (AND, OR, NOT)
3. Check parentheses are balanced
4. Use Simple Search tab to let backend build query

### Performance is slow

**Problem:** Queries take too long

**Solution:**
1. Reduce `rows` parameter
2. Use `fl` to limit fields returned
3. Add filters (`fq`) to narrow results
4. Check Solr query logs
5. Consider adding Solr caching

---

## Migration from Simple UI

### Scenario 1: Search by Application ID

**Simple UI:**
```
Select: "Search by Application ID"
Enter ID: US123
```

**Advanced UI (Simple Search Tab):**
```
Field Name: id
Search Value: US123
Match Type: Exact Match
```

### Scenario 2: Latest Applications

**Simple UI:**
```
Select: "Get Latest Applications"
Number: 10
```

**Advanced UI (Advanced Query Tab):**
```
Main Query: *:*
Sort: id desc
Rows: 10
```

### Scenario 3: Count by Law Firm Status

**Simple UI:**
```
Select: "Count Applications by Law Firm Status"
Law Firm: abc law
```

**Advanced UI (Group By Tab):**
```
Group By Field: disposal_type
Filter Field: law_firm
Filter Value: abc law
```

---

## Advanced Features

### Combining Multiple Facets

**Question:** Show status distribution AND yearly distribution

**Solution:**
```json
{
  "q": "*:*",
  "rows": 0,
  "facet": true,
  "facet_field": ["disposal_type", "app_date_year"]
}
```

### Range Queries

**Question:** Applications from 2018-2022

**Solution:**
```
Advanced Tab:
  Main Query: *:*
  Filter Queries: app_date:[2018-01-01T00:00:00Z TO 2022-12-31T23:59:59Z]
```

### Negative Filters

**Question:** Everything EXCEPT abandoned applications

**Solution:**
```
Advanced Tab:
  Filter Queries: -disposal_type:abandoned
```

### Proximity Searches

**Question:** "battery" within 5 words of "lithium" in title

**Solution:**
```
Advanced Tab:
  Main Query: title:"battery lithium"~5
```

---

## API Integration

### Using in Your Application

```python
import requests

# Simple search
response = requests.post('http://localhost:8000/search', json={
    'field': 'examiner_name',
    'value': 'JOHN DOE',
    'exact_match': True,
    'limit': 10
})

results = response.json()
print(f"Found {results['total_found']} applications")
for app in results['results']:
    print(f"  {app['id']}: {app.get('title', 'No title')}")
```

```javascript
// JavaScript/Node.js
const response = await fetch('http://localhost:8000/group-by', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        group_by_field: 'gau',
        limit: 20
    })
});

const data = await response.json();
data.groups.forEach(group => {
    console.log(`GAU ${group.value}: ${group.count} applications`);
});
```

---

## Summary

The Advanced Search interface gives you **complete control** over Solr queries:

✅ **Any Field** - Search, filter, group, sort on any field
✅ **Three Modes** - Simple, Advanced, Group By for different use cases
✅ **Full Power** - Access all Solr features
✅ **User Friendly** - No need to write Solr queries manually
✅ **Visual Results** - Tables and facet cards
✅ **API First** - Easy to integrate with other tools

**Start Simple → Get Comfortable → Go Advanced**

1. Try Simple Search on known fields
2. Experiment with Group By for analytics
3. Master Advanced Query for complex searches
4. Integrate with your workflows via API

Happy Searching! 🔍
