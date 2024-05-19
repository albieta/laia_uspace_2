from fastapi import APIRouter
from backend.models import FlightPlan
from laiagenlib.Domain.LaiaBaseModel.ModelRepository import ModelRepository
from laiagenlib.Application.LaiaBaseModel import ReadLaiaBaseModel, CreateLaiaBaseModel, DeleteLaiaBaseModel, SearchLaiaBaseModel, UpdateLaiaBaseModel

def ExtraRoutes(repository: ModelRepository=None):
    router = APIRouter(tags=["Extra Routes"])

    repository.db.flightplan.create_index([("route.geometry", "2dsphere")])
    
    @router.get("/flightplan_approval_check/{flightplanId}", openapi_extra={'x-description': 'Verifies possible collisions between a new flightplan before approval'})
    async def get_flightplan_approval_check_flightplanId(flightplanId: str):
        flight_plan = await ReadLaiaBaseModel.read_laia_base_model(flightplanId, FlightPlan, ["admin"], repository)
        if not flight_plan:
            raise HTTPException(status_code=404, detail="Flight plan not found")

        flight_plan_route = flight_plan['route']
        departure_time = flight_plan['departure_time']
        arrival_time = flight_plan['arrival_time']

        if not flight_plan_route or not departure_time or not arrival_time:
            raise HTTPException(status_code=400, detail="Flight plan route, departure time, or arrival time is missing")

        overlapping_flight_plans = await SearchLaiaBaseModel.search_laia_base_model(
            skip=0,
            limit=100,
            filters={
                "departure_time": {"$lt": arrival_time},
                "arrival_time": {"$gt": departure_time},
                "route.geometry": {
                    "$geoIntersects": {
                        "$geometry": flight_plan_route["geometry"]
                    }
                }
            },
            orders={"departure_time": 1},
            model=FlightPlan,
            user_roles=["admin"],
            repository=repository
        )

        possible_collisions = []
        for plan in overlapping_flight_plans['items']:
            if plan['id'] != flightplanId:
                possible_collisions.append(plan)

        return {
            "message": "Flight plan approval check completed",
            "collisions": possible_collisions,
            "flightplan": flight_plan
        }

    return router
                    
""" 
**************************************************************************
Instructions to develop new routes
**************************************************************************

- Import models from the models file with: 
from .models import modelName1, modelName2

- To operate with the crud operations on the models here are examples of the usage:
await CreateLaiaBaseModel.create_laia_base_model(dict(element), modelName1, user_roles, repository)
await UpdateLaiaBaseModel.update_laia_base_model(element_id, values, modelName1, user_roles, repository)
await ReadLaiaBaseModel.read_laia_base_model(element_id, modelName1, user_roles, repository)
await DeleteLaiaBaseModel.delete_laia_base_model(element_id, modelName1, user_roles, repository)
await SearchLaiaBaseModel.search_laia_base_model(skip, limit, filters, orders, modelName1, user_roles, repository)
"""
