"""
Simple Patent Search Application - POC
Minimal backend for basic patent searches
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Literal
import httpx
import json
import io
import pandas as pd
from logger.logger import setup_logger
import traceback
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
logger = setup_logger(logging_enabled=True)

app = FastAPI(title="Patent Search POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STAT_TYPE_MAP = {
    "examiner": "examiner",
    "prosecutor": "all_attorney_names",
    "lawfirm": "law_firm",
    "gau": "gau",
    "assignee": "assignee_last",
    "usc": "usc",
    "entity": "small_entity_indicator",
    "action": "th_all_action",
}

load_dotenv()
# Solr Configuration
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL") 
SOLR_CORE = ""

print(SOLR_BASE_URL)
class PatentSearchRequest(BaseModel):
    """
    This class is used to define the BaseModel for the Patents.
    """
    patent_ids: List[str]
    
class StatsByDateRangeRequest(BaseModel):
    type: Literal[
        "examiner",
        "prosecutor",
        "lawfirm",
        "gau",
        "assignee",
        "usc",
        "entity",
        "action",
    ]             # examiner | prosecutor | lawfirm
    from_date: str
    to_date: str
    limit: int = 10
    sort_order: str = "desc"
    
class ExaminerStatsByDateRequest(BaseModel):
    from_date: str  # YYYY-MM-DD
    to_date: str    # YYYY-MM-DD
    limit: int = 10

class LawFirmSearchRequest(BaseModel):
    """
    This class is used to define the BaseModel for the Lawfirms.
    """
    lawfirms: List[str]
    search_type: str
    limit: int = 10
    
class ProsecutorSearchRequest(BaseModel):
    """
    This class is used to define the BaseModel For the Prosecutor Request.
    """
    prosecutors: List[str]
    search_type: str = "latest_filed"
    limit: int = 10

class ExaminerSearchRequest(BaseModel):
    """
    This class is used to define the BaseModel for the Examiners.
    """
    examiners: List[str]
    search_type: str  # "latest_filed", "latest_approved", "count", "last_10_years", "latest_10_approved"
    limit: int = 10

class GAUSearchRequest(BaseModel):
    gaus: List[str]
    limit: int = 10
    sort: Optional[str] = "app_date desc"

class ExecuteQueryRequest(BaseModel):
    """
    This class is used to define the BaseModel for executing the queries.
    """
    solr_query_url: str

class AttorneySearchRequest(BaseModel):
    attorneys: List[str]
    search_type: Optional[str] = "latest_filed"
    limit: int = 10
  
class AdvancedFilter(BaseModel):
    field: str
    operator: Literal["equals", "contains", "starts_with", "range"]
    value: str


class SortOption(BaseModel):
    field: str
    order: Literal["asc", "desc"]
      
class AdvancedSearchRequest(BaseModel):
    filters: List[AdvancedFilter]
    limit: int = 10
    sort: Optional[SortOption] = None

@app.get("/")
async def root():
    return {"message": "Patent Search API - POC", "status": "running"}


@app.post("/search/patent")
async def search_by_patent(request: PatentSearchRequest):
    """
    Search patent by ID
    Returns: Patent details + Solr URL
    """
    try:
        
        patent_ids = [pid.strip() for pid in request.patent_ids if pid.strip()]


        if not patent_ids:
            raise HTTPException(status_code=400, detail="No valid patent IDs provided")


        # Build Solr query
        if len(patent_ids) == 1:
            q = f"id:{patent_ids[0]}"
        else:
            joined_ids = " OR ".join(patent_ids)
            q = f"id:({joined_ids})"
            
        # Build Solr query
        params = {
            "q": q,
            "wt": "json",
            "indent": "true"
        }
        
        solr_url = f"{SOLR_BASE_URL}/select"
        
        # Execute query
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(solr_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        return {
            "solr_query_url": str(response.url),
            "total_found": data["response"]["numFound"],
            "results": data["response"]["docs"],
            "raw_response": data
        }
        
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/search/examiner")
async def search_by_examiner(request: ExaminerSearchRequest):
    """
    Search by examiner name with different options
    """
    try:
        # Build base query
        q = build_examiner_q(request.examiners)
        
        params = {
            "q": q,
            "wt": "json",
            "indent": "true"
        }
        
        # Handle different search types
        if request.search_type == "latest_filed":
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "count":
            params["rows"] = 0
            
        elif request.search_type == "last_10_years":
            params["fq"] = "app_date_year:[2014 TO 2024]"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_10_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = 10
        
        solr_url = f"{SOLR_BASE_URL}/select"
        
        # Execute query
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(solr_url, params=params)
            response.raise_for_status()
            data = response.json()
        
        return {
            "solr_query_url": str(response.url),
            "search_type": request.search_type,
            "total_found": data["response"]["numFound"],
            "results": data["response"]["docs"],
            "raw_response": data
        }
        
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download/json")
async def download_json(data: dict):
    """
    Download results as JSON file
    """
    try:
        json_str = json.dumps(data, indent=2)
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=patent_results.json"}
        )
    except Exception as e:
        logger.error(traceback.format_exc())


@app.post("/download/excel")
async def download_excel(data: dict):
    """
    Convert results to Excel and download
    """
    try:
        results = data.get("results", [])
        if not results:
            raise HTTPException(status_code=400, detail="No results to convert")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Patent Results')
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=patent_results.xlsx"}
        )
        
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/total")
async def get_total_stats():
    """
    Get total counts for reports
    """
    try:
        solr_url = f"{SOLR_BASE_URL}/solr/{SOLR_CORE}/select"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Total patents
            total_response = await client.get(solr_url, params={"q": "*:*", "rows": 0, "wt": "json"})
            total_data = total_response.json()
            total_patents = total_data["response"]["numFound"]
            
            # Approved patents
            approved_response = await client.get(solr_url, params={
                "q": "disposal_type:iss",
                "rows": 0,
                "wt": "json"
            })
            approved_data = approved_response.json()
            total_approved = approved_data["response"]["numFound"]
            
            # Pending patents
            pending_response = await client.get(solr_url, params={
                "q": "disposal_type:pend",
                "rows": 0,
                "wt": "json"
            })
            pending_data = pending_response.json()
            total_pending = pending_data["response"]["numFound"]
        
        return {
            "total_patents": total_patents,
            "total_approved": total_approved,
            "total_pending": total_pending,
            "total_abandoned": total_patents - total_approved - total_pending
        }
        
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build/attorney-query")
async def build_attorney_query(request: AttorneySearchRequest):
    try: 
        q = " OR ".join([f'all_attorney_names:"{a}"' for a in request.attorneys])

        params = {
            "q": q,
            "rows": request.limit,
            "wt": "json",
            "indent": "true",
        }

        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {"solr_query_url": str(solr_url)}
    
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build/patent-query")
async def build_patent_query(request: PatentSearchRequest):
    
    try:
        patent_ids = [p.strip() for p in request.patent_ids if p.strip()]
        if not patent_ids:
            raise HTTPException(status_code=400, detail="No valid patent IDs provided")

        # Build Solr query
        if len(patent_ids) == 1:
            q = f'id:"{patent_ids[0]}"'
        else:
            q = " OR ".join([f'id:"{pid}"' for pid in patent_ids])

        params = {
            "q": q,
            "wt": "json",
            "indent": "true",
        }

        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {
            "solr_query_url": str(solr_url),
            "query_type": "patent",
            "searched_ids": patent_ids,
        }
    except Exception as e:
        logger.error(traceback.format_exc())

@app.post("/build/examiner-query")
async def build_examiner_query(request: ExaminerSearchRequest):
    
    try:
        q = build_examiner_q(request.examiners)

        params = {
        "q": q,
        "rows": request.limit or 10,
        "wt": "json",
        "indent": "true",
        }
        
        if request.search_type == "latest_filed":
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "count":
            params["rows"] = 0
            
        elif request.search_type == "last_10_years":
            params["fq"] = "app_date_year:[2015 TO 2025]"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_10_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit



        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {
            "solr_query_url": str(solr_url),
            "query_type": "examiner",
            "normalized_name": request.examiners,
        }
    except Exception as e:
        logger.error(traceback.format_exc())



@app.post("/build/lawfirm-query")
async def build_lawfirm_query(request: LawFirmSearchRequest):

    try: 
        q = build_lawfirm_q(request.lawfirms)

        params = {
            "q": q,
            "rows": request.limit or 10,
            "wt": "json",
            "indent": "true",
        }
        
        
        if request.search_type == "latest_filed":
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "count":
            params["rows"] = 0
            
        elif request.search_type == "last_10_years":
            params["fq"] = "app_date_year:[2015 TO 2025]"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit
            
        elif request.search_type == "latest_10_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = 10

        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {
            "solr_query_url": str(solr_url),
            "query_type": "lawfirm",
            "normalized_names": request.lawfirms,
        }
    except Exception as e:
        logger.error(traceback.format_exc())


@app.post("/execute-query")
async def execute_query(request: ExecuteQueryRequest):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.solr_query_url)
            response.raise_for_status()
            data = response.json()

        return {
            "solr_query_url": request.solr_query_url,
            "total_found": data["response"]["numFound"],
            "results": data["response"]["docs"],
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        return {
            "solr_query_url": "",
            "total_found": "",
            "results": "",
        }
        raise HTTPException(status_code=500, detail=str(e))

def build_lawfirm_q(lawfirms: List[str]) -> str:
    try:
        clauses = [
        f'law_firm:"{name.strip().lower()}"'
            for name in lawfirms
            if name.strip()
        ]
        return " OR ".join(clauses)
    
    except Exception as e:
        logger.error(traceback.format_exc())
    
    return ""



def build_examiner_q(examiners: List[str]) -> str:
    try:
        
        clauses = [
            f'examiner:"{name.strip().lower()}"'
            for name in examiners
            if name.strip()
        ]
        return " OR ".join(clauses)
    except Exception as e:
        logger.error(traceback.format_exc())
    
    return ""

@app.post("/build/prosecutor-query")
async def build_prosecutor_query(request: ProsecutorSearchRequest):
    try:
        q = build_prosecutor_q(request.prosecutors)

        params = {
            "q": q,
            "rows": request.limit or 10,
            "wt": "json",
            "indent": "true",
        }

        if request.search_type == "latest_filed":
            params["sort"] = "app_date desc"
            params["rows"] = request.limit

        elif request.search_type == "latest_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit

        elif request.search_type == "count":
            params["rows"] = 0

        elif request.search_type == "last_10_years":
            params["fq"] = "app_date_year:[2015 TO 2025]"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit

        elif request.search_type == "latest_10_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = 10

        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {
            "solr_query_url": str(solr_url),
            "query_type": "prosecutor",
            "normalized_names": request.prosecutors,
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/prosecutor")
async def search_by_prosecutor(request: ProsecutorSearchRequest):
    try:
        q = build_prosecutor_q(request.prosecutors)

        params = {
            "q": q,
            "wt": "json",
            "indent": "true",
        }

        if request.search_type == "latest_filed":
            params["sort"] = "app_date desc"
            params["rows"] = request.limit

        elif request.search_type == "latest_approved":
            params["fq"] = "disposal_type:iss"
            params["sort"] = "app_date desc"
            params["rows"] = request.limit

        solr_url = f"{SOLR_BASE_URL}/select"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(solr_url, params=params)
            response.raise_for_status()
            data = response.json()

        return {
            "solr_query_url": str(response.url),
            "total_found": data["response"]["numFound"],
            "results": data["response"]["docs"],
            "raw_response": data,
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/build/advanced-query")
async def build_advanced_query(request: AdvancedSearchRequest):
    q_parts = []
    fq_parts = []

    for f in request.filters:
        if f.operator == "equals":
            fq_parts.append(f'{f.field}:"{f.value}"')

        elif f.operator == "contains":
            fq_parts.append(f'{f.field}:*{f.value}*')

        elif f.operator == "starts_with":
            fq_parts.append(f'{f.field}:{f.value}*')

        elif f.operator == "range":
            start, end = f.value.split("-")
            fq_parts.append(f'{f.field}:[{start} TO {end}]')

    params = {
        "q": "*:*",
        "fq": fq_parts,
        "rows": request.limit,
        "wt": "json"
    }

    if request.sort:
        params["sort"] = f"{request.sort.field} {request.sort.order}"

    solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)
    return { "solr_query_url": str(solr_url) }


def build_prosecutor_q(prosecutors: List[str]) -> str:
    try:
        clauses = [
            f'all_attorney_names:"{name.strip().lower()}"'
            for name in prosecutors
            if name.strip()
        ]
        return " OR ".join(clauses)
    except Exception as e:
        logger.error(traceback.format_exc())
        return ""

@app.post("/build/gau-query")
async def build_gau_query(request: GAUSearchRequest):
    try:
        gau_query = " OR ".join(f'"{g}"' for g in request.gaus)
        params = {
            "q": f'gau:({gau_query})',
            "rows": request.limit,
            "wt": "json",
            "indent": "true",
            "sort": request.sort,
        }

        solr_url = httpx.URL(f"{SOLR_BASE_URL}/select", params=params)

        return {
            "solr_query_url": str(solr_url),
            "query_type": "gau",
            "gau": request.gaus,
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/gau")
async def search_by_gau(request: GAUSearchRequest):
    try:
        params = {
            "q": f'gau:"{request.gau}"',
            "rows": request.limit,
            "wt": "json",
            "indent": "true",
            "sort": request.sort,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{SOLR_BASE_URL}/select", params=params)
            response.raise_for_status()
            data = response.json()

        return {
            "solr_query_url": str(response.url),
            "total_found": data["response"]["numFound"],
            "results": data["response"]["docs"],
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats/examiners-by-date")
async def examiner_stats_by_date(request: ExaminerStatsByDateRequest):
    try:
       
        params = {
            "q": "*:*",
            "fq": f'app_date:[{request.from_date}T00:00:00Z TO {request.to_date}T23:59:59Z]',
            "rows": 0,   
            "wt": "json",
           "json.facet": json.dumps({
            "examiners": {
                "type": "terms",
                "field": "examiner",
                "limit": request.limit,
                "sort": "count desc",
                "facet": {
                    "gaus": { 
                        "type": "terms", 
                        "field": "gau", 
                        "limit": -1, 
                        "sort": "count desc" 
                    },
                     "cpcs": {   # NEW FACET
                        "type": "terms",
                        "field": "cpc_classification",
                        "limit": -1,
                        "sort": "count desc",
                        "mincount": 1
                    }
                }
            }
            })
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(f"{SOLR_BASE_URL}/select", params=params)
            response.raise_for_status()
            
            data = response.json()
            
        buckets = data["facets"]["examiners"]["buckets"]
        
        examiners = []

        for b in buckets:
            gau_buckets = b.get("gaus", {}).get("buckets", [])
            cpc_buckets = b.get("cpcs",{}).get("buckets",[])

            gaus = [
                {
                    "gau": g["val"],
                    "application_count": g["count"],
                }
                for g in gau_buckets
            ]
            
            # CPC
            
            
            cpcs = [
                {
                    
                    "cpc":c["val"],
                    "application_count":c["count"]
               } for c in cpc_buckets
            ]

            examiners.append({
                "examiner": b["val"],
                "application_count": b["count"],
                "unique_gau_count": len(gaus),
                "unique_cpc_count":len(cpcs),
                "gaus": gaus,
                "cpcs":cpcs,
            })

        return {
            "from_date": request.from_date,
            "to_date": request.to_date,
            "total_examiners": len(examiners),
            "examiners": examiners,
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stats/by-date-range")
async def stats_by_date_range(request: StatsByDateRangeRequest):
    try:
        # Map type → Solr field
        field = STAT_TYPE_MAP.get(request.type)
        if not field:
            raise HTTPException(status_code=400, detail="Invalid stats type")

        # group_field = field_map[request.type]

        facet_sort = f"count {request.sort_order}"
        
        params = {
            "q": "*:*",
            "fq": f'app_date:[{request.from_date}T00:00:00Z TO {request.to_date}T23:59:59Z]',
            "rows": 0,
            "wt": "json",
            "json.facet": json.dumps({
                "groups": {
                    "type": "terms",
                    "field": field,
                    "limit": request.limit,
                    "sort": facet_sort,
                    "facet": {
                        "gaus": {
                            "type": "terms",
                            "field": "gau",
                            "limit": -1,
                            "sort": facet_sort
                        },
                        "cpcs": {   # NEW FACET
                            "type": "terms",
                            "field": "cpc_classification",
                            "limit": 20,
                            "sort": "count desc",
                            "mincount": 1
                    }
                    }
                }
            })
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{SOLR_BASE_URL}/select", params=params)
            response.raise_for_status()
            data = response.json()

        buckets = data["facets"]["groups"]["buckets"]

        results = []

        for b in buckets:
            gau_buckets = b.get("gaus", {}).get("buckets", [])
            cpc_buckets = b.get("cpcs",{}).get("buckets",[])

            gaus = [
                {
                    "gau": g["val"],
                    "application_count": g["count"],
                }
                for g in gau_buckets
            ]
            
            cpcs = [
                {
                    "cpc":g["val"],
                    "application_count":g["count"],
                }
                for g in cpc_buckets
            ]

            results.append({
                request.type: b["val"],                     # dynamic key
                "application_count": b["count"],
                "unique_gau_count": len(gaus),
                "unique_cpc_count":len(cpcs),
                "gaus": gaus,
                "cpcs":cpcs,
            })

        return {
            "type": request.type,
            "from_date": request.from_date,
            "to_date": request.to_date,
            f"total_{request.type}s": len(results),
            f"{request.type}s": results,
        }

    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



