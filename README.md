# FastAPI Boilerplate

# Features
- Async SQLAlchemy session
- Custom user class
- Top-level dependency
- Dependencies for specific permissions
- Celery
- Dockerize(Hot reload)
- Event dispatcher
- Cache

## Run

```python
python3 main.py --env local|dev|prod --debug
```

## SQLAlchemy for asyncio context

```python
from core.db import Transactional, session


@Transactional()
async def create_user(self):
    session.add(User(email="padocon@naver.com"))
```

Do not use explicit `commit()`. `Transactional` class automatically do.

### Standalone session

According to the current settings, the session is set through middleware.

However, it doesn't go through middleware in tests or background tasks.

So you need to use the `@standalone_session` decorator.

```python
from core.db import standalone_session


@standalone_session
def test_something():
    ...
```

### Multiple databases

Go to `core/config.py` and edit `WRITER_DB_URL` and `READER_DB_URL` in the config class.


If you need additional logic to use the database, refer to the `get_bind()` method of `RoutingClass`.

## Custom user for authentication

```python
from fastapi import Request


@home_router.get("/")
def home(request: Request):
    return request.user.id
```

**Note. you have to pass jwt token via header like `Authorization: Bearer 1234`**

Custom user class automatically decodes header token and store user information into `request.user`

If you want to modify custom user class, you have to update below files.

1. `core/fastapi/schemas/current_user.py`
2. `core/fastapi/middlewares/authentication.py`

### CurrentUser

```python
class CurrentUser(BaseModel):
    id: int = Field(None, description="ID")
```

Simply add more fields based on your needs.

### AuthBackend

```python
current_user = CurrentUser()
```

After line 18, assign values that you added on `CurrentUser`.

## Top-level dependency

**Note. Available from version 0.62 or higher.**

Set a callable function when initialize FastAPI() app through `dependencies` argument.

Refer `Logging` class inside of `core/fastapi/dependencies/logging.py` 

## Dependencies for specific permissions

Permissions `IsAdmin`, `IsAuthenticated`, `AllowAll` have already been implemented.
 
```python
from core.fastapi.dependencies import (
    PermissionDependency,
    IsAdmin,
)


user_router = APIRouter()


@user_router.get(
    "",
    response_model=List[GetUserListResponseSchema],
    response_model_exclude={"id"},
    responses={"400": {"model": ExceptionResponseSchema}},
    dependencies=[Depends(PermissionDependency([IsAdmin]))],  # HERE
)
async def get_user_list(
    limit: int = Query(10, description="Limit"),
    prev: int = Query(None, description="Prev ID"),
):
    pass
```
Insert permission through `dependencies` argument.

If you want to make your own permission, inherit `BasePermission` and implement `has_permission()` function.

**Note. In order to use swagger's authorize function, you must put `PermissionDependency` as an argument of `dependencies`.**

## Event dispatcher

Refer the README of https://github.com/teamhide/fastapi-event

## Cache

### Caching by prefix
```python
from core.helpers.cache import Cache


@Cache.cached(prefix="get_user", ttl=60)
async def get_user():
    ...
```

### Caching by tag
```python
from core.helpers.cache import Cache, CacheTag


@Cache.cached(tag=CacheTag.GET_USER_LIST, ttl=60)
async def get_user():
    ...
```

Use the `Cache` decorator to cache the return value of a function.

Depending on the argument of the function, caching is stored with a different value through internal processing.

### Custom Key builder

```python
from core.helpers.cache.base import BaseKeyMaker


class CustomKeyMaker(BaseKeyMaker):
    async def make(self, function: Callable, prefix: str) -> str:
        ...
```

If you want to create a custom key, inherit the BaseKeyMaker class and implement the make() method.

### Custom Backend

```python
from core.helpers.cache.base import BaseBackend


class RedisBackend(BaseBackend):
    async def get(self, key: str) -> Any:
        ...

    async def set(self, response: Any, key: str, ttl: int = 60) -> None:
        ...

    async def delete_startswith(self, value: str) -> None:
        ...
```

