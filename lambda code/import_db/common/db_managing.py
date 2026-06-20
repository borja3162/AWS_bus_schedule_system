import boto3



AWS_REGION = "eu-south-2"
TABLE_NAME = "BusData"
_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def get_db_table():
    
    _table = _dynamodb.Table(TABLE_NAME)
    return _table


def get_active_dataset():
    _table = get_db_table()
    response = _table.get_item(
        Key={
            "PK": "CONFIG",
            "SK": "ACTIVE_DATASET"
        }
    )

    item = response.get("Item")

    if not item:
        raise Exception("ACTIVE_DATASET not found")

    return item["dataset_id"]


# filter query results to only include  elements of a given update/version of the database
def filter_by_dataset(items, dataset_id):
    return [
        item for item in items
        if item.get("dataset_id") == dataset_id
    ]