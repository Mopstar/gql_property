import os
import socket
import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from strawberry.fastapi import GraphQLRouter

import logging
import logging.handlers

from src.GraphTypeDefinitions import schema
from DBDefinitions import startEngine, ComposeConnectionString
from src.DBFeeder import initDB

# region logging setup

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s.%(msecs)03d\t%(levelname)s:\t%(message)s', 
    datefmt='%Y-%m-%dT%I:%M:%S')
SYSLOGHOST = os.getenv("SYSLOGHOST", None)
if SYSLOGHOST is not None:
    [address, strport, *_] = SYSLOGHOST.split(':')
    assert len(_) == 0, f"SYSLOGHOST {SYSLOGHOST} has unexpected structure, try `localhost:514` or similar (514 is UDP port)"
    port = int(strport)
    my_logger = logging.getLogger()
    my_logger.setLevel(logging.INFO)
    handler = logging.handlers.SysLogHandler(address=(address, port), socktype=socket.SOCK_DGRAM)
    #handler = logging.handlers.SocketHandler('10.10.11.11', 611)
    my_logger.addHandler(handler)

# endregion

# region DB setup

## Definice GraphQL typu (pomoci strawberry https://strawberry.rocks/)
## Strawberry zvoleno kvuli moznosti mit federovane GraphQL API (https://strawberry.rocks/docs/guides/federation, https://www.apollographql.com/docs/federation/)
## Definice DB typu (pomoci SQLAlchemy https://www.sqlalchemy.org/)
## SQLAlchemy zvoleno kvuli moznost komunikovat s DB asynchronne
## https://docs.sqlalchemy.org/en/14/core/future.html?highlight=select#sqlalchemy.future.select


## Zabezpecuje prvotni inicializaci DB a definovani Nahodne struktury pro "Univerzity"
# from gql_workflow.DBFeeder import createSystemDataStructureRoleTypes, createSystemDataStructureGroupTypes

connectionString = ComposeConnectionString()

def singleCall(asyncFunc):
    """Dekorator, ktery dovoli, aby dekorovana funkce byla volana (vycislena) jen jednou. Navratova hodnota je zapamatovana a pri dalsich volanich vracena.
    Dekorovana funkce je asynchronni.
    """
    resultCache = {}

    async def result():
        if resultCache.get("result", None) is None:
            resultCache["result"] = await asyncFunc()
        return resultCache["result"]

    return result

@singleCall
async def RunOnceAndReturnSessionMaker():
    """Provadi inicializaci asynchronniho db engine, inicializaci databaze a vraci asynchronni SessionMaker.
    Protoze je dekorovana, volani teto funkce se provede jen jednou a vystup se zapamatuje a vraci se pri dalsich volanich.
    """

    makeDrop = os.getenv("DEMO", None) == "True"
    logging.info(f'starting engine for "{connectionString} makeDrop={makeDrop}"')

    result = await startEngine(
        connectionstring=connectionString, makeDrop=makeDrop, makeUp=True
    )   
    assert result is not None, "Unable to start engine"
    ###########################################################################################################################
    #
    # zde definujte do funkce asyncio.gather
    # vlozte asynchronni funkce, ktere maji data uvest do prvotniho konzistentniho stavu
    async def initDBAndReport():
        logging.info(f"initializing system structures")
        await initDB(result)
        logging.info(f"all done")
        print(f"all done")

    # asyncio.create_task(coro=initDBAndReport())
    await initDBAndReport()

    #
    #
    ###########################################################################################################################
    
    return result

# endregion

