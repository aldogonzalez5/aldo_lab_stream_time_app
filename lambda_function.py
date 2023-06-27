# 1. Import required functionality.

from corva import Api, Cache, Logger, StreamTimeEvent, stream
from constants import DATASET_PROVIDER, DATASET_NAME


# 2. - Decorate your function using @stream. Use the the existing lambda_handler function or define your own function. It must receive three argumets: event, api and cache. The arguments serve as building blocks for your app.

@stream
def lambda_handler(event: StreamTimeEvent, api: Api, cache: Cache):
    
# 3. Here is where you can declare your variables from the argument event: StreamTimeEvent and start using Api, Cache and Logger functionalities. You can obtain key values directly from metadata in the stream app event without making any additional API requests.

    # You have access to asset_id, company_id, and real-time data records from event.
    asset_id = event.asset_id
    company_id = event.company_id
    records = event.records

    # Records is a list
    record_count = len(records)

    # Each element of records has a timestamp. You can declare variables for start and end timestamps. 
    start_timestamp = records[0].timestamp
    end_timestamp = records[-1].timestamp

    # Utilize the Logger functionality. The default log level is Logger.info. To use a different log level, the log level must be specified in the manifest.json file in the "settings.environment": {"LOG_LEVEL": "DEBUG"}. See the Logger documentation for more information.
    Logger.info(f"{asset_id=} {company_id=}")
    Logger.info(f"{start_timestamp=} {end_timestamp=} {record_count=}")

    # Utililize the Cache functionality to get a set key value. The Cache functionality is built on Redis Cache. See the Cache documentation for more information.
    # Getting last exported timestamp from Cache 
    last_exported_timestamp = int(cache.get(key='last_exported_timestamp') or 0)

# 4. Here is where you can add your app logic.
    
    # Setting state to append data to an arrray 
    outputs = []
    for record in records:

        # Making sure we are not processing duplicate data
        if record.timestamp <= last_exported_timestamp:
            continue

        # Each element of records has data. This is how to get specific key values from an embedded object
        pump_spm_1 = record.data.get("pump_spm_1", 0)
        pump_spm_2 = record.data.get("pump_spm_2", 0)

        # This is how to set up a body of a POST request to store the hook_load and weight_on_bit data from the StreamTimeEvent and newly calculated wob_plus_hkld value 
        output = {
            "timestamp": record.timestamp,
            "asset_id": asset_id,
            "company_id": company_id,
            "provider": DATASET_PROVIDER,
            "collection": DATASET_NAME,
            "data": {
                "pump_spm_1": pump_spm_1,
                "pump_spm_2": pump_spm_2,
                "total_pump_spm": pump_spm_1 + pump_spm_2
            },
            "version": 1
        }

        # Appending the new data to the empty array
        outputs.append(output)

# 5. Save the newly calculated data in a custom dataset

    # Set up an if statement so that if request fails, lambda will be reinvoked. So no exception handling
    if outputs:
        # Utilize Logger functionality to confirm data in log files
        Logger.debug(f"{outputs=}")

        # Utilize the Api functionality. The data=outputs needs to be an an array because Corva's data is saved as an array of objects. Objects being records. See the Api documentation for more information.
        api.post(
            f"api/v1/data/{DATASET_PROVIDER}/{DATASET_NAME}/", data=outputs,
        ).raise_for_status()

        # Utililize the Cache functionality to set a key value. The Cache functionality is built on Redis Cache. See the Cache documentation for more information. This example is setting the last timestamp of the output to Cache
        cache.set(key='last_exported_timestamp', value=outputs[-1].get("timestamp"))

    return outputs