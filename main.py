from fastapi import FastAPI, Response, Body, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from pydantic.functional_validators import BeforeValidator
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Annotated
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

PyObjectId= Annotated[str, BeforeValidator(str)]

class ClientModel(BaseModel):
  id: Optional[PyObjectId] = Field(alias='_id', default=None)
  first_name: str = Field(...)
  last_name: str = Field(...)
  email: EmailStr = Field(...)
  gender: str = Field(...)
  address: str = Field(...)
  model_config = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_schema_extra={
      'example':{
        'first_name':'Juan',
        'last_name':'Perez',
        'email':'juan.perez@acme.com',
        'gender':'Male',
        'address':'Calle principal 1234'
      }
    }
  )
  
class CustomHeaderMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request, call_next):
    response = await call_next(request)
    response.headers['X-Attending-POD-name'] = os.getenv('POD_NAME','N/A')
    response.headers['X-Attending-POD-ip'] = os.getenv('POD_IP', 'N/A')
    return response

app = FastAPI(
  title="Customer API Service",
  summary="A sample application showing how to use Kubernetes with an API Service and a external repository"
)
app.add_middleware(CustomHeaderMiddleware)

load_dotenv(override=True)
mongo_client = MongoClient(
  host=os.getenv('MONGO_CONNECTION','').format(
    os.getenv('MONGO_USER'), os.getenv('MONGO_PASSWORD')))
coll = mongo_client.get_database('test').get_collection('clients')

@app.get('/')
async def root():
  return "I'm awaken"

@app.get('/clients', 
         response_model=list[ClientModel], 
         response_model_by_alias=False)
def get_clients():
  cursor=coll.find()
  for rec in cursor:
    yield rec
    

@app.post('/clients', 
          response_model=ClientModel,
          status_code=status.HTTP_201_CREATED,
          response_model_by_alias=False)
def create_client(client: ClientModel=Body(...)):
  new_client=coll.insert_one(client.model_dump(by_alias=True, exclude=['id']))
  created_client = coll.find_one({'_id':new_client.inserted_id})
  return created_client

@app.get('/clients/{id}',
         response_model=ClientModel,
         response_model_by_alias=False)
def get_client(id:str):
  if(client:=coll.find_one({'_id':ObjectId(id)})) is not None:
    return client
  
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                       detail=f'Client {id} not found')
  

@app.delete('/clients/{id}') 
def delete_client(id:str):
  delete_result = coll.delete_one({'_id':ObjectId(id)})
  if(delete_result.deleted_count == 1):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
  
  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Client {id} not found')