import os
import datetime
import uuid

from functools import cache
from uoishelpers.feeders import ImportModels
from uoishelpers.dataloaders import readJsonFile

from src.DBDefinitions import (
    EventModel,
    EventInvitationModel,
    PurchaseModel,
    PurchaseItem,
)


def _parse_datetime(value):
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime.datetime):
        return value
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _normalize_purchase_seed_data(json_data):
    for row in json_data.get("purchases_evolution", []):
        for field in ["handover_request", "requested_delivery", "submitted_at", "created", "lastchange"]:
            if field in row:
                row[field] = _parse_datetime(row[field])
        row.setdefault("status", "draft")

    for row in json_data.get("purchase_items_evolution", []):
        for field in ["created", "lastchange"]:
            if field in row:
                row[field] = _parse_datetime(row[field])


async def _ensure_sample_purchases(asyncSessionMaker):
    import sqlalchemy

    async with asyncSessionMaker() as session:
        result = await session.execute(
            sqlalchemy.select(sqlalchemy.func.count(PurchaseModel.id))
        )
        count = result.scalar_one()
        if count > 0:
            return

        now = datetime.datetime.utcnow()
        sample_purchase = PurchaseModel(
            reason="Nakup noveho pracovniho vybaveni",
            description="Zadost o porizeni notebooku a prislusenstvi pro noveho zamestnance.",
            status="submitted",
            requested_delivery=now + datetime.timedelta(days=14),
            submitted_at=now,
            requester_id=uuid.UUID("2d9dc5ca-a4a2-11ed-b9df-0242ac120003"),
            approver_id=uuid.UUID("45b2df80-ae0f-11ed-9bd8-0242ac110002"),
        )
        sample_purchase.subinfo.extend(
            [
                PurchaseItem(
                    name="Firemni notebook",
                    quantity=1,
                    price=32500.0,
                ),
                PurchaseItem(
                    name="Dokovaci stanice",
                    quantity=1,
                    price=4500.0,
                ),
                PurchaseItem(
                    name='Externi monitor 27"',
                    quantity=2,
                    price=5200.0,
                ),
            ]
        )
        session.add(sample_purchase)
        await session.flush()
        await session.commit()


get_demodata = lambda: readJsonFile(jsonFileName="./systemdata.json")


async def initDB(asyncSessionMaker, filename="./systemdata.json"):

    dbModels = [
    ]

    isDemo = os.environ.get("DEMODATA", None) in ["True", "true", True]
    if isDemo:
        print("Demo mode", flush=True)
        dbModels = [
            EventModel,
            EventInvitationModel,
            PurchaseModel,
            PurchaseItem,
        ]

    jsonData = readJsonFile(filename)
    _normalize_purchase_seed_data(jsonData)
    await ImportModels(asyncSessionMaker, dbModels, jsonData)

    if isDemo:
        await _ensure_sample_purchases(asyncSessionMaker)

    print("Data initialized", flush=True)

async def backupDB(asyncSessionMaker, filename="./systemdata.backup.json"):
    import sqlalchemy
    import dataclasses
    import json
    from src.DBDefinitions.BaseModel import IDType

    dbModels = [
        EventModel,
        EventInvitationModel,
        PurchaseModel,
        PurchaseItem,
    ]
    data = []
    async with asyncSessionMaker() as session:
        for model in dbModels:
            sqlquery = sqlalchemy.select(model)
            rows = await session.execute(sqlquery)
            # vsechny radky do dict
            rowsdict = {}
            for row in rows:
                # print(row)
                asdict = dataclasses.asdict(row[0])
                id = asdict.get("id", None)
                if id is None: continue
                rowsdict[id] = asdict
            # vsechny primarn�� klice do ids
            ids = set(rowsdict.keys())
            todo = set()
            done = set()
            chunk_id = 0
            while len(done) < len(ids):
                for row in rowsdict.values():
                    id = row.get("id", None)
                    if id in done: continue
                    skip_this_id = False
                    for key, value in row.items():
                        if key == "id": continue
                        # if not isinstance(value, IDType): continue
                        if value is None: continue
                        if value not in ids: continue
                        if value not in done: 
                            # print(row, key, value)
                            skip_this_id = True
                            break
                            # primarni klic je zpracovatelny, nemame zavislost na nezpracovanych klicich
                    if skip_this_id: continue
                    row["_chunk"] = chunk_id
                    todo.add(id)
                print(f"{model.__tablename__} chunk {chunk_id} todo/done/all {len(todo)}/{len(done)}/{len(ids)}")
                if len(todo) == 0: break
                done = done.union(todo)
                todo = set()
                chunk_id += 1
            data.append({
                model.__tablename__: list(rowsdict.values())
            })
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False, default=str)
    
    print("backup done", flush=True)
