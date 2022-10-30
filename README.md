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

### 외부 요청 보내기

참고 

[https://github.com/tiangolo/fastapi/issues/236#issuecomment-716548461](https://github.com/tiangolo/fastapi/issues/236#issuecomment-716548461)

[구현 참고](https://github.com/raphaelauv/fastAPI-aiohttp-example/blob/master/src/fastAPI_aiohttp/fastAPI.py#L15)

[주의사항, http client session은 하나의 이벤트 루프에 있어야 함](https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous)

```python
# 외부 api 요청

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

### session scope uuid, ⇒ for sqlalchemy ORM

- 설명 - [원본 저자 블로그 내용 참고](https://www.hides.kr/1101)

> 상태가 있는 컨텍스트 관리자는 동시성 코드에서 상태가 예기치 않게 다른 코드로 유출되는 것을 방지하기 위해 [threading.local()](https://docs.python.org/ko/3/library/threading.html#threading.local)
 대신 context var 를 사용해야 합니다. 
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

- pydantic validation error => RequestValidationError 로 변환하기

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

- [설명](https://fastapi.tiangolo.com/tutorial/encoder/?h=json#using-the-jsonable_encoder) 참고
- Response TypeError 발생시

```python
# core/fastapi/response/custom_response.py
# json_encoder_extend에 
# 타입별 정리법 정리하기 

@router.get(response_model = SomeModel)
def some_api(...):
	data = some_service(...)
	return {"code": "0000", "message": "...", "data": data}

>>> ERROR: ValueError: [TypeError("'numpy.int64' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]

## 적용
from core.fastapi.response.custom_response import CustomORJSONResponse

@router.get(response_model = SomeModel)
def some_api(...):
	data = some_service(...)
	data = custom_jsonable_encoder(data)
	return CustomORJSONResponse(SomModel({"code": "0000", "message": "...", "data": data}).dict(by_alias=True))j

# .dict(by_alias=True), alias가 있으면 alias로 response 나감
```

### aiohttp auth 인증 미들웨어

- 구현 안함, 차후

### Folder path 설명

```bash
├── README.md     # 프로젝트 설명
├── alembic.ini   # alembic 정보
├── api           # API 구현
│   ├── auth      # 유저 AUTH 참고
│   │   ├── auth.py
│   │   ├── request
│   │   │   └── auth.py
│   │   └── response
│   │       └── auth.py
│   ├── home      # 기본 홈 
│   │   └── home.py
│   └── user      # 유저 Login, 등등
│       └── v1
│           ├── request
│           │   └── user.py
│           ├── response
│           │   └── user.py
│           └── user.py
├── __init__.py   # API ahdma
├── app    # resource별 필요코드 모음, enum, models(SQLAlchmey Basemodel), schema(pydantic for Service), service(for logic)
│   ├── auth
│   ├── chart
│   │   └── service.py
│   ├── server.py
│   └── user
├── celery_task/ # 샐러리 관련 폴더
├── core         # 프로젝트 구성에 필요한 공통 코드들 정리 
│   ├── config.py  # config.yaml 읽어서 config class 구성
│   ├── db         # DB 구성
│   │   ├── mixins
│   │   │   └── timestamp_mixin.py
│   │   ├── session.py
│   │   ├── standalone_session.py
│   │   └── transactional.py
│   ├── exceptions  # 예외모음
│   │   ├── base.py
│   │   ├── token.py
│   │   └── user.py
│   ├── fastapi    # FASTAPI 관련된 코드들
│   │   ├── dependencies
│   │   │   ├── logging.py
│   │   │   └── permission.py
│   │   ├── jsonable_encoder.py
│   │   ├── middlewares
│   │   │   ├── authentication.py
│   │   │   └── sqlalchemy.py
│   │   ├── response
│   │   │   └── custom_response.py
│   │   └── schemas
│   │       └── current_user.py
│   ├── helpers  # Helper 함수들
│   │   ├── cache
│   │   │   ├── base
│   │   │   │   ├── backend.py
│   │   │   │   └── key_maker.py
│   │   │   ├── cache_manager.py
│   │   │   ├── cache_tag.py
│   │   │   ├── custom_key_maker.py
│   │   │   └── redis_backend.py
│   │   ├── pandas.py
│   │   └── redis.py
│   ├── http_client # 외부 요청 구현
│   │   └── client.py
│   ├── pydantic   # pydantic 관련
│   │   └── base_model.py
│   ├── repository  # Repository 관련
│   │   ├── base.py
│   │   └── enum.py
│   └── utils       # Util
│       ├── camelcase.py
│       ├── logger.py
│       └── token_helper.py
├── docker  # docker 관련
│   ├── api
│   │   ├── Dockerfile
│   │   └── startup.sh
│   ├── db
│   │   └── Dockerfile
│   └── redis
│       └── Dockerfile
├── docker-compose.yml
├── main.py   # 구동 파일
├── migrations  # alembic migration 정리
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 005ce6e94401_create_user_table.py
├── poetry.lock   # python package managing
├── pyproject.toml  # python package managing
└── tests  # test 
    ├── app
    │   └── user
    │       └── services
    │           └── test_user.py
    └── conftest.py
```

### 구동 설명

```bash
$python --evn [local | dev | prod] --debug 

# --env 에 따라 config.yaml 세팅 가져옴
# --debug 입력시, True

# 추후 환경들 분리 
#	- config.yaml 환경별로 쪼개기
#	or
#	- config 환경별로 overide

# dev is a configuration value for the docker environment
# local is a configuration value for the local environmen
```

### Config

```bash
Root Path에 Config.yaml 필요함
```

해당 내용 적용된 pydantic Setting Model instance

### Logger

```python
from fastapi.logger import logger
...

# Production
logger.info("info message")

# Develop, Debug
logger.debug("debug message") 
```

### FastAPI Path Operation 설명

```python
response_model: Any = None, # response pydantic 모델
status_code: Optional[int] = None, # 정상 응답 코드 200, 201, 202...
tags: Optional[List[Union[str, Enum]]] = None, # API 그룹화 키
dependencies: Optional[Sequence[params.Depends]] = None, # API dependency, 유저 권한 등등 설정가능
summary: Optional[str] = None, # 설명, 값 없으면 함수 이름
description: Optional[str] = None, # API 설명
response_description: str = "Successful Response", # Response 설명
responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None, # Response 코드와 옵션들 여러개 입력
deprecated: Optional[bool] = None, # 버전 지원 안내
operation_id: Optional[str] = None,  # openapi spec을 위한 api 별 ID 생성
response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None, # response 모델 넣을 값
response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None, # response 모델 뺄 값
response_model_by_alias: bool = True, # Response camelCase 변환 여부, CustomORJSONResponse 사용시 상관 없어짐
response_model_exclude_unset: bool = False,  # 값이 지정된 것만 반환 여부
response_model_exclude_defaults: bool = False,  # 값이  default와 같은 것 제외 여부
response_model_exclude_none: bool = False, # None값 제외 여부 
include_in_schema: bool = True, # openapi spec 포함 여부
response_class: Type[Response] = Default(JSONResponse), # 응답 클래스 지정, 클래스에 따라 반환 값 형태를 지정한다.
name: Optional[str] = None, # API 이름
callbacks: Optional[List[BaseRoute]] = None, # openapi 외부 요청 API 문서 만들기
openapi_extra: Optional[Dict[str, Any]] = None, # openapi 용 기타 key:value 값
generate_unique_id_function: Callable[[APIRoute], str] = Default(
generate_unique_id 
), # openapi 용 ID 생성기
```

### SQL Injection 방지 Query 작성

```python
# 일반 connector or cursor 사용시
query = "SELECT * FROM log_data.%s limit %s"
cursor.execute(query, [table_name, limit]) 
data = cursor.fetchall()

or 

query = "SELECT * FROM log_data.%(table_name)s limit %(limit)s"
cursor.execute(query, {"table_name": table_name, "limit": limit}) 
data = cursor.fetchall()

# Fastapi 에서 적용시

from sqlalchemy import text
from psycopg2 import sql
from core.helpers.pandas import get_df_from_sql

param = {
	"table_name": sql.Identifier(table_name) #테이블 네임 같이"" 로 싸는 밸류
	"limit": sql.Literal(limit) # 단순데이터
}
query = "SELECT * FROM log_data.{table_name} limit {limit}").format(**param)
query = text(sql.SQL(query).format(**param)

data_df = await get_df_from_sql(text(query.as_string(AsyncEngine)), AsyncEngine)
```