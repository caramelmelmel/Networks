from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    Header,
    Body,
    Response

)
from fastapi.responses import (JSONResponse, StreamingResponse)
from fastapi.encoders import jsonable_encoder

from .db.users import (
    UserModel,
    ShowUserModel,
    UpdateUserModel
)
from .dependecies import (
    get_user
)
## TAKE NOTE HERE
from .settings import db

from typing import List
from datetime import datetime
from typing import Optional


users = db.get_collection("users")

router = APIRouter()

# ============= Creating path operations ==============
#home page
@router.get("/",response_description="Home page")
async def home():
    return "Welcome to your challenged todo list"

@router.post("/", response_description="Add new user", response_model=UserModel)
async def create_user(user: UserModel):

    #check the existence of the user
    if(await db["users"].find_one({"name": user.name})!= None):
        raise HTTPException(status_code=400, detail="User exists in the database")
    
    if(user.name == '' or user.name == None ):
        raise HTTPException(status_code=406, detail="Please fill in all relevant fields")
    # attributes
    datetime_now = datetime.now()
    user.created_at = datetime_now.strftime("%m/%d/%y %H:%M:%S")
    user.score = 0
    user = jsonable_encoder(user)

    new_user = await db["users"].insert_one(user)
    
    if(new_user == None):
        raise HTTPException(status_code = 401, detail="User is not created successfully")
    
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@router.get(
    "/users", response_description="List 1000 users at each call", response_model=List[ShowUserModel]
)
async def list_users(sortBy: Optional[str] = None, count: Optional[int] = None, offset: Optional[int] = None):
    usr = []
    find = users.find()
    async for user in find:
        usr.append(user)

    if sortBy:
        if sortBy=='score':
            usr = sorted(usr, key = lambda i: i['score'], reverse=True)

        else:
            raise HTTPException(status_code=400,detail="Wrong query parameters")
    if count:
        if count > 0 :
            usr = await db["users"].find().to_list(count)
        else:
            raise HTTPException(status_code = 400, detail='Please enter a count that is more than 0')
    if offset:
        if offset > -1 :
            usr = usr[offset:]
        else: 
            raise HTTPException(status_code=400,detail="Offset has to be more than -1")

    return JSONResponse(status_code = 200, content=usr)
    
@router.get("/user/{user_id}", response_description="Get the user by their id",response_model=ShowUserModel)
async def getUserById(user_id:str):
    return await get_user(user_id)



@router.delete("/user/{user_id}", response_model=UpdateUserModel)
async def delete_user(user_id:str,password: Optional[str]=Header(None)):
    if password == "savemysoul":
        # get the user and see whether he or she exists in the db 
        if await db["users"].find_one({"_id": user_id}) == None:
            raise HTTPException(status_code = 404, detail="Unable to find the user")
        delete_result = await db["users"].delete_one({"_id": user_id})
        if delete_result.deleted_count == 1:
            return JSONResponse(status_code=204)
    else:
        raise HTTPException(status_code = 401, detail="please enter the correct password to delete yourself")


@router.put("/{id}", response_description="Update a student", response_model=UserModel)
async def update_student(id: str, student: UpdateUserModel = Body(...)):
    student = {k: v for k, v in student.dict().items() if v is not None}
    if len(student) >= 1:
        update_result = await db["users"].update_one({"_id": id}, {"$set": student})
        if update_result.modified_count == 1:
            if (
                updated_student := await db["users"].find_one({"_id": id})
            ) is not None:
                return updated_student
    if (existing_student := await db["users"].find_one({"_id": id})) is not None:
        return existing_student
    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.delete("/deleteuserbatch")
def delete_games(response: Response, info: UpdateUserModel, password: Optional[str] = Header(None)):
    if password== "savemysoul":
        if info.score:
            users.delete_many({"score":{"$gt":info.score}})
        if info.name:
            users.delete_many({"name":info.name})
            
        response.status_code = 200
        return "deleted successfully"
        
    else:
        raise HTTPException(status_code = 401, detail="please enter the correct password to delete yourself")
