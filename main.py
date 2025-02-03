from typing import Annotated
import os
from datetime import datetime, date
import json
from fastapi import FastAPI, Response, status, Path, Query, HTTPException

app = FastAPI()

@app.get("/")
async def root():
    """Return home page"""
    return {"response": "Under construction"}

@app.get("/api/v1/status")
async def api_status():
    """Return status of the API"""
    return {"status": "ok"}

@app.get("/api/v1/version")
async def api_version():
    """Return version of the API"""
    return {"version": "0.1.10"}

@app.get("/api/v1/coverage/{year}")
async def api_coverage_year(
    year: Annotated[int, Path(title="The year to be checked", ge=2000, le=3000)]
):
    """Return current data coverage in the API for a given year"""
    filename = f"json/{year}.json"
    # check if data exists
    if os.path.isfile(filename):
        return {
            "year": year,
            "coverage": "ok",
        }

    return {
        "year": year,
        "coverage": "data not available",
    }

@app.get("/api/v1/check_holiday")
async def check_holiday(
    year: Annotated[int, Query(ge=2000, le=3000)],
    month: Annotated[int, Query(ge=1, le=12)],
    day: Annotated[int, Query(ge=1, le=31)],
    response: Response,
):
    """Return whether a given date is a holiday or not with detailed holiday information"""
    date_provided, status_code, result = await get_holiday_info(year, month, day)
    
    if response:
        response.status_code = status_code
    
    # If the status code is not OK, return the result with error details
    if status_code != status.HTTP_200_OK:
        return {"response": result}
    
    # If it is a holiday, return detailed information
    if result["is_holiday"]:
        return result
    
    # If not a holiday, return the response as False
    return {"date": date_provided, "response": False}


@app.get("/api/v1/holiday_info")
async def holiday_info(
    year: Annotated[int, Query(ge=2000, le=3000)],
    month: Annotated[int, Query(ge=1, le=12)],
    day: Annotated[int, Query(ge=1, le=31)],
    response: Response,
):
    """Return information about a given holiday"""
    date_provided, status_code, result = await get_holiday_info(year, month, day)
    if response:
        response.status_code = status_code
    return {"date": date_provided, "response": result}




@app.get("/api/v1/holidays")
async def holidays_list(
    year: Annotated[int, Query(ge=2000, le=3000)],
    month: Annotated[int, Query(ge=1, le=12)]
):
    """Return list of holidays for a given year/month"""
    filename = f"json/{year}.json"
    if not os.path.isfile(filename):
        raise HTTPException(status_code=404, detail="Holiday data not available for the year")

    with open(filename, "r", encoding="utf-8") as file:
        holiday_data = json.load(file)

    holidays_in_month = [
        holiday for holiday in holiday_data if
        datetime.strptime(holiday["start"], "%Y-%m-%d").month == month
    ]

    if holidays_in_month:
        return {"holidays": holidays_in_month}
    return {"response": "No holidays found for this month"}



async def get_holiday_info(year: int, month: int, day: int):
    """Process provided date and return holiday information with status code"""
    try:
        date_to_check = date(year, month, day)
    except (ValueError, TypeError):
        return None, status.HTTP_400_BAD_REQUEST, {"error": "invalid date"}

    filename = f"json/{year}.json"
    if not os.path.isfile(filename):
        return (
            date_to_check,
            status.HTTP_404_NOT_FOUND,
            {"error": "requested year not available"},
        )

    with open(filename, "r", encoding="utf-8") as file:
        holiday_data = json.load(file)

    for holiday in holiday_data:
        start_date = datetime.strptime(holiday["start"], "%Y-%m-%d").date()
        end_date = datetime.strptime(holiday["end"], "%Y-%m-%d").date()

        if start_date <= date_to_check <= end_date:
            return (
                date_to_check,
                status.HTTP_200_OK,
                {
                    "day": date_to_check.strftime("%A"),
                    "week": date_to_check.strftime("%W"),
                    "month": date_to_check.strftime("%B"),
                    "is_holiday": True,
                    "id": holiday["uid"],
                    "holiday": holiday["summary"],
                    "categories": holiday["categories"],  # Updated to match new data structure
                    "holiday_start": holiday["start"],
                    "holiday_end": holiday["end"],
                },
            )

    return (
        date_to_check,
        status.HTTP_200_OK,
        {
            "is_holiday": False,
        },
    )


@app.get("/api/v1/holidays/{year}")
async def holidays_in_year(
    year: Annotated[int, Path(title="The year to be checked", ge=2000, le=3000)],
    response: Response,
):
    """Return a list of all holidays in a given year"""
    filename = f"json/{year}.json"
    
    # Check if the holiday data exists for the given year
    if not os.path.isfile(filename):
        return {
            "year": year,
            "response": "Data not available for this year."
        }

    try:
        # Load the holiday data from the file
        with open(filename, "r", encoding="utf-8") as file:
            holiday_data = json.load(file)
        
        # If holidays exist, return them in a structured format
        holidays = [
            {
                "uid": holiday["uid"],
                "holiday": holiday["summary"],
                "start": holiday["start"],
                "end": holiday["end"],
                "categories": holiday["categories"],
            }
            for holiday in holiday_data
        ]
        
        return {
            "year": year,
            "holidays": holidays,
        }

    except FileNotFoundError:
        return {
            "year": year,
            "response": "Data not available for this year."
        }