# region FastAPI setup
async def get_context(request: Request):
    """Build GraphQL context with UG service integration.
    
    Context includes:
    - request: FastAPI Request object
    - auth_header: JWT token from Authorization header or cookies
    - ug_client: Async function to query external User-Group service
    - user: Resolved user from UG service (id, fullname, email, roles)
    - session: AsyncSession (added by SessionCommitExtensionFactory)
    - loaders: LoaderMap (added by SessionCommitExtensionFactory)
    
    Authentication Flow:
    1. Extract JWT token from Authorization header or cookies
    2. Forward token to UG service to resolve user
    3. Get user's roles with group hierarchy
    4. Store user data in context for authorization extensions
    """
    import httpx
    
    asyncSessionMaker = await RunOnceAndReturnSessionMaker()
        
    from src.Dataloaders import createLoadersContext
    context = createLoadersContext(asyncSessionMaker)

    result = {**context}
    result["request"] = request
    
    # ===========================================================================================
    # Extract JWT token from Authorization header or cookies
    # ===========================================================================================
    auth_header = None
    try:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    except Exception:
        auth_header = None
    
    if auth_header:
        result.setdefault('auth_header', auth_header)
    else:
        # Try common cookie names from frontend login flow
        try:
            cookies = getattr(request, 'cookies', {}) or {}
            for ck in ('access_token', 'accessToken', 'token', 'AUTH_TOKEN', 'authorization'):
                if ck in cookies and cookies.get(ck):
                    token_val = cookies.get(ck)
                    # Normalize to Bearer <token>
                    if not token_val.lower().startswith('bearer '):
                        token_val = 'Bearer ' + token_val
                    result.setdefault('auth_header', token_val)
                    break
        except Exception:
            pass

    # ===========================================================================================
    # Create UG service client helper
    # ===========================================================================================
    async def _ug_client(query, variables=None):
        """Helper to query external User-Group GraphQL service.
        
        Forwards Authorization header from incoming request to UG service.
        Used by authorization extensions to load user roles.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            dict: GraphQL response from UG service
        """
        try:
            headers = {"Content-Type": "application/json"}
            if result.get('auth_header'):
                headers['Authorization'] = result.get('auth_header')
            
            endpoint = os.getenv('GQLUG_ENDPOINT_URL')
            if not endpoint:
                logging.warning('GQLUG_ENDPOINT_URL not configured')
                return {"errors": ["UG service not configured"]}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    endpoint, 
                    json={"query": query, "variables": variables or {}}, 
                    headers=headers
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logging.debug(f"UG client call failed: {e}")
            return {"errors": [str(e)]}

    result['ug_client'] = _ug_client

    # ===========================================================================================
    # Resolve current user from UG service
    # ===========================================================================================
    # Query includes full role structure: group hierarchy + role types
    # Extensions use this for authorization checks
    try:
        me_resp = await _ug_client('''query { 
            me { 
                id 
                fullname 
                email 
                roles {
                    group {
                        id
                        name
                        mastergroupId
                    }
                    roletype {
                        id
                        name
                    }
                }
            } 
        }''')
        me = None
        if isinstance(me_resp, dict):
            me = me_resp.get('data', {}).get('me')
        if me:
            result.setdefault('user', me)
            logging.info(f"User authenticated: {me.get('id')} - {me.get('fullname')}")
    except Exception as e:
        logging.debug(f"Failed to resolve user: {e}")
    
    return result

innerlifespan = None
@asynccontextmanager
async def dummy(app: FastAPI):
    yield 

@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.DBFeeder import backupDB
    icm = dummy if innerlifespan is None else innerlifespan
    async with icm(app):
        print(f"FastAPI.lifespan {innerlifespan is None}")
        initizalizedEngine = await RunOnceAndReturnSessionMaker()
        try:
            yield
        finally:
            pass
        await backupDB(initizalizedEngine)
    
    # print("App shutdown, nothing to do")

app = FastAPI(lifespan=lifespan)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context
)

from uoishelpers.schema import SessionCommitExtensionFactory
from src.Dataloaders import createLoadersContext
schema.extensions.append(
    SessionCommitExtensionFactory(session_maker_factory=RunOnceAndReturnSessionMaker, loaders_factory=createLoadersContext)
)


app.include_router(graphql_app, prefix="/gql")

@app.get("/voyager", response_class=FileResponse)
async def graphiql():
    realpath = os.path.realpath("./src/Htmls/voyager.html")
    return realpath

@app.get("/doc", response_class=FileResponse)
async def graphiql():
    realpath = os.path.realpath("./src/Htmls/liveschema.html")
    return realpath

@app.get("/ui", response_class=FileResponse)
async def graphiql():
    realpath = os.path.realpath("./src/Htmls/livedata.html")
    return realpath

@app.get("/test", response_class=FileResponse)
async def graphiql():
    realpath = os.path.realpath("./src/Htmls/tests.html")
    return realpath

import prometheus_client
@app.get("/metrics")
async def metrics():
    return Response(
        content=prometheus_client.generate_latest(), 
        media_type=prometheus_client.CONTENT_TYPE_LATEST
        )


logging.info("All initialization is done")

# @app.get('/hello')
# def hello():
#    return {'hello': 'world'}

###########################################################################################################################
#
# pokud jste pripraveni testovat GQL funkcionalitu, rozsirte apollo/server.js
#
###########################################################################################################################
# endregion

# region ENV setup tests
def envAssertDefined(name, default=None):
    result = os.getenv(name, default)
    assert result is not None, f"{name} environment variable must be explicitly defined"
    return result

DEMO = envAssertDefined("DEMO", "True")
GQLUG_ENDPOINT_URL = envAssertDefined("GQLUG_ENDPOINT_URL", "http://localhost:8000/graphql")

assert (DEMO in ["True", "true", "False", "false"]), "DEMO environment variable can have only `True` or `False` values"
DEMO = DEMO in ["True", "true"]

if DEMO:
    print("####################################################")
    print("#                                                  #")
    print("# RUNNING IN DEMO                                  #")
    print("#                                                  #")
    print("####################################################")

    logging.info("####################################################")
    logging.info("#                                                  #")
    logging.info("# RUNNING IN DEMO                                  #")
    logging.info("#                                                  #")
    logging.info("####################################################")
else:
    print("####################################################")
    print("#                                                  #")
    print("# RUNNING DEPLOYMENT                               #")
    print("#                                                  #")
    print("####################################################")

    logging.info("####################################################")
    logging.info("#                                                  #")
    logging.info("# RUNNING DEPLOYMENT                               #")
    logging.info("#                                                  #")
    logging.info("####################################################")    

logging.info(f"DEMO = {DEMO}")
logging.info(f"SYSLOGHOST = {SYSLOGHOST}")
logging.info(f"GQLUG_ENDPOINT_URL = {GQLUG_ENDPOINT_URL}")

# endregion
