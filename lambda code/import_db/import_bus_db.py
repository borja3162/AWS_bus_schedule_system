
import json
import boto3
import traceback
from datetime import datetime, timezone

from common.db_managing import get_db_table


def lambda_handler(event, context):

    print("========== LAMBDA START ==========")

    table = get_db_table()
    print("[DEBUG] TABLE NAME =", table.table_name)
    print("[DEBUG] TABLE ARN =", table.table_arn)

    s3 = boto3.client("s3")

    try:
        # reading data from S3
        #######################
        record = event["Records"][0]

        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        print("[S3] bucket =", bucket)
        print("[S3] key =", key)

        response = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(response["Body"].read().decode("utf-8"))

        # ID based on time for version control
        dataset_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        print("[IMPORT] dataset_id =", dataset_id)

        routes = data.get("routes", [])
        print("[IMPORT] routes count =", len(routes))

        written = 0

        # processing data from schedule document
        #######################

        for i, route in enumerate(routes):

            route_id = route.get("route_id")
            trips = route.get("trips", [])

            print(f"[ROUTE {i}] route_id = {route_id}, trips = {len(trips)}")

            for j, trip in enumerate(trips):

                trip_id = trip.get("trip_id")
                stops = trip.get("stops", [])

                print(f"  [TRIP {j}] trip_id = {trip_id}, stops = {len(stops)}")

                for k, stop in enumerate(stops):

                    stop_id = stop.get("stop_id")
                    stop_name = stop.get("stop_name")
                    stop_time = stop.get("time")

                    print(f"    [STOP {k}] stop_id={stop_id}, time={stop_time}")

                    if not stop_id or not stop_time:
                        print("[WARN] skipping invalid stop")
                        continue

                    # destination extraction
                    try:
                        destination = trip["stops"][-1].get("stop_name")
                    except Exception:
                        destination = None

                    # element creation
                    #######################3
                    stop_item = {
                        "PK": f"STOP#{stop_id}",
                        "SK": f"TIME#{stop_time}",
                        "dataset_id": dataset_id,
                        "route": route_id,
                        "trip_id": trip_id,
                        "destination": destination
                    }

                    trip_item = {
                        "PK": f"TRIP#{trip_id}",
                        "SK": f"STOP#{stop_id}",
                        "dataset_id": dataset_id,
                        "stop_name": stop_name,
                        "time": stop_time
                    }
                    # element writing
                    #########################

                    # WRITE STOP ITEM
                    print(">>> WRITING STOP ITEM")
                    print(stop_item)

                    try:
                        table.put_item(Item=stop_item)
                        written += 1
                        print("[WRITE OK] STOP")

                    except Exception as e:
                        print("[WRITE ERROR] STOP")
                        print(str(e))
                        raise

                    
                    # WRITE TRIP ITEM
                    print(">>> WRITING TRIP ITEM")
                    print(trip_item)

                    try:
                        table.put_item(Item=trip_item)
                        written += 1
                        print("[WRITE OK] TRIP")

                    except Exception as e:
                        print("[WRITE ERROR] TRIP")
                        print(str(e))
                        raise

        #  WRITE METADATA/CONFIG
        print(">>> WRITING ACTIVE DATASET")

        table.put_item(Item={
            "PK": "CONFIG",
            "SK": "ACTIVE_DATASET",
            "dataset_id": dataset_id
        })

        print("[IMPORT] TOTAL WRITTEN =", written)
        print("========== LAMBDA SUCCESS ==========")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Import completed",
                "written": written
            })
        }

    except Exception as e:
        print("========== LAMBDA FATAL ERROR ==========")
        print(str(e))
        print(traceback.format_exc())
        raise