If you want to create a custom key, inherit the BaseBackend class and implement the `get()`, `set()`, `delete_startswith()` method.

Pass your custom backend or keymaker as an argument to init. (`/app/server.py`)

```python
def init_cache() -> None:
    Cache.init(backend=RedisBackend(), key_maker=CustomKeyMaker())
```

### Remove all cache by prefix/tag

```python
from core.helpers.cache import Cache, CacheTag


await Cache.remove_by_prefix(prefix="get_user_list")
await Cache.remove_by_tag(tag=CacheTag.GET_USER_LIST)
```

### ?????? ?????? ?????????

?????? 

[https://github.com/tiangolo/fastapi/issues/236#issuecomment-716548461](https://github.com/tiangolo/fastapi/issues/236#issuecomment-716548461)

[?????? ??????](https://github.com/raphaelauv/fastAPI-aiohttp-example/blob/master/src/fastAPI_aiohttp/fastAPI.py#L15)

[????????????, http client session??? ????????? ????????? ????????? ????????? ???](https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous)

```python
# ?????? api ??????

from http_client.client import Aiohttp

@router.post(
   "/url",
    response_model=ModelResponse,
    responses={"200": {"message": "done"}},
)
async def ext_request(body:BodyModel):
    body = body.dict()
    header = {
        "Authorization": "Bearer 1234123412341234",
        "Content-Type": "application/json"
    }
    result = await Aiohttp.query_url("http://127.0.0.1:8002/sample1", headers=header,data=json.dumps(body) ,result_type="json")
    return CustomORJSONResponse(BodyResponse(**{'code': "0000", "message": "success", "data": str(result)}).dict())
```

### session scope uuid, ??? for sqlalchemy ORM

- ?????? - [?????? ?????? ????????? ?????? ??????](https://www.hides.kr/1101)

> ????????? ?????? ???????????? ???????????? ????????? ???????????? ????????? ????????? ?????? ?????? ????????? ???????????? ?????? ???????????? ?????? [threading.local()](https://docs.python.org/ko/3/library/threading.html#threading.local)
 ?????? context var ??? ???????????? ?????????. 
- python context var document
> 

### Pydantic Request Model camelCase Conversion

```python
# api/.../request/...
from pydantic import BaseModel, BaseConfig
from core.utils import snake2camel

class SomeModel(BaseModel)
	log_id: str
	log_agent: str

	class Config(BaseConfig):
		allow_population_by_field_name = True  # This Option makes accept snake_case field.
		alias_generator = snake2camel # register camelCase auto generate func.
```

### Pydantic QueryModel

- pydantic validation error => RequestValidationError ??? ????????????

```python
# query schema

from pydantic import BaseModel, BaseConfig
from core.pydantic.base_model import QueryBaseModel
from core.utils import snake2camel

class SomeQueryModel(QueryBaseModel)
	log_id: str
	log_agent: str

	class Config(BaseConfig):
		alias_generator = snake2camel # register camelCase auto generating func.

# api

from fastapi import Depends
from ...schema import SomeQueryModel

@router.get(response_model = SomeModel)
def some_api(SomeQueryModel: Depends(SomeQueryModel.as_query)):
	data = some_service(...)
	return {"code": "0000", "message": "...", "data": data}

```

### CustomORJSONResponse

- [??????](https://fastapi.tiangolo.com/tutorial/encoder/?h=json#using-the-jsonable_encoder) ??????
- Response TypeError ?????????

```python
# core/fastapi/response/custom_response.py
# json_encoder_extend??? 
# ????????? ????????? ???????????? 

@router.get(response_model = SomeModel)
def some_api(...):
	data = some_service(...)
	return {"code": "0000", "message": "...", "data": data}

>>> ERROR: ValueError: [TypeError("'numpy.int64' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]

## ??????
from core.fastapi.response.custom_response import CustomORJSONResponse

@router.get(response_model = SomeModel)
def some_api(...):
	data = some_service(...)
	data = custom_jsonable_encoder(data)
	return CustomORJSONResponse(SomModel({"code": "0000", "message": "...", "data": data}).dict(by_alias=True))j

# .dict(by_alias=True), alias??? ????????? alias??? response ??????
```

### aiohttp auth ?????? ????????????

- ?????? ??????, ??????

### Folder path ??????

```bash
????????? README.md     # ???????????? ??????
????????? alembic.ini   # alembic ??????
????????? api           # API ??????
??????? ????????? auth      # ?????? AUTH ??????
??????? ??????? ????????? auth.py
??????? ??????? ????????? request
??????? ??????? ??????? ????????? auth.py
??????? ??????? ????????? response
??????? ???????     ????????? auth.py
??????? ????????? home      # ?????? ??? 
??????? ??????? ????????? home.py
??????? ????????? user      # ?????? Login, ??????
???????     ????????? v1
???????         ????????? request
???????         ??????? ????????? user.py
???????         ????????? response
???????         ??????? ????????? user.py
???????         ????????? user.py
???????????__init__.py   # API ahdma
????????? app    # resource??? ???????????? ??????, enum, models(SQLAlchmey Basemodel), schema(pydantic for Service), service(for logic)
??????? ????????? auth
??????? ????????? chart
??????? ??????? ????????? service.py
??????? ????????? server.py
??????? ????????? user
????????? celery_task/ # ????????? ?????? ??????
????????? core         # ???????????? ????????? ????????? ?????? ????????? ?????? 
??????? ????????? config.py  # config.yaml ????????? config class ??????
??????? ????????? db         # DB ??????
??????? ??????? ????????? mixins
??????? ??????? ??????? ????????? timestamp_mixin.py
??????? ??????? ????????? session.py
??????? ??????? ????????? standalone_session.py
??????? ??????? ????????? transactional.py
??????? ????????? exceptions  # ????????????
??????? ??????? ????????? base.py
??????? ??????? ????????? token.py
??????? ??????? ????????? user.py
??????? ????????? fastapi    # FASTAPI ????????? ?????????
??????? ??????? ????????? dependencies
??????? ??????? ??????? ????????? logging.py
??????? ??????? ??????? ????????? permission.py
??????? ??????? ????????? jsonable_encoder.py
??????? ??????? ????????? middlewares
??????? ??????? ??????? ????????? authentication.py
??????? ??????? ??????? ????????? sqlalchemy.py
??????? ??????? ????????? response
??????? ??????? ??????? ????????? custom_response.py
??????? ??????? ????????? schemas
??????? ???????     ????????? current_user.py
??????? ????????? helpers  # Helper ?????????
??????? ??????? ????????? cache
??????? ??????? ??????? ????????? base
??????? ??????? ??????? ??????? ????????? backend.py
??????? ??????? ??????? ??????? ????????? key_maker.py
??????? ??????? ??????? ????????? cache_manager.py
??????? ??????? ??????? ????????? cache_tag.py
??????? ??????? ??????? ????????? custom_key_maker.py
??????? ??????? ??????? ????????? redis_backend.py
??????? ??????? ????????? pandas.py
??????? ??????? ????????? redis.py
??????? ????????? http_client # ?????? ?????? ??????
??????? ??????? ????????? client.py
??????? ????????? pydantic   # pydantic ??????
??????? ??????? ????????? base_model.py
??????? ????????? repository  # Repository ??????
??????? ??????? ????????? base.py
??????? ??????? ????????? enum.py
??????? ????????? utils       # Util
???????     ????????? camelcase.py
???????     ????????? logger.py
???????     ????????? token_helper.py
????????? docker  # docker ??????
??????? ????????? api
??????? ??????? ????????? Dockerfile
??????? ??????? ????????? startup.sh
??????? ????????? db
??????? ??????? ????????? Dockerfile
??????? ????????? redis
???????     ????????? Dockerfile
????????? docker-compose.yml
????????? main.py   # ?????? ??????
????????? migrations  # alembic migration ??????
??????? ????????? README
??????? ????????? env.py
??????? ????????? script.py.mako
??????? ????????? versions
???????     ????????? 005ce6e94401_create_user_table.py
????????? poetry.lock   # python package managing
????????? pyproject.toml  # python package managing
????????? tests  # test 
    ????????? app
    ??????? ????????? user
    ???????     ????????? services
    ???????         ????????? test_user.py
    ????????? conftest.py
```

### ?????? ??????

```bash
$python --evn [local | dev | prod] --debug 

# --env ??? ?????? config.yaml ?????? ?????????
# --debug ?????????, True

# ?????? ????????? ?????? 
#	- config.yaml ???????????? ?????????
#	or
#	- config ???????????? overide

# dev is a configuration value for the docker environment
# local is a configuration value for the local environmen
```

### Config

```bash
Root Path??? Config.yaml ?????????
```

?????? ?????? ????????? pydantic Setting Model instance

### Logger

```python
from fastapi.logger import logger
...

# Production
logger.info("info message")

# Develop, Debug
logger.debug("debug message") 
```

### FastAPI Path Operation ??????

```python
response_model: Any = None, # response pydantic ??????
status_code: Optional[int] = None, # ?????? ?????? ?????? 200, 201, 202...
tags: Optional[List[Union[str, Enum]]] = None, # API ????????? ???
dependencies: Optional[Sequence[params.Depends]] = None, # API dependency, ?????? ?????? ?????? ????????????
summary: Optional[str] = None, # ??????, ??? ????????? ?????? ??????
description: Optional[str] = None, # API ??????
response_description: str = "Successful Response", # Response ??????
responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None, # Response ????????? ????????? ????????? ??????
deprecated: Optional[bool] = None, # ?????? ?????? ??????
operation_id: Optional[str] = None,  # openapi spec??? ?????? api ??? ID ??????
response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None, # response ?????? ?????? ???
response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None, # response ?????? ??? ???
response_model_by_alias: bool = True, # Response camelCase ?????? ??????, CustomORJSONResponse ????????? ?????? ?????????
response_model_exclude_unset: bool = False,  # ?????? ????????? ?????? ?????? ??????
response_model_exclude_defaults: bool = False,  # ??????  default??? ?????? ??? ?????? ??????
response_model_exclude_none: bool = False, # None??? ?????? ?????? 
include_in_schema: bool = True, # openapi spec ?????? ??????
response_class: Type[Response] = Default(JSONResponse), # ?????? ????????? ??????, ???????????? ?????? ?????? ??? ????????? ????????????.
name: Optional[str] = None, # API ??????
callbacks: Optional[List[BaseRoute]] = None, # openapi ?????? ?????? API ?????? ?????????
openapi_extra: Optional[Dict[str, Any]] = None, # openapi ??? ?????? key:value ???
generate_unique_id_function: Callable[[APIRoute], str] = Default(
generate_unique_id 
), # openapi ??? ID ?????????
```

### SQL Injection ?????? Query ??????

```python
# ?????? connector or cursor ?????????
query = "SELECT * FROM log_data.%s limit %s"
cursor.execute(query, [table_name, limit]) 
data = cursor.fetchall()

or 

query = "SELECT * FROM log_data.%(table_name)s limit %(limit)s"
cursor.execute(query, {"table_name": table_name, "limit": limit}) 
data = cursor.fetchall()

# Fastapi ?????? ?????????

from sqlalchemy import text
from psycopg2 import sql
from core.helpers.pandas import get_df_from_sql

param = {
	"table_name": sql.Identifier(table_name) #????????? ?????? ??????"" ??? ?????? ??????
	"limit": sql.Literal(limit) # ???????????????
}
query = "SELECT * FROM log_data.{table_name} limit {limit}").format(**param)
query = text(sql.SQL(query).format(**param)

data_df = await get_df_from_sql(text(query.as_string(AsyncEngine)), AsyncEngine)
```