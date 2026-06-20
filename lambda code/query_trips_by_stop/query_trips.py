import json
import os


from common.db_managing import get_active_dataset, get_db_table , filter_by_dataset
from boto3.dynamodb.conditions import Key



# extracts relevant query input from several different possibilities
# different AWS mechanisms encode input differently
def extract_id_param(event, matching_str ="stop_id" ):

    # 1. Path parameters
    path_params = event.get("pathParameters") or {}

    if matching_str in path_params:
        return path_params[matching_str]

    # 2. Query string parameters
    query_params = event.get("queryStringParameters") or {}

    if matching_str in query_params:
        return query_params[matching_str]

    # 3. JSON body
    body = event.get("body")

    if body:
        try:
            parsed_body = json.loads(body)

            if matching_str in parsed_body:
                return parsed_body[matching_str]

        except json.JSONDecodeError:
            pass

    return None









# simple query for all elements of table with for a given trip (route  at a given time)
def query_trips_by_stop_id(table, stop_id):
    return  table.query(
        KeyConditionExpression=Key("PK").eq(f"STOP#{stop_id}")
    ).get("Items", [])




def query_active_trips_by_stop_id(table, stop_id, active_dataset_id):
    

    items = query_trips_by_stop_id(table, stop_id)
    filtered = filter_by_dataset(items, active_dataset_id)
    return filtered






def lambda_handler(event, context):


    table = get_db_table()

    ##### Parse input
    stop_id = extract_id_param(event)

    if not stop_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "stop_id is required"})
        }

    ##### query database and filter results
    dataset_id = get_active_dataset()
    filtered =  query_active_trips_by_stop_id(table, stop_id,dataset_id)

    ##### return results   
    return {
        "statusCode": 200,
        "body": json.dumps({
            "stop_id": stop_id,
            # "dataset_id": dataset_id,
            "count": len(filtered),
            "items": filtered
        })
    }



